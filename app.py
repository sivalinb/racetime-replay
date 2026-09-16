"""Run: streamlit run app.py. Raw media stays in this process and session directory."""

import hashlib
import io
import json
import os
import shutil
import time
import uuid
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from replay.agent import build_agent, investigate
from replay.analysis import align, summarize
from replay.heart_rate import DEMO_ZONES, HeartRateZones
from replay.ingest import load_csv, load_gpx, load_health_xml, merge_health_route
from replay.observability import trace_session
from replay.performance import clock, performance_review
from replay.player import player_html
from replay.retrieval import EvidenceIndex, documents
from replay.vision import analyze_video, thumbnail

ROOT = Path(__file__).parent
load_dotenv(ROOT / ".env")
# Raw LangGraph state must never be automatically traced.
os.environ["LANGSMITH_TRACING"] = "false"
presentation_mode = st.query_params.get("present") == "1"
st.set_page_config(
    page_title="RaceTime Replay",
    page_icon="▶",
    layout="wide",
    initial_sidebar_state="collapsed" if presentation_mode else "expanded",
)
if st.query_params.get("story") == "1":
    from replay.story import render_story

    render_story(ROOT)
    st.stop()

st.markdown(
    """<style>
.stApp{background:#f7f5ef}header[data-testid="stHeader"]{background:#f7f5ef}
.block-container{padding-top:2rem;max-width:1320px}h1,h2,h3{color:#173a40!important}
[data-testid="stMetric"]{background:white;border:1px solid #e2e8e2;padding:16px;border-radius:12px}
[data-testid="stSidebar"]{background:#edf0e8}.eyebrow{font-size:12px;letter-spacing:2px;color:#55766d;font-weight:700}
.hero{padding:6px 0 22px}.hero h1{font-size:46px;margin:0}.hero p{font-size:18px;color:#60736d;max-width:780px}
</style><div class="hero"><div class="eyebrow">RACETIME / REPLAY LAB</div><h1>See the run behind the numbers.</h1><p>Connect your video with your workout. Find the moments worth reviewing, follow the evidence, and understand what remains uncertain.</p></div>""",
    unsafe_allow_html=True,
)

if presentation_mode:
    st.markdown(
        """<style>.hero{display:none}.block-container{padding-top:3rem}
    [data-testid="stHeader"]{height:2rem}</style>""",
        unsafe_allow_html=True,
    )

if "sid" not in st.session_state:
    st.session_state.sid = uuid.uuid4().hex
runtime = ROOT / ".runtime" / st.session_state.sid
runtime.mkdir(parents=True, exist_ok=True)
# Retention: remove abandoned session directories after 24 hours.
for old in runtime.parent.iterdir():
    if old.is_dir() and old != runtime and time.time() - old.stat().st_mtime > 86400:
        shutil.rmtree(old, ignore_errors=True)

