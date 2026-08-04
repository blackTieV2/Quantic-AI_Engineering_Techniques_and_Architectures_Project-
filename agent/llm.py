from __future__ import annotations

import asyncio
import contextvars
import os
import re
from typing import Any, Protocol
from urllib.parse import urlparse

import httpx

from rag.index import get_index

EvidenceItem = dict[str, Any] | str

_REFINEMENT_STATUS: contextvars.ContextVar[dict[str, Any]] = contextvars.ContextVar(
    "atlas_llm_refinement_status",
    default={"status": "not_called"},
)


class LLMProviderError(RuntimeError):
    """Raised internally when the configured refinement provider cannot return a safe answer."""


class AnswerProvider(Protocol):
    configured: bool
    provider_type: str
    model: str | None

    async def refine(self, draft: str, evidence: list[EvidenceItem]) -> str: ...


def reset_refinement_status() -> None:
    _REFINEMENT_STATUS.set({"status": "not_called"})


def get_refinement_status() -> dict[str, Any]:
    return dict(_REFINEMENT_STATUS.get())


def _set_refinement_status(**payload: Any) -> None:
    _REFINEMENT_STATUS.set(payload)


def _enrich_legacy_snippet(snippet: str) -> EvidenceItem:
    """Recover citation metadata when a legacy caller supplies only a snippet."""
    clean = re.sub(r"\s+", " ", snippet).strip()
    if not clean:
        return snippet
    try:
        results = get_index().ensure().search(clean, limit=1)
    except Exception:
        return snippet
    if not results:
        return snippet
    candidate = results[0]
    candidate_snippet = re.sub(r"\s+", " ", str(candidate.get("snippet", ""))).strip()
    if not candidate_snippet:
        return snippet
    clean_tokens = set(re.findall(r"[a-z0-9]+", clean.lower()))
    candidate_tokens = set(re.findall(r"[a-z0-9]+", candidate_snippet.lower()))
    if not clean_tokens or len(clean_tokens & candidate_tokens) / len(clean_tokens) < 0.55:
        return snippet
    return candidate


def build_grounding_prompt(draft: str, evidence: list[EvidenceItem]) -> str:
    """Build a metadata-rich grounding prompt from citation-ready evidence."""
    records: list[str] = []
    for index, raw_item in enumerate(evidence, start=1):
        item = _enrich_legacy_snippet(raw_item) if isinstance(raw_item, str) else raw_item
        if isinstance(item, str):
            records.append(f"Source {index}\nSnippet: {item}")
            continue
        records.append(
            "\n".join(
                [
                    f"Source {index}",
                    f"Document ID: {item.get('document_id', '')}",
                    f"Title: {item.get('title', '')}",
                    f"Section: {item.get('section', '')}",
                    f"Source path: {item.get('source_path', '')}",
                    f"Chunk ID: {item.get('chunk_id', '')}",
                    f"Snippet: {item.get('snippet', '')}",
                ]
            )
        )
    evidence_text = "\n\n".join(records) or "No policy evidence was supplied."
    return (
        "Rewrite the controlled draft for clarity using only the supplied evidence and structured facts already present "
        "in the draft. Preserve the decision status, uncertainty, policy distinctions, numerical values and every "
        "no-action disclaimer. Do not add new facts, change eligibility, select tools, authorise actions or invent sources. "
        "Return only the revised answer text.\n\n"
        f"Controlled draft:\n{draft}\n\n"
        f"Retrieved evidence with citation metadata:\n{evidence_text}"
    )


class DeterministicProvider:
    configured = False
    provider_type = "deterministic"
    model: str | None = None

    async def refine(self, draft: str, evidence: list[EvidenceItem]) -> str:
        _set_refinement_status(status="not_configured", provider=self.provider_type, model=None)
        return draft


class OpenAICompatibleProvider:
    """Constrained OpenAI-compatible answer refinement with bounded retries and safe fallback."""

    configured = True
    provider_type = "openai-compatible"

    def __init__(self) -> None:
        self.base_url = os.environ["ATLAS_LLM_BASE_URL"].rstrip("/")
        self.api_key = os.environ["ATLAS_LLM_API_KEY"]
        self.model = os.environ["ATLAS_LLM_MODEL"]
        self.timeout_seconds = float(os.getenv("ATLAS_LLM_TIMEOUT_SECONDS", "90"))
        self.max_retries = max(0, int(os.getenv("ATLAS_LLM_MAX_RETRIES", "2")))

    async def refine(self, draft: str, evidence: list[EvidenceItem]) -> str:
        prompt = build_grounding_prompt(draft, evidence)
        last_error: Exception | None = None
        for attempt in range(self.max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                    response = await client.post(
                        f"{self.base_url}/chat/completions",
                        headers={
                            "Authorization": f"Bearer {self.api_key}",
                            "Content-Type": "application/json",
                            "HTTP-Referer": os.getenv("ATLAS_PUBLIC_URL", "https://atlas-hr-agent.onrender.com"),
                            "X-Title": "Atlas HR Agent - Quantic Project",
                        },
                        json={
                            "model": self.model,
                            "temperature": 0,
                            "messages": [
                                {
                                    "role": "system",
                                    "content": (
                                        "You are a constrained answer-refinement component. Use only the supplied policy "
                                        "evidence and structured facts. You do not choose tools, approve actions, disclose "
                                        "hidden data or override safety controls."
                                    ),
                                },
                                {"role": "user", "content": prompt},
                            ],
                        },
                    )
                if response.status_code == 429 or response.status_code >= 500:
                    response.raise_for_status()
                if response.status_code >= 400:
                    detail = response.text[:500]
                    raise LLMProviderError(f"Provider returned HTTP {response.status_code}: {detail}")
                payload = response.json()
                content = payload.get("choices", [{}])[0].get("message", {}).get("content")
                if not isinstance(content, str) or not content.strip():
                    raise LLMProviderError("Provider returned an empty or malformed answer")
                revised = content.strip()
                _set_refinement_status(
                    status="completed",
                    provider=self.provider_type,
                    model=self.model,
                    evidence_items=len(evidence),
                    attempts=attempt + 1,
                )
                return revised
            except LLMProviderError as exc:
                last_error = exc
                break
            except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError) as exc:
                last_error = exc
                if attempt >= self.max_retries:
                    break
                await asyncio.sleep(min(2**attempt, 4))
        _set_refinement_status(
            status="fallback_to_controlled_draft",
            provider=self.provider_type,
            model=self.model,
            evidence_items=len(evidence),
            error=str(last_error),
        )
        return draft


def get_provider() -> AnswerProvider:
    required = ("ATLAS_LLM_BASE_URL", "ATLAS_LLM_API_KEY", "ATLAS_LLM_MODEL")
    if all(os.getenv(name) for name in required):
        return OpenAICompatibleProvider()
    return DeterministicProvider()


def provider_status() -> dict[str, Any]:
    provider = get_provider()
    if not provider.configured:
        return {
            "status": "deterministic",
            "type": provider.provider_type,
            "model": None,
            "note": "No active external LLM provider is configured.",
        }
    base_url = os.environ["ATLAS_LLM_BASE_URL"]
    return {
        "status": "configured",
        "type": provider.provider_type,
        "model": provider.model,
        "endpoint_host": urlparse(base_url).netloc,
        "verification": "A successful cited chat response records llm_refinement=completed.",
    }
