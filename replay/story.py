"""A short, progressive demonstration of watch readings → video → a reviewed plan.

This route uses the same Python analysis, alignment, evidence and player as the
full workspace. The two stock clips are separate examples. All paired workout
values are simulated; the app never attributes them to the people in the clips.
"""

import hashlib
import json
import uuid
from pathlib import Path

import altair as alt
import streamlit as st

from replay.agent import investigate
from replay.analysis import align, summarize
from replay.heart_rate import DEMO_ZONES
from replay.ingest import load_csv
from replay.performance import clock, performance_review
from replay.player import player_html
from replay.vision import analyze_video

LABELS = ["Why video?", "Read the watch", "Reveal the moment", "Plan next time"]
FOCUS_FIELDS = {"heart_rate_bpm", "heart_rate_zone", "pace_min_km"}


@st.cache_data(show_spinner=False)
def story_evidence(video_path: str, workout_path: str, version: str):
    """Analyze only the bundled synthetic example; version invalidates stale cache."""
    visual, metadata = analyze_video(video_path)
    aligned = align(visual, load_csv(workout_path), zone_profile=DEMO_ZONES)
    report = summarize(aligned)
    report["performance_review"] = performance_review(aligned, report, simulated=True)
    return aligned, report, metadata


def _go(step: int) -> None:
    """Move between authored stages without accepting or saving an observation."""
    if step == 0:
        # A new walkthrough starts with an unanswered, unsaved review.
        st.session_state.pop("story_answer", None)
        st.session_state.pop("story_saved_plan", None)
    st.session_state.story_step = step


def _sources() -> None:
    """Display the source and scope beside the media, not just in an appendix."""
    st.caption(
        "Real stock footage · Simulated workout data · Two separate examples. "
        "[Stream: Mixkit](https://mixkit.co/free-stock-video/couple-running-over-a-stream-44352/) · "
        "[Rocky POV: K / Pexels](https://www.pexels.com/video/a-hiker-walking-on-the-edge-of-a-cliff-4606798/)"
    )


def _metrics(brief: dict) -> None:
    """Show only the three comparisons required to understand this story."""
    items = [item for item in brief["comparison"] if item["field"] in FOCUS_FIELDS]
    for column, item in zip(st.columns(3), items, strict=True):
        unit = (
            " bpm"
            if item["field"] == "heart_rate_bpm"
            else (" /km" if item["field"] == "pace_min_km" else "")
        )
        column.metric(item["metric"], f"{item['baseline_display']} → {item['peak_display']}{unit}")


def render_story(root: Path) -> None:
    """Render an actual local app flow with explicit review and downloadable output."""
    media = root / "demo/story"
    required = [
        "rocky.mp4",
        "stream.mp4",
        "rocky-workout.csv",
        "provenance.json",
        "rocky-poster.jpg",
    ]
    if not all((media / name).is_file() for name in required):
        st.error("Story footage is not prepared yet. Run python scripts/prepare_story_demo.py.")
        st.link_button("Open the full workspace", "/")
        return
    st.markdown(
        "<style>" + (Path(__file__).with_name("ui") / "story.css").read_text() + "</style>",
        unsafe_allow_html=True,
    )
    st.session_state.setdefault("story_step", 1 if st.query_params.get("start") == "watch" else 0)
    step = st.session_state.story_step
    top, navigation = st.columns([3, 2])
    top.markdown(
        '<div class="story-brand">RACETIME <span>REPLAY</span></div>'
        '<div class="story-tagline">Your effort. The situation. A better plan.</div>',
        unsafe_allow_html=True,
    )
    restart, workspace = navigation.columns(2)
    restart.button("Restart story", on_click=_go, args=(0,), width="stretch")
    workspace.link_button("Full workspace ↗", "/", width="stretch")
    steps = "".join(
        f'<div class="story-step {"active" if i == step else ""}">'
        f"<span>{i + 1:02}</span> {label}</div>"
        for i, label in enumerate(LABELS)
    )
    st.markdown(f'<div class="story-steps">{steps}</div>', unsafe_allow_html=True)
    if step == 0:
        _opening(media)
        return

    version = hashlib.sha256(
        (media / "rocky-workout.csv").read_bytes() + (media / "provenance.json").read_bytes()
    ).hexdigest()
    with st.spinner("Matching the rocky clip with the simulated workout…"):
        aligned, report, _ = story_evidence(
            str(media / "rocky.mp4"), str(media / "rocky-workout.csv"), version
        )
    brief = report["performance_review"]
    if step == 1:
        _watch(aligned, brief)
    elif step == 2:
        _reveal(media, aligned, report, brief)
    else:
        _plan(root, media, report, brief, version)


