# Deployed Application

## Public URLs

- Application: https://atlas-hr-agent.onrender.com/
- Health: https://atlas-hr-agent.onrender.com/health
- Deep health and MCP rediscovery: https://atlas-hr-agent.onrender.com/health?deep=true
- OpenAPI documentation: https://atlas-hr-agent.onrender.com/docs
- MCP tool registry: https://atlas-hr-agent.onrender.com/api/tools

## Verified live release

The deployed release is version `2.1.0`. It uses genuine MCP over stdio, a configured OpenAI-compatible LLM and learned semantic embeddings in the persistent SQLite RAG index.

### Active LLM verification

GitHub Actions run `30877051735` independently tested the public Render service and proved:

- application status `ok` and mode `agentic-rag-mcp-llm`;
- a structured configured OpenAI-compatible provider;
- completed grounded LLM refinement with provider and model recorded in the trace;
- genuine MCP stdio connectivity to the `Atlas HR Tools` server;
- discovery of all eight MCP tools;
- the international remote-work workflow with the expected MCP sequence and `POL-RW-*` citations;
- the PTO confirmation gate and confirmed no-send mock email;
- prompt-injection refusal before MCP or LLM access.

Evidence artifact:

- Name: `atlas-deployed-v21-llm-evidence`
- Artifact ID: `8879953426`

### Learned semantic RAG verification

GitHub Actions run `30877645852` independently tested the public Render service after the embedding upgrade and proved:

- `semantic_embeddings: true`;
- embedding provider `openrouter`;
- a learned embedding model rather than the local hashing fallback;
- no embedding error recorded in health metadata;
- a ready SQLite RAG index containing 14 documents, 126 chunks and 34.5 estimated pages;
- a semantic multi-policy question returning both `POL-RW-*` and `POL-SEC-*` evidence;
- completed LLM refinement on the grounded response;
- preserved remote-work, PTO, action-confirmation and prompt-injection controls.

Evidence artifact:

- Name: `atlas-deployed-semantic-rag-evidence`
- Artifact ID: `8880135790`
- Digest: `sha256:68599bedf405c576b0a08accf9f7b7dc4862edab778b8d30a88f59e48ba46b24`

The reproducible public checks are retained in `.github/workflows/live-smoke.yml`.

## Deployment architecture

The Render Blueprint deploys `main` as one Python web service. FastAPI, the agent orchestrator, the official MCP stdio client/server, the synthetic JSON records and the local SQLite vector index run within the service. Render is configured with `autoDeployTrigger: checksPass`, so new commits deploy only after GitHub Actions succeeds.

At startup, the RAG index uses the configured OpenAI-compatible embeddings endpoint. The service stores learned dense vectors in SQLite and uses cosine retrieval with lexical signals. A deterministic local hashing representation remains available as a tested fallback for CI or provider outages; health metadata makes the active path and any fallback error visible.

The LLM is applied after deterministic MCP/RAG orchestration. It receives the controlled draft and citation metadata, but it does not select tools, approve actions, bypass safeguards or invent evidence. If refinement fails, Atlas returns the controlled draft and records the fallback in the trace.

The health response reports:

- application status, release version and operating mode;
- genuine MCP transport and discovered tool names;
- RAG index document, chunk and page counts;
- active embedding provider, model, dimensions and semantic/fallback status;
- configured LLM provider, model and endpoint host;
- synthetic-data-only status.

## Free-tier cold start

The free instance may spin down after inactivity. The first request can take approximately 50 seconds or more. On a new instance, Atlas rebuilds the SQLite retrieval index under `/tmp`, obtains the policy embeddings and performs an MCP discovery check. Warm requests are substantially faster. Transient `429`, `502`, `503` or `504` conditions are retried by the relevant provider and deployment checks. A failed new deployment does not replace the last healthy Render instance.

## Storage and actions

The vector index and mock-action log are ephemeral local files. They contain only synthetic information. The email and ticket tools never contact external systems; they create fictional local records only after explicit confirmation.
