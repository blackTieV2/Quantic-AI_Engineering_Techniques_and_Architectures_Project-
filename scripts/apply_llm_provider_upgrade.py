from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace(path: str, old: str, new: str) -> None:
    target = ROOT / path
    text = target.read_text(encoding="utf-8")
    if old not in text:
        raise SystemExit(f"Expected text not found in {path}: {old[:120]!r}")
    target.write_text(text.replace(old, new), encoding="utf-8")


llm_source = '''from __future__ import annotations

import asyncio
import os
from typing import Any, Protocol
from urllib.parse import urlparse

import httpx

EvidenceItem = dict[str, Any] | str


class LLMProviderError(RuntimeError):
    """Raised when the configured refinement provider cannot return a safe answer."""


class AnswerProvider(Protocol):
    configured: bool
    provider_type: str
    model: str | None

    async def refine(self, draft: str, evidence: list[EvidenceItem]) -> str: ...


def build_grounding_prompt(draft: str, evidence: list[EvidenceItem]) -> str:
    """Build a metadata-rich grounding prompt from citation-ready evidence."""
    records: list[str] = []
    for index, item in enumerate(evidence, start=1):
        if isinstance(item, str):
            records.append(f"Source {index}\\nSnippet: {item}")
            continue
        records.append(
            "\\n".join(
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
    evidence_text = "\\n\\n".join(records) or "No policy evidence was supplied."
    return (
        "Rewrite the controlled draft for clarity using only the supplied evidence and structured facts already present "
        "in the draft. Preserve the decision status, uncertainty, policy distinctions, numerical values and every "
        "no-action disclaimer. Do not add new facts, change eligibility, select tools, authorise actions or invent sources. "
        "Return only the revised answer text.\\n\\n"
        f"Controlled draft:\\n{draft}\\n\\n"
        f"Retrieved evidence with citation metadata:\\n{evidence_text}"
    )


class DeterministicProvider:
    configured = False
    provider_type = "deterministic"
    model: str | None = None

    async def refine(self, draft: str, evidence: list[EvidenceItem]) -> str:
        return draft


class OpenAICompatibleProvider:
    """Constrained OpenAI-compatible answer refinement with bounded retries."""

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
                return content.strip()
            except LLMProviderError:
                raise
            except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError) as exc:
                last_error = exc
                if attempt >= self.max_retries:
                    break
                await asyncio.sleep(min(2 ** attempt, 4))
        raise LLMProviderError(f"Provider request failed after retries: {last_error}")


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
        "verification": "A successful chat trace records llm_refinement=completed.",
    }
'''
(ROOT / "agent/llm.py").write_text(llm_source, encoding="utf-8")

replace(
    "agent/orchestrator.py",
    "                    answer = await self.provider.refine(answer, _snippets(citations))\n",
    "                    # LLM refinement is applied once at the API boundary after controlled orchestration.\n",
)

replace(
    "app/main.py",
    "from agent.orchestrator import AtlasOrchestrator\n",
    "from agent.llm import LLMProviderError, get_provider, provider_status\nfrom agent.orchestrator import AtlasOrchestrator\n",
)
replace(
    "app/main.py",
    '    version="2.0.0",\n',
    '    version="2.1.0",\n',
)
replace(
    "app/main.py",
    '        "llm_provider": "openai-compatible" if os.getenv("ATLAS_LLM_API_KEY") else "deterministic",\n',
    '        "llm_provider": provider_status(),\n',
)
replace(
    "app/main.py",
    "async def chat(request: ChatRequest) -> dict[str, Any]:\n    orchestrator = AtlasOrchestrator()\n    return (await orchestrator.handle(request.message, request.confirm_action)).as_dict()\n",
    '''async def chat(request: ChatRequest) -> dict[str, Any]:
    orchestrator = AtlasOrchestrator()
    result = await orchestrator.handle(request.message, request.confirm_action)
    provider = get_provider()
    refinable_statuses = {
        "completed",
        "provisionally_eligible",
        "not_eligible",
        "mock_action_completed",
        "escalated",
    }
    if provider.configured and result.citations and result.status in refinable_statuses:
        try:
            result.answer = await provider.refine(result.answer, result.citations)
            result.trace.append(
                {
                    "step": len(result.trace) + 1,
                    "event": "llm_refinement",
                    "status": "completed",
                    "provider": provider.provider_type,
                    "model": provider.model,
                    "evidence_items": len(result.citations),
                }
            )
        except LLMProviderError as exc:
            result.trace.append(
                {
                    "step": len(result.trace) + 1,
                    "event": "llm_refinement",
                    "status": "fallback_to_controlled_draft",
                    "provider": provider.provider_type,
                    "model": provider.model,
                    "error": str(exc),
                }
            )
    return result.as_dict()
''',
)

