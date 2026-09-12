"""Check Nebius on synthetic evidence; no real media or training jobs are sent."""

import argparse
import json
import os
from pathlib import Path

from dotenv import load_dotenv

from replay.agent import investigate
from replay.llm import list_nebius_models

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    """List available models or record one bounded inference check."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--list-models", action="store_true")
    args = parser.parse_args()
    load_dotenv(ROOT / ".env")
    os.environ["LANGSMITH_TRACING"] = "false"
    if args.list_models:
        print("\n".join(list_nebius_models()))
        return
    if not os.getenv("NEBIUS_API_KEY") or not os.getenv("NEBIUS_MODEL"):
        output = {
            "provider": "nebius",
            "status": "not_executed",
            "reason": "API key and model ID are required.",
        }
    else:
        report = json.loads((ROOT / "reports/demo-analysis.json").read_text())
        result = investigate(
            "Summarize the measured events.", report, cloud=True, provider="nebius"
        )
        output = {
            "provider": "nebius",
            "status": "executed" if "cloud_draft" in result else "failed_with_local_fallback",
            "provenance": "synthetic",
            "result": result,
        }
    (ROOT / "reports/nebius-integration.json").write_text(json.dumps(output, indent=2))
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
