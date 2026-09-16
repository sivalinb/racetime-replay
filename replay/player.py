"""Build a local player: one video clock drives every displayed measurement."""

import base64
import json
from pathlib import Path

UI = Path(__file__).with_name("ui")
PLAYER_COLUMNS = [
    "video_s",
    "heart_rate_bpm",
    "heart_rate_zone",
    "pace_min_km",
    "speed_mps",
    "cadence_spm",
    "altitude_m",
    "running_power_w",
    "spo2_percent",
    "spo2_sample_s",
    "core_temperature_c",
    "core_temperature_source",
    "core_temperature_sample_s",
]


def player_html(
    video_path: str | Path, aligned, events: list[dict], poster_path: str | Path | None = None
) -> str:
    """Embed only local media and measurements; this component has no network calls.

    Separate readable HTML/CSS/JS files keep presentation behavior reviewable.
    Unknown optional measurements serialize as null and remain visibly unknown.
    """
    media = base64.b64encode(Path(video_path).read_bytes()).decode("ascii")
    poster = ""
    if poster_path is not None:
        encoded = base64.b64encode(Path(poster_path).read_bytes()).decode("ascii")
        poster = f'poster="data:image/jpeg;base64,{encoded}"'
    rows = json.loads(aligned.reindex(columns=PLAYER_COLUMNS).to_json(orient="records"))
    payload = json.dumps(
        {
            "rows": rows,
            "events": events,
            "profile": aligned.attrs.get("heart_rate_zones"),
        }
    ).replace("<", "\\u003c")
    html = (UI / "player.html").read_text()
    for token, value in {
        "@@CSS@@": (UI / "player.css").read_text(),
        "@@JS@@": (UI / "player.js").read_text(),
        "@@MEDIA@@": media,
        "@@POSTER@@": poster,
        "@@DATA@@": payload,
    }.items():
        html = html.replace(token, value)
    return html
