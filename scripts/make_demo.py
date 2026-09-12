"""Generate a reproducible synthetic fixture, not real runner footage."""

import json
from pathlib import Path

import cv2
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def make_demo(destination=None):
    dest = Path(destination or ROOT / "demo")
    dest.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(71)
    texture = rng.integers(0, 255, (360, 2000, 3), dtype=np.uint8)
    texture = cv2.GaussianBlur(texture, (7, 7), 0)
    for x in range(0, 2000, 70):
        cv2.line(texture, (x, 0), (x + 100, 360), (35, 85, 38), 14)
    # Video intentionally has a stop, a moving-camera GPS conflict and a frozen-camera interval.
    writer = cv2.VideoWriter(
        str(dest / "replay-demo.mp4"), cv2.VideoWriter_fourcc(*"avc1"), 12, (640, 360)
    )
    if not writer.isOpened():
        raise RuntimeError("H.264 encoder unavailable; install an OpenCV build with video support.")
    shift = 0
    for i in range(90 * 12):
        t = i / 12
        if not (20 <= t < 30 or 65 <= t < 69):
            shift += 2
        offset = shift % 1300
        frame = texture[:, offset : offset + 640].copy()
        cv2.rectangle(frame, (0, 0), (640, 40), (15, 28, 35), -1)
        cv2.putText(
            frame,
            "SYNTHETIC TEST FIXTURE - NOT RACE FOOTAGE",
            (12, 25),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.52,
            (245, 245, 245),
            1,
        )
        writer.write(frame)
    writer.release()
    times = np.arange(90, dtype=float)
    speed = np.full(90, 2.8)
    speed[20:30] = 0
    speed[45:50] = 0
    speed[75:81] = np.nan
    df = pd.DataFrame(
        {
            "elapsed_s": times,
            "speed_mps": speed,
            "heart_rate_bpm": 135 + 8 * np.sin(times / 18),
            "latitude": 40 + times * 0.00001,
            "longitude": -105 + times * 0.000015,
            "altitude_m": 1600 + times * 0.15,
        }
    )
    df.to_csv(dest / "workout.csv", index=False)
    (dest / "ground-truth.json").write_text(
        json.dumps(
            {
                "provenance": "Programmatically generated texture video and workout signals. No personal data.",
                "stop": [20, 30],
                "gps_conflict": [45, 50],
                "frozen_camera": [65, 69],
                "missing_speed": [75, 81],
                "duration_s": 90,
                "offset_s": 0,
                "limitation": "Tests mechanics only; not field validation or medical evidence.",
            },
            indent=2,
        )
    )
    print(dest)


if __name__ == "__main__":
    make_demo()
