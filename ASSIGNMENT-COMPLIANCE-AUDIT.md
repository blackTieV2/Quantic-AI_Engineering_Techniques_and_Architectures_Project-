# Assignment Compliance Audit

Audit updated: 4 August 2026

Scope: current `main` implementation compared requirement-by-requirement with the Quantic **AI Engineering Techniques and Architectures Project** brief. This audit distinguishes technical functionality, documentation evidence and external submission actions. It is not an official grade.

## Executive finding

The two previously identified technical interpretation risks have now been closed and independently verified in the public deployment:

1. Atlas uses a configured OpenAI-compatible LLM to refine grounded answers after deterministic orchestration; and
2. Atlas uses a learned semantic embedding model through an OpenAI-compatible embeddings endpoint, with a tested local hashing fallback for CI and outages.

The technical implementation is therefore aligned with the assignment's LLM, RAG, MCP, deployment, workflow, evaluation and CI/CD requirements. The remaining items are external submission actions: recording the required presentation and confirming the explicit `quantic-grader` invitation is visible or accepted in GitHub settings.

## Requirement-by-requirement audit

| Area | Requirement | Evidence reviewed | Finding |
|---|---|---|---|
| Project overview | Agentic HR system with RAG, MCP, mock data and grounded responses | `app/`, `agent/`, `rag/`, `mcp_client/`, `mcp_server/`, `mock_data/` | PASS |
| Learning outcome | Working LLM-based agentic system | `agent/llm.py`, `/chat` LLM trace, public smoke run `30877051735` | PASS; active provider call completed in the public deployment |
| Environment | Virtual environment and dependency instructions | `README.md`, `requirements.txt` | PASS |
| Environment | Setup, local run, deployment and evaluation instructions | `README.md`, `deployed.md`, `.env.example` | PASS |
| Environment | Deterministic or fixed behavior where applicable | stable chunking, deterministic routing, temperature zero, controlled fallback | PASS |
| Environment | Secrets from environment and not committed | `.env.example`, `.gitignore`, Render environment configuration | PASS |
| Corpus | 5–20 policy files totaling 30–120 pages | 14 Markdown/HTML files, about 10,000 words, 34.5 estimated pages | PASS; page count is estimated |
| Corpus | Synthetic structured data without real PII | `mock_data/*.json` | PASS |
| Ingestion | At least two formats | Markdown and HTML loaders | PASS |
| Ingestion | Clean, heading-aware chunking with justified overlap | `rag/ingest.py`, 120/20 selected through ablation | PASS |
| Embeddings | Free/local learned embedding model or free-tier API | `rag/index.py`, OpenRouter embedding provider, public smoke run `30877645852` | PASS; learned semantic embeddings independently verified |
| Embedding resilience | Safe behavior if provider is unavailable | local hashing fallback and regression tests | PASS; fallback is visible in health metadata |
| Vector store | Lightweight local vector database | SQLite dense-vector index | PASS |
| Metadata | Document ID/title/section/source/chunk/snippet | stored in index, returned by RAG and supplied to LLM prompt | PASS |
| RAG | Top-k semantic retrieval and filtering | dense cosine retrieval plus document-prefix filtering | PASS |
| RAG | Prompt chunks and source metadata into LLM context | `agent/llm.py`, `tests/test_llm.py`, completed live refinement trace | PASS |
| RAG | Cited answers and supporting snippets | `/chat`, UI citation cards | PASS |
| RAG | Guardrails and unsupported-question handling | injection refusal and `insufficient_evidence` | PASS |
| RAG | Multi-document question | remote-work/confidential-information query returns `POL-RW-*` and `POL-SEC-*` | PASS; live-tested with semantic embeddings |
| Agent | Interpret intent, select path and call tools | `agent/orchestrator.py` | PASS through explicit routing |
| Agent | Two multi-step workflows | remote work and PTO/email | PASS and live-tested |
| Agent | Concise operational trace | tool discovery, calls and LLM-refinement event | PASS |
| Agent | Graceful failures | missing records, ambiguous requests, MCP/provider failure, insufficient evidence | PASS |
| Agent | Confirmation before mock actions | email and ticket require confirmation | PASS |
| MCP | MCP-compatible server and transport | FastMCP stdio server and official client | PASS |
| MCP | At least five tools | eight typed tools | PASS |
| MCP | RAG and structured/mock tools | search, profile, PTO, benefits, compliance, email and ticket tools | PASS |
| MCP | Agent actually calls MCP-exposed tools | protocol tests and public smoke tests | PASS |
| MCP docs | Architecture, transport, schemas and discovery | design documentation and source | PASS |
| Web | Chat interface | deployed FastAPI UI | PASS |
| Web | `/chat` answer/citations/snippets/trace | `app/main.py` | PASS |
| Web | `/health` application, MCP, RAG, embedding and LLM status | `/health?deep=true` | PASS |
| Web | Reproducible demo tasks | UI presets and demo script | PASS |
| Deployment | Shareable free-tier URL | Render deployment | PASS |
| Deployment | No paid database | local SQLite/JSON | PASS |
| Deployment | Cold-start behavior documented | README and `deployed.md` | PASS |
| CI/CD | Runs on push or PR | `.github/workflows/ci.yml` | PASS |
| CI/CD | Install, build/import/start and tests | compile, pytest and Uvicorn deep health | PASS |
| CI/CD | MCP discovery or call test | `scripts/smoke_mcp.py`, `tests/test_mcp.py` | PASS |
| CI/CD | Deploy only if tests pass | Render `autoDeployTrigger: checksPass` | PASS |
| Evaluation | 20–30 questions/tasks | 25 items | PASS |
| Evaluation | Straightforward, multi-doc, tool, ambiguous and out-of-scope cases | `evaluation/golden_set.json` | PASS |
| Evaluation | Gold answers or rubrics | statuses, exact tool sequences, citation families and gold keywords | PASS as a deterministic rubric |
| Evaluation | Groundedness and citation metrics | reproducible rule-based proxies | PASS with qualification: not independent semantic judging |
| Evaluation | Tool/workflow/escalation/action-safety metrics | evaluation script | PASS |
| Evaluation | p50/p95 latency for representative tasks | designated 15-task warm sample | PASS |
| Evaluation | Cold versus warm behavior | warm metrics plus documented free-tier cold start | PASS at minimum |
| Evaluation | Ablation/comparison | three chunk configurations | PASS |
| Design docs | Design choices and architecture | `design-and-evaluation.md`, `docs/architecture.md` | PASS |
| Design docs | Two workflows and expected MCP calls | design and demo script | PASS |
| AI tooling | Tools used, how, what worked and what failed | `ai-tooling.md` | PASS |
| Submission | Required repository evidence | README, design, evaluation, deployment, mock data and MCP code | PASS |
| Submission | Share with `quantic-grader` | student reports account added | EXTERNAL CHECK: verify invitation visible or accepted in Settings |
| Submission | 7–10 minute screen-share, camera, government ID and two tasks | script only | PENDING EXTERNAL ACTION |

