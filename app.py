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
from replay.ingest import load_csv, load_gpx, load_health_xml, merge_health_route
from replay.observability import trace_session
from replay.player import player_html
from replay.retrieval import EvidenceIndex, documents
from replay.vision import analyze_video, thumbnail

ROOT = Path(__file__).parent
load_dotenv(ROOT / ".env")
# Raw LangGraph state must never be automatically traced.
os.environ["LANGSMITH_TRACING"] = "false"
st.set_page_config(page_title="RaceTime Replay", page_icon="▶", layout="wide")
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
        "Video: exported MP4/MOV, up to 15 minutes and 150 MB. Workout: CSV, GPX, or Apple Health XML."
    )
    video_path = ROOT / "demo/replay-demo.mp4"
    workout_path = ROOT / "demo/workout.csv"
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
)
if st.session_state.get("analysis_key") != cache_key:
    try:
        with st.spinner("Reading frames and aligning workout samples…"):
            visual, meta = analyze_video(video_path)
            aligned = align(visual, workout, offset, tolerance)
            report = summarize(aligned)
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
if source == "Explore demo":
    st.info(
        "SYNTHETIC DEMO · A generated motion video and invented workout test stops, frozen frames, missing samples, and sensor disagreements. These are not your results or real trail footage."
    )
cols = st.columns(4)
cols[0].metric("Video analyzed", f"{meta['duration_s']:.0f} sec")
cols[1].metric("Candidate stop time", f"{report['stop_candidate_s']:.1f} sec")
cols[2].metric("Speed sample coverage", f"{report['speed_coverage']:.0%}")
cols[3].metric("Events for review", len(report["events"]))
replay_tab, ask_tab, proof_tab, story_tab = st.tabs(
    ["Replay & events", "Ask the evidence", "Build & evaluation", "Why this matters"]
)
with replay_tab:
    st.iframe(player_html(video_path, aligned, report["events"]), height=520)
    st.subheader("Review the moments")
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
            verdict = st.radio(
                "Your review",
                ["Unreviewed", "Confirmed", "Rejected"],
                key="review_" + event["id"],
                horizontal=True,
            )
            note = st.text_input("Review note", key="note_" + event["id"])
            reviews = {
                e["id"]: {
                    "review": st.session_state.get("review_" + e["id"], "Unreviewed"),
                    "note": st.session_state.get("note_" + e["id"], ""),
                }
                for e in report["events"]
            }
            (runtime / "reviews.json").write_text(json.dumps(reviews, indent=2))
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
with ask_tab:
    st.subheader("Ask about this recording")
    st.caption(
        "Local evidence mode works without an API key. Scene understanding and personalized optimization are future extensions."
    )
    question = st.text_input("Question", "Where did I stop during this run?")
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
            st.info("Set NEBIUS_MODEL to a current chat model ID from your Token Factory account.")
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
with story_tab:
    st.subheader("Your watch records the effort. Your camera records the context.")
    st.image(
        str(ROOT / "assets/replay-workflow.svg"),
        caption="Video and workout measurements aligned for evidence review.",
    )
    st.markdown((ROOT / "docs/PRODUCT.md").read_text())
