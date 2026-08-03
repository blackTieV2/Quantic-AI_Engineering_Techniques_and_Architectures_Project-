# Assignment Compliance Audit

Audit date: 3 August 2026

Scope: current `main` implementation compared requirement-by-requirement with the Quantic **AI Engineering Techniques and Architectures Project** brief. This audit distinguishes technical functionality, documentation evidence and external submission actions. It is not an official grade.

## Executive finding

The repository has a strong deployed MCP/RAG foundation and satisfies most implementation requirements. It should **not yet be represented as unquestionably score-5 complete** because two technical interpretation risks remain:

1. the public deployment currently runs deterministic synthesis rather than an active LLM provider; and
2. the RAG index uses hashing TF-IDF vectors rather than a learned local or hosted embedding model.

The recorded video is also outstanding, and explicit `quantic-grader` invitation status must be checked in GitHub settings.

## Requirement-by-requirement audit

| Area | Requirement | Evidence reviewed | Finding |
|---|---|---|---|
| Project overview | Agentic HR system with RAG, MCP, mock data and grounded responses | `app/`, `agent/`, `rag/`, `mcp_client/`, `mcp_server/`, `mock_data/` | PASS for functional architecture |
| Learning outcome | Working LLM-based agentic system | `agent/llm.py`, `/health` behavior, `render.yaml` | PARTIAL: provider code exists, but current deployment reports deterministic mode |
| Environment | Virtual environment instructions | `README.md` | PASS |
| Environment | Dependency manifest | `requirements.txt` | PASS; MCP dependency is range-pinned rather than exact |
| Environment | Setup, local run, deployment and evaluation instructions | `README.md`, `deployed.md` | PASS |
| Environment | Fixed seeds or deterministic behavior | deterministic chunking, stable hashing, temperature zero when provider enabled | PASS where applicable; no stochastic sampling is used |
| Environment | Secrets from environment and not committed | `.env.example`, `.gitignore` | PASS |
| Corpus | 5–20 policy files totaling 30–120 pages | 14 Markdown/HTML files, about 10,000 words, 34.5 estimated pages | PASS; page count is an estimate rather than rendered pagination |
| Corpus | Synthetic structured data without real PII | `mock_data/*.json` | PASS |
| Ingestion | At least two formats | Markdown and HTML loaders | PASS |
| Ingestion | Clean and heading-aware chunking | `rag/ingest.py` | PASS |
| Ingestion | Justified chunking with overlap | 120/20 selected via ablation | PASS |
| Embeddings | Free/local embedding model or free-tier API | hashing TF-IDF vector representation | REVIEW RISK: valid local vectors, but not a learned embedding model |
| Vector store | Lightweight local vector database | SQLite vector index | PASS; SQLite is explicitly acceptable in the recommended architecture |
| Metadata | Document ID/title/section/snippet | stored and returned by RAG | PASS |
| RAG | Top-k retrieval and optional filtering | `rag/index.py`, document-prefix filters | PASS |
| RAG | Prompt retrieved chunks and source metadata into LLM context | `agent/llm.py` | PARTIAL: optional prompt uses snippets; active provider is not configured and full metadata is not injected |
| RAG | Cited answers and supporting snippets | `/chat`, UI citation cards | PASS |
| RAG | Guardrails and unsupported-question handling | injection refusal and `insufficient_evidence` | PASS |
| RAG | Multi-document question | international/confidential-data path retrieves `POL-RW-*` and `POL-SEC-*` | PASS functionally; evaluation prefix coverage check should be strengthened |
| Agent | Interpret intent, decide RAG/tool path, select and call tools | `agent/orchestrator.py` | PASS through explicit deterministic routing |
| Agent | Two multi-step workflows | remote work and PTO/email | PASS and live-tested |
| Agent | Concise operational trace | discovery and tool-call trace | PASS |
| Agent | Graceful failures | missing records, ambiguous requests, MCP failure, insufficient evidence | PASS |
| Agent | Confirmation before mock actions | email and ticket require `confirmed=true` | PASS |
| MCP | MCP-compatible server and transport | FastMCP stdio server | PASS |
| MCP | At least five tools | eight tools | PASS |
| MCP | RAG tool and structured/mock tool | policy search, employee/PTO/benefits, email/ticket | PASS |
| MCP | Agent actually calls MCP-exposed tools | official stdio client and public smoke test | PASS |
| MCP docs | Architecture, transport, schemas and discovery | design docs and code | PASS after explicit schema table was added in the audit revision |
| Web | Chat interface | deployed FastAPI UI | PASS |
| Web | `/chat` answer/citations/snippets/trace | `app/main.py` | PASS |
| Web | `/health` app and MCP status | `/health?deep=true` | PASS |
| Web | Two reproducible demo tasks | UI presets and demo script | PASS |
| Deployment | Shareable free-tier URL | Render deployment | PASS |
| Deployment | No paid database | local SQLite/JSON | PASS |
| Deployment | Cold-start behavior documented | README and `deployed.md` | PASS; documented rather than rigorously benchmarked |
| CI/CD | Runs on push or PR | `.github/workflows/ci.yml` | PASS |
| CI/CD | Install, build/import/start and tests | compile, pytest, Uvicorn deep health | PASS |
| CI/CD | MCP discovery or call test | `scripts/smoke_mcp.py`, `tests/test_mcp.py` | PASS |
| CI/CD | Deploy only if tests pass | Render `autoDeployTrigger: checksPass` | PASS |
| Evaluation | 20–30 questions/tasks | 25 items | PASS |
| Evaluation | Straightforward, multi-doc, tool, ambiguous and OOS cases | `evaluation/golden_set.json` | PASS |
| Evaluation | Correct/gold answers or rubrics | expected statuses, tools, citation prefixes and gold keywords | PASS as a rubric; full prose gold answers would strengthen evidence |
| Evaluation | Groundedness and citation metrics | rule-based proxies | PARTIAL QUALITY: reproducible but not semantic entailment or independent judging |
| Evaluation | Tool/workflow/escalation/action-safety metrics | evaluation script | PASS as deterministic regression metrics |
| Evaluation | p50/p95 latency for representative tasks | warm evaluation p50/p95 over all 25 items | MOSTLY PASS; a designated 10–20 task latency subset would align more literally |
| Evaluation | Cold versus warm behavior | warm metrics plus cold-start note | PASS at minimum; no controlled cold-start benchmark |
| Evaluation | Ablation/comparison | three chunk configurations | PASS |
| Design docs | Design choices and architecture | `design-and-evaluation.md`, `docs/architecture.md` | PASS after audit revision |
| Design docs | Two workflows and expected MCP calls | design and demo script | PASS |
| AI tooling | Tools used, how, what worked and what did not | `ai-tooling.md` | PASS after audit revision |
| Submission | README, design, AI tooling, deployed, evaluation, mock data and MCP code | repository | PASS |
| Submission | Share with `quantic-grader` | student reports account added | EXTERNAL CHECK: verify invitation visible or accepted in Settings |
| Submission | 7–10 minute screen-share, camera, government ID and two tasks | script only | PENDING EXTERNAL ACTION |