def _opening(media: Path) -> None:
    st.title("Would your watch show you this?")
    left, right = st.columns([1.6, 1], gap="large")
    with left:
        st.video(str(media / "stream.mp4"), autoplay=True, muted=True, loop=True)
        st.caption("Opening example: runners crossing a stream. No watch readings are attached.")
    with right:
        st.markdown("### It records your effort.")
        st.write("Heart rate. Pace. Training zones.")
        st.markdown("### Video records the situation.")
        st.write("Here, it is a water crossing. In the next example, it is uneven rocky footing.")
        st.markdown("**Replay connects a change in effort to a moment you can inspect.**")
        st.button(
            "Start the guided review →", type="primary", on_click=_go, args=(1,), width="stretch"
        )
    _sources()


def _watch(aligned, brief: dict) -> None:
    st.title("More effort. Slower pace. What happened?")
    st.caption(
        f"Separate rocky-trail example · invented readings at {clock(brief['baseline_s'])} "
        f"and {clock(brief['peak_s'])}. They are not the filmed hiker’s measurements."
    )
    _metrics(brief)
    chart, question = st.columns([1.6, 1], gap="large")
    with chart:
        readings = aligned[["video_s", "heart_rate_bpm"]]
        plot = alt.Chart(readings).encode(
            x=alt.X("video_s:Q", title="Clip time (seconds)", scale=alt.Scale(domain=[0, 29])),
            y=alt.Y(
                "heart_rate_bpm:Q",
                title="Heart rate (bpm)",
                scale=alt.Scale(domain=[120, 160], zero=False),
            ),
        )
        line = plot.mark_line(color="#177e70", strokeWidth=3)
        peak = plot.transform_filter(alt.datum.video_s == brief["peak_s"])
        st.altair_chart(
            (
                line
                + peak.mark_point(color="#173a40", size=90, filled=True)
                + peak.mark_text(dy=-15, color="#173a40").encode(text=alt.value("Peak · 0:12"))
            ).properties(height=210),
            width="stretch",
        )
        st.caption("Illustrative zones: Zone 2 starts at 120 bpm; Zone 3 at 140 bpm.")
    with question:
        st.markdown("### The chart gives us a question.")
        st.write(
            "Heart rate rises as the pace slows. The numbers cannot show the surface underfoot."
        )
        st.markdown("**What does the matching clip add?**")
        st.button(
            "Reveal the matching video →", type="primary", on_click=_go, args=(2,), width="stretch"
        )
    _sources()


def _reveal(media: Path, aligned, report: dict, brief: dict) -> None:
    st.title("Now look at the footing.")
    st.caption(
        "Real rocky-trail footage · Simulated readings · Start at the example’s peak, then replay the segment."
    )
    st.iframe(
        player_html(
            media / "rocky.mp4",
            aligned,
            report["events"],
            media / "rocky-poster.jpg",
            focused=True,
            start_s=brief["peak_s"],
        ),
        height=390,
    )
    note, next_step = st.columns([1.7, 1])
    note.markdown(
        "**Visible context:** boots stepping across uneven rocks. "
        "This is a human-reviewed demo note, not an automatic terrain diagnosis."
    )
    next_step.button(
        "Make a plan for next time →", type="primary", on_click=_go, args=(3,), width="stretch"
    )