## Verified implementation evidence

### Core CI

GitHub Actions run `30877510559` completed successfully for the learned-embedding change. It covered dependency installation, compilation, persistent index build, the complete pytest suite, genuine MCP discovery and calls, application startup/deep health, golden-set evaluation, ablation and evidence upload.

### Active LLM deployment verification

GitHub Actions run `30877051735` independently exercised the public Render service and proved:

- release `2.1.0` and mode `agentic-rag-mcp-llm`;
- a configured OpenAI-compatible provider;
- a completed `llm_refinement` event containing provider and model evidence;
- MCP stdio availability and all eight tools;
- remote-work and PTO workflows;
- the confirmation gate and no-send mock action;
- prompt-injection refusal before tool or model access.

Artifact: `atlas-deployed-v21-llm-evidence`, ID `8879953426`.

### Learned semantic RAG deployment verification

GitHub Actions run `30877645852` independently exercised the public Render service after the embedding upgrade and proved:

- `semantic_embeddings: true`;
- embedding provider `openrouter`;
- a learned embedding model rather than `atlas-hashing-tfidf-v1`;
- no recorded embedding build error;
- the 14-document, 126-chunk SQLite index;
- a multi-policy semantic question returning both remote-work and information-security policy families;
- completed LLM refinement;
- preserved MCP workflows, action confirmation and prompt-injection refusal.

Artifact: `atlas-deployed-semantic-rag-evidence`, ID `8880135790`, digest `sha256:68599bedf405c576b0a08accf9f7b7dc4862edab778b8d30a88f59e48ba46b24`.

## Evaluation results

The deterministic 25-item regression evaluation reports:

- groundedness proxy: 1.000;
- citation-family accuracy: 1.000;
- exact MCP tool-sequence accuracy: 1.000;
- workflow completion: 1.000;
- clarification/escalation accuracy: 1.000;
- action-safety pass rate: 1.000;
- status accuracy: 1.000;
- mean keyword score: 0.940;
- warm latency over 15 representative deterministic tasks: p50 2.72 ms, p95 4.59 ms.

These remain deterministic regression proxies, not independent expert or LLM-judge scores. The public deployment smoke tests separately prove that the configured learned embedding and LLM paths are active.

## Remaining submission risks

### 1. Grader access

The student reports that `quantic-grader` has been added. Before submission, verify the account appears as invited or accepted under **Settings → Collaborators**. A public-repository `read` result does not prove explicit collaboration.

### 2. Recorded presentation

The student must personally complete the external presentation requirement:

- 7–10 minutes;
- screen capture with voiceover;
- presenter on camera;
- government ID shown if required by the brief;
- two tasks demonstrated end-to-end;
- explanation of MCP tool names, arguments, outputs, citations, LLM refinement and final action behavior;
- repository, deployment, CI/CD and evaluation evidence briefly shown.

## Current rubric position

The technical implementation now addresses the previously open LLM and embedding requirements and is positioned to compete for the highest rubric level. That is an implementation assessment, not a promise or certification of a score. Final grading remains Quantic's decision and also depends on the quality and compliance of the submitted presentation and repository access.
