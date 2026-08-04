# Atlas Technical Verification Record — Score-5 Target

This file records technical test evidence. It does **not** certify a Quantic grade or claim that external submission actions are complete. The strict requirement assessment is in `ASSIGNMENT-COMPLIANCE-AUDIT.md`.

## Current technical state

The public Atlas release is version `2.1.0` and has independently verified evidence for:

- active OpenAI-compatible LLM refinement;
- learned semantic embeddings through OpenRouter;
- persistent SQLite vector retrieval;
- genuine MCP stdio discovery and tool calls;
- the two required multi-step workflows;
- citations, confirmation controls and prompt-injection refusal;
- deterministic fallback and regression testing.

## Core CI evidence

GitHub Actions run **30877510559** completed successfully for the semantic-embedding release. The run included:

1. Python 3.11 setup and dependency installation.
2. Compilation of `app`, `agent`, `rag`, `mcp_server`, `mcp_client`, `evaluation`, and `scripts`.
3. Persistent SQLite RAG index build.
4. Complete pytest suite, including learned-embedding and fallback tests.
5. Genuine MCP stdio discovery and calls through the official Python MCP client.
6. FastAPI startup and deep `/health?deep=true` check.
7. Twenty-five-item deterministic rubric evaluation.
8. Retrieval chunk-size ablation.
9. Evidence artifact upload.

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

## Active LLM deployment evidence

GitHub Actions run **30877051735** independently exercised the public Render service. It proved:

- version `2.1.0` and mode `agentic-rag-mcp-llm`;
- a configured OpenAI-compatible provider;
- completed `llm_refinement` with provider and model recorded in the response trace;
- the remote-work workflow and correct `POL-RW-*` citation family;
- the PTO confirmation gate and confirmed mock email with the no-send disclaimer;
- prompt-injection refusal before MCP or model access.

Evidence artifact:

- Name: `atlas-deployed-v21-llm-evidence`
- Workflow run: `30877051735`
- Artifact ID: `8879953426`

## Learned semantic embedding evidence

GitHub Actions run **30877645852** independently exercised the public Render service after the semantic-index upgrade. It required and proved:

- `rag_index.semantic_embeddings` equal to `true`;
- embedding provider `openrouter`;
- a learned embedding model rather than `atlas-hashing-tfidf-v1`;
- no recorded embedding error;
- 14 policy documents and 126 chunks in the SQLite index;
- a multi-policy semantic query returning both `POL-RW-*` and `POL-SEC-*` evidence;
- completed LLM refinement;
- preserved MCP transport, workflows, citations, confirmation safety and injection refusal.

Evidence artifact:

- Name: `atlas-deployed-semantic-rag-evidence`
- Workflow run: `30877645852`
- Artifact ID: `8880135790`
- Digest: `sha256:68599bedf405c576b0a08accf9f7b7dc4862edab778b8d30a88f59e48ba46b24`

## Representative verified health fields

```json
{
  "status": "ok",
  "service": "atlas-hr-agent",
  "version": "2.1.0",
  "mode": "agentic-rag-mcp-llm",
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
    "semantic_embeddings": true,
    "embedding_provider": "openrouter",
    "embedding_model": "<verified learned model>",
    "embedding_error": null,
    "chunk_words": 120,
    "overlap_words": 20
  },
  "llm_provider": {
    "status": "configured",
    "type": "openai-compatible",
    "model": "<configured model>",
    "endpoint_host": "openrouter.ai"
  },
  "synthetic_data_only": true
}
```

Model names are represented generically in this documentation excerpt; the non-secret deployed health response and workflow artifact retain the exact configured identifiers. API keys are never returned.

## Evaluation results

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

These are deterministic rubric-based proxy metrics. Groundedness is not an independent semantic-entailment judgment. Citation accuracy requires every expected policy family, and tool accuracy requires the exact expected MCP call sequence. The live smoke tests separately prove active provider execution.

## Retrieval ablation

| Configuration | Chunk / overlap | Hit@3 | Hit@5 | MRR |
|---|---:|---:|---:|---:|
| Compact | 60 / 10 | 1.000 | 1.000 | 0.900 |
| Balanced | 120 / 20 | 1.000 | 1.000 | 0.950 |
| Broad | 220 / 30 | 1.000 | 1.000 | 0.950 |

The balanced configuration remains the selected default because it matches the best MRR while using fewer chunks than the compact alternative and smaller evidence units than the broad alternative.

## Remaining non-technical requirements

Technical CI does not complete or prove:

- explicit acceptance of the `quantic-grader` collaborator invitation;
- the required 7–10 minute presentation, camera presence and government-ID check;
- the quality of the final presentation and submission;
- the final Quantic grading decision.

The repository is a score-5-target implementation with verified technical evidence. Only Quantic can award the grade.
