"""Optional LoRA-trained request classifier; deliberately not the production default."""

from functools import lru_cache
from pathlib import Path

LABELS = ["stops", "signals", "summary", "knowledge"]


@lru_cache(maxsize=1)
def load_router(model_path: str):
    """Load locally merged model weights and tokenizer once per process."""
    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    path = Path(model_path)
    if not path.is_dir():
        raise FileNotFoundError("Run training/train_router.py to create the experimental router.")
    return (
        AutoTokenizer.from_pretrained(path, local_files_only=True),
        AutoModelForSequenceClassification.from_pretrained(path, local_files_only=True).eval(),
    )


def classify(question: str, model_path: str | None = None) -> str:
    """Predict one of four routing labels; returns no physiological or visual judgment."""
    import torch

    path = model_path or str(Path(__file__).resolve().parents[1] / "training/merged")
    tokenizer, model = load_router(path)
    inputs = tokenizer(question, return_tensors="pt", truncation=True, max_length=64)
    with torch.no_grad():
        logits = model(**inputs).logits
    return LABELS[int(logits.argmax(-1).item())]
