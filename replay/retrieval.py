"""Hybrid retrieval over bounded event records and a documented knowledge corpus."""

import json
from pathlib import Path

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

from replay.performance import performance_document

ROOT = Path(__file__).resolve().parents[1]


def event_document(event: dict) -> dict:
    """Describe measured facts consistently, including on retrieval failure."""
    text = (
        f"{event['kind']} from {event['start_s']} to {event['end_s']} seconds. "
        f"Duration {event['duration_s']} seconds. Measured candidate; human review needed."
    )
    if event["kind"] == "heart_rate_zone_change":
        profile = event.get("profile") or {}
        text = (
            f"Heart rate enters zone {event['to_zone']} from zone {event['from_zone']} "
            f"at {event['start_s']} seconds and stays in that band until {event['end_s']} seconds. "
            f"Recorded heart rate in this interval: {event['min_hr_bpm']:g}–"
            f"{event['peak_hr_bpm']:g} bpm. "
            f"Zone profile: {profile.get('source', 'supplied thresholds')}; "
            f"lower bounds for zones 2–5: {profile.get('lower_bounds_bpm', [])} bpm. "
            "Review the matching video for visible context. The readings do not establish "
            "a climb, terrain difficulty, fatigue, recovery or the cause of the change."
        )
        units = {
            "pace_min_km": "pace (decimal min/km)",
            "cadence_spm": "cadence (steps/min)",
            "altitude_m": "elevation (m)",
            "running_power_w": "running power (W)",
            "spo2_percent": "intermittent SpO2 (%)",
            "core_temperature_c": "sensor-reported core temperature (°C)",
        }
        ranges = event.get("context_ranges", {})
        if ranges:
            text += (
                " Available context: "
                + "; ".join(
                    f"{units[key]} {values['min']:g}–{values['max']:g}"
                    for key, values in ranges.items()
                    if key in units
                )
                + "."
            )
        if "spo2_percent" not in ranges:
            text += " No blood-oxygen reading is available in this interval."
        if event.get("core_temperature_sources"):
            text += (
                " Core-temperature source: " + "; ".join(event["core_temperature_sources"]) + "."
            )
            text += " This is not skin or ambient temperature and does not establish heat strain."
    return {
        "id": event["id"],
        "text": text,
        "source": f"video:{event['start_s']}-{event['end_s']}",
    }


def documents(report: dict) -> list[dict]:
    """Combine versioned explanatory passages with bounded measured event records."""
    docs = json.loads((ROOT / "docs/knowledge.json").read_text())
    for event in report["events"]:
        docs.append(event_document(event))
    if report.get("performance_review"):
        docs.append(performance_document(report["performance_review"]))
    return docs


class EvidenceIndex:
    def __init__(self, docs, dense=False):
        self.docs = docs
        self.vectorizer = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True)
        self.sparse = self.vectorizer.fit_transform([d["text"] for d in docs])
        self.encoder = None
        self.dense = None
        self.mode = "TF-IDF lexical retrieval"
        if dense:
            from sentence_transformers import SentenceTransformer

            self.encoder = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
            self.dense = self.encoder.encode([d["text"] for d in docs], normalize_embeddings=True)
            self.mode = "Hybrid MiniLM dense + TF-IDF"

    def search(self, query: str, top_k: int = 4) -> list[dict]:
        """Rank evidence using lexical or hybrid scores and reject zero-support hits."""
        sparse = (self.sparse @ self.vectorizer.transform([query]).T).toarray().ravel()
        scores = sparse
        if self.encoder is not None:
            q = self.encoder.encode([query], normalize_embeddings=True)[0]
            scores = 0.5 * sparse + 0.5 * np.maximum(0, self.dense @ q)
        order = np.argsort(-scores)[:top_k]
        return [
            dict(self.docs[i], score=round(float(scores[i]), 4)) for i in order if scores[i] > 0.025
        ]

    def persist(self, destination: str | Path) -> None:
        """Persist corpus and dense vectors for reproducible inspection."""
        destination = Path(destination)
        destination.mkdir(parents=True, exist_ok=True)
        (destination / "documents.json").write_text(json.dumps(self.docs, indent=2))
        if self.dense is not None:
            np.save(destination / "embeddings.npy", self.dense)
