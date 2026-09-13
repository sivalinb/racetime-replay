"""Send one synthetic investigation trace to the configured Braintrust project."""

import argparse
import json
import os
from pathlib import Path

from dotenv import load_dotenv

from replay.agent import investigate
from replay.observability import trace_session, verify_trace

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    """Check real synthetic spans, optionally including one bounded cloud call."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--provider", choices=["nebius", "gemini"], help="Opt into one synthetic cloud draft."
    )
    args = parser.parse_args()
    load_dotenv(ROOT / ".env")
    os.environ["LANGSMITH_TRACING"] = "false"
    report = json.loads((ROOT / "reports/demo-analysis.json").read_text())
    # Do not spend inference tokens when the requested tracing cannot start.
    if not os.getenv("BRAINTRUST_API_KEY") or not os.getenv("BRAINTRUST_PROJECT_ID"):
        output = {"braintrust": {"status": "not_configured", "remote_verified": False}}
        (ROOT / "reports/braintrust-integration.json").write_text(
            json.dumps(output, indent=2) + "\n"
        )
        print(json.dumps(output, indent=2))
        return
    with trace_session(enabled=True, provenance="synthetic") as trace:
        cloud_enabled = bool(args.provider) and trace.get("status") == "recording"
        result = investigate(
            "Where did I stop?", report, cloud=cloud_enabled, provider=args.provider
        )
    expected = ["racetime.investigation"] + [s["name"] for s in result["spans"]]
    if cloud_enabled:
        expected.append("llm." + args.provider)
    tokens = result.get("cloud_usage", {}).get("total_tokens")
    if tokens is None:
        tokens = result.get("cloud_usage", {}).get("totalTokenCount")
    trace = verify_trace(trace, expected, expected_tokens=tokens)
    output = {
        "braintrust": trace,
        "local_answer_status": result["status"],
        "cloud_draft_present": "cloud_draft" in result,
        "actual_nodes": [s["name"] for s in result["spans"]],
    }
    (ROOT / "reports/braintrust-integration.json").write_text(json.dumps(output, indent=2))
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
