# Quantic Requirements Compliance Matrix

This matrix distinguishes implemented technical controls from requirements that still need external completion or stronger evidence. It is not an official grading determination.

| ID | Requirement | Implementation / evidence | Status |
|---|---|---|---|
| R1 | Build an agentic HR policy and operations system | Explicit single-agent orchestration with clarification, escalation, retrieval, MCP tools and confirmation in `agent/orchestrator.py` | Implemented |
| R2 | RAG over 5–20 internal documents totalling approximately 30–120 pages | 14 fictional policies, approximately 10,000 words and 34.5 estimated pages, in Markdown and HTML | Implemented |
| R3 | Parse and clean at least two source formats | Heading-aware Markdown and HTML loaders in `rag/ingest.py` | Implemented |
| R4 | Chunking with a justified strategy | 120-word chunks with 20-word overlap; ablation compares 60/10, 120/20 and 220/30 | Implemented |
| R5 | Embed chunks using a free/local embedding model or free-tier API | Deterministic hashing TF-IDF vector representation in `rag/index.py` | Review risk: produces embeddings, but is not a learned neural embedding model |
| R6 | Lightweight vector database and citation metadata | SQLite stores vectors, document ID, title, section, source path, chunk ID and snippets | Implemented |
| R7 | Top-k RAG, filters, grounded citations and multi-document retrieval | Top-k search, document-prefix filters, citation-ready results and a remote-work/security multi-document path | Implemented |
| R8 | Prompting strategy that injects retrieved chunks and source metadata into an LLM context | Optional OpenAI-compatible refinement exists in `agent/llm.py`; current Render health reports deterministic mode, and the prompt currently receives snippets rather than the complete citation metadata object | Partial; active LLM configuration and metadata-rich prompt should be completed for strict compliance |
| R9 | Two multi-step agentic workflows | International remote work and PTO plus confirmed mock email | Implemented and live-tested |
| R10 | Visible operational trace without hidden chain-of-thought | Tool discovery, selected tools, arguments, concise outputs, citations and escalation decisions are returned | Implemented |
| R11 | Graceful failures and confirmation before actions | Prompt-injection refusal, missing record, insufficient evidence, MCP-unavailable response and confirmation gates | Implemented |
| R12 | Genuine MCP server with at least five tools | FastMCP server exposes eight tools in `mcp_server/`; official client uses stdio | Implemented and protocol-tested |
| R13 | Web chat, `/chat`, `/health` and two reproducible tasks | FastAPI UI and structured endpoints in `app/main.py` | Implemented and deployed |
| R14 | Free-tier deployment and cold-start documentation | Render single-service Blueprint; SQLite index generated at startup; URLs and cold-start notes in `deployed.md` | Implemented |
| R15 | CI/CD on push/PR, app startup and MCP call test | `.github/workflows/ci.yml` installs, compiles, builds index, runs pytest, starts FastAPI, calls genuine MCP tools, evaluates and uploads artifacts | Implemented |
| R16 | Deployment only after tests pass | `render.yaml` uses `autoDeployTrigger: checksPass` | Implemented |
| R17 | Evaluation set of 20–30 tasks with answers or rubrics | 25 items include expected status, tools, citation prefixes and gold keywords | Implemented as a deterministic rubric; full prose gold answers would strengthen it |
| R18 | Groundedness, citation, tool, workflow, safety and latency metrics | `evaluation/run_evaluation.py` reports rule-based proxy metrics and warm p50/p95; ablation is included | Implemented with methodology limitations documented in the audit |
| R19 | Design documentation, architecture, tool schemas and workflow sequences | `design-and-evaluation.md`, `docs/architecture.md` and demo script | Mostly implemented; explicit schema table is added in the audit-alignment revision |
| R20 | AI tooling disclosure including what worked and what did not | `ai-tooling.md` | Implemented in the audit-alignment revision |
| R21 | Share repository with `quantic-grader` | Student reports the account has been added | Student verification required: confirm the collaborator invitation is visible or accepted in repository settings |
| R22 | 7–10 minute recorded demo with two tasks, camera/ID and explanation of MCP arguments/results/citations | Timed script exists in `docs/demo-script.md` | External student action required |

## Current submission blockers

1. **Active LLM use:** the deployed application currently reports deterministic synthesis unless `ATLAS_LLM_BASE_URL`, `ATLAS_LLM_API_KEY` and `ATLAS_LLM_MODEL` are configured. The project brief explicitly calls for a working LLM-based agentic system.
2. **Embedding-model interpretation:** hashing TF-IDF is a deterministic local vector representation, but a grader may interpret “embedding model” as requiring a learned local or hosted embedding model.
3. **Recorded presentation:** the video cannot be completed in the repository.
4. **Grader sharing evidence:** verify the explicit collaborator invitation in GitHub settings rather than relying on public read access.

## Verification note

The fully expanded human-readable source tree passed the technical CI pipeline and the deployed workflows passed a public smoke test. These checks prove implementation behavior; they do not certify that Quantic will award a rubric score of 5.