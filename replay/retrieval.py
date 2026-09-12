"""Hybrid retrieval over bounded event records and a documented knowledge corpus."""

import json
from pathlib import Path

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

ROOT = Path(__file__).resolve().parents[1]


def documents(report: dict) -> list[dict]:
    """Combine versioned explanatory passages with bounded measured event records."""
    docs = json.loads((ROOT / "docs/knowledge.json").read_text())
    for event in report["events"]:
        docs.append(
            {
                "id": event["id"],
                "text": f"{event['kind']} from {event['start_s']} to {event['end_s']} seconds. Duration {event['duration_s']} seconds. Measured candidate; human review needed.",
                "source": f"video:{event['start_s']}-{event['end_s']}",
            }
        )
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
