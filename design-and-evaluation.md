# Design and Evaluation

## 1. Design objective

Atlas is a controlled single-agent HR assistant built for the Quantic AI Engineering Techniques and Architectures Project. It combines policy retrieval, synthetic structured data, genuine MCP tool discovery and calls, two multi-step workflows, confirmation gates, free-tier deployment, CI/CD and reproducible evaluation.

All policies, employees, balances and actions are fictional.

## 2. Architecture decisions

### 2.1 Explicit single orchestrator

`agent/orchestrator.py` implements manual orchestration. It classifies the request, identifies missing fields, discovers tools, calls MCP-exposed functions, checks structured results, retrieves evidence, applies confirmation gates and produces the response. The operational trace records tool names, arguments, concise results, citations and escalation decisions without exposing private chain-of-thought.

This approach was selected because the workflow is small enough to remain explicit and testable. It provides stronger control over action safety than allowing an unconstrained model to choose arbitrary operations.

### 2.2 MCP server and transport

`mcp_server/server.py` uses the official Python MCP SDK's `FastMCP` implementation. `mcp_client/client.py` uses the official client over stdio. The MCP server runs as a separate subprocess within the same Render service, preserving a real protocol boundary without requiring a second paid service.

Every normal request starts by discovering the available tools. If discovery or a call fails, the orchestrator returns `mcp_unavailable` rather than bypassing MCP with a hidden direct call.

### 2.3 MCP tool schemas

| Tool | Required inputs | Optional inputs | Structured result / behavior |
|---|---|---|---|
| `search_policy_documents` | `query: str` | `limit: int`, `document_prefix: str` | Citation-ready chunks, scores and index metadata |
| `get_policy_section` | `document_id: str` | `section: str` | Matching policy sections or a structured `not_found` error |
| `lookup_employee_profile` | `employee_id: str` | — | Synthetic employee profile or `employee_not_found` |
| `check_pto_balance` | `employee_id: str` | `requested_days: int` | Balance, sufficiency and remaining balance |
| `lookup_benefits_status` | `employee_id: str` | — | Synthetic eligibility/enrolment record |
| `check_policy_compliance` | `workflow: str`, `employee_id: str` | `requested_days: int`, `destination: str` | Eligibility, reasons, limits and required approvals |
| `draft_hr_email` | `employee_id: str`, `purpose: str` | `requested_days: int`, `confirmed: bool` | Local fictional draft only when `confirmed=true`; always `sent=false` |
| `create_mock_hr_ticket` | `employee_id: str`, `category: str`, `summary: str` | `confirmed: bool` | Local fictional ticket only when confirmed; never contacts production |

Every tool returns a common `ok/data/error` envelope.

### 2.4 Policy corpus, ingestion and chunking

The corpus contains 14 fictional policies in Markdown and HTML, approximately 10,000 words and 34.5 estimated pages. `rag/ingest.py` extracts document ID, title, section heading, source path and page estimate from both formats.

The selected configuration is heading-aware 120-word windows with 20-word overlap, deterministic ordering and stable chunk IDs. The ablation compares 60/10, 120/20 and 220/30 configurations.

### 2.5 Vector representation and store

`rag/index.py` creates a deterministic 384-dimensional hashing TF-IDF vector representation and stores vectors and citation metadata in SQLite. Retrieval combines cosine similarity, lexical overlap and heading bonuses. At least one meaningful query token must occur in a candidate, reducing hash-collision false positives.

This design is free-tier safe and reproducible. It is also a strict-assignment review risk: the brief refers to a free or local **embedding model**, and a grader may expect a learned neural embedding model rather than a hashing TF-IDF representation. This limitation is recorded rather than concealed.

### 2.6 Retrieval controls

- top-k retrieval with limits between four and five for normal workflows;
- optional document-prefix filtering;
- separate remote-work and security retrieval for the multi-document query;
- document ID, title, section, path, chunk ID, score and supporting snippet returned to the caller;
- `insufficient_evidence` when no result exceeds the relevance threshold;
- workflow-specific policy filters to prevent irrelevant citation families.

### 2.7 LLM provider and current deployment status

`agent/llm.py` contains an optional OpenAI-compatible refinement provider controlled by `ATLAS_LLM_BASE_URL`, `ATLAS_LLM_API_KEY` and `ATLAS_LLM_MODEL`. Temperature is fixed at zero. The provider refines an already controlled draft after tools and evidence have been selected; it cannot select tools or override guardrails.

The grounding prompt supports citation metadata including document ID, title, section, source path, chunk ID and snippet. The remote-work workflow passes the complete citation objects into this refinement layer. Tests verify the metadata-rich prompt construction.

The current public Render health response reports deterministic mode because the provider variables are not configured. The course brief explicitly asks for a working LLM-based system. Therefore, the present deployment is technically functional but is not represented as fully satisfying that requirement until an active provider is configured and tested. Broader use of the refinement layer across every response path is not required for tool control, but it could strengthen the demonstration of LLM-based answer synthesis.

## 3. Required agentic workflows

### 3.1 International remote work

```text
discover_tools
→ search_policy_documents(query, limit=5, document_prefix="POL-RW-")
→ lookup_employee_profile(employee_id)
→ check_policy_compliance(workflow="remote_work", employee_id, requested_days)
→ cited provisional result or ineligibility
```

