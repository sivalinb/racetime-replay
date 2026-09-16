"""Behavior at personal-zone, optional-sensor and interpretation boundaries."""

import io

import numpy as np
import pandas as pd
import pytest

from replay.agent import investigate
from replay.analysis import align, summarize
from replay.heart_rate import DEMO_ZONES, HeartRateZones, add_zones, zone_changes
from replay.ingest import load_csv, load_health_xml, merge_health_route, normalize
from replay.performance import performance_review
from scripts.make_mountain_workout import make_workout


def video(times):
    return pd.DataFrame(
        {"video_s": np.asarray(times, dtype=float), "motion_px": 2.0, "frame_difference": 2.0}
    )


def test_zones_need_explicit_thresholds_and_preserve_missing_readings():
    readings = pd.DataFrame({"heart_rate_bpm": [119, 120, 140, 160, 180, np.nan]})
    assert add_zones(readings, None).heart_rate_zone.isna().all()
    result = add_zones(readings, DEMO_ZONES)
    assert result.heart_rate_zone.iloc[:5].tolist() == [1, 2, 3, 4, 5]
    assert pd.isna(result.heart_rate_zone.iloc[5])
    with pytest.raises(ValueError):
        HeartRateZones((120, 140, 140, 180))


def test_zone_events_require_sustained_changes_and_do_not_bridge_gaps():
    readings = pd.DataFrame(
        {"video_s": list(range(9)), "heart_rate_bpm": [130, 160, 160, 130, 160, 160, 160, 160, 160]}
    )
    result = zone_changes(add_zones(readings, DEMO_ZONES))
    assert [(e["start_s"], e["end_s"]) for e in result] == [(4, 9)]
    readings.loc[4, "heart_rate_bpm"] = np.nan
    assert zone_changes(add_zones(readings, DEMO_ZONES)) == []
    readings = pd.DataFrame(
        {
            "video_s": [0, 1, 10, 11, 12, 13, 14],
            "heart_rate_bpm": [130, 130, 160, 160, 160, 160, 160],
        }
    )
    assert zone_changes(add_zones(readings, DEMO_ZONES)) == []


def test_spot_oxygen_does_not_become_a_continuous_signal():
    workout = normalize(pd.DataFrame({"elapsed_s": [0.0, 10.0], "spo2_percent": [98.0, 97.0]}))
    output = align(video([0, 0.5, 1, 5, 10]), workout, tolerance_s=5)
    assert output.spo2_percent.notna().tolist() == [True, True, False, False, True]
    assert output.spo2_sample_s.iloc[1] == 0
    assert output.spo2_sample_s.iloc[4] == 10


def test_health_oxygen_fraction_and_power_units():
    xml = b"""<HealthData>
    <Record type="HKQuantityTypeIdentifierOxygenSaturation" startDate="2026-09-01T10:00:00Z" unit="%" value="0.98"/>
    <Record type="HKQuantityTypeIdentifierRunningPower" startDate="2026-09-01T10:00:00Z" unit="W" value="250"/>
    <Record type="HKQuantityTypeIdentifierBodyTemperature" startDate="2026-09-01T10:00:00Z" unit="degC" value="38"/>
    <Record type="HKQuantityTypeIdentifierRunningPower" startDate="2026-09-01T10:00:00Z" unit="unknown" value="900"/>
    </HealthData>"""
    result = load_health_xml(io.BytesIO(xml))
    assert result.iloc[0].spo2_percent == 98
    assert result.iloc[0].running_power_w == 250
    assert result.core_temperature_c.isna().all()


def test_integer_csv_times_align_and_oxygen_keeps_original_gpx_timestamp():
    workout = load_csv(io.BytesIO(b"elapsed_s,heart_rate_bpm\n0,130\n1,140\n"))
    assert align(video([0, 1]), workout).heart_rate_bpm.tolist() == [130, 140]
    route = normalize(
        pd.DataFrame(
            {
                "timestamp": ["2026-09-01T10:00:00Z", "2026-09-01T10:00:01Z"],
                "speed_mps": [2, 2],
            }
        )
    )
    health = normalize(
        pd.DataFrame({"timestamp": ["2026-09-01T10:00:00.400Z"], "spo2_percent": [98]})
    )
    merged = merge_health_route(route, health)
    result = align(video([0, 0.4, 1]), merged)
    assert result.spo2_sample_s.iloc[1] == pytest.approx(0.4)
    assert pd.isna(result.spo2_percent.iloc[2])


