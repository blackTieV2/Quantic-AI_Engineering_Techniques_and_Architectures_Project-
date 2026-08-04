# Design and Evaluation

## 1. Design objective

Atlas is a controlled single-agent HR assistant built for the Quantic AI Engineering Techniques and Architectures Project. It combines learned semantic policy retrieval, synthetic structured data, genuine MCP tool discovery and calls, constrained LLM answer refinement, two multi-step workflows, confirmation gates, free-tier deployment, CI/CD and reproducible evaluation.

All policies, employees, balances and actions are fictional.

## 2. Architecture decisions

### 2.1 Explicit single orchestrator

`agent/orchestrator.py` implements manual orchestration. It classifies the request, identifies missing fields, discovers tools, calls MCP-exposed functions, checks structured results, retrieves evidence, applies confirmation gates and produces a controlled draft. The operational trace records tool names, arguments, concise results, citations, provider outcomes and escalation decisions without exposing private chain-of-thought.

This approach was selected because the workflow is small enough to remain explicit and testable. It gives deterministic code authority over tool selection, policy-family filters, action safety and escalation rather than delegating those controls to an unconstrained model.

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

### 2.5 Learned embeddings and vector store

`rag/index.py` uses an OpenAI-compatible `/embeddings` endpoint in the public deployment. It embeds policy chunks with a learned model, stores dense vectors and citation metadata in SQLite, and ranks candidates through cosine similarity with bounded lexical and heading signals.

The index records and reports:

- requested and active embedding model;
- embedding provider;
- dense or fallback vector format;
- vector dimensions;
- any provider/build error;
- chunk and overlap configuration.

A deterministic 384-dimensional hashing TF-IDF representation remains as a tested fallback for CI and provider outages. The fallback is visible through `/health`; it is not represented as the learned production path.

GitHub Actions run `30877645852` independently verified the public deployment had `semantic_embeddings: true`, provider `openrouter`, a learned model, no embedding error and a successful multi-policy semantic query.

### 2.6 Retrieval controls

- top-k retrieval with bounded limits;
- optional document-prefix filtering;
- separate remote-work and security evidence for the multi-document query;
- document ID, title, section, path, chunk ID, score and supporting snippet returned to the caller;
- `insufficient_evidence` when the available evidence is inadequate;
- workflow-specific policy filters to prevent irrelevant citation families;
- safe query-time fallback behavior if the embedding endpoint is transiently unavailable.

### 2.7 LLM provider and control boundary

`agent/llm.py` uses a configured OpenAI-compatible provider controlled by environment variables. Temperature is fixed at zero. The provider refines an already controlled draft after tools and evidence have been selected; it cannot select tools, alter eligibility, override guardrails or authorise actions.

The grounding prompt includes:

- document ID;
- title;
- section;
- source path;
- chunk ID;
- retrieved snippet;
- the controlled draft and its numerical/action constraints.

The prompt explicitly requires preservation of uncertainty, policy distinctions, numerical values and no-action disclaimers. If provider refinement fails, Atlas returns the controlled draft and appends a visible fallback trace entry.

GitHub Actions run `30877051735` independently verified a completed LLM-refinement call in the public deployment, including provider and model evidence in the operational trace.

## 3. Required agentic workflows

### 3.1 International remote work

```text
discover_tools
→ search_policy_documents(query, limit=5, document_prefix="POL-RW-")
→ lookup_employee_profile(employee_id)
→ check_policy_compliance(workflow="remote_work", employee_id, requested_days)
→ controlled cited provisional result
→ constrained LLM refinement
```

The workflow combines policy evidence with employment classification, months of service and rolling remote-day data. It distinguishes provisional policy eligibility from final manager, HR, tax, immigration and information-security approval.

### 3.2 PTO and mock manager email

```text
discover_tools
→ search_policy_documents(query, limit=5, document_prefix="POL-PTO-")
→ lookup_employee_profile(employee_id)
→ check_pto_balance(employee_id, requested_days)
→ check_policy_compliance(workflow="pto", employee_id, requested_days)
→ deterministic confirmation gate
→ draft_hr_email(..., confirmed=true)
→ constrained LLM refinement preserving sent=false
```

