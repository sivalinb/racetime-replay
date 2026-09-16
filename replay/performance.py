"""Transparent performance review from aligned samples, without a fitness score.

The comparison uses the first valid heart-rate sample and the first peak in the
clip. It is descriptive, not a causal model or proof of a training improvement.
Proposed experiments are templates for human review, not prescribed targets.
"""

import math

import pandas as pd

METRICS = {
    "heart_rate_bpm": ("Heart rate", "bpm"),
    "heart_rate_zone": ("Training zone", "zone"),
    "pace_min_km": ("Pace", "min/km"),
    "cadence_spm": ("Cadence", "steps/min"),
    "altitude_m": ("Elevation", "m"),
    "running_power_w": ("Running power", "W"),
    "core_temperature_c": ("Sensor-reported core temperature", "°C"),
    "spo2_percent": ("Blood oxygen · spot sample", "%"),
}


def clock(seconds: float) -> str:
    """Format the video clock; measurements retain their numeric timestamps."""
    return f"{int(seconds) // 60}:{int(seconds) % 60:02d}"


def display_value(field: str, value: float | None) -> str:
    """Keep missing values explicit and pace legible as minutes:seconds."""
    if value is None:
        return "No reading"
    if field == "pace_min_km":
        return clock(round(value * 60))
    if field == "heart_rate_zone":
        return f"Zone {value:.0f}"
    if field == "core_temperature_c":
        return f"{value:.2f}"
    return f"{value:g}"


def performance_review(aligned: pd.DataFrame, report: dict, simulated: bool = False) -> dict:
    """Return measured comparisons, an interpretation and a reviewable next step.

    No metric is carried forward from an earlier instant. Optional measurements
    have to exist at the compared times. Core temperature needs parser-validated
    provenance. Heart-rate zones require the user's supplied thresholds.
    """
    review = {
        "id": "P001",
        "data_status": "Simulated example" if simulated else "Uploaded recording · unvalidated",
        "status": "insufficient_evidence",
        "comparison": [],
        "observations": [],
        "interpretation": "A comparison needs at least two aligned heart-rate samples.",
        "experiments": [],
        "limits": [
            "A short clip cannot measure endurance, establish a cause, or prove an improvement.",
            "Video context requires human review; the app does not recognize terrain or technique.",
        ],
        "event_ids": [],
    }
    samples = aligned.dropna(subset=["heart_rate_bpm"]).sort_values("video_s")
    if len(samples) < 2:
        return review
    baseline = samples.iloc[0]
    peak = samples.loc[samples.heart_rate_bpm.idxmax()]
    if peak.video_s == baseline.video_s:
        review["interpretation"] = (
            "The first heart-rate sample is already the clip maximum. "
            "There is no later rise to compare; choose a longer recording."
        )
        return review

    def number(row, field):
        value = row.get(field)
        return round(float(value), 3) if pd.notna(value) and math.isfinite(value) else None

    for field, (label, unit) in METRICS.items():
        a, b = number(baseline, field), number(peak, field)
        review["comparison"].append(
            {
                "field": field,
                "metric": label,
                "unit": unit,
                "baseline": a,
                "peak": b,
                "change": round(b - a, 3) if a is not None and b is not None else None,
                "baseline_display": display_value(field, a),
                "peak_display": display_value(field, b),
            }
        )
    review.update(
        {
            "status": "needs_review",
            "baseline_s": float(baseline.video_s),
            "peak_s": float(peak.video_s),
            "event_ids": [
                e["id"] for e in report["events"] if e["kind"] == "heart_rate_zone_change"
            ],
        }
    )
    hr_change = peak.heart_rate_bpm - baseline.heart_rate_bpm
    review["observations"] = [
        f"Heart rate rose by {hr_change:g} bpm: {baseline.heart_rate_bpm:g} at "
        f"{clock(baseline.video_s)} → {peak.heart_rate_bpm:g} at {clock(peak.video_s)}.",
    ]
    paired = {m["field"]: m for m in review["comparison"]}
    conditions = []
    for field, phrase in [
        ("altitude_m", "recorded elevation increased"),
        ("running_power_w", "recorded running power increased"),
        ("pace_min_km", "pace became slower"),
    ]:
        change = paired[field]["change"]
        if change is not None and change > 0:
            conditions.append(phrase)
    review["interpretation"] = (
        "Heart rate rose while " + ", ".join(conditions) + ". "
        "This is a pattern to investigate, not evidence that any one signal caused the change."
        if conditions
        else "The heart-rate rise identifies a moment to inspect. The available readings do not explain its cause."
    )
    if paired["core_temperature_c"]["peak"] is not None:
        review["core_temperature_source"] = str(peak.core_temperature_source)
        review["limits"].append(
            "Core temperature is sensor-reported and separate from skin/ambient temperature. "
            "This clip does not establish heat strain or a temperature-performance relationship."
        )
    else:
        review["limits"].append("No core-temperature reading is available at the HR peak.")
    if paired["spo2_percent"]["peak"] is None:
        review["limits"].append(
            "No blood-oxygen reading exists at the HR peak. An earlier spot sample cannot explain this moment."
        )
    review["experiments"] = [
        {
            "title": "Test steadier effort on a comparable segment",
            "action": "Use your own training plan or coach's effort target. Compare a deliberately steadier attempt with this segment; do not chase a suggested heart-rate or temperature number.",
            "measure": "Compare segment time, time in your planned zone, perceived effort, and the video. Keep route, sensor setup and conditions as comparable as possible.",
            "success": "A similar segment time with fewer departures from the intended effort is a candidate improvement to verify over repeated sessions.",
        },
        {
            "title": "Review one visible technique change",
            "action": "Inspect the higher-effort moment for a concrete, visible adjustment to discuss with a coach, such as line choice. Record your observation before deciding what to change.",
            "measure": "Review the same section on another attempt alongside cadence, pace, power when recorded, and perceived effort.",
            "success": "Confirm a useful change across matched recordings; a single replay does not establish better technique.",
        },
    ]
    return review


def performance_document(review: dict) -> dict:
    """Expose the same measured brief to retrieval without changing its facts."""
    text = f"**{review['data_status']}** · " + " ".join(review["observations"])
    if review["comparison"]:
        text += (
            " Start → HR peak: "
            + "; ".join(
                f"{m['metric']} {m['baseline_display']} → {m['peak_display']} {m['unit']}"
                for m in review["comparison"]
            )
            + ". "
        )
    text += (
        "\n\n**Interpretation:** " + review["interpretation"] + "\n\n" + " ".join(review["limits"])
    )
    if review["experiments"]:
        experiment = review["experiments"][0]
        text += (
            f"\n\nProposed experiment for review: {experiment['title']}. {experiment['measure']}"
        )
    return {"id": review["id"], "text": text, "source": "aligned-measurements:performance-review"}