replace(
    "tests/test_app.py",
    '        assert payload["version"] == "2.0.0"\n',
    '        assert payload["version"] == "2.1.0"\n        assert payload["llm_provider"]["status"] == "deterministic"\n',
)

llm_tests = '''from __future__ import annotations

from agent.llm import build_grounding_prompt, provider_status


def test_grounding_prompt_includes_citation_metadata() -> None:
    prompt = build_grounding_prompt(
        "Controlled draft",
        [
            {
                "document_id": "POL-RW-01",
                "title": "International Remote Work Policy",
                "section": "Eligibility",
                "source_path": "policies/pol-rw-01-international-remote-work-policy.md",
                "chunk_id": "POL-RW-01:eligibility:1",
                "snippet": "International remote work is limited to 20 days.",
            }
        ],
    )
    assert "Document ID: POL-RW-01" in prompt
    assert "Title: International Remote Work Policy" in prompt
    assert "Section: Eligibility" in prompt
    assert "Source path: policies/pol-rw-01-international-remote-work-policy.md" in prompt
    assert "Chunk ID: POL-RW-01:eligibility:1" in prompt
    assert "limited to 20 days" in prompt
    assert "Do not add new facts" in prompt


def test_grounding_prompt_remains_compatible_with_snippets() -> None:
    prompt = build_grounding_prompt("Draft", ["Legacy snippet"])
    assert "Snippet: Legacy snippet" in prompt


def test_provider_status_requires_complete_configuration(monkeypatch) -> None:
    monkeypatch.delenv("ATLAS_LLM_BASE_URL", raising=False)
    monkeypatch.delenv("ATLAS_LLM_API_KEY", raising=False)
    monkeypatch.delenv("ATLAS_LLM_MODEL", raising=False)
    assert provider_status()["status"] == "deterministic"

    monkeypatch.setenv("ATLAS_LLM_BASE_URL", "https://openrouter.ai/api/v1")
    monkeypatch.setenv("ATLAS_LLM_API_KEY", "test-secret-not-real")
    monkeypatch.setenv("ATLAS_LLM_MODEL", "test/free-model")
    status = provider_status()
    assert status["status"] == "configured"
    assert status["model"] == "test/free-model"
    assert status["endpoint_host"] == "openrouter.ai"
'''
(ROOT / "tests/test_llm.py").write_text(llm_tests, encoding="utf-8")

replace(
    ".env.example",
    "# Optional OpenAI-compatible refinement layer. Leave unset for deterministic mode.\n# ATLAS_LLM_BASE_URL=https://api.openai.com/v1\n# ATLAS_LLM_API_KEY=\n# ATLAS_LLM_MODEL=gpt-4.1-mini\n",
    "# OpenAI-compatible refinement layer. Keep the real key only in Render or your local shell.\n# ATLAS_LLM_BASE_URL=https://openrouter.ai/api/v1\n# ATLAS_LLM_API_KEY=\n# ATLAS_LLM_MODEL=openrouter/free\n# ATLAS_LLM_TIMEOUT_SECONDS=90\n# ATLAS_LLM_MAX_RETRIES=2\n# ATLAS_PUBLIC_URL=https://atlas-hr-agent.onrender.com\n",
)

replace(
    ".github/workflows/live-smoke.yml",
    '                      candidate.get("version") == "2.0.0"\n',
    '                      candidate.get("version") == "2.1.0"\n                      and candidate.get("llm_provider", {}).get("status") == "configured"\n                      and candidate.get("llm_provider", {}).get("model")\n',
)
replace(
    ".github/workflows/live-smoke.yml",
    "          assert all(\n              citation[\"document_id\"].startswith(\"POL-RW-\")\n              for citation in remote[\"citations\"]\n          ), remote[\"citations\"]\n",
    "          assert all(\n              citation[\"document_id\"].startswith(\"POL-RW-\")\n              for citation in remote[\"citations\"]\n          ), remote[\"citations\"]\n          refinements = [\n              item for item in remote.get(\"trace\", [])\n              if item.get(\"event\") == \"llm_refinement\"\n          ]\n          assert len(refinements) == 1, refinements\n          assert refinements[0].get(\"status\") == \"completed\", refinements\n          assert refinements[0].get(\"model\"), refinements\n",
)
replace(
    ".github/workflows/live-smoke.yml",
    "          print(\"Deployed Atlas v2 health, MCP, workflows, citations and guardrails passed.\")\n",
    "          print(\"Deployed Atlas v2.1 active-LLM, MCP, workflows, citations and guardrails passed.\")\n",
)

print("Active LLM provider upgrade applied.")
