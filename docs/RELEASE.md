# Release readiness

Current intended release: reproducible local prototype and synthetic demonstration.

| Gate | State |
|---|---|
| Python app and OpenCV pipeline | Implemented; local UI and behavior tests recorded |
| Dataset provenance | Synthetic video and authored questions clearly labeled |
| Event and routing evaluation | Local report includes baseline, measured results and limitations |
| Fine-tuned router | Experiment completed; not promoted due to weak held-out accuracy |
| NeMo and Guardrails AI | Executed checks; optional integrated policy mode |
| Raw-data cloud tracing | Disabled by default |
| LangSmith hosted proof | Blocked by account monthly unique-trace quota on verified attempt |
| Real runner data | Not supplied; field validation remains outstanding |
| Medical or training advice | Outside this release |
| Public multi-user uploads | Not approved by this prototype; needs authentication, isolated processing, retention and abuse controls |

Before a real-data pilot, review consent, verify two synchronization anchors, label events, compare metrics across recordings, and test deletion. Before a production release, set numeric acceptance thresholds with users, test concurrency, apply dependency updates, configure monitoring and costs, and rehearse rollback. Do not treat synthetic accuracy as production readiness.

Rollback: stop the server, check out the prior tested commit, reinstall its dependency lock, and rerun the regression suite. Uploaded sessions are excluded from version control and should follow the user's retention choice.
