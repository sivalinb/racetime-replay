"""Executable NeMo input rail and Guardrails AI output validation."""

import json
from functools import lru_cache

from replay.safety import EvidenceAnswer, input_policy


@lru_cache(maxsize=1)
def nemo_rails():
    """Build a local input rail; its fake LLM is a deterministic passthrough."""
    from langchain_core.language_models.fake import FakeListLLM
    from nemoguardrails import LLMRails, RailsConfig

    config = RailsConfig.from_content(
        config={
            "models": [],
            "passthrough": True,
            "rails": {"input": {"flows": ["check replay policy"]}},
        },
        colang_content="""
define flow check replay policy
  $blocked = execute replay_policy_check
  if $blocked
    bot refuse to respond
    stop

define bot refuse to respond
  "REPLAY_POLICY_BLOCKED"
""",
    )
    rails = LLMRails(config, llm=FakeListLLM(responses=["REPLAY_POLICY_ALLOWED"]))

    async def check(context=None, **kwargs):
        return input_policy((context or {}).get("user_message", "")) is not None

    rails.register_action(check, name="replay_policy_check")
    return rails


def nemo_check(question: str) -> bool:
    """Return whether the NeMo input rail permits this request."""
    response = nemo_rails().generate(messages=[{"role": "user", "content": question}])
    return "REPLAY_POLICY_BLOCKED" not in response.get("content", "")


def guardrails_check(result: dict) -> bool:
    """Validate the response schema locally without reasking a model."""
    from guardrails import Guard

    guard = Guard.for_pydantic(output_class=EvidenceAnswer)
    guard.configure(allow_metrics_collection=False)
    outcome = guard.parse(json.dumps(result), num_reasks=0)
    return bool(outcome.validation_passed)
