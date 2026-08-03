# Atlas Technical Verification Record — Score-5 Target

This file records technical test evidence. It does **not** certify a Quantic grade or claim that every assignment requirement is complete. The strict requirement assessment is in `ASSIGNMENT-COMPLIANCE-AUDIT.md`.

## Current assignment-alignment run

GitHub Actions run **30798365389** executed against pull request #6 and completed successfully. The run included:

1. Python 3.11 setup and dependency installation.
2. Compilation of `app`, `agent`, `rag`, `mcp_server`, `mcp_client`, `evaluation`, and `scripts`.
3. Persistent SQLite RAG index build.
4. Complete pytest suite.
5. Genuine MCP stdio discovery and calls through the official Python MCP client.
6. FastAPI startup and deep `/health?deep=true` check.
7. Strengthened twenty-five-item rubric evaluation.
8. Retrieval chunk-size ablation.
9. Evidence artifact upload.

Evidence artifact:

- Name: `atlas-score-5-evidence`
- Workflow run: `30798365389`
- Artifact ID: `8849788261`
- Digest: `sha256:d88caf542730f03d35ebb43709256aba36f43af2f2a3baac898edb69a903248e`

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

The protocol smoke test called a policy-search tool and a structured employee-data tool. The application refuses to bypass an unavailable MCP service with hidden direct calls.

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
  "llm_provider": "deterministic",
  "synthetic_data_only": true
}
```

The `llm_provider` field is important: the public release currently uses deterministic synthesis unless an OpenAI-compatible provider is configured. The assignment audit treats active LLM use as an unresolved strict-compliance risk.

## Strengthened evaluation results

| Metric | Result |
|---|---:|
| Items | 25 |
| Groundedness proxy | 1.000 |
| Citation-family accuracy | 1.000 |
| Exact MCP tool-sequence accuracy | 1.000 |
| Workflow completion | 1.000 |
| Clarification/escalation accuracy | 1.000 |
| Action-safety pass rate | 1.000 |
| Status accuracy | 1.000 |
| Mean keyword coverage | 0.940 |
| Representative warm-latency sample | 15 tasks |
| Warm latency p50 | 2.72 ms |
| Warm latency p95 | 4.59 ms |

These are deterministic rubric-based proxy metrics. Groundedness is not an independent semantic-entailment judgment. Citation accuracy requires every expected policy family, and tool accuracy requires the exact expected MCP call sequence.

## Retrieval ablation

| Configuration | Chunk / overlap | Hit@3 | Hit@5 | MRR |
|---|---:|---:|---:|---:|
| Compact | 60 / 10 | 1.000 | 1.000 | 0.900 |
| Balanced | 120 / 20 | 1.000 | 1.000 | 0.950 |
| Broad | 220 / 30 | 1.000 | 1.000 | 0.950 |

The balanced configuration remains the selected default because it matches the best MRR while using fewer chunks than the compact alternative and smaller evidence units than the broad alternative.

## Public deployment evidence

The earlier public Render smoke run **30792651006** proved:

- version `2.0.0`, mode `agentic-rag-mcp`, MCP `available`, stdio transport and eight tools;
- a ready 14-document/126-chunk index;
- the remote-work workflow and `POL-RW-*` citation restriction;
- the PTO confirmation gate and confirmed mock email with `sent: false`;
- prompt-injection refusal before MCP access.

Public-deployment artifact:

- Name: `atlas-deployed-v2-evidence`
- Artifact ID: `8847626586`
- Digest: `sha256:0d386d80c9a052a666a467a60c62aae584969e6b7a2f51f0529082ba46b04b55`

## Remaining non-verified requirements

Technical CI does not complete or prove:

- active LLM configuration in the public deployment;
- whether the hashing TF-IDF representation satisfies the grader's interpretation of “embedding model”;
- explicit acceptance of the `quantic-grader` collaborator invitation;
- the required 7–10 minute presentation, camera presence and government-ID check;
- the final Quantic grading decision.
