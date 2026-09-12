# Safety privacy and governance

## Intended use and audience

Post-run review for athletes, coaches and engineering learners. The current release is a local prototype with a synthetic public demonstration. It is not a medical device, live hazard detector or autonomous training coach.

## Threat model

| Boundary | Risk | Implemented control | Remaining limitation |
|---|---|---|---|
| Uploaded files | Malformed input and oversized media | Extension/size/duration limits, defused XML, bounded frame sampling | Native decoders need normal patching; public uploads need isolated workers |
| Untrusted content | Prompt injection through questions or future OCR/transcripts | Deterministic input policies; no arbitrary shell/network tools; evidence-reference allowlist | Regex detection is incomplete; tool permissions are the stronger boundary |
| Generated output | Unsupported facts or citations | Canonical measured evidence remains primary; schema/citation validation; cloud text labeled draft | Schema validity does not prove semantic factuality |
| Health and location | Disclosure in telemetry or publication | Local processing by default, no external map service, raw automatic tracing disabled | Redaction is best effort; no public raw-data upload is part of this demo |
| Session storage | Residual media and review notes | Per-session directories; delete control; abandoned directory cleanup after 24 hours on app activity | No cryptographic erasure or enterprise retention guarantee |
| Model routing | Misrouting | Bounded tools and deterministic default; learned router experimental | Unknown queries can map to broad summary; inspect evidence |

## Framework execution

Install `requirements-safety.txt` and set `REPLAY_FRAMEWORK_GUARDS=true` to run the actual NeMo input rail and Guardrails AI output validator inside the agent. NeMo's custom action executes the local policy; a fake passthrough LLM makes this particular policy test reproducible without a provider. It is explicitly not an LLM-based attack classifier. Guardrails AI validates response structure; the local allowlist validates citations. `reports/guardrails-evaluation.json` records allowed and blocked examples.

## Privacy choices

Uploads, exact coordinates, video and raw Health XML stay on the machine running the Python process. If deployed on a server, that server is the processing machine: do not describe server uploads as on-device processing. The optional cloud checkbox sends a redacted question plus aggregate event evidence to the selected Gemini or Nebius provider. It does not send video, raw Health records or coordinates. Free-form questions may still contain sensitive text not caught by the limited redactor; review inputs before opting in.

Automatic LangGraph/LangSmith tracing of real sessions is disabled. Integration scripts use only authored synthetic fixtures. Public demo deployment should set `REPLAY_ALLOW_UPLOADS=false` and should not contain API credentials. Do not upload raw health exports, location tracks, identifying bystander footage or private keys to GitHub. Personal story imagery is separate from evaluation data.

GDPR and HIPAA applicability depends on the deployment, jurisdiction, relationships and processed data. This prototype does not claim compliance. A deployment assessment would need purpose and legal-basis review where applicable, access controls, contracts with processors, deletion/retention verification and an incident response process. No compliance badge follows from running a PII regex.

## Red teaming and governance

The suite includes instruction overrides, secret requests, medical requests, invalid output and unknown citations, plus malformed files and source disagreements. Test results are bounded to those cases. Add independently authored attacks and real consented recordings before deployment. Measure both attack blocking and benign-request rejection.

The repository owner is the proposed release decision-maker. An athlete or coach confirms event interpretations. Store model/prompt/dataset versions with evaluation reports. Document unresolved risks and changes in a release review, and retain a known-working commit for rollback. Stop deployment when private data escapes, references become unverifiable, or data corruption is detected. NIST AI RMF provides a framework for assigning and reviewing these responsibilities: https://www.nist.gov/itl/ai-risk-management-framework
