"""Keep the demonstration's invented data honest and its visible event reproducible."""

import pandas as pd

from replay.analysis import align, summarize
from replay.heart_rate import DEMO_ZONES
from replay.ingest import normalize
from replay.performance import performance_review
from scripts.prepare_story_demo import story_workout


def test_story_fixture_has_one_reviewable_peak_and_no_invented_optional_sensors():
    raw = story_workout()
    assert (raw.speed_mps > 0).all()
    workout = normalize(raw)
    frames = pd.DataFrame({"video_s": raw.elapsed_s, "motion_px": 2.0, "frame_difference": 2.0})
    aligned = align(frames, workout, zone_profile=DEMO_ZONES)
    report = summarize(aligned)
    brief = performance_review(aligned, report, simulated=True)
    assert brief["data_status"] == "Simulated example"
    assert brief["peak_s"] == 12
    fields = {item["field"]: item for item in brief["comparison"]}
    assert fields["heart_rate_bpm"]["peak"] == 154
    assert fields["heart_rate_zone"]["peak"] == 3
    assert fields["pace_min_km"]["peak_display"] == "10:30"
    assert fields["spo2_percent"]["peak"] is None
    assert fields["core_temperature_c"]["peak"] is None
    assert any(event["kind"] == "heart_rate_zone_change" for event in report["events"])
