from __future__ import annotations

import asyncio

from evaluation.run_evaluation import LATENCY_SAMPLE_IDS, run


def test_golden_set_evaluation_thresholds() -> None:
    report = asyncio.run(run("inprocess"))
    summary = report["summary"]
    assert summary["items"] >= 20
    assert summary["groundedness_proxy"] >= 0.9
    assert summary["citation_prefix_accuracy"] >= 0.9
    assert summary["exact_tool_sequence_accuracy"] >= 0.9
    assert summary["workflow_completion_rate"] >= 0.9
    assert summary["action_safety_pass_rate"] == 1.0
    assert summary["latency_sample_count"] == len(LATENCY_SAMPLE_IDS)
    assert 10 <= summary["latency_sample_count"] <= 20


def test_multi_document_item_requires_both_policy_families() -> None:
    report = asyncio.run(run("inprocess"))
    item = next(result for result in report["results"] if result["id"] == "POL-04")
    assert item["expected_tools"] == ["search_policy_documents", "search_policy_documents"]
    assert item["actual_tools"] == item["expected_tools"]
    assert any(document_id.startswith("POL-RW-") for document_id in item["citation_ids"])
    assert any(document_id.startswith("POL-SEC-") for document_id in item["citation_ids"])
    assert item["citation_accuracy_pass"] is True
