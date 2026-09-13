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


def test_model_span_is_nested_and_only_records_safe_usage(monkeypatch):
    from replay.observability import trace_model

    logger = configured_logger(monkeypatch)
    with trace_session(True, "synthetic"), trace_step("answer"):
        with trace_model("nebius") as usage:
            usage.update(
                prompt_tokens=11,
                completion_tokens=7,
                total_tokens=18,
                prompt="private prompt",
                api_key="secret credential",
            )
    node = logger.start_span.return_value.start_span.return_value
    node.start_span.assert_called_once_with(
        name="llm.nebius", type="llm", metadata={"provider": "nebius"}
    )
    node.start_span.return_value.log.assert_called_once_with(
        metrics={"prompt_tokens": 11, "completion_tokens": 7, "tokens": 18},
        output={"status": "returned"},
    )
    assert "private prompt" not in str(logger.mock_calls)
    assert "secret credential" not in str(logger.mock_calls)


def test_failed_model_span_preserves_error_without_exporting_message(monkeypatch):
    from replay.observability import trace_model

    logger = configured_logger(monkeypatch)
    with trace_session(True, "synthetic"), trace_step("answer"):
        with pytest.raises(TimeoutError):
            with trace_model("nebius"):
                raise TimeoutError("private request content")
    calls = str(logger.mock_calls)
    assert "TimeoutError" in calls and "failed" in calls
    assert "private request content" not in calls


@pytest.mark.parametrize(
    "matching_root, tokens, verified", [(True, 18, True), (False, 18, False), (True, 99, False)]
)
def test_readback_requires_exact_trace_and_token_total(
    monkeypatch, matching_root, tokens, verified
):
    from replay.observability import verify_trace

    monkeypatch.setenv("BRAINTRUST_API_KEY", "test-placeholder")
    monkeypatch.setenv("BRAINTRUST_PROJECT_ID", "00000000-0000-0000-0000-000000000001")
    response = Mock()
    response.json.return_value = {
        "events": [
            {
                "root_span_id": "root" if matching_root else "different",
                "span_id": "root",
                "span_attributes": {"name": "racetime.investigation"},
                "metrics": {"tokens": tokens},
            },
            {
                "root_span_id": "root" if matching_root else "different",
                "span_id": "child",
                "span_attributes": {"name": "llm.nebius"},
            },
        ]
    }
    get = Mock(return_value=response)
    monkeypatch.setattr("replay.observability.requests.get", get)
    result = verify_trace(
        {"status": "flush_completed_unverified", "root_span_id": "root"},
        ["racetime.investigation", "llm.nebius"],
        expected_tokens=18,
    )
    assert result["remote_verified"] is verified
    assert get.call_args.kwargs["allow_redirects"] is False


def test_readback_failure_cannot_claim_remote_success(monkeypatch):
    from replay.observability import verify_trace

    monkeypatch.setenv("BRAINTRUST_API_KEY", "test-placeholder")
    monkeypatch.setenv("BRAINTRUST_PROJECT_ID", "00000000-0000-0000-0000-000000000001")
    monkeypatch.setattr(
        "replay.observability.requests.get", Mock(side_effect=TimeoutError("secret"))
    )
    result = verify_trace({"status": "flush_completed_unverified", "root_span_id": "root"}, [])
    assert result["status"] == "readback_failed"
    assert result["remote_verified"] is False
    assert "secret" not in str(result)
