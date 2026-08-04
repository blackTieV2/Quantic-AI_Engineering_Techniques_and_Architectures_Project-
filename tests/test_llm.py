from __future__ import annotations

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
    assert "Snippet:" in prompt
    assert "Legacy snippet" in prompt


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
