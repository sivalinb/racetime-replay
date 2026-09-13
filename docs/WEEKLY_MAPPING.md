# Six week curriculum mapping

This table distinguishes working code, measured evidence and unfinished external requirements. It does not claim course certification or submission.

| Week | Learning demonstrated | Code and evidence | Status |
|---|---|---|---|
| 1 Data application | Python app, dataset import, charts, filters, interactive video, iterative AI-assisted development | [App](../app.py), [player](../replay/player.py), [data guide](DATA_GUIDE.md), [build log](BUILD_LOG.md) | Implemented and UI checked; a presentation script is supplied, but no narrated Loom is recorded |
| 2 RAG | Defined corpus, cleaning into bounded event passages, lexical and dense embedding retrieval, persisted vectors, cited answers and insufficient-evidence behavior | [Retrieval](../replay/retrieval.py), [corpus](knowledge.json), [verified integration report](../reports/integrations.json) | Hybrid MiniLM and TF-IDF executed; corpus is small; broader retrieval benchmark remains future work |
| 3 Agentic systems | Stateful LangGraph, routed evidence tools, checkpoints, failure recovery, evidence validation, human event review | [Agent](../replay/agent.py), [behavior tests](../tests/test_core.py), [developer guide](DEVELOPER_GUIDE.md) | Implemented bounded workflow; default router and canonical answer are deterministic; optional model-written draft verified |
| 4 Evaluation | Versioned authored cases, quality and latency metrics, source-conflict baseline, failure analysis and measured improvements | [50-case report](../reports/evaluation.json), [evaluation runner](../scripts/evaluate.py), [integration check](../scripts/check_integrations.py) | Local evaluation complete; LangSmith hosted trace proof blocked by monthly account quota; data is synthetic and not independently human-labeled |
| 5 Fine tuning | Labeled routing dataset, frozen baseline, rank-8 LoRA, loss and per-class metrics, adapter save/merge | [Training script](../training/train_router.py), [dataset](../training/dataset.json), [measured report](../reports/router-evaluation.json), [course variant](../training/qwen_lora.yaml) | BERT-tiny LoRA experiment executed, 52.5% to 60% accuracy; exact Qwen3/LLaMA-Factory handout run is supplied as a recipe and NOT executed |
| 6 Safety and deployment | Threats, hallucination boundaries, prompt injection, NeMo input rail, Guardrails AI schema, privacy, adversarial tests, governance and release gate | [Safety](SAFETY.md), [framework code](../replay/framework_guards.py), [framework results](../reports/guardrails-evaluation.json), [release checklist](RELEASE.md) | Local controls and framework checks executed; real-run and production validation remain outstanding |

## Submission assets

[Product explanation](PRODUCT.md), [five-minute walkthrough script](DEMO_SCRIPT.md), [code](https://github.com/sivalinb/racetime-replay), test reports and architecture are supplied. The user retains control of course submission, video narration and any instructor communications.

## Scope of the evidence

The handouts include example projects and specific tooling. This is a custom capstone adapting those learning objectives. Its small encoder LoRA experiment is not the Qwen generative-model training exercise. A framework configuration is not counted as executed unless its report exists. Local node timing is not a substitute for a verified hosted LangSmith trace. No real runner video or Watch export was supplied, so field performance is unmeasured.

## Nebius extension
[Token Factory integration](NEBIUS.md) adds provider selection, bounded text synthesis, token usage, timeout recovery and transport tests. A live synthetic inference check succeeded on September 12, 2026 with Qwen3-30B-A3B-Instruct-2507 (481 tokens, about 5.5 seconds; existing schema and citation checks passed). This verifies one integration path, not answer quality; the model exceeded the requested three sentences. See the [recorded result](../reports/nebius-integration.json). Vision, hosted fine-tuning and model comparison are documented extensions.

## Braintrust observability
[Braintrust integration](OBSERVABILITY.md) adds optional real node spans and a scored synthetic evaluation importer with server readback. Local boundary tests passed. On September 12, 2026, API readback verified one live synthetic Nebius trace with all eight spans and matching 163-token usage. See the [verification report](../reports/braintrust-integration.json). Braintrust does not replace course-specific LangSmith proof; scored experiment import remains separate.