with st.sidebar:
    st.markdown("### Your replay")
    choices = ["Explore demo"]
    if os.getenv("REPLAY_ALLOW_UPLOADS", "true").lower() == "true":
        choices.append("Upload my recording")
    source = st.radio("Recording source", choices)
    st.caption(
        "Garmin · COROS · Suunto · Apple Watch. Use a compatible CSV/GPX export; "
        "Apple Health XML is also supported. No direct watch-account connection. "
        "Video: MP4/MOV, up to 15 minutes and 150 MB."
    )
    video_path = ROOT / "demo/replay-demo.mp4"
    workout_path = ROOT / "demo/workout.csv"
    mountain_demo = False
    if source == "Explore demo":
        examples = ["Diagnostic motion fixture"]
        if (ROOT / "demo/mountain-pov.mp4").exists():
            examples.insert(0, "Mountain trail POV")
        mountain_demo = st.selectbox("Demo recording", examples) == "Mountain trail POV"
        if mountain_demo:
            video_path = ROOT / "demo/mountain-pov.mp4"
            workout_path = ROOT / "demo/mountain-workout.csv"
    workout = None
    if source == "Upload my recording":
        video = st.file_uploader("Runner video", type=["mp4", "mov"])
        data = st.file_uploader("Workout data", type=["csv", "gpx", "xml"])
        health = st.file_uploader("Optional Health XML to combine with GPX", type=["xml"])
        if not video or not data:
            st.info(
                "Add a video and workout file to begin. Demo mode is available without uploads."
            )
            st.stop()
        if video.size > 150 * 1024 * 1024:
            st.error("Trim or compress this video below 150 MB.")
            st.stop()
        video_path = runtime / (
            hashlib.sha256(video.getvalue()).hexdigest() + Path(video.name).suffix.lower()
        )
        if not video_path.exists() or video_path.stat().st_size != video.size:
            video_path.write_bytes(video.getvalue())
        try:
            suffix = Path(data.name).suffix.lower()
            if suffix == ".csv":
                workout = load_csv(io.BytesIO(data.getvalue()))
            elif suffix == ".gpx":
                workout = load_gpx(io.BytesIO(data.getvalue()))
            else:
                start = st.text_input("Workout start ISO timestamp (UTC or with timezone)", "")
                end = st.text_input("Workout end ISO timestamp (UTC or with timezone)", "")
                if not start or not end:
                    st.info("Choose the workout time range before reading Health XML.")
                    st.stop()
                workout = load_health_xml(io.BytesIO(data.getvalue()), start, end)
            if health and suffix == ".gpx":
                hr = load_health_xml(
                    io.BytesIO(health.getvalue()), workout.timestamp.min(), workout.timestamp.max()
                )
                workout = merge_health_route(workout, hr)
        except Exception as e:
            st.error(str(e))
            st.stop()
    else:
        workout = load_csv(workout_path)
    zone_options = ["No zone profile", "My watch's zone thresholds"]
    if mountain_demo:
        zone_options.insert(0, "Illustrative demo zones")
    zone_mode = st.selectbox("Heart-rate zone profile", zone_options)
    zone_profile = None
    if zone_mode == "Illustrative demo zones":
        zone_profile = DEMO_ZONES
    elif zone_mode == "My watch's zone thresholds":
        with st.expander("Enter your zone boundaries", expanded=True):
            st.caption("Copy the lower bounds for zones 2–5 from your own watch profile.")
            bounds = tuple(
                st.number_input(
                    f"Zone {z} begins at (bpm)",
                    min_value=26,
                    max_value=249,
                    value=default,
                    key=f"zone_{z}",
                )
                for z, default in zip(range(2, 6), (120, 140, 160, 180), strict=True)
            )
            accepted = st.checkbox("These are my watch's zone boundaries")
            if accepted:
                try:
                    zone_profile = HeartRateZones(bounds)
                except ValueError as error:
                    st.error(str(error))
                    st.stop()
            else:
                st.caption("Zones remain unset until you confirm your own values.")
    offset = st.number_input(
        "Workout seconds at video start",
        value=0.0,
        step=1.0,
        help="If your video begins 30 seconds after workout start, enter +30. Verify with a known event.",
    )
    tolerance = st.slider("Nearest-sample tolerance (seconds)", 0.5, 5.0, 2.0, 0.5)
    st.caption("Samples beyond this tolerance remain missing. No interpolation over long gaps.")
    if st.button("Delete my session files", type="secondary"):
        shutil.rmtree(runtime, ignore_errors=True)
        for key in list(st.session_state):
            del st.session_state[key]
        st.rerun()

fingerprint = hashlib.sha256(video_path.read_bytes()).hexdigest()
cache_key = (
    source,
    fingerprint,
    offset,
    tolerance,
    hashlib.sha256(workout.to_csv(index=False).encode()).hexdigest(),
    json.dumps(zone_profile.as_dict() if zone_profile else None),
)
if st.session_state.get("analysis_key") != cache_key:
    try:
        with st.spinner("Reading frames and aligning workout samples…"):
            visual, meta = analyze_video(video_path)
            aligned = align(visual, workout, offset, tolerance, zone_profile)
            report = summarize(aligned)
            report["performance_review"] = performance_review(
                aligned, report, source == "Explore demo"
            )
            st.session_state.update(
                analysis_key=cache_key, aligned=aligned, report=report, meta=meta
            )
            st.session_state.pop("answer", None)
            st.session_state.pop("graph_key", None)
            for key in list(st.session_state):
                if key.startswith(("review_", "note_")):
                    del st.session_state[key]
    except Exception as e:
        st.error(str(e))
        st.stop()
aligned = st.session_state.aligned
report = st.session_state.report
meta = st.session_state.meta
reviews_path = runtime / (
    "reviews-" + hashlib.sha256(repr(cache_key).encode()).hexdigest()[:16] + ".json"
)
if presentation_mode:
    status_label = (
        "DEMO: stock hiking footage + simulated readings and zones"
        if mountain_demo
        else (
            "SYNTHETIC diagnostic fixture"
            if source == "Explore demo"
            else "Uploaded recording · verify alignment and zones"
        )
    )
    st.caption(
        "RACETIME REPLAY · Garmin / COROS / Suunto / Apple Watch compatible exports · "
        + status_label
    )
