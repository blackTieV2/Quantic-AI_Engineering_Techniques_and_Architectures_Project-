from __future__ import annotations

from pathlib import Path

from rag.index import RagIndex
from rag.ingest import load_policy_sections


def test_multi_format_policy_loader() -> None:
    policy_dir = Path(__file__).resolve().parents[1] / "policies"
    sections = load_policy_sections(policy_dir)
    assert len({section.document_id for section in sections}) == 14
    assert any(section.source_path.endswith(".md") for section in sections)
    assert any(section.source_path.endswith(".html") for section in sections)
    assert sum(section.estimated_pages for section in {section.document_id: section for section in sections}.values()) >= 30


def test_persistent_index_and_citation_metadata(tmp_path: Path) -> None:
    index = RagIndex(tmp_path / "rag.sqlite3")
    stats = index.build(force=True)
    assert stats["documents"] == 14
    assert stats["chunks"] > 40
    results = index.search("international remote work rolling limit immigration", limit=3)
    assert results
    assert results[0]["document_id"].startswith("POL-RW-")
    assert results[0]["source_path"]
    assert results[0]["section"]
    assert results[0]["snippet"]
