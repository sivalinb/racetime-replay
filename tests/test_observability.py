"""Check opt-in, telemetry data boundaries and isolation from SDK failures."""

from unittest.mock import Mock

import pytest

from replay.agent import investigate
from replay.observability import log_outcome, trace_session, trace_step


def test_no_tracing_of_user_uploads(monkeypatch):
    factory = Mock()
    monkeypatch.setattr("replay.observability._logger", factory)
    with trace_session(enabled=True, provenance="user") as status:
        pass
    assert status["status"] == "disabled"
    factory.assert_not_called()


def test_missing_credentials_preserves_local_workflow(monkeypatch):
    monkeypatch.delenv("BRAINTRUST_API_KEY", raising=False)
    with trace_session(True, "synthetic") as status:
        result = investigate("Show my run", {"events": []})
    assert status["status"] == "not_configured"
    assert result["status"] == "insufficient_evidence"


def configured_logger(monkeypatch):
    monkeypatch.setenv("BRAINTRUST_API_KEY", "test-placeholder")
    monkeypatch.setenv("BRAINTRUST_PROJECT_ID", "test-project")
    logger = Mock()
    monkeypatch.setattr("replay.observability._logger", lambda: logger)
    return logger


def test_spans_capture_real_nodes_without_question_or_health(monkeypatch):
    logger = configured_logger(monkeypatch)
    with trace_session(True, "synthetic") as status:
        investigate("contact me@example.com about my run", {"events": []})
        log_outcome(
            {"answer": "private text", "latitude": 40.123456, "cloud_usage": {"total_tokens": 45}}
        )
    root = logger.start_span.return_value
    assert [call.kwargs["name"] for call in root.start_span.call_args_list] == [
        "guard",
        "route",
        "retrieve",
        "investigate",
        "answer",
        "verify",
    ]
    sent = str(logger.mock_calls)
    assert "me@example.com" not in sent and "private text" not in sent and "40.123456" not in sent
    assert status["remote_verified"] is False


def test_telemetry_failure_does_not_break_investigation(monkeypatch):
    logger = configured_logger(monkeypatch)
    logger.start_span.side_effect = RuntimeError("unavailable")
    with trace_session(True, "synthetic") as status:
        result = investigate("Show run", {"events": []})
    assert status["status"] == "telemetry_unavailable"
    assert result["status"] == "insufficient_evidence"


def test_tracing_does_not_swallow_application_error(monkeypatch):
    configured_logger(monkeypatch)
    with pytest.raises(ValueError):
        with trace_session(True, "synthetic"), trace_step("answer"):
            raise ValueError("application bug")