if source == "Explore demo" and not presentation_mode:
    if mountain_demo:
        st.info(
            "MOUNTAIN POV DEMO · Real hiking footage with simulated watch metrics on the same "
            "60-second timeline. All workout and external-sensor readings are invented, "
            "including core temperature and a single SpO₂ sample. They were not recorded "
            "by the person filming. Zones are illustrative."
        )
        st.caption(
            "Footage: [I Am Sorin / Pexels](https://www.pexels.com/video/point-of-view-of-a-person-hiking-a-rocky-hill-6798218/) "
            "· [Pexels license](https://www.pexels.com/license/). "
            "The diagnostic fixture remains available for controlled stop and frozen-frame tests."
        )
    else:
        st.info(
            "SYNTHETIC DEMO · A generated motion video and invented workout test stops, frozen frames, missing samples, and sensor disagreements. These are not your results or real trail footage."
        )
if not presentation_mode:
    cols = st.columns(4)
    cols[0].metric("Video analyzed", f"{meta['duration_s']:.0f} sec")
    cols[1].metric(
        "Peak heart rate",
        f"{aligned.heart_rate_bpm.max():.0f} bpm"
        if aligned.heart_rate_bpm.notna().any()
        else "No readings",
    )
    cols[2].metric("Heart-rate coverage", f"{report['heart_rate_coverage']:.0%}")
    cols[3].metric(
        "Zone changes to review",
        sum(e["kind"] == "heart_rate_zone_change" for e in report["events"]),
    )
replay_tab, ask_tab, review_tab, proof_tab = st.tabs(
    ["1 · Replay effort", "2 · Ask Replay", "3 · Review & improve", "Build & evidence"]
)
with replay_tab:
    poster_path = ROOT / "demo/mountain-poster.jpg" if mountain_demo else None
    st.iframe(
        player_html(video_path, aligned, report["events"], poster_path),
        height=610 if presentation_mode else 700,
    )
    st.caption(
        "Next: Ask Replay for the evidence, then review the performance comparison and save one observation."
    )
with review_tab:
    brief = report["performance_review"]
    st.subheader("Measured results → an improvement to test")
    st.caption(brief["data_status"] + " · A proposed experiment is not a proven improvement.")
    measured_column, next_step_column = st.columns([1.15, 1])
    with measured_column:
        if brief["comparison"]:
            for observation in brief["observations"]:
                st.write("**" + observation + "**")
            st.table(
                [
                    {
                        "Measurement": item["metric"],
                        f"Start · {clock(brief['baseline_s'])}": item["baseline_display"],
                        f"HR peak · {clock(brief['peak_s'])}": item["peak_display"],
                        "Unit": item["unit"],
                    }
                    for item in brief["comparison"]
                ]
            )
    with next_step_column:
        st.markdown("**Possible interpretation**")
        st.write(brief["interpretation"])
        if brief.get("core_temperature_source"):
            st.caption("Core-temperature source: " + brief["core_temperature_source"])
        with st.expander("Evidence limits"):
            for limit in brief["limits"]:
                st.caption(limit)
        if brief["experiments"]:
            selected_experiment = st.selectbox(
                "Proposed improvement to test",
                brief["experiments"],
                format_func=lambda item: item["title"],
            )
            st.write(selected_experiment["action"])
            st.markdown("**Compare next time:** " + selected_experiment["measure"])
            st.markdown("**What would count as progress:** " + selected_experiment["success"])
    st.subheader("Save a reviewed observation")
    if report["events"]:
        event = st.selectbox(
            "Event to inspect",
            report["events"],
            format_func=lambda e: (
                f"{e['id']} · {e['start_s']:.1f}–{e['end_s']:.1f}s · {e['kind'].replace('_', ' ')}"
            ),
        )
        c1, c2 = st.columns([1, 1.4])
        frame = thumbnail(video_path, event["start_s"] + 1)
        if frame is not None:
            c1.image(frame, caption=f"Frame near {event['start_s'] + 1:.1f}s")
        with c2:
            st.write(
                "These are measurements to inspect, not explanations of your physiology or automatic scene labels."
            )
            with st.form("review_form_" + event["id"]):
                verdict = st.radio(
                    "Your review",
                    ["Unreviewed", "Observation confirmed", "Rejected"],
                    key="review_" + event["id"],
                    horizontal=True,
                )
                note = st.text_input(
                    "What do you actually see?",
                    key="note_" + event["id"],
                    placeholder="Describe visible context; keep causes as hypotheses.",
                )
                if st.form_submit_button("Save reviewed observation", type="primary"):
                    reviews = json.loads(reviews_path.read_text()) if reviews_path.exists() else {}
                    reviews[event["id"]] = {
                        "review": verdict,
                        "note": note,
                        "experiment": selected_experiment if brief["experiments"] else None,
                        "data_status": brief["data_status"],
                    }
                    reviews_path.write_text(json.dumps(reviews, indent=2))
                    st.success("Saved locally. The proposed experiment remains unvalidated.")
    else:
        st.caption(
            "No events passed the current thresholds. This does not prove the recording has no issues."
        )
    st.download_button(
        "Download event evidence JSON",
        json.dumps(report, indent=2),
        "replay-evidence.json",
        "application/json",
    )
    st.download_button(
        "Download aligned measurements CSV",
        aligned.to_csv(index=False),
        "aligned-measurements.csv",
        "text/csv",
    )
    if reviews_path.exists():
        st.download_button(
            "Download my reviewed observations",
            reviews_path.read_text(),
            "reviewed-observations.json",
            "application/json",
        )
