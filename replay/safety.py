"""Deterministic trust boundaries complement configurable guardrail frameworks."""

import re

from pydantic import BaseModel, Field

INJECTION = re.compile(
    r"ignore.{0,35}(instruction|previous|rule)|system\s*prompt|reveal.{0,25}(secret|key|token)|exfiltrat|<\s*script|override.{0,20}(policy|rule)|send.{0,30}(api.key|password)",
    re.IGNORECASE,
)
MEDICAL = re.compile(
    r"diagnos|am i (dehydrated|injured)|heat\s*stroke|prescribe|medication|safe to keep running",
    re.IGNORECASE,
)


def redact(text: str) -> str:
    """Remove common email, token and precise-coordinate patterns before cloud use."""
    text = re.sub(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", "[email removed]", text)
    text = re.sub(r"\b(?:sk-|AIza)[\w-]{12,}", "[secret removed]", text)
    text = re.sub(r"(?<!\d)-?\d{1,3}\.\d{4,}(?!\d)", "[precise coordinate removed]", text)
    return text


def input_policy(question: str) -> str | None:
    """Return a refusal reason for recognized disallowed requests, otherwise None."""
    if len(question) > 2000:
        return "Question is too long. Please limit it to 2,000 characters."
    if INJECTION.search(question):
        return "I cannot follow instructions that override evidence or expose private data."
    if MEDICAL.search(question):
        return "These recordings cannot establish a medical diagnosis or whether it is safe to continue running. I can summarize recorded observations."
    return None


class EvidenceAnswer(BaseModel):
    status: str
    route: str
    answer: str = Field(max_length=8000)
    evidence_ids: list[str]
    caveats: list[str]


def validate_answer(result: dict, allowed_ids: list[str]) -> dict:
    """Validate response shape and enforce the evidence-reference allowlist."""
    validated = EvidenceAnswer(**{k: result[k] for k in EvidenceAnswer.model_fields}).model_dump()
    if not set(validated["evidence_ids"]).issubset(set(allowed_ids)):
        raise ValueError("Output contains an unknown evidence reference.")
    if INJECTION.search(validated["answer"]):
        raise ValueError("Output failed instruction-leakage checks.")
    return validated
