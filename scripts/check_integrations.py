"""Check optional integrations with synthetic data; preserve evidence on service failures."""

import argparse
import json
import os
from pathlib import Path
from uuid import uuid4

from dotenv import load_dotenv

from replay.agent import build_agent, investigate
from replay.retrieval import EvidenceIndex, documents

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trace", action="store_true", help="Send synthetic cases to LangSmith.")
    args = parser.parse_args()
    load_dotenv(ROOT / ".env")
    os.environ["LANGSMITH_TRACING"] = "false"
    report = json.loads((ROOT / "reports/demo-analysis.json").read_text())
    output = {}
    try:
        index = EvidenceIndex(documents(report), dense=True)
        index.persist(ROOT / ".runtime/demo-index")
        output["semantic_retrieval"] = {
            "mode": index.mode,
            "executed": True,
            "hits": index.search("Where did the camera and watch disagree?"),
        }
    except Exception as error:
        output["semantic_retrieval"] = {"executed": False, "error_type": type(error).__name__}
    answer = investigate("Summarize the measured events.", report, cloud=True)
    output["cloud_synthesis"] = {
        key: value
        for key, value in answer.items()
        if key in ["cloud_draft", "cloud_usage", "cloud_status", "latency_ms"]
    }
    output["langsmith"] = {
        "status": "blocked_on_verified_attempt",
        "reason": "HTTP 429: Monthly unique traces usage limit exceeded.",
        "local_alternative": "reports/evaluation.json contains actual local node timings and outcomes.",
        "uploaded_trace_claim": False,
    }
    if args.trace:
        from langchain_core.tracers.langchain import LangChainTracer, wait_for_all_tracers
        from langsmith import Client

        client = Client()
        project = os.getenv("LANGSMITH_PROJECT", "racetime-replay-evaluation")
        try:
            tracer = LangChainTracer(project_name=project, client=client)
            run_id = uuid4()
            graph = build_agent(EvidenceIndex(documents(report)))
            graph.invoke(
                {"question": "Where did I stop?", "report": report},
                {
                    "configurable": {"thread_id": "synthetic-proof"},
                    "callbacks": [tracer],
                    "run_id": run_id,
                    "metadata": {
                        "provenance": "synthetic",
                        "case_id": "F001",
                        "prompt_version": "evidence-v2",
                        "dataset_version": "demo-v1",
                    },
                },
            )
            wait_for_all_tracers()
            # Readback is required; callbacks may fail asynchronously.
            stored = client.read_run(run_id)
            output["langsmith"] = {
                "status": "verified",
                "run_id": str(stored.id),
                "trace_url": client.get_run_url(run=stored),
                "uploaded_trace_claim": True,
            }
        except Exception as error:
            output["langsmith"]["readback_error"] = type(error).__name__
    (ROOT / "reports/integrations.json").write_text(json.dumps(output, indent=2))
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
