"""User-defined heart-rate bands and sustained changes for video review.

Zones are derived from supplied thresholds, never from age or a guessed maximum
heart rate. They describe a recorded signal; they do not establish terrain,
effort, fitness, recovery, or the reason a measurement changed.
"""

from dataclasses import dataclass
from math import isfinite

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class HeartRateZones:
    """Lower bounds for zones 2–5; exact-boundary samples enter the higher zone."""

    lower_bounds: tuple[float, float, float, float]
    source: str = "User-entered zone thresholds"

    def __post_init__(self) -> None:
        bounds = self.lower_bounds
        if len(bounds) != 4 or any(not isfinite(b) or not 25 < b < 250 for b in bounds):
            raise ValueError("Enter four finite zone boundaries between 25 and 250 bpm.")
        if any(a >= b for a, b in zip(bounds, bounds[1:], strict=False)):
            raise ValueError("Zone boundaries must increase from zone 2 through zone 5.")

    def as_dict(self) -> dict:
        """Include profile provenance beside every displayed zone calculation."""
        return {"lower_bounds_bpm": list(self.lower_bounds), "source": self.source}


DEMO_ZONES = HeartRateZones((120, 140, 160, 180), "Illustrative demo zones, not personal zones")


def add_zones(df: pd.DataFrame, profile: HeartRateZones | None) -> pd.DataFrame:
    """Classify valid aligned readings; absent profiles or readings stay unknown."""
    out = df.copy()
    out["heart_rate_zone"] = np.nan
    out.attrs["heart_rate_zones"] = profile.as_dict() if profile else None
    if profile is not None:
        valid = out.heart_rate_bpm.between(25, 250)
        out.loc[valid, "heart_rate_zone"] = (
            np.searchsorted(profile.lower_bounds, out.loc[valid, "heart_rate_bpm"], side="right")
            + 1
        )
    return out


def zone_changes(df: pd.DataFrame, minimum_s: float = 5.0) -> list[dict]:
    """Find sustained band changes without bridging missing HR or video samples.

    The first band is a baseline, not a transition. A new band must persist for
    at least five seconds. Ending timestamps are half-open on the video clock.
    Missing values reset the baseline; a later value is not a guessed transition.
    """
    if "heart_rate_zone" not in df or len(df) < 2:
        return []
    samples = df.sort_values("video_s").reset_index(drop=True)
    step = float(samples.video_s.diff().median())
    if not isfinite(step) or step <= 0:
        return []
    groups: list[list[int]] = []
    current: list[int] = []
    for i, row in samples.iterrows():
        if current:
            previous = samples.iloc[current[-1]]
            if (
                pd.isna(row.heart_rate_zone)
                or row.heart_rate_zone != previous.heart_rate_zone
                or row.video_s - previous.video_s > 1.5 * step
            ):
                groups.append(current)
                current = []
        if pd.notna(row.heart_rate_zone):
            current.append(i)
    if current:
        groups.append(current)
    events = []
    for group in groups:
        first = group[0]
        if first == 0:
            continue
        block = samples.iloc[group]
        previous = samples.iloc[first - 1]
        start, end = float(block.video_s.iloc[0]), float(block.video_s.iloc[-1] + step)
        zone = int(block.heart_rate_zone.iloc[0])
        if (
            pd.isna(previous.heart_rate_zone)
            or previous.heart_rate_zone == zone
            or start - previous.video_s > 1.5 * step
            or end - start < minimum_s
        ):
            continue
        events.append(
            {
                "kind": "heart_rate_zone_change",
                "start_s": round(start, 2),
                "end_s": round(end, 2),
                "duration_s": round(end - start, 2),
                "from_zone": int(previous.heart_rate_zone),
                "to_zone": zone,
                "start_hr_bpm": float(block.heart_rate_bpm.iloc[0]),
                "min_hr_bpm": float(block.heart_rate_bpm.min()),
                "peak_hr_bpm": float(block.heart_rate_bpm.max()),
                "profile": df.attrs.get("heart_rate_zones"),
            }
        )
    return events
