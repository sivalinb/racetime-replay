"""Align independently sampled sources without interpolating across gaps."""

import numpy as np
import pandas as pd

from replay.heart_rate import HeartRateZones, add_zones, zone_changes
from replay.ingest import MEASUREMENTS


def align(
    video: pd.DataFrame,
    workout: pd.DataFrame,
    offset_s: float = 0.0,
    tolerance_s: float = 2.0,
    zone_profile: HeartRateZones | None = None,
) -> pd.DataFrame:
    """Join independently sampled streams with an explicit offset and gap limit."""
    # video time 0 corresponds to workout elapsed offset_s.
    out = video.copy().sort_values("video_s")
    out["workout_s"] = out.video_s + offset_s
    out["speed_mps"] = np.nan
    out["heart_rate_bpm"] = np.nan
    for col in MEASUREMENTS:
        fields = ["elapsed_s", col]
        if col == "core_temperature_c":
            fields.append("core_temperature_source")
        valid = workout[fields].dropna(subset=[col]).sort_values("elapsed_s")
        if valid.empty:
            out[col] = np.nan
            if col == "core_temperature_c":
                out["core_temperature_source"] = ""
            continue
        merged = pd.merge_asof(
            out[["workout_s"]],
            valid,
            left_on="workout_s",
            right_on="elapsed_s",
            direction="nearest",
            tolerance=min(tolerance_s, 0.5) if col == "spo2_percent" else tolerance_s,
        )
        out[col] = merged[col].to_numpy()
        if col == "spo2_percent":
            out["spo2_sample_s"] = merged.elapsed_s.to_numpy() - offset_s
        if col == "core_temperature_c":
            out["core_temperature_source"] = merged.core_temperature_source.fillna("").to_numpy()
            out["core_temperature_sample_s"] = merged.elapsed_s.to_numpy() - offset_s
    out["pace_min_km"] = (1000 / 60 / out.speed_mps).where(out.speed_mps >= 0.4)
    out["sensor_conflict"] = (out.speed_mps < 0.4) & (out.motion_px > 1.0)
    out["low_motion"] = out.motion_px < 0.15
    out["stop_candidate"] = (out.speed_mps < 0.4) & out.low_motion
    out["repeated_frame"] = out.frame_difference < 0.03
    out["missing_speed"] = out.speed_mps.isna()
    return add_zones(out, zone_profile)


def intervals(df: pd.DataFrame, column: str, minimum_s: float = 2.0) -> list[dict]:
    """Group a boolean signal into half-open intervals on the video clock."""
    if len(df) < 2:
        return []
    df = df.sort_values("video_s").reset_index(drop=True)
    step = float(df.video_s.diff().median())
    found, start, previous = [], None, None

    def close(end: float) -> None:
        nonlocal start
        if start is not None and end - start >= minimum_s:
            found.append(
                {
                    "start_s": round(start, 2),
                    "end_s": round(end, 2),
                    "duration_s": round(end - start, 2),
                    "kind": column,
                }
            )
        start = None

    for i, row in df.iterrows():
        if previous is not None and row.video_s - previous > 1.5 * step:
            close(previous + step)
        if bool(row[column]) and start is None:
            start = float(row.video_s)
        # Close before a false sample; never bridge a sampling gap.
        is_last = i == df.index[-1]
        if start is not None and (not bool(row[column]) or is_last):
            end = float(row.video_s) + (step if is_last and bool(row[column]) else 0)
            close(end)
        previous = float(row.video_s)
    return found


def summarize(df: pd.DataFrame) -> dict:
    """Build a JSON-serializable report of candidates, coverage and limitations."""
    events = []
    for field in ["stop_candidate", "sensor_conflict", "repeated_frame", "missing_speed"]:
        events += intervals(df, field)
    events += zone_changes(df)
    events.sort(key=lambda x: (x["start_s"], x["kind"]))
    for n, event in enumerate(events, 1):
        event["id"] = f"E{n:03d}"
        if event["kind"] == "heart_rate_zone_change":
            block = df[(df.video_s >= event["start_s"]) & (df.video_s < event["end_s"])]
            event["context_ranges"] = {
                field: {
                    "min": round(float(block[field].min()), 2),
                    "max": round(float(block[field].max()), 2),
                }
                for field in [
                    "pace_min_km",
                    "cadence_spm",
                    "altitude_m",
                    "running_power_w",
                    "spo2_percent",
                    "core_temperature_c",
                ]
                if field in block and block[field].notna().any()
            }
            event["core_temperature_sources"] = sorted(
                set(block.get("core_temperature_source", pd.Series(dtype=str)).dropna()) - {""}
            )
    return {
        "events": events,
        "stop_candidate_s": sum(e["duration_s"] for e in events if e["kind"] == "stop_candidate"),
        "speed_coverage": float(df.speed_mps.notna().mean()),
        "heart_rate_coverage": float(df.heart_rate_bpm.notna().mean()),
        "conflict_samples": int(df.sensor_conflict.sum()),
        "heart_rate_zones": df.attrs.get("heart_rate_zones"),
        "duration_s": float(df.video_s.max()),
        "interpretation": (
            "Events identify moments to review. Heart-rate zones use the selected thresholds; "
            "a zone change does not establish terrain difficulty or its cause. "
            "Camera motion is not running speed."
        ),
    }