with ask_tab:
    st.subheader("Ask about this recording")
    st.caption(
        "Local evidence mode works without an API key. Answers cite measured events; "
        "the Review & improve tab proposes experiments for you to assess."
    )
    question = st.text_input(
        "Question", "Compare my performance readings and propose an improvement to test."
    )
    with st.expander("Optional AI & tracing"):
        dense = st.checkbox(
            "Use semantic + keyword retrieval",
            value=False,
            help="Downloads a public MiniLM embedding model on first use; embeddings run locally.",
        )
        cloud = st.checkbox(
            "Add a cloud-written draft from redacted evidence",
            value=False,
            help="Sends your redacted question and aggregate event evidence to the selected provider, not video, coordinates, or raw health samples.",
        )
        provider = st.selectbox("Cloud provider", ["gemini", "nebius"], disabled=not cloud)
        if cloud:
            credential = "NEBIUS_API_KEY" if provider == "nebius" else "GEMINI_API_KEY"
            if not os.getenv(credential):
                st.info(
                    f"Set {credential} in your local .env to enable this provider. Local evidence still works."
                )
            if provider == "nebius" and not os.getenv("NEBIUS_MODEL"):
                st.info(
                    "Set NEBIUS_MODEL to a current chat model ID from your Token Factory account."
                )
        trace_demo = st.checkbox(
            "Send synthetic demo telemetry to Braintrust",
            value=False,
            disabled=source != "Explore demo",
            help="Requires local Braintrust configuration. Sends step timings and outcome labels, not question text, video or health records.",
        )
    if st.button("Investigate", type="primary"):
        with st.spinner("Following the evidence…"):
            try:
                graph_key = (cache_key, dense)
                if st.session_state.get("graph_key") != graph_key:
                    index = EvidenceIndex(documents(report), dense=dense)
                    st.session_state.graph = build_agent(index)
                    st.session_state.graph_key = graph_key
                with trace_session(
                    trace_demo, "synthetic" if source == "Explore demo" else "user"
                ) as trace:
                    st.session_state.answer = investigate(
                        question,
                        report,
                        cloud=cloud,
                        provider=provider,
                        dense=dense,
                        thread_id=st.session_state.sid,
                        graph=st.session_state.graph,
                    )
                st.session_state.answer["braintrust"] = trace
                st.session_state.answer_question = question

            except Exception as e:
                st.error(
                    f"Investigation unavailable: {type(e).__name__}. Your replay is still available."
                )
    if "answer" in st.session_state:
        answer = st.session_state.answer
        st.caption("Answer to: " + st.session_state.get("answer_question", "previous question"))
        st.markdown(answer["answer"])
        for item in answer["caveats"]:
            st.caption(item)
        if "cloud_draft" in answer:
            st.markdown("**Cloud draft for review**\n\n" + answer["cloud_draft"])
        if "cloud_status" in answer:
            st.caption(answer["cloud_status"])
        with st.expander("Evidence workflow"):
            st.json(answer)
with proof_tab:
    st.subheader("A measurable capstone")
    st.markdown((ROOT / "docs/WEEKLY_MAPPING.md").read_text())
    for f in ["evaluation.json", "router-evaluation.json", "guardrails-evaluation.json"]:
        if (ROOT / "reports" / f).exists():
            with st.expander(f):
                st.json(json.loads((ROOT / "reports" / f).read_text()))
    with st.expander("Why this matters"):
        st.markdown((ROOT / "docs/PRODUCT.md").read_text())
