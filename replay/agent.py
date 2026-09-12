"""Bounded LangGraph investigator with evidence tools, verification and review state."""

import hashlib
import os
import time
from collections.abc import Callable
from typing import TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph

from replay.llm import Provider, cloud_synthesis
from replay.observability import log_outcome, trace_step
from replay.retrieval import EvidenceIndex, documents
from replay.safety import input_policy, validate_answer

LABELS = ["stops", "signals", "summary", "knowledge"]


def route_question(question: str) -> str:
    """Select a bounded evidence tool using the transparent default rule router."""
    q = question.lower()
    if any(
        w in q
        for w in ["how does", "what is", "privacy", "optical", "future", "export", "optimization"]
    ):
        return "knowledge"
    if any(w in q for w in ["stop", "pause", "stationary", "waiting", "lost time"]):
        return "stops"
    if any(
        w in q
        for w in ["gap", "missing", "disagree", "conflict", "sync", "offset", "frozen", "gps"]
    ):
        return "signals"
    return "summary"


class State(TypedDict, total=False):
    question: str
    report: dict
    route: str
    evidence: list
    result: dict
    steps: list
    blocked: str | None
    cloud: bool
    provider: Provider | None
    spans: list[dict]


def build_agent(index: EvidenceIndex, router: Callable[[str], str] | None = None):
    """Compile an evidence workflow with session checkpoints and bounded fallbacks."""

    def guard(s):
        blocked_reason = input_policy(s["question"])
        if os.getenv("REPLAY_FRAMEWORK_GUARDS", "false").lower() == "true":
            from replay.framework_guards import nemo_check

            if not nemo_check(s["question"]):
                blocked_reason = blocked_reason or "Request blocked by the input policy."
        return {"blocked": blocked_reason, "steps": ["input_policy"]}

    def routing(s):
        try:
            label = (router or route_question)(s["question"])
            if label not in LABELS:
                raise ValueError("Unknown route")
            return {"route": label, "steps": s["steps"] + ["route:" + label]}
        except Exception:
            return {
                "route": route_question(s["question"]),
                "steps": s["steps"] + ["router_failure:local_fallback"],
            }

    def blocked(s):
        return {
            "result": {
                "status": "declined",
                "route": "safety",
                "answer": s["blocked"],
                "evidence_ids": [],
                "caveats": ["No tool or model was called."],
            }
        }

    def retrieve(s):
        try:
            hits = index.search(s["question"])
            return {"evidence": hits, "steps": s["steps"] + ["retrieve_evidence"]}
        except Exception:
            return {
                "evidence": [],
                "steps": s["steps"] + ["retrieval_failure:structured_evidence_fallback"],
            }

    def investigate(s):
        report = s["report"]
        route = s["route"]
        kinds = {
            "stops": {"stop_candidate"},
            "signals": {"sensor_conflict", "missing_speed", "repeated_frame"},
        }
        events = [
            e
            for e in report["events"]
            if e["kind"] in kinds.get(route, {e["kind"] for e in report["events"]})
        ]
        evidence = list(s["evidence"])
        ids = {d["id"] for d in evidence}
        for e in events:
            if e["id"] not in ids:
                evidence.append(
                    {
                        "id": e["id"],
                        "text": f"{e['kind']} from {e['start_s']} to {e['end_s']} seconds; duration {e['duration_s']} seconds.",
                        "source": f"video:{e['start_s']}-{e['end_s']}",
                    }
                )
        return {"evidence": evidence, "steps": s["steps"] + ["tool:" + route]}

    def answer(s):
        events = {e["id"]: e for e in s["report"]["events"]}
        refs = [d for d in s["evidence"] if d["id"] in events]
        if s["route"] == "knowledge":
            refs = [d for d in s["evidence"] if d["id"].startswith("K")]
        elif s["route"] == "stops":
            refs = [d for d in refs if events[d["id"]]["kind"] == "stop_candidate"]
        elif s["route"] == "signals":
            refs = [d for d in refs if events[d["id"]]["kind"] != "stop_candidate"]
        refs = refs[:8]
        if refs:
            text = "\n\n".join(f"{d['text']} [{d['id']}]" for d in refs)
            status = "needs_review" if s["route"] != "knowledge" else "answered"
        else:
            text = "No matching evidence was found in this recording and knowledge corpus."
            status = "insufficient_evidence"
        result = {
            "status": status,
            "route": s["route"],
            "answer": text,
            "evidence_ids": [d["id"] for d in refs],
            "caveats": [
                "Camera motion does not establish running speed or a physiological cause.",
                "Alignment and detected events require human review.",
            ],
        }
        if s.get("cloud") and refs:
            try:
                output, usage = cloud_synthesis(s["question"], refs, s.get("provider"))
                # Keep cloud prose explicitly supplemental; canonical observations remain unchanged.
                valid = validate_answer(
                    {**result, "answer": output["answer"], "evidence_ids": output["evidence_ids"]},
                    [d["id"] for d in refs],
                )
                result["cloud_draft"] = valid["answer"]
                result["cloud_usage"] = usage
                result["cloud_status"] = "Draft for review; evidence above remains authoritative."
            except Exception as ex:
                result["cloud_status"] = (
                    f"Cloud synthesis unavailable ({type(ex).__name__}); local evidence retained."
                )
        return {"result": result, "steps": s["steps"] + ["compose_evidence"]}

    def verify(s):
        validate_answer(s["result"], [d["id"] for d in s["evidence"]])
        if os.getenv("REPLAY_FRAMEWORK_GUARDS", "false").lower() == "true":
            from replay.framework_guards import guardrails_check

            if not guardrails_check(s["result"]):
                raise ValueError("Output failed framework validation.")
        return {"steps": s["steps"] + ["verify_references", "human_review_available"]}

    g = StateGraph(State)
    for name, fn in [
        ("guard", guard),
        ("blocked", blocked),
        ("route", routing),
        ("retrieve", retrieve),
        ("investigate", investigate),
        ("answer", answer),
        ("verify", verify),
    ]:

        def measured(state: State, function=fn, node_name=name) -> dict:
            started = time.perf_counter()
            with trace_step(node_name):
                update = function(state)
            previous = [] if node_name == "guard" else state.get("spans", [])
            update["spans"] = previous + [
                {
                    "name": node_name,
                    "latency_ms": round((time.perf_counter() - started) * 1000, 3),
                    "status": "completed",
                }
            ]
            return update

        g.add_node(name, measured)
    g.add_edge(START, "guard")
    g.add_conditional_edges("guard", lambda s: "blocked" if s["blocked"] else "route")
    g.add_edge("blocked", END)
    for a, b in [
        ("route", "retrieve"),
        ("retrieve", "investigate"),
        ("investigate", "answer"),
        ("answer", "verify"),
        ("verify", END),
    ]:
        g.add_edge(a, b)
    return g.compile(checkpointer=InMemorySaver())


def investigate(
    question: str,
    report: dict,
    cloud: bool = False,
    dense: bool = False,
    thread_id: str = "review",
    router: Callable[[str], str] | None = None,
    graph=None,
    provider: Provider | None = None,
) -> dict:
    """Investigate one question using a reusable graph or a fresh isolated session."""
    if graph is None:
        index = EvidenceIndex(documents(report), dense=dense)
        graph = build_agent(index, router)
        retrieval_mode = index.mode
    else:
        retrieval_mode = "Session evidence index"
    started = time.perf_counter()
    state = graph.invoke(
        {"question": question, "report": report, "cloud": cloud, "provider": provider},
        {"configurable": {"thread_id": thread_id}, "recursion_limit": 12},
    )
    result = state["result"]
    result["steps"] = state.get("steps", [])
    result["spans"] = state.get("spans", [])
    result["latency_ms"] = round((time.perf_counter() - started) * 1000, 2)
    result["retrieval_mode"] = retrieval_mode
    result["question_hash"] = hashlib.sha256(question.encode()).hexdigest()[:16]
    result["review"] = "pending" if result["status"] == "needs_review" else "not_required"
    log_outcome(result)
    return result
