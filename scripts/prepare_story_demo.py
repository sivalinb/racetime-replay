"""Prepare two licensed, separate story clips and an explicitly simulated workout.

Run from the repository: python scripts/prepare_story_demo.py --ffmpeg /path/to/ffmpeg
The stream opener has no associated measurements. The rocky POV fixture is
illustrative: no measurement belongs to the person shown in the stock footage.
Original speed and chronology are preserved; only resolution/encoding change.
"""

import argparse
import hashlib
import json
import shutil
import subprocess
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SOURCES = {
    "rocky": {
        "url": "https://videos.pexels.com/video-files/4606798/4606798-uhd_2560_1440_24fps.mp4",
        "page": "https://www.pexels.com/video/a-hiker-walking-on-the-edge-of-a-cliff-4606798/",
        "creator": "K / Pexels",
        "license": "https://www.pexels.com/license/",
        "poster_s": 12,
    },
    "stream": {
        "url": "https://assets.mixkit.co/videos/44352/44352-720.mp4",
        "page": "https://mixkit.co/free-stock-video/couple-running-over-a-stream-44352/",
        "creator": "Mixkit",
        "license": "https://mixkit.co/license/",
        "poster_s": 2,
    },
}


def story_workout() -> pd.DataFrame:
    """Return invented readings on the 28.875-second rocky-video clock.

    The first peak is at 12 seconds, when the source clip shows boots crossing
    uneven rocks. This chosen alignment is a demo fixture, never field evidence.
    Optional signals are omitted rather than filled with invented sensor data.
    """
    seconds = np.arange(0, 29, 0.5)
    anchors = [0, 4, 8, 12, 18, 28.5]
    pace = np.interp(seconds, anchors, [8, 8.4, 9.5, 10.5, 10.2, 9.7])
    return pd.DataFrame(
        {
            "elapsed_s": seconds,
            "heart_rate_bpm": np.interp(seconds, anchors, [134, 137, 145, 154, 151, 146]),
            "speed_mps": 1000 / (60 * pace),
        }
    )


def main() -> None:
    """Download source assets when needed, then build local presentation media."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ffmpeg", default=shutil.which("ffmpeg"))
    parser.add_argument(
        "--sources", type=Path, help="Optional directory of already fetched sources"
    )
    args = parser.parse_args()
    if not args.ffmpeg:
        parser.error("Install FFmpeg or provide --ffmpeg /path/to/ffmpeg")
    output = ROOT / "demo/story"
    output.mkdir(parents=True, exist_ok=True)
    source_dir = args.sources or output / ".sources"
    source_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "status": "Real stock footage; all workout readings and zone thresholds are simulated.",
        "relationship": "Two independent examples, not one outing. The stream opener has no watch data.",
        "limits": "No automatic scene labels, medical conclusions, hazard alerts or proven improvements.",
        "sources": {},
    }
    for name, item in SOURCES.items():
        original = source_dir / ("rocky-pov-source.mp4" if name == "rocky" else "stream-source.mp4")
        if not original.exists():
            request = urllib.request.Request(
                item["url"], headers={"User-Agent": "RaceTime-Replay-Demo"}
            )
            with urllib.request.urlopen(request, timeout=60) as response:
                original.write_bytes(response.read())
        common = [args.ffmpeg, "-hide_banner", "-loglevel", "error", "-y"]
        subprocess.run(
            common
            + [
                "-i",
                str(original),
                "-vf",
                "scale=1280:-2",
                "-an",
                "-c:v",
                "libx264",
                "-preset",
                "fast",
                "-crf",
                "23",
                "-pix_fmt",
                "yuv420p",
                "-movflags",
                "+faststart",
                str(output / f"{name}.mp4"),
            ],
            check=True,
        )
        subprocess.run(
            common
            + [
                "-ss",
                str(item["poster_s"]),
                "-i",
                str(output / f"{name}.mp4"),
                "-frames:v",
                "1",
                "-update",
                "1",
                str(output / f"{name}-poster.jpg"),
            ],
            check=True,
        )
        manifest["sources"][name] = {
            **item,
            "source_sha256": hashlib.sha256(original.read_bytes()).hexdigest(),
            "prepared_sha256": hashlib.sha256((output / f"{name}.mp4").read_bytes()).hexdigest(),
        }
    story_workout().to_csv(output / "rocky-workout.csv", index=False)
    (output / "provenance.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Prepared story assets in {output}")


if __name__ == "__main__":
    main()
