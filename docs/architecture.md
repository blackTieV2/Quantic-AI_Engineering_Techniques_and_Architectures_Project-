# Architecture

```text
Browser / API client
        |
        v
FastAPI web service (`app/main.py`)
        |
        v
Request guardrails + explicit orchestrator (`agent/orchestrator.py`)
        |
        v
Official MCP client over stdio (`mcp_client/client.py`)
        |
        v
FastMCP server process (`mcp_server/server.py`)
        |
        +--> policy tools --> SQLite vector index (`rag/index.py`)
        |                       ^
        |                       |
        |          learned embeddings via OpenRouter
        |          deterministic hashing fallback
        |                       ^
        |                       |
        |               Markdown + HTML corpus
        |
        +--> record tools --> synthetic JSON datasets
        |
        +--> confirmed mock-action tools --> ephemeral JSONL action log
        |
        v
Controlled draft + citation metadata
        |
        v
Constrained OpenAI-compatible LLM refinement (`agent/llm.py`)
        |
        v
Answer + citations + MCP/LLM operational trace
```

## Trust boundaries

1. The request guardrail runs before any tool or model access.
2. The orchestrator discovers available tools from the MCP server for every request session.
3. Tool arguments are typed by MCP schemas and checked again by the implementation.
4. Tool results use a standard `ok/data/error` envelope and are checked before synthesis.
5. Write-like tools require `confirmed=true` and create only local fictional records.
6. Citations are created from index metadata: document ID, title, section, path, chunk ID, score and snippet.
7. The LLM receives only the controlled draft and retrieved citation evidence. It does not select tools, grant eligibility, authorise actions or bypass confirmation.
8. A provider failure returns the controlled draft and records a visible fallback event.
9. User-visible traces contain operational events, tool names, arguments, concise results and provider status—not hidden chain-of-thought.

## Transport choice

The deployed application uses the official MCP Python SDK over **stdio**. A fresh Python subprocess hosts the FastMCP server for each agent request. This keeps the free-tier deployment to one Render service while maintaining a real protocol boundary and separate server/client components. The `inprocess` transport exists for deterministic unit evaluation; CI separately proves genuine stdio discovery and calls.

## RAG design

The corpus contains 14 fictional policies in Markdown and HTML, totalling 34.5 estimated pages and roughly 10,000 words. The loader preserves document and heading metadata. The selected chunking configuration is heading-aware 120-word windows with 20-word overlap and stable chunk IDs.

In the public deployment, `rag/index.py` obtains learned embeddings from an OpenAI-compatible `/embeddings` endpoint, stores dense vectors and citation metadata in SQLite, and uses cosine similarity with bounded lexical signals. The active provider, model, vector dimensions and error/fallback status are exposed by `/health`.

For CI or provider outages, Atlas can build a deterministic 384-dimensional hashing TF-IDF index. That fallback is tested and is never represented as the active learned embedding path when it is not.

## LLM design

`agent/llm.py` calls a configured OpenAI-compatible `/chat/completions` endpoint after the orchestrator and MCP tools have produced a controlled draft. The grounding prompt includes:

- document ID;
- policy title;
- section;
- source path;
- chunk ID;
- retrieved snippet;
- the controlled decision, numerical values and action disclaimer.

Temperature is zero. The model is instructed to improve clarity without introducing facts, changing eligibility, selecting tools or approving actions. Successful and fallback outcomes are recorded as `llm_refinement` trace entries.

## Deployment verification

Public GitHub-hosted smoke tests independently verified:

- active LLM refinement in run `30877051735`;
- learned semantic embeddings and multi-policy retrieval in run `30877645852`;
- MCP stdio, eight tools, both required workflows, confirmation safety, citations and injection refusal.
