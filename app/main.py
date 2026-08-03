from __future__ import annotations

import os
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from agent.orchestrator import AtlasOrchestrator
from mcp_client.client import MCPGateway, MCPGatewayError
from rag.index import get_index


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.index = get_index().ensure()
    gateway = MCPGateway()
    try:
        app.state.mcp = await gateway.discover()
    except MCPGatewayError as exc:
        app.state.mcp = {"status": "unavailable", "transport": gateway.transport, "error": str(exc), "tools": []}
    yield


app = FastAPI(
    title="Atlas HR Agent",
    version="2.0.0",
    description="A synthetic agentic HR assistant with persistent policy RAG and genuine MCP tool calls.",
    lifespan=lifespan,
)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    confirm_action: bool = False


class ChatResponse(BaseModel):
    answer: str
    citations: list[dict[str, Any]]
    supporting_snippets: list[str]
    trace: list[dict[str, Any]]
    status: str
    requires_confirmation: bool
    confidence: str
    mcp: dict[str, Any]


@app.get("/health")
async def health(deep: bool = Query(False)) -> dict[str, Any]:
    mcp_status = getattr(app.state, "mcp", {"status": "unknown", "tools": []})
    if deep:
        gateway = MCPGateway()
        try:
            mcp_status = await gateway.discover()
            app.state.mcp = mcp_status
        except MCPGatewayError as exc:
            mcp_status = {"status": "unavailable", "transport": gateway.transport, "error": str(exc), "tools": []}
    index_status = get_index().stats()
    return {
        "status": "ok" if index_status.get("status") == "ready" else "degraded",
        "service": "atlas-hr-agent",
        "version": app.version,
        "mode": "agentic-rag-mcp",
        "mcp": mcp_status,
        "rag_index": index_status,
        "llm_provider": "openai-compatible" if os.getenv("ATLAS_LLM_API_KEY") else "deterministic",
        "synthetic_data_only": True,
    }


@app.get("/api/tools")
async def tools() -> dict[str, Any]:
    gateway = MCPGateway()
    try:
        return await gateway.discover()
    except MCPGatewayError as exc:
        return {"status": "unavailable", "transport": gateway.transport, "error": str(exc), "tools": []}


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> dict[str, Any]:
    orchestrator = AtlasOrchestrator()
    return (await orchestrator.handle(request.message, request.confirm_action)).as_dict()


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
    body { margin: 0; background: #080d1d; color: #edf1fb; min-height: 100vh; }
    main { max-width: 1080px; margin: 0 auto; padding: 34px 18px 64px; }
    .hero { display: grid; gap: 8px; margin-bottom: 22px; }
    h1 { margin: 0; font-size: clamp(2rem, 5vw, 3.4rem); }
    .subtitle { color: #a8b3cf; line-height: 1.55; max-width: 800px; }
    .badge { display: inline-flex; width: fit-content; padding: 6px 10px; border: 1px solid #44517a; border-radius: 999px; color: #c3cff9; background: #121a33; font-size: .84rem; }
    .panel { background: #11182c; border: 1px solid #293454; border-radius: 16px; padding: 18px; box-shadow: 0 18px 55px rgba(0,0,0,.28); }
    textarea { width: 100%; min-height: 112px; resize: vertical; border-radius: 12px; border: 1px solid #3a466a; background: #0b1121; color: #fff; padding: 14px; font: inherit; }
    button { border: 0; border-radius: 10px; padding: 11px 16px; background: #7c8cff; color: #071023; font-weight: 800; cursor: pointer; }
    button.secondary { background: #263252; color: #e8ecf5; }
    .actions, .examples { display: flex; flex-wrap: wrap; gap: 9px; margin-top: 12px; }
    .example { font-size: .86rem; padding: 8px 10px; background: #1a2441; color: #cbd4ee; }
    #output { margin-top: 18px; display: none; }
    .answer { white-space: pre-wrap; line-height: 1.6; }
    .meta { color: #9eabc9; font-size: .9rem; margin-top: 14px; }
    .citation, .trace-item { background: #0c1326; border-left: 3px solid #7c8cff; padding: 10px 12px; margin-top: 10px; border-radius: 8px; overflow-wrap: anywhere; }
    .trace-item { border-left-color: #58c4a3; font-family: ui-monospace, SFMono-Regular, Consolas, monospace; font-size: .82rem; }
    details { margin-top: 14px; }
    summary { cursor: pointer; color: #c8d2f2; font-weight: 700; }
    .footer { color: #7f8baa; margin-top: 18px; font-size: .85rem; }
  </style>
</head>
<body>
<main>
  <section class="hero">
    <span class="badge">Quantic AI Engineering Project · MCP + Persistent RAG</span>
    <h1>Atlas HR Agent</h1>
    <p class="subtitle">A fictional HR assistant that discovers and calls MCP tools, retrieves policy evidence from a persistent SQLite vector index, cites sources, and requires confirmation before mock actions.</p>
  </section>
  <section class="panel">
    <strong>Ask Atlas</strong>
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
      <details><summary>Tool-call trace</summary><div id="trace"></div></details>
    </div>
  </section>
  <div class="footer">All people, records, policies and actions are fictional. Mock email and ticket tools never contact a production system.</div>
</main>
<script>
  const message = document.getElementById('message');
  const output = document.getElementById('output');
  const answer = document.getElementById('answer');
  const meta = document.getElementById('meta');
  const citations = document.getElementById('citations');
  const trace = document.getElementById('trace');
  const confirmButton = document.getElementById('confirm');

  async function submit(confirmAction=false) {
    const value = message.value.trim(); if (!value) return;
    answer.textContent = 'Working…'; citations.innerHTML = ''; trace.innerHTML = '';
    output.style.display = 'block'; confirmButton.style.display = 'none';
    try {
      const response = await fetch('/chat', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({message:value, confirm_action:confirmAction})});
      const data = await response.json();
      answer.textContent = data.answer || JSON.stringify(data);
      meta.textContent = `Status: ${data.status} · Confidence: ${data.confidence} · MCP: ${data.mcp?.status || 'unknown'} (${data.mcp?.transport || 'n/a'})`;
      for (const item of (data.citations || [])) {
        const div = document.createElement('div'); div.className = 'citation';
        div.innerHTML = `<strong>${item.document_id}: ${item.title}</strong><br>${item.section}<br><span>${item.snippet}</span><br><small>${item.source_path || ''} · score ${item.score ?? ''}</small>`;
        citations.appendChild(div);
      }
      for (const item of (data.trace || [])) {
        const div = document.createElement('div'); div.className = 'trace-item'; div.textContent = JSON.stringify(item, null, 2); trace.appendChild(div);
      }
      if (data.requires_confirmation) confirmButton.style.display = 'inline-block';
    } catch (error) { answer.textContent = `Request failed: ${error}`; }
  }
  document.getElementById('send').addEventListener('click', () => submit(false));
  confirmButton.addEventListener('click', () => submit(true));
  document.querySelectorAll('[data-q]').forEach(button => button.addEventListener('click', () => {message.value = button.dataset.q; message.focus();}));
</script>
</body>
</html>"""
