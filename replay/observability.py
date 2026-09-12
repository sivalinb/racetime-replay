"""Opt-in Braintrust spans containing allowlisted synthetic-run telemetry only.

Manual instrumentation avoids copying LangGraph state, question text, health
records or model drafts into a third-party trace. Telemetry failures never
change the investigator's answer. These hooks are inactive outside a session.
"""

import os
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any

_CURRENT: ContextVar[Any] = ContextVar("replay_braintrust_span", default=None)
_ALLOWED_NODES = {"guard", "blocked", "route", "retrieve", "investigate", "answer", "verify"}


def _safe_call(function, *args, **kwargs):
    """Isolate telemetry errors without suppressing application failures."""
    try:
        return function(*args, **kwargs)
    except Exception:
        return None


def _logger():
    """Load the optional SDK only after opt-in and credential checks."""
    import braintrust

    return braintrust.init_logger(
        project_id=os.environ["BRAINTRUST_PROJECT_ID"],
        api_key=os.environ["BRAINTRUST_API_KEY"],
        app_url="https://www.braintrust.dev",
        async_flush=False,
        set_current=False,
    )


@contextmanager
def trace_session(enabled: bool = False, provenance: str = "user") -> Iterator[dict]:
    """Trace an explicitly enabled synthetic run; never accept real uploads.

    The returned status describes local submission only. A successful flush is
    not proof that the trace is visible remotely; verify that in Braintrust.
    """
    status = {"status": "disabled", "remote_verified": False}
    if not enabled or provenance != "synthetic":
        yield status
        return
    if not os.getenv("BRAINTRUST_API_KEY") or not os.getenv("BRAINTRUST_PROJECT_ID"):
        status["status"] = "not_configured"
        yield status
        return
    logger = _safe_call(_logger)
    root = (
        None
        if logger is None
        else _safe_call(
            logger.start_span,
            name="racetime.investigation",
            metadata={
                "provenance": "synthetic",
                "dataset_version": "demo-v1",
                "prompt_version": "evidence-v3",
            },
        )
    )
    if root is None:
        status["status"] = "telemetry_unavailable"
        yield status
        return
    token = _CURRENT.set(root)
    status["status"] = "recording"
    try:
        yield status
    finally:
        _CURRENT.reset(token)
        _safe_call(root.end)
        try:
            logger.flush()
            status["status"] = "flush_completed_unverified"
        except Exception:
            status["status"] = "flush_failed"


@contextmanager
def trace_step(name: str) -> Iterator[None]:
    """Measure a real graph node without logging its input or output state."""
    parent = _CURRENT.get()
    span = None
    if parent is not None and name in _ALLOWED_NODES:
        span = _safe_call(parent.start_span, name=name)
    try:
        yield
    except Exception as error:
        if span is not None:
            _safe_call(span.log, metadata={"error_type": type(error).__name__})
        raise
    finally:
        if span is not None:
            _safe_call(span.end)


def log_outcome(result: dict) -> None:
    """Record allowlisted outcome labels and numeric usage, never free text."""
    span = _CURRENT.get()
    if span is None:
        return
    safe_status = {"answered", "needs_review", "insufficient_evidence", "declined"}
    safe_routes = {"stops", "signals", "summary", "knowledge", "safety"}
    usage = result.get("cloud_usage", {})
    metrics = {"evidence_count": len(result.get("evidence_ids", []))}
    for source, destination in [
        ("prompt_tokens", "prompt_tokens"),
        ("completion_tokens", "completion_tokens"),
        ("total_tokens", "tokens"),
        ("promptTokenCount", "prompt_tokens"),
        ("candidatesTokenCount", "completion_tokens"),
        ("totalTokenCount", "tokens"),
    ]:
        if isinstance(usage.get(source), (int, float)):
            metrics[destination] = usage[source]
    _safe_call(
        span.log,
        output={
            "status": result.get("status") if result.get("status") in safe_status else "unknown",
            "route": result.get("route") if result.get("route") in safe_routes else "unknown",
            "cloud_draft_present": "cloud_draft" in result,
        },
        metrics=metrics,
        metadata={
            "provider": usage.get("provider")
            if usage.get("provider") in {"gemini", "nebius"}
            else "local"
        },
    )
