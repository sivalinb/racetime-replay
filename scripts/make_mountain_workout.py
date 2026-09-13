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
    """Write paired 1 Hz demo exports, including deliberate sensor error cases."""
    destination.mkdir(parents=True, exist_ok=True)
    seconds = np.arange(60)
    # Gentle climb scenario: the values illustrate a timeline, not a measured run.
    true_demo_speed = 1.8 + 0.2 * np.sin(seconds / 6)
    recorded_speed = true_demo_speed.copy()
    recorded_speed[20:27] = 0  # Deliberate false zero while the camera moves.
    recorded_speed[43:51] = np.nan  # Missing speed; HR remains available.
    hr = np.rint(138 + 0.35 * seconds + 3 * np.sin(seconds / 9)).astype(int)
    distance = np.cumsum(true_demo_speed) - true_demo_speed[0]
    start = datetime(2026, 8, 1, 7, 0, tzinfo=UTC)
    timestamps = [start + timedelta(seconds=int(t)) for t in seconds]
    df = pd.DataFrame(
        {
            "timestamp": [t.isoformat() for t in timestamps],
            "elapsed_s": seconds,
            "speed_mps": np.round(recorded_speed, 3),
            "heart_rate_bpm": hr,
            "latitude": 40 + distance / 111320,
            "longitude": -105 + 0.00012 * np.sin(seconds / 18),
            "altitude_m": 1600 + distance * 0.1,
        }
    )
    df.to_csv(destination / "mountain-workout.csv", index=False)
    root = Element("HealthData", locale="en_US")
    for row in df.to_dict("records"):
        for field, quantity, unit in (
            ("heart_rate_bpm", "HeartRate", "count/min"),
            ("speed_mps", "RunningSpeed", "m/s"),
        ):
            if pd.isna(row[field]):
                continue
            SubElement(
                root,
                "Record",
                {
                    "type": "HKQuantityTypeIdentifier" + quantity,
                    "sourceName": "RaceTime simulated watch — NOT Apple Watch measurements",
                    "unit": unit,
                    "value": str(row[field]),
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
                "workout": "All speed, heart rate, altitude, coordinates, and dates are simulated, not inferred from footage or exported from a real watch.",
                "offset_s": 0,
                "mock_zero_speed_s": [20, 27],
                "mock_missing_speed_s": [43, 51],
                "limitation": "Same demo timeline does not imply real correspondence between this hiker and simulated health signals. Not field-validation data.",
            },
            indent=2,
        )
        + "\n"
    )


if __name__ == "__main__":
    make_workout()
