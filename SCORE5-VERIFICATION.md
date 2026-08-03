# Atlas Score-5 Verification Record

Verified on 3 August 2026 through three independent GitHub Actions runs.

- Packaged-source verification: run **30791401824**.
- Fully expanded `main` source verification: run **30791902570**.
- Public Render v2 deployment verification: run **30792651006**.

The expanded-source run executed directly against the normal, human-readable repository tree now merged into `main`; no source-packaging step was required. The deployed-service run exercised the public Render URL from a GitHub-hosted runner.

## Pipeline result

The `validate` job completed successfully. Every stage passed:

1. Checkout and Python 3.11 setup.
2. Dependency installation.
3. Compilation of `app`, `agent`, `rag`, `mcp_server`, `mcp_client`, `evaluation`, and `scripts`.
4. Persistent SQLite RAG index build.
5. Complete pytest suite.
6. Genuine MCP stdio discovery and calls through the official Python MCP client.
7. FastAPI startup and deep `/health?deep=true` check.
8. Twenty-five-item golden-set evaluation.
9. Retrieval chunk-size ablation.
10. Upload of the `atlas-score-5-evidence` artifact.

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
    "tools": [
      "check_policy_compliance",
      "check_pto_balance",
      "create_mock_hr_ticket",
      "draft_hr_email",
      "get_policy_section",
      "lookup_benefits_status",
      "lookup_employee_profile",
      "search_policy_documents"
    ]
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

## Public deployment verification

The live smoke test called `https://atlas-hr-agent.onrender.com` and proved:

- public deep health returned version `2.0.0`, mode `agentic-rag-mcp`, MCP `available`, transport `stdio`, eight discovered tools, and a ready 14-document/126-chunk RAG index;
- remote-work eligibility completed with the exact tool sequence `search_policy_documents` → `lookup_employee_profile` → `check_policy_compliance` and only `POL-RW-*` citations;
- the PTO request stopped at `confirmation_required` without calling `draft_hr_email`;
- explicit confirmation completed the mock email action with `sent: false` and a no-send disclaimer;
- the prompt-injection test was refused before MCP access.

The check tolerates documented Render free-tier cold starts and transient `429`, `502`, `503`, or `504` responses, but it does not accept an incorrect release, unavailable MCP server, wrong tool sequence, unsafe action, or irrelevant citations.

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
- Warm latency p50: **2.73 ms**
- Warm latency p95: **4.69 ms**

## Retrieval ablation

| Configuration | Chunk / overlap | Hit@3 | Hit@5 | MRR |
|---|---:|---:|---:|---:|
| Compact | 60 / 10 | 1.000 | 1.000 | 0.900 |
| Balanced | 120 / 20 | 1.000 | 1.000 | 0.950 |
| Broad | 220 / 30 | 1.000 | 1.000 | 0.950 |

The balanced configuration remains the selected default because it achieved the best MRR while using fewer chunks than the compact alternative.

## Evidence artifacts

### Public Render v2 deployment

- Name: `atlas-deployed-v2-evidence`
- Workflow run: `30792651006`
- Artifact ID: `8847626586`
- Digest: `sha256:0d386d80c9a052a666a467a60c62aae584969e6b7a2f51f0529082ba46b04b55`
- Verification PR: #5, closed without merge after successful validation.

### Fully expanded source

- Name: `atlas-score-5-evidence`
- Workflow run: `30791902570`
- Artifact ID: `8847359957`
- Digest: `sha256:4570cd84ff1009ad0ab1fe61e9d8d7c073a3b89a0e69c24d1f09ea047c87978f`
- Verification PR: #4, closed without merge after successful validation.

### Packaged source

- Name: `atlas-score-5-evidence`
- Workflow run: `30791401824`
- Artifact ID: `8847177885`
- Digest: `sha256:ec0654d565feff211818ce26c124d7f2c654bd683c1793f49b6b1028c842a28c`
- Verification PR: #2, closed without merge after successful validation.
