from __future__ import annotations

import os
from typing import Protocol

import httpx


class AnswerProvider(Protocol):
    async def refine(self, draft: str, evidence: list[str]) -> str: ...


class DeterministicProvider:
    async def refine(self, draft: str, evidence: list[str]) -> str:
        return draft


class OpenAICompatibleProvider:
    """Optional provider used only when explicitly configured; deterministic mode remains the default."""

    def __init__(self) -> None:
        self.base_url = os.environ["ATLAS_LLM_BASE_URL"].rstrip("/")
        self.api_key = os.environ["ATLAS_LLM_API_KEY"]
        self.model = os.getenv("ATLAS_LLM_MODEL", "gpt-4.1-mini")

    async def refine(self, draft: str, evidence: list[str]) -> str:
        prompt = (
            "Rewrite the draft for clarity using only the supplied evidence. Preserve uncertainty and citations.\n\n"
            f"Draft:\n{draft}\n\nEvidence:\n" + "\n".join(evidence)
        )
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": self.model,
                    "temperature": 0,
                    "messages": [{"role": "user", "content": prompt}],
                },
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]


def get_provider() -> AnswerProvider:
    if os.getenv("ATLAS_LLM_BASE_URL") and os.getenv("ATLAS_LLM_API_KEY"):
        return OpenAICompatibleProvider()
    return DeterministicProvider()
