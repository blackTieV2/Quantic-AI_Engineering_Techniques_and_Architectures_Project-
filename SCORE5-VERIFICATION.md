# Atlas Score-5 Verification Record

Verified on 3 August 2026 through GitHub Actions pull-request run **30791401824**.

## Pipeline result

The `validate` job completed successfully. Every stage passed:

1. Checkout and Python 3.11 setup.
2. SHA-256-verified complete source materialisation.
3. Dependency installation.
4. Compilation of `app`, `agent`, `rag`, `mcp_server`, `mcp_client`, `evaluation`, and `scripts`.
5. Persistent SQLite RAG index build.
6. Complete pytest suite.
7. Genuine MCP stdio discovery and calls through the official Python MCP client.
8. FastAPI startup and deep `/health?deep=true` check.
9. Twenty-five-item golden-set evaluation.
10. Retrieval chunk-size ablation.
11. Upload of the `atlas-score-5-evidence` artifact.

## MCP protocol evidence

The CI client launched **Atlas HR Tools** over stdio and discovered eight MCP tools:

- `check_policy_compliance`
- `check_pto_balance`
- `create_mock_hr_ticket`
- `draft_hr_email`
- `get_policy_section`
- `lookup_benefits_status`
- `lookup_employee_profile`
- `search_policy_documents`

The protocol smoke test successfully called a policy-search tool and a structured employee-data tool.

## Deep-health evidence

```json
{
  "status": "ok",
  "service": "atlas-hr-agent",
  "version": "2.0.0",
  "mode": "agentic-rag-mcp",
  "mcp": {
    "status": "available",
    "transport": "stdio",
    "server": "Atlas HR Tools",
    "tool_count": 8
  },
  "rag_index": {
    "status": "ready",
    "documents": 14,
    "chunks": 126,
    "estimated_pages": 34.5,
    "embedding_model": "atlas-hashing-tfidf-v1",
    "chunk_words": 120,
    "overlap_words": 20
  },
  "synthetic_data_only": true
}
```

## Golden-set results

- Items: 25
- Groundedness: **1.000**
- Citation accuracy: **1.000**
- Tool-selection accuracy: **1.000**
- Workflow completion: **1.000**
- Clarification/escalation accuracy: **1.000**
- Action-safety pass rate: **1.000**
- Status accuracy: **1.000**
- Mean keyword coverage: **0.820**
- Warm latency p50: **2.69 ms**
- Warm latency p95: **4.75 ms**

## Retrieval ablation

| Configuration | Chunk / overlap | Hit@3 | Hit@5 | MRR |
|---|---:|---:|---:|---:|
| Compact | 60 / 10 | 1.000 | 1.000 | 0.900 |
| Balanced | 120 / 20 | 1.000 | 1.000 | 0.950 |
| Broad | 220 / 30 | 1.000 | 1.000 | 0.950 |

The balanced configuration remains the selected default because it achieved the best MRR while using fewer chunks than the compact alternative.

## Evidence artifact

- Name: `atlas-score-5-evidence`
- Artifact ID: `8847177885`
- Digest: `sha256:ec0654d565feff211818ce26c124d7f2c654bd683c1793f49b6b1028c842a28c`
- Source verification PR: #2 (closed without merge after successful verification)
