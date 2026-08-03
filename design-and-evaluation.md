# Design and Evaluation

## Design objective

Atlas is a controlled single-agent HR assistant built against the Quantic score-5 rubric. It combines policy RAG, structured synthetic data, genuine MCP tool discovery and calls, two multi-step workflows, confirmation gates, free-tier deployment, CI/CD and reproducible evaluation.

## Architecture decisions

### Single explicit orchestrator

A single agent is easier to test, explain and govern than a multi-agent design for this scope. `agent/orchestrator.py` classifies the request, identifies missing fields, discovers tools, calls only MCP-exposed functions, checks structured results, retrieves evidence, applies confirmation gates and synthesises the response. The trace records operational events without exposing hidden reasoning.

### MCP server and transport

`mcp_server/server.py` uses the official Python SDK's FastMCP implementation and exposes eight tools:

1. `search_policy_documents`
2. `get_policy_section`
3. `lookup_employee_profile`
4. `check_pto_balance`
5. `lookup_benefits_status`
6. `check_policy_compliance`
7. `draft_hr_email`
8. `create_mock_hr_ticket`

The application uses an official MCP client over stdio. The server is a separate subprocess, but remains in the same Render service for free-tier compatibility. Every request begins with tool discovery. Errors are returned through a standard `ok/data/error` envelope and the orchestrator refuses to bypass an unavailable MCP service.

### RAG ingestion and index

The corpus contains 14 fictional policies in Markdown and HTML, about 10,000 words and 34.5 declared pages. The loader extracts document ID, title, section heading, source path and page estimate. The selected chunking configuration is 120 words with 20-word overlap. A deterministic 384-dimensional hashing TF-IDF embedding avoids model downloads and API costs. SQLite stores vectors and citation metadata. The index is rebuilt on cold start and persists for the life of the Render instance.

### Retrieval and citation controls

Retrieval combines cosine similarity with lexical overlap and heading bonuses. At least one meaningful query token must occur in a candidate, reducing hash-collision false positives. Topic-aware document filters are used for specialised workflows. Answers include document ID, title, section, path, chunk ID, score and supporting snippet. Unsupported questions return `insufficient_evidence` rather than a generic policy dump.

### Optional LLM provider

Deterministic synthesis is the default and supports reproducible grading. `agent/llm.py` provides an optional OpenAI-compatible refinement layer controlled by environment variables. It is applied only after tools and evidence have been selected; the provider cannot select tools or override safety controls.

## Required workflows

### International remote work

```text
discover_tools
→ search_policy_documents
→ lookup_employee_profile
→ check_policy_compliance
→ cited provisional result or ineligibility
```

The workflow combines retrieved policy evidence with service, classification and rolling-day data. It distinguishes provisional policy eligibility from final tax, immigration, security and manager approval.

### PTO and mock manager email

```text
discover_tools
→ search_policy_documents
→ lookup_employee_profile
→ check_pto_balance
→ check_policy_compliance
→ confirmation gate
→ draft_hr_email(confirmed=true)
```

The first pass never invokes the write-like tool. After explicit confirmation, the tool creates a local fictional draft with an action ID and clearly states that no email was sent.

## Safety and failure handling

- prompt-injection patterns are refused before MCP access;
- sensitive conduct, legal and medical matters are escalated;
- missing employee records return a clear `not_found` response;
- unsupported questions return `insufficient_evidence`;
- MCP unavailability returns `mcp_unavailable` without hidden direct calls;
- write-like tools reject unconfirmed requests;
- all records and outputs are synthetic;
- concise tool traces are shown instead of private chain-of-thought.

## Golden-set evaluation

`evaluation/golden_set.json` contains 25 items covering direct policy questions, a multi-document question, structured lookups, remote-work and PTO workflows, ambiguity, missing records, out-of-scope questions, prompt injection, escalation and confirmed actions.

The fully expanded source was evaluated in GitHub Actions run `30791902570` and produced:

| Metric | Result |
|---|---:|
| Items | 25 |
| Groundedness | 1.000 |
| Citation accuracy | 1.000 |
| Tool-selection accuracy | 1.000 |
| Workflow-completion rate | 1.000 |
| Clarification/escalation accuracy | 1.000 |
| Action-safety pass rate | 1.000 |
| Status accuracy | 1.000 |
| Mean keyword score | 0.820 |
| Warm latency p50 | 2.73 ms |
| Warm latency p95 | 4.69 ms |

These values are deterministic application-level results using the in-process evaluation transport. They do not replace the MCP protocol test. CI separately starts the official stdio server, discovers tools, calls one policy tool and one structured-data tool, and performs a deep application health check through stdio.

## Public deployment validation

GitHub Actions run `30792651006` tested the public Render deployment rather than a local process. It verified version `2.0.0`, mode `agentic-rag-mcp`, MCP stdio availability, all eight discovered tools, the 14-document/126-chunk index, the remote-work tool sequence and citation family, the PTO confirmation gate, the confirmed mock email with `sent: false`, and prompt-injection refusal before tool access. The resulting `atlas-deployed-v2-evidence` artifact is identified in `deployed.md` and `SCORE5-VERIFICATION.md`.

Render cold-start latency is documented separately because it includes host wake-up, index creation and MCP discovery. The deployed smoke workflow retries only transient free-tier readiness responses; it does not relax functional assertions.

## Retrieval ablation

Three chunk configurations were compared on ten labelled retrieval queries:

| Configuration | Chunk words | Overlap | Hit@3 | Hit@5 | MRR | Approx. chunks |
|---|---:|---:|---:|---:|---:|---:|
| Compact | 60 | 10 | 1.000 | 1.000 | 0.900 | 212 |
| Balanced | 120 | 20 | 1.000 | 1.000 | 0.950 | 126 |
| Broad | 220 | 30 | 1.000 | 1.000 | 0.950 | 126 |

The balanced configuration was selected because it matches the best MRR while preserving smaller evidence units than the broad configuration and requiring fewer chunks than the compact configuration.

## Known limitations

- The corpus and records are fictional and intentionally small.
- The deterministic embedding is less semantically rich than a hosted neural embedding model, but it is reproducible and free-tier safe.
- The stdio server starts per request rather than remaining as a separate always-on service.
- `/tmp` storage is ephemeral and is rebuilt after a cold start.
- The optional LLM provider is not required or exercised in the checked-in metrics.
