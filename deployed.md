# Deployed Application

## Public URLs

- Application: https://atlas-hr-agent.onrender.com/
- Health: https://atlas-hr-agent.onrender.com/health
- OpenAPI documentation: https://atlas-hr-agent.onrender.com/docs
- Tool registry: https://atlas-hr-agent.onrender.com/api/tools

## Verification status

Verified live on 3 August 2026.

The Render service is deployed from the `main` branch using the repository-root `render.yaml` Blueprint.

Observed health response:

```json
{
  "status": "ok",
  "service": "atlas-hr-agent",
  "version": "1.0.0",
  "policy_documents": 7,
  "synthetic_employee_records": 3,
  "registered_tools": 8,
  "mode": "deterministic-demonstration"
}
```

The root browser interface loaded successfully, Render reported the deployment as live, `/health` returned status `ok`, and `/docs` exposed the FastAPI OpenAPI interface.

## Hosting note

The service uses Render's free instance plan. A sleeping instance may take approximately 50 seconds or more to respond to the first request after inactivity.

## Scope boundary

This deployment verifies the working baseline. It currently provides deterministic policy retrieval, structured synthetic employee lookups, controlled HR workflows, citations, escalation and confirmation before mock actions. Formal MCP transport, a larger multi-format corpus, persistent vector storage and extended evaluation remain future increments.
