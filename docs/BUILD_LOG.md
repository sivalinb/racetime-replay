# Build and iteration record

The user requested a Python computer-vision capstone combining runner footage and Apple Watch data, a GitHub repository, a product-focused main document, personal illustrations and week-by-week evidence. They confirmed Insta360 as the intended camera brand and said no matching personal video/workout export was available. They then requested a different image and clear coding guidelines and documentation.

The build used AI-assisted development to create separated ingestion, OpenCV, alignment, retrieval, agent, safety and UI modules. The first verified fixture exposed a useful tradeoff: requiring camera-motion support removed GPS-induced false stops but missed the first half-second of the planted stop. The initial routing suite passed 49 of 50 cases; a definition question containing the word stop was misrouted. Prioritizing definition intent fixed that development case. The final 50-case result is therefore a development-set result, not an untouched generalization estimate.

The independent LoRA experiment used separately worded synthetic training and test requests and completed a fixed training schedule once. Held-out accuracy improved from 52.5% to 60%, so the model was not promoted to the default route. The default rule router and learned model are not compared on different datasets as though they were the same experiment.

Both guardrail frameworks executed allowed and rejected examples. Hybrid retrieval and a Gemini synthesis were exercised on synthetic aggregate records. LangSmith rejected hosted trace ingestion with HTTP 429 because the account exceeded its monthly unique-trace allowance. Local per-node timings and evaluation artifacts were retained; no hosted trace success is claimed.

Browser verification exercised the replay event seek: clicking the conflict at 45 seconds updated the video timestamp, recorded speed and heart rate together. The replacement personal image uses the sunrise ultramarathon photo; new conceptual artwork uses the alternative photo references. Python code was formatted and linted with Ruff and the behavior suite was run. See machine-readable reports for measured results.

- Added an optional Nebius Token Factory provider after reviewing current official API and deprecation documentation. Six cloud-boundary tests passed; the live smoke runner records missing credentials rather than claiming success.
- Added a regression check ensuring event durations do not bridge missing video samples.

- Inspected the supplied Braintrust wizard script and integrated the Python SDK directly. Added manual synthetic-only tracing and a scored evaluation importer. Five telemetry-boundary tests passed; live service verification awaits credentials.

- Browser verification exercised both demo and uploaded-fixture paths, confirmed 5 events, timestamp seeking, cited answers, policy rejection and disabled Braintrust telemetry for uploads. Source changes invalidate cached review answers; answer text identifies its question.

- Public release uses a neutral workflow diagram. Personal photographs, generated identity artwork and the illustrated DOCX are excluded from the published source tree.