## Material risks before submission

### 1. Active LLM requirement

The brief says the project should implement a **working LLM-based agentic system** and a prompting strategy that injects retrieved chunks and metadata into the LLM context. The current Render release reports `llm_provider: deterministic` unless external provider variables are configured. The optional refinement code is not equivalent to proving active LLM use in the deployed application.

Recommended closure:

- configure a free-tier OpenAI-compatible provider in Render;
- format evidence with document ID, title, section and snippet in the model prompt;
- add a CI test using a mocked provider and a live demo showing the configured provider mode;
- retain deterministic safety and tool-selection controls around the model.

### 2. Embedding-model interpretation

Hashing TF-IDF is lightweight, deterministic and produces vectors, but the wording “embedding model” may be interpreted as a learned semantic embedding model.

Recommended closure:

- use a small local ONNX embedding model or a free embedding API; or
- obtain written confirmation from the instructor that deterministic TF-IDF vectorization satisfies the requirement.

### 3. Evaluation claims

The 1.000 figures are deterministic regression proxies. They should not be described as independent expert scores. The multi-document citation check and exact tool-sequence validation should be strengthened before calling the evaluation “outstanding.”

### 4. Submission actions

- verify `quantic-grader` is explicitly invited or accepted;
- record the 7–10 minute video;
- be on camera and show the required government ID;
- demonstrate two tasks end-to-end and explain tool names, arguments, outputs, citations and final behavior;
- include the presentation link and repository link in the Quantic submission.

## Current rubric estimate

- **Technical implementation excluding the active-LLM issue:** strong score-4 territory and potentially score-5 quality in MCP, deployment, workflows and CI.
- **Strict reading of the complete brief today:** not yet safe to claim score 5 because the deployed system is not currently using an active LLM and the embedding implementation may be challenged.
- **After closing those two technical risks and recording a strong demo:** the project would be positioned to compete for score 5, subject to Quantic’s grading judgment.
