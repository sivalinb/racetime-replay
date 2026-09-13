# Observability with Braintrust

Braintrust is the recommended application observability and evaluation workspace for this prototype. It can follow the evidence workflow, collect quality scores and support provider comparisons. Keep LangSmith as a separate course-specific integration where the handout requires it; a Braintrust trace is not proof of completing a LangSmith assignment.

## What each tool does

| Tool | Role here |
|---|---|
| OpenCV | Measures video locally |
| LangGraph | Orchestrates the bounded investigation |
| Gemini or Nebius Token Factory | Optional model-written draft |
| Braintrust | Trace review, scored experiments and later human feedback |
| Local JSON reports and pytest | Reproducible checks even when cloud services are unavailable |

## Implemented Python integration

Install `requirements-observability.txt`. Add `BRAINTRUST_API_KEY` and `BRAINTRUST_PROJECT_ID` to your ignored `.env`. The local workspace is preconfigured with the project ID supplied during onboarding. The public example leaves account identifiers blank.

```bash
python -m pip install -r requirements-observability.txt
PYTHONPATH=. python scripts/check_braintrust.py
# Include one bounded Nebius inference and verify its trace and token total:
PYTHONPATH=. python scripts/check_braintrust.py --provider nebius
PYTHONPATH=. python scripts/publish_braintrust_eval.py
```

The first script executes a synthetic investigation and creates spans during actual node execution. With `--provider nebius`, it includes one real cloud call and nests an `llm.nebius` span inside the answer node, recording duration, numeric token usage and a returned/failed outcome. Missing Braintrust credentials skip inference. After flushing, it reads the project logs and requires the exact root trace, expected span names and (when available) matching token totals before marking the run verified. Readback is bounded and incomplete ingestion stays unverified. The second imports the 50 previously measured development cases as a scored experiment, then reads back row IDs. Imported evaluation measurements are not presented as live spans. Both scripts require your API key; local reports distinguish missing configuration, submission and verified readback.

The app also has an explicit **Send synthetic demo telemetry to Braintrust** checkbox. It is disabled for uploaded recordings. Manual hooks in `replay/observability.py` log only allowlisted node names, result categories, evidence counts, provider labels and numeric token usage. They do not log question text, model drafts, full graph state, GPS coordinates, raw health samples, source filenames or images. Exceptions from telemetry preserve the local answer; application errors still propagate.

Braintrust supports automatic LangGraph instrumentation, but that normally captures inputs and outputs. This app deliberately uses bounded manual telemetry for its privacy requirements. Tests cover opt-in, user-upload exclusion, nested model spans, payload boundaries, service failure, application error propagation and exact-trace readback. Unrelated traces or mismatched token totals cannot pass verification. Remote visibility is never inferred solely from calling `flush()`.

## Connection status

The local project ID is configured. As of September 12, 2026, the Braintrust API key is still missing, so live Braintrust visibility has not been verified. The Nebius API key authenticates to Nebius only. Save a Braintrust API key as `BRAINTRUST_API_KEY` in the ignored local `.env`, then run the cloud trace check above. A successful Nebius inference alone does not establish Braintrust ingestion.

## Useful views and scores

- Trace duration by node: policy, routing, retrieval, investigation, composition and verification.
- Fallback rate and blocked-request rate, with benign and adversarial cases evaluated separately.
- Reference validity and unsupported-claim rate. A valid reference is necessary but does not prove factual accuracy.
- Gemini versus Nebius latency, token usage and human-reviewed usefulness on the same questions. Calculate cost from current provider prices; do not assume Braintrust knows pricing for every custom endpoint.
- Accepted or corrected event labels from consented review sessions, after a separate privacy review of any feedback export.

Human feedback export, provider-comparison dashboards, alert configuration and production monitoring are follow-up work. The current app stores event feedback locally. Braintrust does not replace infrastructure uptime, memory or disk monitoring.

## About the supplied shell command

The supplied `setup.sh` was downloaded and inspected. It installs the official interactive setup wizard from Braintrust's release repository and launches it. The project integrates the Python SDK directly, so the wizard was not executed and no second coding agent was launched. Markdown link syntax and escaped underscores in a copied command must be removed before using it in a terminal.

## Sources

- [Trace application logic](https://www.braintrust.dev/docs/instrument/trace-application-logic)
- [LangGraph integration](https://www.braintrust.dev/docs/integrations/agent-frameworks/langgraph)
- [Python SDK](https://www.braintrust.dev/docs/reference/sdks/python)
- [Official setup script](https://www.braintrust.dev/wizard/setup.sh)