def test_core_temperature_requires_explicit_provenance_and_own_column():
    result = normalize(
        pd.DataFrame(
            {
                "elapsed_s": [0.0, 1.0, 2.0, 3.0],
                "temperature": [38, 38, 38, 38],
                "skin_temperature_c": [35, 35, 35, 35],
                "core_temperature_c": [38, 38, 100, np.nan],
                "core_temperature_source": [
                    "",
                    "External CORE sensor export",
                    "External sensor",
                    "",
                ],
            }
        )
    )
    assert result.core_temperature_c.notna().tolist() == [False, True, False, False]
    output = align(video([1, 5]), result, tolerance_s=1)
    assert output.iloc[0].core_temperature_source == "External CORE sensor export"
    assert pd.isna(output.iloc[1].core_temperature_c)
    assert output.iloc[1].core_temperature_source == ""


def test_simulated_exports_comparison_and_cited_improvement(tmp_path):
    make_workout(tmp_path)
    workout = load_csv(tmp_path / "mountain-workout.csv")
    health = load_health_xml(tmp_path / "mountain-health.xml")
    assert (workout.speed_mps > 0).all()
    for metric in ["heart_rate_bpm", "speed_mps", "running_power_w", "spo2_percent"]:
        np.testing.assert_allclose(workout[metric], health[metric], equal_nan=True)
    aligned = align(video(range(60)), workout, zone_profile=DEMO_ZONES)
    report = summarize(aligned)
    assert [(e["start_s"], e["to_zone"]) for e in report["events"]] == [(15, 3), (40, 4)]
    brief = performance_review(aligned, report, simulated=True)
    assert brief["peak_s"] == 48
    by_field = {item["field"]: item for item in brief["comparison"]}
    assert by_field["heart_rate_bpm"]["change"] == 34
    assert by_field["heart_rate_zone"]["peak"] == 4
    assert by_field["pace_min_km"]["baseline_display"] == "8:46"
    assert by_field["pace_min_km"]["peak_display"] == "10:45"
    assert by_field["spo2_percent"]["peak"] is None
    assert "Simulated" in brief["core_temperature_source"]
    assert "prove an improvement" in brief["limits"][0]
    report["performance_review"] = brief
    answer = investigate("Compare performance and propose an improvement to test", report)
    assert answer["evidence_ids"] == ["P001"]
    assert "168" in answer["answer"] and "Proposed experiment" in answer["answer"]
    assert "No reading" in answer["answer"]
    heart_rate = investigate("Compare heart rate and zone changes", report)
    assert heart_rate["evidence_ids"] == ["E001", "E002"] or set(heart_rate["evidence_ids"]) == {
        "E001",
        "E002",
    }
    assert "sensor_conflict" not in heart_rate["answer"]


def test_no_performance_comparison_without_supporting_readings():
    aligned = align(video([0, 1]), normalize(pd.DataFrame({"elapsed_s": [0.0, 1.0]})))
    review = performance_review(aligned, summarize(aligned))
    assert review["status"] == "insufficient_evidence"
    assert review["comparison"] == [] and review["experiments"] == []


def test_no_invented_thermal_or_oxygen_conclusion_from_heart_rate():
    workout = normalize(pd.DataFrame({"elapsed_s": [0.0, 1.0], "heart_rate_bpm": [130, 160]}))
    aligned = align(video([0, 1]), workout)
    review = performance_review(aligned, summarize(aligned))
    by_field = {item["field"]: item for item in review["comparison"]}
    for field in ["core_temperature_c", "spo2_percent", "running_power_w", "heart_rate_zone"]:
        assert by_field[field]["peak"] is None
    assert "do not explain its cause" in review["interpretation"]
