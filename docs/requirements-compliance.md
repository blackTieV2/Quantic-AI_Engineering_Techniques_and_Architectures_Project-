# Quantic Requirements Compliance Matrix

This matrix distinguishes verified technical controls from external submission actions. It is not an official grading determination.

| ID | Requirement | Implementation / evidence | Status |
|---|---|---|---|
| R1 | Build an agentic HR policy and operations system | Explicit single-agent orchestration with clarification, escalation, retrieval, MCP tools, LLM refinement and confirmation in `agent/` | Verified |
| R2 | RAG over 5–20 internal documents totalling approximately 30–120 pages | 14 fictional policies, approximately 10,000 words and 34.5 estimated pages, in Markdown and HTML | Verified |
| R3 | Parse and clean at least two source formats | Heading-aware Markdown and HTML loaders in `rag/ingest.py` | Verified |
| R4 | Chunking with a justified strategy | 120-word chunks with 20-word overlap; ablation compares 60/10, 120/20 and 220/30 | Verified |
| R5 | Embed chunks using a free/local learned embedding model or free-tier API | Learned OpenRouter embedding path in `rag/index.py`; public run `30877645852` verified semantic embeddings and provider/model metadata | Verified |
| R6 | Lightweight vector database and citation metadata | SQLite stores dense vectors, document ID, title, section, source path, chunk ID and snippets | Verified |
| R7 | Top-k RAG, filters, grounded citations and multi-document retrieval | Cosine retrieval, document-prefix filters, citation-ready results and a live-tested remote-work/security multi-policy query | Verified |
| R8 | Inject retrieved chunks and source metadata into an LLM context | `agent/llm.py` receives document ID, title, section, path, chunk ID and snippet; public run `30877051735` verified completed refinement | Verified |
| R9 | Two multi-step agentic workflows | International remote work and PTO plus confirmed mock email | Verified live |
| R10 | Visible operational trace without hidden chain-of-thought | Tool discovery, tools, arguments, concise outputs, citations, decisions and LLM-refinement status are returned | Verified |
| R11 | Graceful failures and confirmation before actions | Injection refusal, missing records, insufficient evidence, MCP/provider fallback and confirmation gates | Verified |
| R12 | Genuine MCP server with at least five tools | FastMCP server exposes eight tools; official client uses stdio | Verified protocol and live |
| R13 | Web chat, `/chat`, `/health` and two reproducible tasks | FastAPI UI and structured endpoints in `app/main.py` | Verified and deployed |
| R14 | Free-tier deployment and cold-start documentation | Render single-service Blueprint; SQLite index generated at startup; URLs and cold-start notes in `deployed.md` | Verified |
| R15 | CI/CD on push/PR, app startup and MCP call test | CI installs, compiles, builds index, runs pytest, starts FastAPI, calls MCP tools, evaluates and uploads artifacts | Verified |
| R16 | Deployment only after tests pass | `render.yaml` uses `autoDeployTrigger: checksPass` | Verified |
| R17 | Evaluation set of 20–30 tasks with answers or rubrics | 25 items include expected status, exact tool sequence, citation families and gold keywords | Verified as deterministic rubric |
| R18 | Groundedness, citation, tool, workflow, safety and latency metrics | Rule-based proxy metrics and warm p50/p95 plus retrieval ablation | Verified with methodology qualification |
| R19 | Design documentation, architecture, tool schemas and workflow sequences | `design-and-evaluation.md`, `docs/architecture.md` and demo script | Verified |
| R20 | AI tooling disclosure including what worked and what did not | `ai-tooling.md` | Verified |
| R21 | Share repository with `quantic-grader` | Student reports account added | External check: confirm invitation is visible or accepted in repository settings |
| R22 | 7–10 minute recorded demo with two tasks, camera/ID and explanation of tools/results/citations | Timed script exists in `docs/demo-script.md` | External student action required |

## Technical verification summary

### Active LLM

GitHub Actions run `30877051735` independently exercised the public Render service and verified:

- configured OpenAI-compatible provider;
- model identity in non-secret health/trace metadata;
- completed grounded `llm_refinement`;
- remote-work and PTO workflows;
- confirmation-gated no-send action;
- refusal before MCP or model access for the injection test.

### Learned semantic embeddings

GitHub Actions run `30877645852` independently exercised the public Render service and verified:

- `semantic_embeddings: true`;
- provider `openrouter` and a learned embedding model;
- no embedding error;
- 14 documents and 126 chunks;
- a semantic multi-policy query retrieving `POL-RW-*` and `POL-SEC-*` evidence;
- active LLM refinement and unchanged workflow safety.

Artifact: `atlas-deployed-semantic-rag-evidence`, ID `8880135790`, digest `sha256:68599bedf405c576b0a08accf9f7b7dc4862edab778b8d30a88f59e48ba46b24`.

### Deterministic regression evaluation

The 25-item regression suite reports 1.000 for groundedness proxy, citation-family accuracy, exact tool-sequence accuracy, workflow completion, clarification/escalation accuracy, action safety and status accuracy; mean keyword coverage is 0.940. These are rule-based regression proxies, not independent human or LLM-judge grades.

## Remaining submission actions

1. **Recorded presentation:** complete the 7–10 minute video using `docs/demo-script.md`.
2. **Grader sharing evidence:** verify `quantic-grader` appears as invited or accepted under **Settings → Collaborators**.
3. **Submission quality control:** check the final links, video permissions, sound, camera/ID visibility and repository accessibility before submitting.

## Verification note

The human-readable source tree, CI pipeline and public deployment have passed technical verification. These checks show that the implementation addresses the assignment requirements; they do not certify that Quantic will award a particular score.