The first pass never invokes the write-like tool. After explicit confirmation, the tool creates a local fictional draft with an action ID and `sent=false`.

### 3.3 Multi-policy semantic query

```text
Which policy covers working abroad while accessing confidential company information?
```

The deployed semantic-RAG verification requires evidence from both `POL-RW-*` and `POL-SEC-*` families. This demonstrates cross-document retrieval and grounded LLM synthesis rather than a single-policy lookup.

## 4. Safety and failure handling

- prompt-injection patterns are refused before MCP or LLM access;
- sensitive conduct, legal and medical matters are escalated;
- missing employee records return `not_found` and stop downstream calls;
- unsupported questions return `insufficient_evidence`;
- MCP unavailability returns `mcp_unavailable` without hidden direct calls;
- write-like tools reject unconfirmed requests;
- ineligible responses state the reason rather than returning only a balance;
- LLM failure returns the controlled draft and a visible fallback event;
- embedding build failure uses a visible deterministic index fallback;
- all records and outputs are synthetic;
- operational traces are shown instead of hidden chain-of-thought.

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
SQLite semantic  Synthetic JSON     Mock local action log
RAG index        employee data      (confirmation required)
        ↓
Controlled draft + citation metadata
        ↓
Constrained OpenAI-compatible LLM refinement
```

Render deploys the components as one free-tier Python service. The index and mock action log are stored under `/tmp` and are recreated after a cold start. Secrets are stored in Render environment variables and are not committed.

## 6. Evaluation set and expected-answer rubric

`evaluation/golden_set.json` contains 25 tasks covering direct policy questions, a multi-document policy question, remote-work and PTO workflows, structured benefits lookups, ambiguity, missing records, out-of-scope requests, prompt injection, sensitive-case escalation and confirmation-gated actions.

Each item records the query, expected status, expected tools, required citation prefixes, gold answer keywords and confirmation state. These fields form a deterministic expected-answer rubric. Full prose gold answers are not stored for every item; adding them would make manual review easier but is not required for the current automated checks.

## 7. Metric methodology

`evaluation/run_evaluation.py` reports status accuracy, exact expected-tool sequence, citation-family accuracy, a groundedness proxy, workflow completion, clarification/escalation behavior, action safety, keyword coverage and warm p50/p95 latency.

The checked-in values are deterministic, rule-based proxy metrics. They are not an independent human review and are not an LLM-judge evaluation. In particular:

- the groundedness proxy requires expected citation families, supporting snippets and minimum gold-keyword coverage;
- citation accuracy rejects citations outside the allowed families and requires every expected family;
- tool accuracy requires the exact expected MCP call sequence;
- the warm latency sample contains 15 designated representative deterministic tasks and excludes Render wake-up, embedding-provider and LLM-provider latency.

The public workflow smoke tests separately verify active providers and genuine stdio MCP behavior.

## 8. Checked-in evaluation results

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
| Representative deterministic latency tasks | 15 |
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

## 10. Independent deployment evidence

- Active LLM verification: workflow run `30877051735`, artifact `atlas-deployed-v21-llm-evidence`, ID `8879953426`.
- Learned semantic RAG verification: workflow run `30877645852`, artifact `atlas-deployed-semantic-rag-evidence`, ID `8880135790`, digest `sha256:68599bedf405c576b0a08accf9f7b7dc4862edab778b8d30a88f59e48ba46b24`.

## 11. Known limitations and external actions

- Free provider availability and rate limits can affect cold-start and response latency; retries and controlled fallbacks are implemented.
- The stdio server starts per request rather than remaining as a separate always-on service.
- `/tmp` storage is ephemeral and is rebuilt after a cold start.
- Rule-based evaluation metrics are regression checks, not independent semantic grading.
- The recorded presentation and explicit grader-collaborator confirmation remain external student actions.

See `ASSIGNMENT-COMPLIANCE-AUDIT.md` for the current submission-readiness decision.
