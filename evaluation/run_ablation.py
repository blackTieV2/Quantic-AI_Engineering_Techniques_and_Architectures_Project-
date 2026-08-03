from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

from rag.index import RagIndex

ROOT = Path(__file__).resolve().parents[1]
QUERIES = [
    ("international remote work rolling day limit", "POL-RW-"),
    ("corporate VPN multi-factor authentication overseas", "POL-SEC-"),
    ("PTO carry over five days", "POL-PTO-"),
    ("benefits qualifying life event enrolment", "POL-BEN-"),
    ("harassment confidential HR escalation", "POL-CON-"),
    ("expense receipt threshold", "POL-EXP-"),
    ("mock ticket does not contact production", "POL-SVC-"),
    ("manager approval matrix tax immigration", "POL-APR-"),
    ("part-time employment classification", "POL-ONB-"),
    ("medical leave documentation privacy", "POL-LVE-"),
]
CONFIGURATIONS = [
    {"name": "compact", "chunk_words": 60, "overlap_words": 10},
    {"name": "balanced", "chunk_words": 120, "overlap_words": 20},
    {"name": "broad", "chunk_words": 220, "overlap_words": 30},
]


def evaluate(configuration: dict[str, int | str]) -> dict[str, object]:
    with tempfile.TemporaryDirectory() as directory:
        index = RagIndex(Path(directory) / "index.sqlite3")
        index.build(
            chunk_words=int(configuration["chunk_words"]),
            overlap_words=int(configuration["overlap_words"]),
            force=True,
        )
        rows = []
        reciprocal_ranks = []
        hit_at_3 = 0
        hit_at_5 = 0
        for query, prefix in QUERIES:
            results = index.search(query, limit=5)
            rank = next((position for position, item in enumerate(results, 1) if item["document_id"].startswith(prefix)), None)
            if rank:
                reciprocal_ranks.append(1 / rank)
                hit_at_5 += 1
                if rank <= 3:
                    hit_at_3 += 1
            else:
                reciprocal_ranks.append(0)
            rows.append({"query": query, "expected_prefix": prefix, "rank": rank, "top_ids": [item["document_id"] for item in results]})
        stats = index.stats()
        stats["path"] = "<temporary-index>"
        return {
            **configuration,
            "hit_at_3": round(hit_at_3 / len(QUERIES), 3),
            "hit_at_5": round(hit_at_5 / len(QUERIES), 3),
            "mean_reciprocal_rank": round(sum(reciprocal_ranks) / len(reciprocal_ranks), 3),
            "index": stats,
            "queries": rows,
        }


def to_markdown(report: dict[str, object]) -> str:
    lines = [
        "# Retrieval Ablation",
        "",
        "The comparison changes chunk size and overlap while keeping the deterministic embedding model and query set fixed.",
        "",
        "| Configuration | Chunk words | Overlap | Hit@3 | Hit@5 | MRR | Chunks |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for item in report["configurations"]:
        lines.append(
            f"| {item['name']} | {item['chunk_words']} | {item['overlap_words']} | {item['hit_at_3']} | "
            f"{item['hit_at_5']} | {item['mean_reciprocal_rank']} | {item['index']['chunks']} |"
        )
    best = max(report["configurations"], key=lambda item: (item["hit_at_3"], item["mean_reciprocal_rank"]))
    lines += ["", f"Selected configuration: **{best['name']}** because it produced the strongest Hit@3/MRR trade-off in this deterministic test.", ""]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="evaluation/ablation-results.json")
    parser.add_argument("--markdown", default="evaluation/ablation-results.md")
    args = parser.parse_args()
    report = {"queries": len(QUERIES), "configurations": [evaluate(item) for item in CONFIGURATIONS]}
    output = ROOT / args.output if not Path(args.output).is_absolute() else Path(args.output)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    md_output = ROOT / args.markdown if not Path(args.markdown).is_absolute() else Path(args.markdown)
    md_output.write_text(to_markdown(report), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
