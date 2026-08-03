# Atlas HR Agent

Atlas is a deployable, synthetic HR assistant created for the **Quantic AI Engineering Techniques and Architectures Project**. It demonstrates retrieval-grounded answers, citations, structured employee lookups, multi-step workflows, escalation, prompt-injection resistance and explicit confirmation before mock actions.

> All employees, records, policies and actions in this repository are fictional. The application does not send email, create real tickets or connect to a production HR system.

## Live capabilities

- FastAPI web application and responsive browser UI
- `POST /chat` policy and workflow endpoint
- `GET /health` deployment health endpoint
- `GET /api/tools` tool registry
- `GET /docs` OpenAPI interface
- citation-bearing policy retrieval
- synthetic employee, PTO, benefits and remote-work records
- international remote-work eligibility workflow
- PTO balance and mock manager-email workflow
- confirmation gate before mock actions
- sensitive-case escalation and prompt-injection guardrail
- automated tests and GitHub Actions CI
- Render Blueprint deployment through `render.yaml`

## Demonstration records

| Employee ID | Employment type | Service | PTO | Remote days used | Benefits |
|---|---:|---:|---:|---:|---|
| `E1001` | Full-time | 26 months | 14 days | 4 | Enrolled |
| `E1002` | Full-time | 4 months | 8 days | 0 | Eligible, not enrolled |
| `E1003` | Contractor | 18 months | 0 days | 12 | Not eligible |

## Example prompts

```text
Can E1001 work remotely overseas for 10 days?
How much PTO does E1001 have and draft an email for 5 days?
What is the benefits status for E1002?
I want legal advice about a harassment complaint.
```

## Local setup

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

macOS/Linux:

```bash
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000`.

## Tests

```bash
pytest -q
```

The test suite covers health, remote-work eligibility, PTO confirmation, sensitive-case escalation and prompt-injection handling.

## API example

```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Can E1001 work remotely overseas for 10 days?"}'
```

## Render deployment

The repository root contains `render.yaml`. In Render:

1. Select **New + → Blueprint**.
2. Connect this repository.
3. Select branch `main`.
4. Keep the Blueprint path as `render.yaml`.
5. Apply the Blueprint.
6. Verify `/`, `/health` and `/docs` on the resulting service URL.

The deployment does not require an LLM API key because the demonstration engine is deterministic and self-contained.

## Architecture

```text
Browser UI
   |
FastAPI routes (/chat, /health, /api/tools)
   |
Controlled request classifier and workflow engine
   |---------------------------|
Policy retrieval         Synthetic structured records
   |                           |
Citations, compliance checks, escalation and confirmation
```

The architecture deliberately keeps model-free deterministic behaviour available for reproducible marking. A future LLM adapter can be placed after retrieval and policy controls without changing the public API.

## Repository structure

```text
app/
  engine.py      policy retrieval, records and controlled workflows
  main.py        FastAPI routes and browser interface
tests/
  test_app.py    automated workflow tests
.github/workflows/ci.yml
render.yaml
requirements.txt
README.md
```

## Safety design

- no production employee data
- no irreversible external action
- confirmation required before mock write actions
- insufficient-evidence response instead of unsupported claims
- sensitive HR, legal and medical matters escalated
- prompt-injection patterns rejected
- citations returned with each policy-grounded answer

## Current scope boundary

This is a working deployable baseline. The next project increments are a formal MCP transport, a larger multi-format document corpus, persistent vector storage, an evaluation dashboard and optional LLM answer synthesis. Those should be added only after the deployed baseline is stable and green in CI.
