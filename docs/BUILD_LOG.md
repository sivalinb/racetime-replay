# Build and iteration record

The project combines runner footage and workout exports in a documented Python application. Its development record distinguishes implemented behavior, synthetic measurements and remaining field validation.

The build used AI-assisted development to create separated ingestion, OpenCV, alignment, retrieval, agent, safety and UI modules. The first verified fixture exposed a useful tradeoff: requiring camera-motion support removed GPS-induced false stops but missed the first half-second of the planted stop. The initial routing suite passed 49 of 50 cases; a definition question containing the word stop was misrouted. Prioritizing definition intent fixed that development case. The final 50-case result is therefore a development-set result, not an untouched generalization estimate.

The independent LoRA experiment used separately worded synthetic training and test requests and completed a fixed training schedule once. Held-out accuracy improved from 52.5% to 60%, so the model was not promoted to the default route. The default rule router and learned model are not compared on different datasets as though they were the same experiment.

Both guardrail frameworks executed allowed and rejected examples. Hybrid retrieval and a Gemini synthesis were exercised on synthetic aggregate records. LangSmith rejected hosted trace ingestion with HTTP 429 because the account exceeded its monthly unique-trace allowance. Local per-node timings and evaluation artifacts were retained; no hosted trace success is claimed.

Browser verification confirmed that seeking to an event updates video, speed and heart rate together. Python code was formatted and linted with Ruff and the behavior suite was run. See machine-readable reports for measured results.

- Added an optional Nebius Token Factory provider and cloud-boundary tests. The later credentialed integration check succeeded; [the report](../reports/nebius-integration.json) records its latency, token usage and limits.
- Added a regression check ensuring event durations do not bridge missing video samples.

- Integrated the Braintrust Python SDK with manual synthetic-only tracing and a scored evaluation importer. Later API readback verified all eight spans and matching token usage for one Nebius investigation; see [the verification report](../reports/braintrust-integration.json).

- Browser verification exercised bundled and uploaded-fixture paths, timestamp seeking, cited answers, policy rejection and disabled Braintrust telemetry for uploads. Source changes invalidate cached review answers; answer text identifies its question.

- Public release uses a neutral workflow diagram. Personal photographs, generated identity artwork and the illustrated DOCX are excluded from the published source tree.