def _plan(root: Path, media: Path, report: dict, brief: dict, version: str) -> None:
    st.title("One observation. One improvement to test.")
    st.caption(
        "Review what you saw before saving. The footage does not prove why heart rate changed."
    )
    evidence, action = st.columns([1, 1.25], gap="large")
    with evidence:
        answer = st.session_state.get("story_answer")
        if not answer:
            st.image(
                str(media / "rocky-poster.jpg"), caption="Evidence frame · 0:12 · rocky POV example"
            )
            st.markdown("**Measured in the simulated example**")
            st.write(brief["observations"][0])
        with st.expander("Ask Replay for the measurement evidence", expanded=bool(answer)):
            st.caption(
                "Runs the existing local evidence workflow. No video or health records are sent to a cloud."
            )
            if st.button("Explain these readings", key="story_ask"):
                st.session_state.story_answer = investigate(
                    "Compare my performance readings and propose an improvement to test.",
                    report,
                    cloud=False,
                    dense=False,
                )
                st.rerun()
            if answer:
                if brief["id"] in answer["evidence_ids"]:
                    # Render the cited structured evidence, not a new model-generated claim.
                    st.markdown(f"**Measurement evidence · {brief['id']}**")
                    st.write(brief["observations"][0])
                    st.write(brief["interpretation"])
                    st.markdown("**Experiment to review**")
                    st.write(brief["experiments"][0]["title"] + ".")
                    st.download_button(
                        "Download full measurement evidence",
                        answer["answer"],
                        "racetime-measurement-evidence.txt",
                        "text/plain",
                        width="stretch",
                    )
                else:
                    st.markdown(answer["answer"])
    with action:
        with st.form("story_review"):
            observation = st.text_input(
                "What can you actually see?",
                "Boots stepping across uneven rocks near 0:12.",
            )
            experiment = st.text_area(
                "My next-run experiment",
                "Practice comparable rocky terrain and test steadier effort using my own training plan. "
                "Allow realistic time for technical sections.",
                height=92,
            )
            st.caption(
                "Compare next time: segment time, time in your intended zone, perceived effort and video."
            )
            confirmed = st.checkbox("I reviewed the clip and confirm this observation.")
            save = st.form_submit_button("Save my next-run plan", type="primary", width="stretch")
        if save:
            if not confirmed or not observation.strip() or not experiment.strip():
                st.warning(
                    "Review and confirm the observation, and enter an experiment before saving."
                )
            else:
                st.session_state.setdefault("sid", uuid.uuid4().hex)
                runtime = root / ".runtime" / st.session_state.sid
                runtime.mkdir(parents=True, exist_ok=True)
                result = {
                    "data_status": "Simulated example; not the filmed person's workout",
                    "clip": "rocky.mp4",
                    "evidence_s": brief["peak_s"],
                    "fixture_version": version,
                    "measurement_evidence_id": brief["id"],
                    "reviewed_observation": observation.strip(),
                    "confirmed_by_viewer": True,
                    "experiment": experiment.strip(),
                    "compare": "Segment time, intended-zone time, perceived effort and video",
                    "status": "Proposed experiment, not a proven improvement",
                }
                text = json.dumps(result, indent=2)
                (runtime / "story-next-run-plan.json").write_text(text + "\n")
                st.session_state.story_saved_plan = text
        if "story_saved_plan" in st.session_state:
            st.success("Plan saved locally. You now have something specific to test next time.")
            st.download_button(
                "Download saved plan",
                st.session_state.story_saved_plan,
                "racetime-next-run-plan.json",
                "application/json",
                width="stretch",
            )
    _sources()
    with st.expander("More signals and future possibilities"):
        st.write(
            "The full workspace supports available cadence, elevation, power, spot oxygen and explicitly "
            "sourced core-temperature readings. This focused example uses only heart rate, zones and pace. "
            "Automatic terrain, wildlife or weather labels and live SOS are not implemented."
        )
