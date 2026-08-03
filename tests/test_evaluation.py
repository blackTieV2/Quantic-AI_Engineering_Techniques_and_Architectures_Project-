from __future__ import annotations

import asyncio

from evaluation.run_evaluation import run


def test_golden_set_evaluation_thresholds() -> None:
    report = asyncio.run(run("inprocess"))
    summary = report["summary"]
    assert summary["items"] >= 20
    assert summary["groundedness"] >= 0.9
    assert summary["citation_accuracy"] >= 0.9
    assert summary["tool_selection_accuracy"] >= 0.9
    assert summary["workflow_completion_rate"] >= 0.9
    assert summary["action_safety_pass_rate"] == 1.0
