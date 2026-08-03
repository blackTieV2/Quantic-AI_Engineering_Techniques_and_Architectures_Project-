from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from app.engine import EMPLOYEES, POLICIES, TOOLS
from app.request_controls import controlled_respond

app = FastAPI(
    title="Atlas HR Agent",
    version="1.0.1",
    description="A synthetic, citation-grounded HR assistant built for the Quantic AI Engineering project.",
)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    confirm_action: bool = False


class ChatResponse(BaseModel):
    answer: str
    citations: list[dict]
    trace: list[str]
    status: str
    requires_confirmation: bool


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "service": "atlas-hr-agent",
        "version": app.version,
        "policy_documents": len(POLICIES),
        "synthetic_employee_records": len(EMPLOYEES),
        "registered_tools": len(TOOLS),
        "mode": "deterministic-demonstration",
    }


@app.get("/api/tools")
def tools() -> dict:
    return {
        "tools": [
            {
                "name": name,
                "execution": "local synthetic demonstration",
                "side_effects": name in {"draft_hr_email", "create_mock_hr_ticket"},
            }
            for name in TOOLS
        ]
    }


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> dict:
    return controlled_respond(request.message, request.confirm_action).as_dict()


@app.get("/", response_class=HTMLResponse)
def home() -> str:
    return """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Atlas HR Agent</title>
  <style>
    :root { color-scheme: dark; font-family: Inter, ui-sans-serif, system-ui, sans-serif; }
    * { box-sizing: border-box; }
    body { margin: 0; background: #0b1020; color: #e8ecf5; min-height: 100vh; }
    main { max-width: 980px; margin: 0 auto; padding: 36px 18px 64px; }
    .hero { display: grid; gap: 8px; margin-bottom: 22px; }
    h1 { margin: 0; font-size: clamp(2rem, 5vw, 3.5rem); }
    .subtitle { color: #a8b3cf; line-height: 1.55; max-width: 760px; }
    .badge { display: inline-flex; width: fit-content; padding: 6px 10px; border: 1px solid #44517a; border-radius: 999px; color: #b9c6f4; background: #121a33; font-size: .86rem; }
    .panel { background: #11182c; border: 1px solid #293454; border-radius: 16px; padding: 18px; box-shadow: 0 18px 55px rgba(0,0,0,.28); }
    textarea { width: 100%; min-height: 110px; resize: vertical; border-radius: 12px; border: 1px solid #3a466a; background: #0b1121; color: #fff; padding: 14px; font: inherit; }
    button { border: 0; border-radius: 10px; padding: 11px 16px; background: #7c8cff; color: #071023; font-weight: 800; cursor: pointer; }
    button.secondary { background: #263252; color: #e8ecf5; }
    .actions { display: flex; flex-wrap: wrap; gap: 10px; margin-top: 12px; }
    .examples { display: flex; flex-wrap: wrap; gap: 8px; margin: 14px 0 4px; }
    .example { font-size: .88rem; padding: 8px 10px; background: #1a2441; color: #cbd4ee; }
    #output { margin-top: 18px; display: none; }
    .answer { white-space: pre-wrap; line-height: 1.6; }
    .meta { color: #9eabc9; font-size: .9rem; margin-top: 14px; }
    .citation { background: #0c1326; border-left: 3px solid #7c8cff; padding: 10px 12px; margin-top: 10px; border-radius: 8px; }
    .citation strong { color: #dce3ff; }
    code { color: #bfcbff; }
    .footer { color: #7f8baa; margin-top: 18px; font-size: .85rem; }
  </style>
</head>
<body>
<main>
  <section class="hero">
    <span class="badge">Quantic AI Engineering Project</span>
    <h1>Atlas HR Agent</h1>
    <p class="subtitle">A synthetic HR assistant demonstrating policy retrieval, citations, structured employee lookups, controlled workflows, escalation, and confirmation before mock actions.</p>
  </section>
  <section class="panel">
    <label for="message"><strong>Ask Atlas</strong></label>
    <div class="examples">
      <button class="example secondary" data-q="Can E1001 work remotely overseas for 10 days?">Remote work</button>
      <button class="example secondary" data-q="How much PTO does E1001 have and draft an email for 5 days?">PTO workflow</button>
      <button class="example secondary" data-q="What is the benefits status for E1002?">Benefits</button>
      <button class="example secondary" data-q="I want legal advice about a harassment complaint">Sensitive case</button>
    </div>
    <textarea id="message" placeholder="Example: Can E1001 work remotely overseas for 10 days?"></textarea>
    <div class="actions">
      <button id="send">Send</button>
      <button id="confirm" class="secondary" style="display:none">Confirm mock action</button>
    </div>
    <div id="output">
      <h2>Response</h2>
      <div id="answer" class="answer"></div>
      <div id="meta" class="meta"></div>
      <div id="citations"></div>
    </div>
  </section>
  <div class="footer">All people, records, policies and actions in this demonstration are fictional. No email or ticket is sent.</div>
</main>
<script>
  const message = document.getElementById('message');
  const output = document.getElementById('output');
  const answer = document.getElementById('answer');
  const meta = document.getElementById('meta');
  const citations = document.getElementById('citations');
  const confirmButton = document.getElementById('confirm');

  async function submit(confirmAction=false) {
    const value = message.value.trim();
    if (!value) return;
    answer.textContent = 'Working…';
    citations.innerHTML = '';
    output.style.display = 'block';
    confirmButton.style.display = 'none';
    try {
      const response = await fetch('/chat', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({message: value, confirm_action: confirmAction})
      });
      const data = await response.json();
      answer.textContent = data.answer || JSON.stringify(data);
      meta.textContent = `Status: ${data.status} · Trace: ${(data.trace || []).join(' → ')}`;
      for (const item of (data.citations || [])) {
        const div = document.createElement('div');
        div.className = 'citation';
        div.innerHTML = `<strong>${item.document_id}: ${item.title}</strong><br>${item.section}<br><span>${item.snippet}</span>`;
        citations.appendChild(div);
      }
      if (data.requires_confirmation) confirmButton.style.display = 'inline-block';
    } catch (error) {
      answer.textContent = `Request failed: ${error}`;
    }
  }

  document.getElementById('send').addEventListener('click', () => submit(false));
  confirmButton.addEventListener('click', () => submit(true));
  document.querySelectorAll('[data-q]').forEach(button => button.addEventListener('click', () => {
    message.value = button.dataset.q;
    message.focus();
  }));
</script>
</body>
</html>"""
