"""OpenCV measurements are pixel-motion observations, never athlete diagnoses."""

from pathlib import Path

import cv2
import numpy as np
import pandas as pd


def analyze_video(
    path: str | Path, sample_hz: float = 2.0, max_seconds: int = 900
) -> tuple[pd.DataFrame, dict]:
    """Decode a bounded recording and measure motion and quality at sampled frames."""
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        raise ValueError("Cannot decode video. Export a standard MP4 H.264 file.")
    fps = float(cap.get(cv2.CAP_PROP_FPS))
    count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if not np.isfinite(fps) or fps <= 0 or count <= 0:
        cap.release()
        raise ValueError("Video has invalid timing metadata.")
    duration = count / fps
    if duration > max_seconds:
        cap.release()
        raise ValueError(f"Trim video to {max_seconds // 60} minutes for this prototype.")
    step = max(1, round(fps / sample_hz))
    rows, prev = [], None
    try:
        for frame_no in range(0, count, step):
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_no)
            ok, frame = cap.read()
            if not ok:
                continue
            gray = cv2.cvtColor(cv2.resize(frame, (320, 180)), cv2.COLOR_BGR2GRAY)
            # Decode timestamps when available; nominal FPS is fallback only.
            decoded = float(cap.get(cv2.CAP_PROP_POS_MSEC)) / 1000
            t = decoded if decoded > 0 else frame_no / fps
            motion = difference = np.nan
            if prev is not None:
                flow = cv2.calcOpticalFlowFarneback(prev, gray, None, 0.5, 3, 15, 3, 5, 1.2, 0)
                motion = float(np.median(np.linalg.norm(flow, axis=2)))
                difference = float(np.mean(cv2.absdiff(prev, gray)))
            rows.append(
                {
                    "video_s": t,
                    "motion_px": motion,
                    "frame_difference": difference,
                    "sharpness": float(cv2.Laplacian(gray, cv2.CV_64F).var()),
                    "brightness": float(gray.mean()),
                }
            )
            prev = gray
    finally:
        cap.release()
    if len(rows) < 2:
        raise ValueError("Too few decoded frames for motion analysis.")
    return pd.DataFrame(rows), {
        "fps": fps,
        "duration_s": duration,
        "sample_hz": fps / step,
        "frames_analyzed": len(rows),
        "timing": "Decoder timestamps with nominal FPS fallback",
    }


def thumbnail(path: str | Path, seconds: float) -> np.ndarray | None:
    """Return a local RGB evidence frame, or None when decoding fails."""
    cap = cv2.VideoCapture(str(path))
    try:
        cap.set(cv2.CAP_PROP_POS_MSEC, max(0, seconds) * 1000)
        ok, frame = cap.read()
        if not ok:
            return None
        return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    finally:
        cap.release()
