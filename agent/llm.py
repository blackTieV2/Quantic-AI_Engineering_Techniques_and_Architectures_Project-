from __future__ import annotations

import os
from typing import Any, Protocol

import httpx


class AnswerProvider(Protocol):
    async def refine(self, draft: str, evidence: list[dict[str, Any]]) -> str: ...


def build_grounding_prompt(draft: str, evidence: list[dict[str, Any]]) -> str:
    """Build a metadata-rich prompt from citation-ready RAG chunks.

    The model is asked only to refine an already controlled draft. Tool choice,
    action confirmation and safety decisions remain outside the model.
    """
    records: list[str] = []
    for index, item in enumerate(evidence, start=1):
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
        "in the draft. Preserve uncertainty, policy distinctions and all no-action disclaimers. Do not add new facts. "
        "Do not remove or invent source references.\n\n"
        f"Controlled draft:\n{draft}\n\n"
        f"Retrieved evidence with citation metadata:\n{evidence_text}"
    )


class DeterministicProvider:
    async def refine(self, draft: str, evidence: list[dict[str, Any]]) -> str:
        return draft


class OpenAICompatibleProvider:
    """Optional provider used only when explicitly configured; deterministic mode remains the default."""

    def __init__(self) -> None:
        self.base_url = os.environ["ATLAS_LLM_BASE_URL"].rstrip("/")
        self.api_key = os.environ["ATLAS_LLM_API_KEY"]
        self.model = os.getenv("ATLAS_LLM_MODEL", "gpt-4.1-mini")

    async def refine(self, draft: str, evidence: list[dict[str, Any]]) -> str:
        prompt = build_grounding_prompt(draft, evidence)
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": self.model,
                    "temperature": 0,
                    "messages": [
                        {
                            "role": "system",
                            "content": (
                                "You are a constrained answer-refinement component. Follow the supplied policy evidence only. "
                                "You do not choose tools, approve actions or override safety controls."
                            ),
                        },
                        {"role": "user", "content": prompt},
                    ],
                },
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]


def get_provider() -> AnswerProvider:
    if os.getenv("ATLAS_LLM_BASE_URL") and os.getenv("ATLAS_LLM_API_KEY"):
        return OpenAICompatibleProvider()
    return DeterministicProvider()
