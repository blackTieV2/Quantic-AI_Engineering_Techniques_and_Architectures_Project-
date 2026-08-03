# Deployed Application

## Public URLs

- Application: https://atlas-hr-agent.onrender.com/
- Health: https://atlas-hr-agent.onrender.com/health
- Deep health and MCP rediscovery: https://atlas-hr-agent.onrender.com/health?deep=true
- OpenAPI documentation: https://atlas-hr-agent.onrender.com/docs
- MCP tool registry: https://atlas-hr-agent.onrender.com/api/tools

## Verified live release

The deployed score-5 release is version `2.0.0`. It was independently verified from a GitHub-hosted runner on 3 August 2026 in workflow run `30792651006`.

The deployed smoke test proved:

- application status `ok` and mode `agentic-rag-mcp`;
- genuine MCP stdio connectivity to the `Atlas HR Tools` server;
- discovery of all eight MCP tools;
- a ready persistent SQLite RAG index containing 14 documents, 126 chunks and 34.5 estimated pages;
- the international remote-work workflow with the expected three MCP tool calls and only `POL-RW-*` citations;
- the PTO workflow's confirmation gate;
- the confirmed `draft_hr_email` mock action with `sent: false` and a no-send disclaimer;
- prompt-injection refusal before MCP access.

Evidence artifact:

- Name: `atlas-deployed-v2-evidence`
- Artifact ID: `8847626586`
- Digest: `sha256:0d386d80c9a052a666a467a60c62aae584969e6b7a2f51f0529082ba46b04b55`

The reproducible check is retained in `.github/workflows/live-smoke.yml` and can be run manually from GitHub Actions.

## Deployment architecture

The Render Blueprint deploys `main` as one Python web service. FastAPI, the agent orchestrator, the official MCP stdio client/server, the synthetic JSON records and the local SQLite vector index run within the service. Render is configured with `autoDeployTrigger: checksPass`, so new commits deploy only after GitHub Actions passes.

The health response reports:

- application status and release version;
- genuine MCP transport and discovered tool names;
- RAG index document, chunk and page counts;
- embedding model and chunk configuration;
- deterministic or optional LLM provider mode.

## Free-tier cold start

The free instance may spin down after inactivity. The first request can take approximately 50 seconds or more. On a new instance, Atlas rebuilds the SQLite retrieval index under `/tmp` and performs an MCP discovery check. Warm requests are substantially faster. Transient `502`, `503` or `504` responses can occur while a free instance or a replacement deployment becomes ready; the live smoke test retries these conditions. A failed new deployment does not replace the last healthy Render instance.

## Storage and actions

The vector index and mock-action log are ephemeral local files. They contain only synthetic information. The email and ticket tools never contact external systems; they create fictional local records only after explicit confirmation.