The workflow combines policy evidence with employment classification, months of service and rolling remote-day data. It distinguishes provisional policy eligibility from final manager, HR, tax, immigration and information-security approval.

### 3.2 PTO and mock manager email

```text
discover_tools
→ search_policy_documents(query, limit=5, document_prefix="POL-PTO-")
→ lookup_employee_profile(employee_id)
→ check_pto_balance(employee_id, requested_days)
→ check_policy_compliance(workflow="pto", employee_id, requested_days)
→ confirmation gate
→ draft_hr_email(..., confirmed=true)
```

The first pass never invokes the write-like tool. After explicit confirmation, the tool creates a local fictional draft with an action ID and `sent=false`.

## 4. Safety and failure handling

- prompt-injection patterns are refused before MCP access;
- sensitive conduct, legal and medical matters are escalated;
- missing employee records return `not_found` and stop downstream structured-data calls;
- unsupported questions return `insufficient_evidence`;
- MCP unavailability returns `mcp_unavailable` without hidden direct calls;
- write-like tools reject unconfirmed requests;
- ineligible PTO responses state the reason rather than returning only a balance;
- all records and outputs are synthetic;
- tool traces are shown instead of hidden chain-of-thought.

## 5. Web and deployment architecture

```text
Browser / API client
        ↓
FastAPI web app
        ↓
Request controls + Atlas orchestrator
        ↓
Official MCP client over stdio
        ↓
FastMCP server subprocess
   ┌───────────────┬──────────────────┬────────────────────┐
   ↓               ↓                  ↓
SQLite RAG     Synthetic JSON     Mock local action log
index          employee data     (confirmation required)
        ↓
Optional OpenAI-compatible LLM refinement
```

Render deploys the components as one free-tier Python service. The index and mock action log are stored under `/tmp` and are recreated after a cold start.

## 6. Evaluation set and expected-answer rubric

`evaluation/golden_set.json` contains 25 tasks covering direct policy questions, a multi-document policy question, remote-work and PTO workflows, structured benefits lookups, ambiguity, missing records, out-of-scope requests, prompt injection, sensitive-case escalation and confirmation-gated actions.

Each item records the query, expected status, expected tools, required citation prefixes, gold answer keywords and confirmation state. These fields form a deterministic expected-answer rubric. Full prose gold answers are not currently stored for every item; adding them would make manual review easier.

## 7. Metric methodology

`evaluation/run_evaluation.py` reports status accuracy, exact expected-tool sequence, citation-family accuracy, a groundedness proxy, workflow completion, clarification/escalation behavior, action safety, keyword coverage and warm p50/p95 latency.

The checked-in values are deterministic, rule-based proxy metrics. They are not an independent human review and are not an LLM-judge evaluation. In particular:

- the groundedness proxy requires expected citation families, supporting snippets and at least 50% gold-keyword coverage for cited items;
- citation accuracy rejects citations outside the allowed families and requires every expected family, including both families in the multi-document item;
- tool accuracy requires the exact expected MCP call sequence;
- the warm latency sample contains 15 designated representative tasks and excludes Render wake-up time.

The public workflow smoke test separately verifies genuine stdio MCP behavior and the deployed workflows.

## 8. Checked-in evaluation results

Source: GitHub Actions run `30798365389`, artifact `8849788261`.

| Metric | Result |
|---|---:|
| Items | 25 |
| Groundedness proxy | 1.000 |
| Citation-family accuracy | 1.000 |
| Exact MCP tool-sequence accuracy | 1.000 |
| Workflow-completion rate | 1.000 |
| Clarification/escalation accuracy | 1.000 |
| Action-safety pass rate | 1.000 |
| Status accuracy | 1.000 |
| Mean keyword score | 0.940 |
| Representative latency tasks | 15 |
| Warm latency p50 | 2.72 ms |
| Warm latency p95 | 4.59 ms |

The complete summary and item results are recorded in `evaluation/results.json` and `evaluation/results.md`. Render cold-start behavior is documented separately in `deployed.md`.

## 9. Retrieval ablation

| Configuration | Chunk words | Overlap | Hit@3 | Hit@5 | MRR | Approx. chunks |
|---|---:|---:|---:|---:|---:|---:|
| Compact | 60 | 10 | 1.000 | 1.000 | 0.900 | 212 |
| Balanced | 120 | 20 | 1.000 | 1.000 | 0.950 | 126 |
| Broad | 220 | 30 | 1.000 | 1.000 | 0.950 | 126 |

The balanced configuration is selected because it matches the best MRR while retaining smaller evidence units than the broad configuration and fewer chunks than the compact configuration.

## 10. Known limitations and strict-alignment actions

- The current public deployment uses deterministic synthesis unless an LLM provider is configured.
- The hashing TF-IDF vector representation may not meet a strict interpretation of “embedding model.”
- Rule-based evaluation metrics are useful regression checks but are not independent semantic grading.
- The stdio server starts per request rather than remaining as a separate always-on service.
- `/tmp` storage is ephemeral and is rebuilt after a cold start.
- The recorded presentation and explicit grader-collaborator verification remain external student actions.

See `ASSIGNMENT-COMPLIANCE-AUDIT.md` for the submission-readiness decision.