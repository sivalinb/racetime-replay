# Router fine-tuning experiment

The measured local experiment uses `prajjwal1/bert-tiny`, a pretrained encoder, with a four-class sequence-classification head. It does not train a video model or generative LLM.

Labels: stops, signals, summary, knowledge. Training data: 144 authored synthetic requests. Final test data: 40 requests with separately authored wording. The test set was not used in optimizer updates. There is no independent human review, real-user test or statistical significance claim. Future tuning should introduce a separate development split and preserve a new untouched test set.

Both comparison arms begin with the same random seed and frozen pretrained encoder. Both train the classifier head on the same data, batches, epochs and optimizer. The LoRA arm additionally trains rank-8 query/value adapters. The notebook-equivalent Python script records losses, trainable parameters, per-class precision/recall/F1, confusion matrices, timing and predictions, then saves and merges the adapter.

| Arm | Accuracy | Macro F1 |
|---|---:|---:|
| Frozen encoder plus trained head | 52.5% | 0.522 |
| Same model plus LoRA | 60.0% | 0.596 |

These results demonstrate the experiment and its limits. They do not justify deploying the tuned router. The deterministic router remains the default. Load the experimental model explicitly with `replay.router.classify` only for comparison.

## Reproduce

```bash
python -m pip install -r training/requirements.txt
python training/train_router.py
```

This downloads the public base checkpoint and tokenizer on the first run. Local cached weights were used for the recorded experiment. Large model caches and weights are excluded from Git. The script regenerates adapter and merged weights. Results are in `reports/router-evaluation.json`.

## Course Qwen and LLaMA Factory variant

The Week 5 handout specifically demonstrates Qwen3-1.7B-Base through LLaMA Factory. That exact run is not the local experiment above. `prepare_qwen.py` creates ShareGPT training data and registration metadata from training rows only; `qwen_lora.yaml` supplies a starting LoRA configuration for a suitable GPU runtime.

```bash
python training/prepare_qwen.py
# Install LLaMA Factory from its official repository in a separate GPU environment.
llamafactory-cli train training/qwen_lora.yaml
```

Add a stratified development split before tuning, run the held-out evaluation on the same labels for both models, inspect per-class mistakes, merge the adapter with the official export workflow, and smoke-test inference. Treat this variant as pending until actual artifacts and held-out results exist. Do not describe the local BERT run as the handout's Qwen run.
