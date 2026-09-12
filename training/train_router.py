"""Reproducible, small LoRA experiment; no video understanding is claimed.
Compare equally trained classifier heads: frozen encoder vs LoRA encoder.
Authored synthetic data, template-disjoint test set; not a real-user benchmark.
"""

import hashlib
import json
import random
import time
from pathlib import Path

import numpy as np
import torch
from peft import LoraConfig, TaskType, get_peft_model
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_recall_fscore_support,
)
from transformers import AutoTokenizer, BertConfig, BertForSequenceClassification

ROOT = Path(__file__).resolve().parent
MODEL = "prajjwal1/bert-tiny"
LABELS = ["stops", "signals", "summary", "knowledge"]
SEED = 42
random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)
torch.set_num_threads(4)
subjects = [
    "this run",
    "the morning session",
    "the selected recording",
    "my workout",
    "the trail video",
    "this interval",
]
patterns = {
    "stops": [
        "Find stops in {}.",
        "Show pauses in {}.",
        "How long was I stationary during {}?",
        "Find waiting time in {}.",
        "List stopped intervals for {}.",
        "Inspect the stop candidates in {}.",
    ],
    "signals": [
        "Find missing samples in {}.",
        "Do video and GPS disagree in {}?",
        "Check synchronization in {}.",
        "Inspect sensor conflicts in {}.",
        "Look for frozen frames in {}.",
        "Identify data gaps in {}.",
    ],
    "summary": [
        "Summarize {}.",
        "Give me a recap of {}.",
        "What happened during {}?",
        "List the main events of {}.",
        "Show notable moments from {}.",
        "Give an overview of {}.",
    ],
    "knowledge": [
        "Explain how optical flow works for {}.",
        "What does sample tolerance mean for {}?",
        "How does privacy work for {}?",
        "Explain workout export for {}.",
        "What does the future roadmap add to {}?",
        "How are video measurements computed for {}?",
    ],
}
train = [
    {"text": p.format(s), "label": label, "split": "train"}
    for label, ps in patterns.items()
    for p in ps
    for s in subjects
]
tests = {
    "stops": [
        "Locate intervals where I was not moving.",
        "Find the time spent standing still.",
        "Which pauses lasted longest?",
        "Show me when I stopped to wait.",
        "Add up the stationary sections.",
        "Review the candidate halt at twenty seconds.",
        "Find places where my progress stopped.",
        "Was there a pause in the footage?",
        "Show stop timestamps.",
        "Give me a breakdown of waiting.",
    ],
    "signals": [
        "The watch and camera tell different stories.",
        "Are the clocks aligned?",
        "Which readings are absent?",
        "Does this file contain repeated frames?",
        "Could a GPS dropout explain the disagreement?",
        "Show intervals with conflicting sensors.",
        "Check for clock offset.",
        "Where does the speed stream disappear?",
        "Investigate the frozen recording.",
        "Review gaps in watch measurements.",
    ],
    "summary": [
        "Catch me up on this recording.",
        "What are the key observations?",
        "Brief me on the workout timeline.",
        "Tell me the recorded sequence.",
        "Give me a concise session report.",
        "What deserves a closer look?",
        "Describe the measured events.",
        "Make a short overview of the activity.",
        "Recap the run for me.",
        "Summarize all observations.",
    ],
    "knowledge": [
        "Define optical flow.",
        "Explain the stop detection algorithm.",
        "What information does Apple Health export?",
        "How are private locations protected?",
        "Why do empty samples remain blank?",
        "What are the limitations of motion analysis?",
        "Describe the planned vision extension.",
        "How does the app compare timestamps?",
        "What is a nearest-sample tolerance?",
        "Explain what this system cannot conclude.",
    ],
}
heldout = [
    {"text": text, "label": label, "split": "test"}
    for label, requests in tests.items()
    for text in requests
]
ROOT.mkdir(exist_ok=True)
(ROOT / "dataset.json").write_text(
    json.dumps(
        {
            "provenance": "Author-created synthetic routing requests. Test wording authored separately from training templates. No external race data.",
            "train": train,
            "test": heldout,
        },
        indent=2,
    )
)
cache = ROOT / "cache"
cache.mkdir(exist_ok=True)
tok = AutoTokenizer.from_pretrained("google-bert/bert-base-uncased", cache_dir=cache)
X = tok(
    [x["text"] for x in train],
    padding=True,
    truncation=True,
    max_length=64,
    return_tensors="pt",
)
Y = torch.tensor([LABELS.index(x["label"]) for x in train])
T = tok(
    [x["text"] for x in heldout],
    padding=True,
    truncation=True,
    max_length=64,
    return_tensors="pt",
)
TY = [LABELS.index(x["label"]) for x in heldout]
results = {}
predictions = {}
for mode in ["frozen_encoder", "lora"]:
    torch.manual_seed(SEED)
    model = BertForSequenceClassification.from_pretrained(
        MODEL,
        config=BertConfig.from_pretrained(MODEL, num_labels=4, cache_dir=cache),
        cache_dir=cache,
    )
    for p in model.parameters():
        p.requires_grad = False
    for p in model.classifier.parameters():
        p.requires_grad = True
    if mode == "lora":
        model = get_peft_model(
            model,
            LoraConfig(
                task_type=TaskType.SEQ_CLS,
                r=8,
                lora_alpha=16,
                lora_dropout=0.05,
                target_modules=["query", "value"],
                modules_to_save=["classifier"],
            ),
        )
    optimizer = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad], lr=0.002)
    started = time.monotonic()
    losses = []
    model.train()
    for epoch in range(16):
        order = torch.randperm(len(Y), generator=torch.Generator().manual_seed(SEED + epoch))
        for ids in order.split(24):
            optimizer.zero_grad()
            out = model(**{k: v[ids] for k, v in X.items()}, labels=Y[ids])
            out.loss.backward()
            optimizer.step()
            losses.append(float(out.loss.detach()))
    model.eval()
    with torch.no_grad():
        pred = model(**T).logits.argmax(-1).tolist()
    precision, recall, f1, _ = precision_recall_fscore_support(
        TY, pred, labels=list(range(4)), zero_division=0
    )
    results[mode] = {
        "accuracy": accuracy_score(TY, pred),
        "macro_f1": f1_score(TY, pred, average="macro"),
        "precision_by_label": dict(zip(LABELS, precision.tolist(), strict=True)),
        "recall_by_label": dict(zip(LABELS, recall.tolist(), strict=True)),
        "f1_by_label": dict(zip(LABELS, f1.tolist(), strict=True)),
        "confusion_matrix": confusion_matrix(TY, pred, labels=list(range(4))).tolist(),
        "trainable_parameters": sum(p.numel() for p in model.parameters() if p.requires_grad),
        "train_seconds": round(time.monotonic() - started, 3),
        "initial_loss": losses[0],
        "final_loss": losses[-1],
        "steps": len(losses),
    }
    predictions[mode] = [
        {"text": x["text"], "expected": x["label"], "predicted": LABELS[y]}
        for x, y in zip(heldout, pred, strict=True)
    ]
    if mode == "lora":
        model.save_pretrained(ROOT / "checkpoints" / "adapter")
        tok.save_pretrained(ROOT / "checkpoints" / "adapter")
        merged = model.merge_and_unload()
        merged.save_pretrained(ROOT / "merged")
        tok.save_pretrained(ROOT / "merged")
    print(mode, json.dumps(results[mode]), flush=True)
report = {
    "model": MODEL,
    "base_revision": getattr(model.config, "_commit_hash", None),
    "seed": SEED,
    "labels": LABELS,
    "train_count": len(train),
    "test_count": len(heldout),
    "comparison": "Identical frozen pretrained encoder and classifier initialization; classifier trained in both arms. LoRA arm additionally trains rank-8 query/value adapters. Same data, batches, epochs and optimizer learning rate.",
    "limitations": [
        "Small authored synthetic dataset; no independent human review.",
        "One seed, one split; no significance or real-user generalization claim.",
        "Encoder classifier experiment, not a generative LLM or video model.",
        "No deployment decision was made using training accuracy.",
    ],
    "results": results,
    "predictions": predictions,
    "dataset_sha256": hashlib.sha256((ROOT / "dataset.json").read_bytes()).hexdigest(),
}
(ROOT.parent / "reports" / "router-evaluation.json").write_text(json.dumps(report, indent=2))
