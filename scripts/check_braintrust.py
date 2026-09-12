"""Send one synthetic investigation trace to the configured Braintrust project."""

import json
import os
from pathlib import Path

from dotenv import load_dotenv

from replay.agent import investigate
from replay.observability import trace_session

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    """Exercise actual node spans without sending user media or buying inference."""
    load_dotenv(ROOT / ".env")
    os.environ["LANGSMITH_TRACING"] = "false"
    report = json.loads((ROOT / "reports/demo-analysis.json").read_text())
    with trace_session(enabled=True, provenance="synthetic") as trace:
        result = investigate("Where did I stop?", report)
    output = {
        "braintrust": trace,
        "local_answer_status": result["status"],
        "actual_nodes": [s["name"] for s in result["spans"]],
    }
    (ROOT / "reports/braintrust-integration.json").write_text(json.dumps(output, indent=2))
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
