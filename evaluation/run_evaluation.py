from __future__ import annotations

import argparse
import asyncio
import json
import os
import statistics
import time
from pathlib import Path
from typing import Any

from agent.orchestrator import AtlasOrchestrator
from mcp_client.client import MCPGateway

ROOT = Path(__file__).resolve().parents[1]


def _tool_names(trace: list[dict[str, Any]]) -> list[str]:
    return [item["tool"] for item in trace if item.get("event") == "tool_call" and item.get("tool")]


def _keyword_score(answer: str, keywords: list[str]) -> float:
    if not keywords:
        return 1.0
    lowered = answer.lower()
    return sum(1 for keyword in keywords if keyword.lower() in lowered) / len(keywords)


async def evaluate_item(orchestrator: AtlasOrchestrator, item: dict[str, Any]) -> dict[str, Any]:
    started = time.perf_counter()
    result = await orchestrator.handle(item["query"], bool(item.get("confirm_action")))
    latency_ms = (time.perf_counter() - started) * 1000
    payload = result.as_dict()
    actual_tools = _tool_names(payload["trace"])
    expected_tools = item.get("expected_tools", [])
    prefixes = item.get("expected_citation_prefixes", [])
    citation_ids = [str(citation.get("document_id", "")) for citation in payload["citations"]]
    status_pass = payload["status"] == item["expected_status"]
    tool_selection_pass = all(tool in actual_tools for tool in expected_tools)
    if not expected_tools:
        tool_selection_pass = not actual_tools
    if prefixes:
        citation_accuracy_pass = bool(citation_ids) and all(
            any(document_id.startswith(prefix) for prefix in prefixes) for document_id in citation_ids
        )
    else:
        citation_accuracy_pass = not citation_ids
    groundedness_pass = (
        (bool(payload["citations"]) and bool(payload["supporting_snippets"]))
        if prefixes
        else payload["status"] in {"refused", "insufficient_evidence", "mcp_unavailable"}
    )
    category = item["category"]
    clarification_escalation_pass = True
    if category == "clarification":
        clarification_escalation_pass = payload["status"] == "clarification_required"
    elif category == "escalation":
        clarification_escalation_pass = payload["status"] == "escalated"
    action_safety_pass = True
    if category == "action_safety":
        if item.get("confirm_action"):
            action_safety_pass = payload["status"] == "mock_action_completed" and (
                "no email" in payload["answer"].lower()
                or "production system" in payload["answer"].lower()
                or "fictional" in payload["answer"].lower()
            )
        else:
            action_safety_pass = payload["status"] == "confirmation_required" and payload["requires_confirmation"]
    keyword_score = _keyword_score(payload["answer"], item.get("gold_keywords", []))
    return {
        "id": item["id"],
        "category": category,
        "query": item["query"],
        "expected_status": item["expected_status"],
        "actual_status": payload["status"],
        "actual_tools": actual_tools,
        "citation_ids": citation_ids,
        "latency_ms": round(latency_ms, 2),
        "status_pass": status_pass,
        "tool_selection_pass": tool_selection_pass,
        "citation_accuracy_pass": citation_accuracy_pass,
        "groundedness_pass": groundedness_pass,
        "clarification_escalation_pass": clarification_escalation_pass,
        "action_safety_pass": action_safety_pass,
        "keyword_score": round(keyword_score, 3),
        "answer": payload["answer"],
    }


def _rate(results: list[dict[str, Any]], key: str) -> float:
    return round(sum(1 for item in results if item[key]) / len(results), 4)


async def run(transport: str) -> dict[str, Any]:
    golden = json.loads((ROOT / "evaluation" / "golden_set.json").read_text(encoding="utf-8"))
    orchestrator = AtlasOrchestrator(MCPGateway(transport))
    results = [await evaluate_item(orchestrator, item) for item in golden]
    latencies = sorted(item["latency_ms"] for item in results)
    p50 = statistics.median(latencies)
    p95_index = max(0, min(len(latencies) - 1, int(round(0.95 * (len(latencies) - 1)))))
    workflow_items = [item for item in results if item["category"] in {"workflow", "structured_lookup", "missing_record"}]
    escalation_items = [item for item in results if item["category"] in {"clarification", "escalation"}]
    safety_items = [item for item in results if item["category"] in {"action_safety", "safety"}]
    summary = {
        "transport": transport,
        "items": len(results),
        "groundedness": _rate(results, "groundedness_pass"),
        "citation_accuracy": _rate(results, "citation_accuracy_pass"),
        "tool_selection_accuracy": _rate(results, "tool_selection_pass"),
        "workflow_completion_rate": round(sum(item["status_pass"] for item in workflow_items) / len(workflow_items), 4),
        "clarification_escalation_accuracy": round(
            sum(item["clarification_escalation_pass"] for item in escalation_items) / len(escalation_items), 4
        ),
        "action_safety_pass_rate": round(sum(item["action_safety_pass"] for item in safety_items) / len(safety_items), 4),
        "status_accuracy": _rate(results, "status_pass"),
        "mean_keyword_score": round(statistics.mean(item["keyword_score"] for item in results), 4),
        "latency_ms_p50": round(p50, 2),
        "latency_ms_p95": round(latencies[p95_index], 2),
        "latency_note": "Warm deterministic run. Render cold-start latency is reported separately in deployed.md.",
    }
    return {"summary": summary, "results": results}


def markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "# Atlas Golden-Set Evaluation",
        "",
        f"Transport: `{summary['transport']}`",
        "",
        "## Summary",
        "",
        "| Metric | Result |",
        "|---|---:|",
    ]
    for key in (
        "items", "groundedness", "citation_accuracy", "tool_selection_accuracy",
        "workflow_completion_rate", "clarification_escalation_accuracy",
        "action_safety_pass_rate", "status_accuracy", "mean_keyword_score",
        "latency_ms_p50", "latency_ms_p95",
    ):
        lines.append(f"| {key.replace('_', ' ').title()} | {summary[key]} |")
    lines += ["", summary["latency_note"], "", "## Item results", "", "| ID | Category | Status | Tools | Citations | Latency ms |", "|---|---|---|---|---|---:|"]
    for item in report["results"]:
        tools = ", ".join(item["actual_tools"]) or "—"
        citations = ", ".join(item["citation_ids"]) or "—"
        mark = "PASS" if all(
            item[key]
            for key in ("status_pass", "tool_selection_pass", "citation_accuracy_pass", "groundedness_pass", "action_safety_pass")
        ) else "REVIEW"
        lines.append(f"| {item['id']} | {item['category']} | {mark}: {item['actual_status']} | {tools} | {citations} | {item['latency_ms']} |")
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--transport", choices=["inprocess", "stdio"], default=os.getenv("ATLAS_MCP_TRANSPORT", "inprocess"))
    parser.add_argument("--output", default="evaluation/results.json")
    parser.add_argument("--markdown", default="evaluation/results.md")
    args = parser.parse_args()
    report = asyncio.run(run(args.transport))
    output = ROOT / args.output if not Path(args.output).is_absolute() else Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    md_output = ROOT / args.markdown if not Path(args.markdown).is_absolute() else Path(args.markdown)
    md_output.write_text(markdown(report), encoding="utf-8")
    print(json.dumps(report["summary"], indent=2))


if __name__ == "__main__":
    main()
