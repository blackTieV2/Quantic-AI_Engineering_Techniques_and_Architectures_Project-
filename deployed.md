# Deployed Application

## Public URLs

- Application: https://atlas-hr-agent.onrender.com/
- Health: https://atlas-hr-agent.onrender.com/health
- Deep health and MCP rediscovery: https://atlas-hr-agent.onrender.com/health?deep=true
- OpenAPI documentation: https://atlas-hr-agent.onrender.com/docs
- MCP tool registry: https://atlas-hr-agent.onrender.com/api/tools

## Deployment architecture

The Render Blueprint deploys `main` as one Python web service. FastAPI, the agent orchestrator, the official MCP stdio client/server, the synthetic JSON records and the local SQLite vector index run within the service. Render is configured with `autoDeployTrigger: checksPass`, so new commits deploy only after GitHub Actions passes.

The current score-5 release is version `2.0.0`. Its health response reports:

- application status;
- genuine MCP transport and discovered tool names;
- RAG index document, chunk and page counts;
- embedding model and chunk configuration;
- deterministic or optional LLM provider mode.

## Free-tier cold start

The free instance may spin down after inactivity. The first request can take approximately 50 seconds or more. On a new instance, Atlas rebuilds the SQLite retrieval index under `/tmp` and performs an MCP discovery check. Warm requests are substantially faster. A failed new deployment does not replace the last healthy Render instance.

## Storage and actions

The vector index and mock-action log are ephemeral local files. They contain only synthetic information. The email and ticket tools never contact external systems; they create fictional local records only after explicit confirmation.
