from __future__ import annotations

from agent.llm import build_grounding_prompt


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
    assert "Chunk ID: POL-RW-01:eligibility:1" in prompt
    assert "limited to 20 days" in prompt


def test_grounding_prompt_remains_compatible_with_snippets() -> None:
    prompt = build_grounding_prompt("Draft", ["Legacy snippet"])
    assert "Snippet: Legacy snippet" in prompt
