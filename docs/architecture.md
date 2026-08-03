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
        +--> optional answer provider (`agent/llm.py`)
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
        |                  Markdown + HTML corpus
        |
        +--> record tools --> synthetic JSON datasets
        |
        +--> confirmed mock-action tools --> ephemeral JSONL action log
```

## Trust boundaries

1. The request guardrail runs before any tool access.
2. The orchestrator discovers available tools from the MCP server for every request session.
3. Tool arguments are typed by MCP schemas and checked again by the implementation.
4. Tool results use a standard `ok/data/error` envelope and are checked before synthesis.
5. Write-like tools require `confirmed=true` and create only local fictional records.
6. Citations are created from index metadata: document ID, title, section, path, chunk ID and score.
7. User-visible traces contain operational events, tool names, arguments and concise results—not hidden chain-of-thought.

## Transport choice

The deployed application uses the official MCP Python SDK over **stdio**. A fresh Python subprocess hosts the FastMCP server for each agent request. This keeps the free-tier deployment to one Render service while maintaining a real protocol boundary and separate server/client components. The `inprocess` transport exists only for deterministic unit evaluation; CI separately proves genuine stdio discovery and tool calls.

## RAG design

The corpus contains 14 fictional policies in Markdown and HTML, totalling 34.5 declared pages and roughly 10,000 words. The loader preserves document and heading metadata. The index uses heading-aware chunks, 120 words with 20-word overlap, and a deterministic 384-dimensional hashing TF-IDF embedding. Vectors and metadata are stored in SQLite. The file is regenerated on a cold start under `/tmp`, which is compatible with Render's free service and avoids a paid database.
