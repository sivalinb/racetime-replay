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
from uuid import uuid4

import requests

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
    root_id = str(uuid4())
    logger = _safe_call(_logger)
    root = (
        None
        if logger is None
        else _safe_call(
            logger.start_span,
            name="racetime.investigation",
            span_id=root_id,
            root_span_id=root_id,
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
    status["root_span_id"] = root_id
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
    token = _CURRENT.set(span)
    try:
        yield
    except Exception as error:
        if span is not None:
            _safe_call(span.log, metadata={"error_type": type(error).__name__})
        raise
    finally:
        _CURRENT.reset(token)
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
    metrics.update(_token_metrics(usage))
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


def _token_metrics(usage: dict) -> dict:
    """Allowlist numeric provider token counts without copying response fields."""
    metrics = {}
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
    return metrics


@contextmanager
def trace_model(provider: str | None) -> Iterator[dict]:
    """Nest a metadata-only model span inside the active composition node.

    The caller fills the yielded usage dictionary after the actual API call.
    No prompts, completions, credentials or exception messages are exported.
    Outside an opted-in synthetic trace, this context makes no SDK calls.
    """
    selected = provider or os.getenv("REPLAY_LLM_PROVIDER", "gemini")
    selected = selected if selected in {"gemini", "nebius"} else "unknown"
    parent = _CURRENT.get()
    span = None
    if parent is not None:
        span = _safe_call(
            parent.start_span,
            name="llm." + selected,
            type="llm",
            metadata={"provider": selected},
        )
    usage = {}
    outcome = "returned"
    try:
        yield usage
    except Exception as error:
        outcome = "failed"
        if span is not None:
            _safe_call(span.log, metadata={"error_type": type(error).__name__})
        raise
    finally:
        if span is not None:
            _safe_call(span.log, metrics=_token_metrics(usage), output={"status": outcome})
            _safe_call(span.end)


def verify_trace(
    trace: dict, expected_names: list[str], expected_tokens: int | None = None
) -> dict:
    """Read back the exact synthetic trace before claiming remote visibility.

    This explicit diagnostic is not part of the application's request path.
    Fetch at most three pages; incomplete ingestion or pagination stays unverified.
    Only identifiers, span names and numeric totals are returned to the caller.
    """
    result = {**trace, "remote_verified": False}
    if trace.get("status") != "flush_completed_unverified":
        return result
    key, project = os.getenv("BRAINTRUST_API_KEY"), os.getenv("BRAINTRUST_PROJECT_ID")
    root_id = trace.get("root_span_id")
    if not key or not project or not root_id:
        result["status"] = "readback_not_configured"
        return result
    try:
        # UUID validation also prevents an environment value changing the URL path.
        from uuid import UUID

        project = str(UUID(project))
        cursor = None
        own_rows = []
        for _ in range(3):
            params = {"limit": 100}
            if cursor:
                params["cursor"] = cursor
            response = requests.get(
                f"https://api.braintrust.dev/v1/project_logs/{project}/fetch",
                headers={"Authorization": f"Bearer {key}"},
                params=params,
                timeout=15,
                allow_redirects=False,
            )
            response.raise_for_status()
            payload = response.json()
            own_rows.extend(row for row in payload["events"] if row.get("root_span_id") == root_id)
            names = {row.get("span_attributes", {}).get("name") for row in own_rows}
            root = next((row for row in own_rows if row.get("span_id") == root_id), {})
            tokens = root.get("metrics", {}).get("tokens")
            result["observed_names"] = sorted(name for name in names if isinstance(name, str))
            result["observed_tokens"] = tokens if isinstance(tokens, (int, float)) else None
            complete = set(expected_names).issubset(names)
            complete = (
                complete and bool(root) and (expected_tokens is None or tokens == expected_tokens)
            )
            if complete:
                result.update(status="verified", remote_verified=True)
                return result
            cursor = payload.get("cursor")
            if not cursor:
                break
        result["status"] = "readback_incomplete"
    except Exception as error:
        result.update(status="readback_failed", error_type=type(error).__name__)
    return result
