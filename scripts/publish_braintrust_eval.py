"""Publish the existing synthetic evaluation report as a Braintrust experiment.

This uploads authored test questions and recorded outcomes, not private run
inputs. It does not rerun models or report imported timings as live traces.
"""

import json
import os
from datetime import UTC, datetime
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    """Write synthetic scored rows and verify their IDs by server readback."""
    load_dotenv(ROOT / ".env")
    if not os.getenv("BRAINTRUST_API_KEY") or not os.getenv("BRAINTRUST_PROJECT_ID"):
        raise SystemExit("Set BRAINTRUST_API_KEY and BRAINTRUST_PROJECT_ID in local .env first.")
    import braintrust

    report = json.loads((ROOT / "reports/evaluation.json").read_text())
    experiment = braintrust.init(
        project_id=os.environ["BRAINTRUST_PROJECT_ID"],
        api_key=os.environ["BRAINTRUST_API_KEY"],
        experiment="replay-synthetic-" + datetime.now(UTC).strftime("%Y%m%d-%H%M%S"),
        is_public=False,
        metadata={"provenance": "synthetic", "kind": "imported_local_evaluation"},
    )
    ids = []
    for case in report["cases"]:
        ids.append(
            experiment.log(
                input={"question": case["question"]},
                expected={"route": case.get("expected_route"), "pass": True},
                output={"route": case.get("predicted_route"), "passed": case["pass"]},
                scores={"case_pass": float(case["pass"])},
                metrics={"local_agent_latency_ms": case["latency_ms"]},
                metadata={"case_id": case["id"], "dataset_version": "demo-v1"},
            )
        )
    experiment.flush()
    stored = {row["id"] for row in experiment.fetch()}
    verified = set(ids).issubset(stored)
    output = {
        "status": "verified" if verified else "readback_incomplete",
        "rows_written": len(ids),
        "rows_verified": len(set(ids) & stored),
        "remote_verified": verified,
    }
    (ROOT / "reports/braintrust-evaluation-upload.json").write_text(json.dumps(output, indent=2))
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
