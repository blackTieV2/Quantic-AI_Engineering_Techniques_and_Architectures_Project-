from __future__ import annotations

import re

from app.engine import Result, respond as engine_respond


_INJECTION_PATTERNS = (
    re.compile(
        r"\b(?:ignore|disregard|override|forget)\b.{0,60}"
        r"\b(?:previous|prior|all|hidden|system)?\s*(?:instructions?|rules?|safeguards?|policy)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:reveal|show|print|expose|leak|dump)\b.{0,60}"
        r"\b(?:system prompt|hidden instructions?|private data|personal data|confidential data|secrets?)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:bypass|disable|evade|circumvent)\b.{0,40}"
        r"\b(?:safeguards?|controls?|policy|restrictions?)\b",
        re.IGNORECASE,
    ),
)


def _is_prompt_injection(message: str) -> bool:
    return any(pattern.search(message) for pattern in _INJECTION_PATTERNS)


def _citation_prefixes(message: str) -> tuple[str, ...] | None:
    lowered = message.lower()
    if any(term in lowered for term in ("remote", "overseas", "work abroad")):
        return ("POL-RW-",)
    if any(term in lowered for term in ("pto", "leave", "vacation")):
        return ("POL-PTO-",)
    if any(term in lowered for term in ("benefit", "medical plan", "insurance")):
        return ("POL-BEN-",)
    if any(
        term in lowered
        for term in (
            "harassment",
            "discrimination",
            "retaliation",
            "legal advice",
            "lawsuit",
            "assault",
            "medical diagnosis",
        )
    ):
        return ("POL-CON-",)
    return None


def controlled_respond(message: str, confirm_action: bool = False) -> Result:
    """Apply boundary controls before and after the deterministic workflow engine."""

    if _is_prompt_injection(message):
        return Result(
            answer=(
                "I cannot follow instructions that attempt to override safeguards, expose hidden configuration, "
                "or disclose private or confidential information. I can still help with a normal synthetic HR "
                "policy question."
            ),
            citations=[],
            trace=["classify_request", "apply_prompt_injection_guardrail"],
            status="refused",
        )

    result = engine_respond(message, confirm_action)
    prefixes = _citation_prefixes(message)
    if prefixes is not None:
        result.citations = [
            citation
            for citation in result.citations
            if str(citation.get("document_id", "")).startswith(prefixes)
        ]
    return result
