# Developer guide

## Design principles

The application is Python-first. Keep acquisition, measurement, inference, safety, presentation and evaluation in separate modules. Functions crossing module boundaries have type hints and docstrings. Dataframes follow the named schemas in DATA_GUIDE.md. Use explicit units in field names, pure transformations where practical, and clear errors at input boundaries.

Use snake_case functions, PascalCase classes and UPPER_CASE constants. Prefer a short function with one purpose over hidden mutation. Do not put business logic in the player template. Treat every uploaded field, transcript and model response as untrusted. Never catch and silently discard an error in the analysis path. The bounded agent catches external router/retrieval/provider failures only to record a fallback or retain known evidence; exception types are reported without leaking secrets.

Format and lint with Ruff. Tests should verify meaningful behavior, including sparse samples, offsets, unit conversion, malformed XML, citation allowlists, policy rejection and tool failure. Do not assert that an LLM is correct merely because its output is fluent. No real health or precise-location fixtures belong in the repository.

## Module responsibilities

| Module | Responsibility |
|---|---|
| `replay/ingest.py` | Bounded CSV, GPX and Health XML parsing, units and timestamps |
| `replay/vision.py` | OpenCV decoding, optical flow, quality measurements and evidence frames |
| `replay/analysis.py` | Alignment, explicit missing values, interval detection and summary |
| `replay/retrieval.py` | Versioned corpus, lexical/dense retrieval and persisted vectors |
| `replay/agent.py` | LangGraph routing, tool fallbacks, synthesis, reference verification and node timings |
| `replay/llm.py` | Explicit Gemini/Nebius provider boundary, bounded text payloads, timeouts and token usage |
| `replay/observability.py` | Opt-in Braintrust spans with allowlisted synthetic telemetry |
| `replay/safety.py` | Local trust boundaries, redaction and output schema |
| `replay/framework_guards.py` | Executable NeMo input rail and Guardrails AI schema checks |
| `replay/router.py` | Optional locally trained classifier inference |
| `replay/player.py` | Python-rendered sandboxed player; small JavaScript layer follows the video clock |
| `app.py` | Streamlit session orchestration and review controls |
| `scripts/` | Reproducible fixtures, evaluation and integration checks |
| `training/` | Reproducible LoRA experiment and separate Qwen course recipe |

## Agent execution

The graph follows input policy → route → retrieve → investigate → compose → verify. Four permitted tools cover stops, signals, summary and knowledge. The default router is deterministic and inspectable. The optional learned router can be supplied through `build_agent(index, router=classify)`; it remains experimental because held-out results are weak. Cloud synthesis is optional and does not replace canonical measured observations.

An in-memory checkpointer retains graph state within the Streamlit session. Rebuilding the evidence index after new uploads or alignment changes starts a new graph. State does not survive server restart. Event review decisions are stored in a per-session local directory. This is bounded agentic orchestration, not a general autonomous agent with arbitrary tools or shell access.

## Safe extension example

To add a new event type, first define its measured evidence, uncertainty and expected failure modes. Add a pure function and independently labeled test cases, then expose the result as a bounded evidence record. Update retrieval text and the agent's tool allowlist. Require a reference to every new claim. Do not add a natural-language instruction field that can authorize a tool action.

A vision-model extension should return structured observations with clip timestamps, model version and review state. Do not overwrite numeric measurements or treat a visual label as physiological ground truth. Persist the distinction between measured, model-suggested and human-confirmed evidence.

## Commands

```bash
python -m pytest -q
ruff check .
ruff format --check .
PYTHONPATH=. python scripts/evaluate.py
PYTHONPATH=. python scripts/check_guardrails.py
PYTHONPATH=. python scripts/check_integrations.py
```

`check_integrations.py` may send only synthetic aggregate evidence to the configured model. Add `--trace` only when you want to test synthetic LangSmith tracing; success requires server readback. The verified initial attempt hit the account's monthly trace quota. Local node timing evidence is saved regardless of cloud tracing.

See [Nebius integration](NEBIUS.md) for provider configuration and fake-transport tests. No live provider is called by the unit tests.
