"""Create reproducible mock watch exports for the 60-second stock POV clip.

The CSV and Apple Health-shaped XML contain the same invented HR/speed samples.
Coordinates describe a fictional route, not the filming location. No physiological
values are inferred from pixels. The original video is never modified here.
"""

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from xml.etree.ElementTree import Element, ElementTree, SubElement, indent

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def make_workout(destination: Path = ROOT / "demo") -> None:
    """Write a gradual, explicitly simulated rise in HR with contextual signals."""
    destination.mkdir(parents=True, exist_ok=True)
    seconds = np.arange(60)
    # The profile is authored independently of the clip. No video-derived
    # physiological or terrain labels are claimed. Speed remains positive.
    knots = [0, 10, 20, 30, 40, 48, 59]
    recorded_speed = np.interp(seconds, knots, [1.9, 1.9, 1.8, 1.7, 1.6, 1.55, 1.7])
    hr = np.rint(np.interp(seconds, knots, [134, 136, 144, 152, 160, 168, 158])).astype(int)
    cadence = np.rint(np.interp(seconds, knots, [158, 158, 156, 154, 152, 150, 154])).astype(int)
    power = np.rint(np.interp(seconds, knots, [205, 210, 225, 245, 265, 275, 235])).astype(int)
    # One illustrative spot measurement; no invented continuous oxygen stream.
    oxygen = np.full(60, np.nan)
    oxygen[0] = 98
    distance = np.cumsum(recorded_speed) - recorded_speed[0]
    start = datetime(2026, 8, 1, 7, 0, tzinfo=UTC)
    timestamps = [start + timedelta(seconds=int(t)) for t in seconds]
    df = pd.DataFrame(
        {
            "timestamp": [t.isoformat() for t in timestamps],
            "elapsed_s": seconds,
            "speed_mps": np.round(recorded_speed, 3),
            "heart_rate_bpm": hr,
            "cadence_spm": cadence,
            "running_power_w": power,
            "spo2_percent": oxygen,
            "core_temperature_c": np.round(np.interp(seconds, [0, 59], [37.8, 37.9]), 2),
            "core_temperature_source": "Simulated external core-temperature sensor",
            "latitude": 40 + distance / 111320,
            "longitude": -105 + 0.00012 * np.sin(seconds / 18),
            "altitude_m": np.round(1600 + np.interp(seconds, knots, [0, 1, 4, 9, 15, 20, 23]), 1),
        }
    )
    df.to_csv(destination / "mountain-workout.csv", index=False)
    root = Element("HealthData", locale="en_US")
    for row in df.to_dict("records"):
        for field, quantity, unit in (
            ("heart_rate_bpm", "HeartRate", "count/min"),
            ("speed_mps", "RunningSpeed", "m/s"),
            ("running_power_w", "RunningPower", "W"),
            ("spo2_percent", "OxygenSaturation", "%"),
        ):
            if pd.isna(row[field]):
                continue
            SubElement(
                root,
                "Record",
                {
                    "type": "HKQuantityTypeIdentifier" + quantity,
                    "sourceName": "RaceTime simulated sports watch — NOT real measurements",
                    "unit": unit,
                    "value": str(row[field] / 100 if field == "spo2_percent" else row[field]),
                    "startDate": row["timestamp"],
                    "endDate": row["timestamp"],
                },
            )
    indent(root)
    ElementTree(root).write(
        destination / "mountain-health.xml", encoding="utf-8", xml_declaration=True
    )
    (destination / "mountain-provenance.json").write_text(
        json.dumps(
            {
                "video": "Real first-person hiking footage, not footage of the user or a verified run.",
                "creator": "I Am Sorin",
                "source": "https://www.pexels.com/video/point-of-view-of-a-person-hiking-a-rocky-hill-6798218/",
                "license": "https://www.pexels.com/license/",
                "processing": "Downscaled to 1280x720 at 24 fps, H.264; no speed change, loops, inserted freezes, or scene generation.",
                "workout": "All speed, heart rate, cadence, power, oxygen, core temperature, altitude, coordinates, and dates are simulated, not inferred from footage or exported from a real watch.",
                "offset_s": 0,
                "scenario": "Heart rate rises from 134 to 168 bpm, then falls to 158 bpm; positive speed throughout.",
                "zone_lower_bounds_bpm": [120, 140, 160, 180],
                "zones": "Illustrative thresholds, not the user's or the filmed person's training zones.",
                "oxygen": "One simulated 98% spot reading at 0 seconds; no oxygen reading during the higher-zone interval.",
                "core_temperature": "Simulated external sensor reports 37.80–37.90 °C. CSV only. Not skin/ambient temperature or a heat-strain finding.",
                "devices": "Brand-neutral canonical CSV; no direct Garmin, COROS, Suunto or Apple Watch account integration. XML is an optional Apple Health-shaped subset.",
                "limitation": "Same demo timeline does not imply real correspondence between this hiker and simulated health signals. Not field-validation data.",
            },
            indent=2,
        )
        + "\n"
    )


if __name__ == "__main__":
    make_workout()
