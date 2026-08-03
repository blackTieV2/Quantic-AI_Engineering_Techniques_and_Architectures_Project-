# Quantic Requirements Compliance Matrix

| ID | Requirement | Implementation | Evidence | Status |
|---|---|---|---|---|
| R1 | Build an agentic HR policy and operations system | Explicit single-agent orchestration with clarification, escalation, retrieval, MCP tools and confirmation | `agent/orchestrator.py`, deployed UI | Complete |
| R2 | RAG over 5–20 internal documents totalling approximately 30–120 pages | 14 fictional policies, 34.5 declared pages, Markdown and HTML | `policies/`, `/health` index statistics | Complete |
| R3 | Preserve citation metadata and supporting snippets | Document ID, title, section, source path, chunk ID, score and snippet | `rag/index.py`, `/chat` responses | Complete |
| R4 | Use synthetic structured HR data | Eight employee profiles, PTO, benefits, offices and empty ticket seed | `mock_data/` | Complete |
| R5 | Genuine MCP server with at least five tools | FastMCP server exposes eight typed tools | `mcp_server/server.py`, `mcp_server/tools.py` | Complete |
| R6 | Agent discovers and calls MCP tools | Official client lists tools and calls them over stdio | `mcp_client/client.py`, `scripts/smoke_mcp.py` | Complete |
| R7 | Two end-to-end multi-step workflows | International remote work and PTO plus confirmed mock email | UI presets, `tests/test_app.py` | Complete |
| R8 | Graceful failures and safety controls | Prompt-injection refusal, missing record, sensitive escalation, MCP-unavailable response, confirmation gates | Tests and golden set | Complete |
| R9 | Web chat, `/chat`, `/health`, citations and trace | FastAPI browser UI and structured endpoints | `app/main.py`, public Render URL | Complete |
| R10 | Free-tier deployment and cold-start documentation | One-service Render Blueprint with SQLite index generated at startup | `render.yaml`, `deployed.md` | Complete |
| R11 | CI on push/PR with startup and MCP test | Compile, index build, pytest, genuine MCP smoke call, deep health, evaluation and ablation | `.github/workflows/ci.yml`, `SCORE5-VERIFICATION.md` | Complete |
| R12 | 20–30 evaluation items | 25-item golden set across policy, workflows, ambiguity, missing records, safety and actions | `evaluation/golden_set.json` | Complete |
| R13 | Quality and behaviour metrics | Groundedness, citation accuracy, tool selection, workflow completion, escalation, action safety, p50/p95 | `evaluation/results.*`, `SCORE5-VERIFICATION.md` | Complete |
| R14 | At least one ablation | Three chunk-size/overlap configurations with Hit@3, Hit@5 and MRR | `evaluation/ablation-results.*` | Complete |
| R15 | Design documentation and architecture | Transport, schemas, chunking, vector store, safety and workflow sequences documented | `design-and-evaluation.md`, `docs/architecture.md` | Complete |
| R16 | AI tooling disclosure | Development use and accountability recorded | `ai-tooling.md` | Complete |
| R17 | Deployed URLs and health endpoint | Public app, health, docs and tool registry recorded | `deployed.md` | Complete |
| R18 | 7–10 minute recorded demonstration | Timed script provided | `docs/demo-script.md` | Student recording required |
| R19 | Share repository with `quantic-grader` | GitHub collaborator permission verified as `read` on 3 August 2026 | Repository collaborator permission | Complete |

## Verification note

The fully expanded human-readable source tree passed the complete score-5 CI pipeline in run `30791902570`. The evidence artifact and exact metrics are recorded in `SCORE5-VERIFICATION.md`.
