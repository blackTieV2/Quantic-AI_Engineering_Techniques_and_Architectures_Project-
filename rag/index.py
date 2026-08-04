from __future__ import annotations

import hashlib
import json
import math
import os
import re
import sqlite3
import tempfile
import time
from collections import Counter
from pathlib import Path
from threading import Lock
from typing import Any

import httpx

from rag.ingest import chunk_sections, load_policy_sections

ROOT = Path(__file__).resolve().parents[1]
POLICY_DIR = ROOT / "policies"
DEFAULT_INDEX_PATH = Path(tempfile.gettempdir()) / "atlas-rag" / "rag_index.sqlite3"
TOKEN_PATTERN = re.compile(r"[a-z0-9][a-z0-9-]{1,}")
STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "has", "have", "how", "i",
    "in", "is", "it", "of", "on", "or", "that", "the", "this", "to", "was", "what", "when", "with", "you",
}
HASH_MODEL = "atlas-hashing-tfidf-v1"
DEFAULT_REMOTE_MODEL = "nvidia/nemotron-3-embed-1b:free"
_LOCK = Lock()


def index_path() -> Path:
    return Path(os.getenv("ATLAS_INDEX_PATH", str(DEFAULT_INDEX_PATH)))


def tokenize(text: str) -> list[str]:
    return [token for token in TOKEN_PATTERN.findall(text.lower()) if token not in STOP_WORDS]


def _bucket(token: str, dimensions: int) -> str:
    digest = hashlib.sha256(token.encode("utf-8")).digest()
    return str(int.from_bytes(digest[:4], "big") % dimensions)


def _sparse_vector(tokens: list[str], idf: dict[str, float], dimensions: int) -> dict[str, float]:
    counts = Counter(tokens)
    values: dict[str, float] = {}
    for token, count in counts.items():
        bucket = _bucket(token, dimensions)
        values[bucket] = values.get(bucket, 0.0) + (1.0 + math.log(count)) * idf.get(token, 1.0)
    norm = math.sqrt(sum(value * value for value in values.values())) or 1.0
    return {key: value / norm for key, value in values.items()}


def _sparse_cosine(left: dict[str, float], right: dict[str, float]) -> float:
    if len(left) > len(right):
        left, right = right, left
    return sum(value * right.get(key, 0.0) for key, value in left.items())


def _dense_cosine(left: list[float], right: list[float]) -> float:
    if len(left) != len(right) or not left:
        return 0.0
    left_norm = math.sqrt(sum(value * value for value in left)) or 1.0
    right_norm = math.sqrt(sum(value * value for value in right)) or 1.0
    return sum(a * b for a, b in zip(left, right, strict=True)) / (left_norm * right_norm)


def _embedding_config() -> dict[str, str] | None:
    base_url = os.getenv("ATLAS_EMBEDDING_BASE_URL") or os.getenv("ATLAS_LLM_BASE_URL")
    api_key = os.getenv("ATLAS_EMBEDDING_API_KEY") or os.getenv("ATLAS_LLM_API_KEY")
    if not base_url or not api_key:
        return None
    return {
        "base_url": base_url.rstrip("/"),
        "api_key": api_key,
        "model": os.getenv("ATLAS_EMBEDDING_MODEL", DEFAULT_REMOTE_MODEL),
    }


def _requested_embedding_model() -> str:
    config = _embedding_config()
    return config["model"] if config else HASH_MODEL


def _remote_embeddings(texts: list[str], config: dict[str, str]) -> list[list[float]]:
    """Generate learned embeddings in bounded batches using an OpenAI-compatible endpoint."""
    if not texts:
        return []
    batch_size = max(1, min(int(os.getenv("ATLAS_EMBEDDING_BATCH_SIZE", "32")), 64))
    timeout = float(os.getenv("ATLAS_EMBEDDING_TIMEOUT_SECONDS", "120"))
    retries = max(0, int(os.getenv("ATLAS_EMBEDDING_MAX_RETRIES", "3")))
    vectors: list[list[float]] = []
    headers = {
        "Authorization": f"Bearer {config['api_key']}",
        "Content-Type": "application/json",
        "HTTP-Referer": os.getenv("ATLAS_PUBLIC_URL", "https://atlas-hr-agent.onrender.com"),
        "X-Title": "Atlas HR Agent - Quantic Project",
    }

    for offset in range(0, len(texts), batch_size):
        batch = texts[offset : offset + batch_size]
        last_error: Exception | None = None
        for attempt in range(retries + 1):
            try:
                with httpx.Client(timeout=timeout) as client:
                    response = client.post(
                        f"{config['base_url']}/embeddings",
                        headers=headers,
                        json={"model": config["model"], "input": batch, "encoding_format": "float"},
                    )
                if response.status_code == 429 or response.status_code >= 500:
                    response.raise_for_status()
                if response.status_code >= 400:
                    raise RuntimeError(f"Embedding provider returned HTTP {response.status_code}: {response.text[:300]}")
                payload = response.json()
                items = sorted(payload.get("data", []), key=lambda item: int(item.get("index", 0)))
                current = [item.get("embedding") for item in items]
                if len(current) != len(batch) or any(not isinstance(vector, list) or not vector for vector in current):
                    raise RuntimeError("Embedding provider returned malformed vectors")
                vectors.extend([[float(value) for value in vector] for vector in current])
                last_error = None
                break
            except (httpx.HTTPError, RuntimeError, ValueError, TypeError, KeyError) as exc:
                last_error = exc
                if attempt >= retries:
                    break
                time.sleep(min(2**attempt, 8))
        if last_error is not None:
            raise RuntimeError(f"Embedding request failed after retries: {last_error}")
    return vectors


class RagIndex:
    def __init__(self, path: Path | None = None, *, dimensions: int = 384) -> None:
        self.path = path or index_path()
        self.dimensions = dimensions

    def build(self, *, chunk_words: int = 120, overlap_words: int = 20, force: bool = False) -> dict[str, Any]:
        with _LOCK:
            if self.path.exists() and not force:
                return self.stats()
            self.path.parent.mkdir(parents=True, exist_ok=True)
            if self.path.exists():
                self.path.unlink()

            sections = load_policy_sections(POLICY_DIR)
            chunks = chunk_sections(sections, chunk_words=chunk_words, overlap_words=overlap_words)
            tokenized = [tokenize(str(chunk["content"])) for chunk in chunks]
            requested_model = _requested_embedding_model()
            embedding_config = _embedding_config()
            actual_model = HASH_MODEL
            provider = "local-hashing-fallback" if embedding_config else "local-hashing"
            vector_format = "sparse"
            embedding_error = ""
            idf: dict[str, float] = {}
            vectors: list[list[float] | dict[str, float]] = []
            dimensions = self.dimensions

            if embedding_config:
                try:
                    embedding_inputs = [
                        f"{chunk['title']}\n{chunk['section']}\n{chunk['content']}" for chunk in chunks
                    ]
                    dense_vectors = _remote_embeddings(embedding_inputs, embedding_config)
                    dimensions = len(dense_vectors[0]) if dense_vectors else 0
                    if dimensions <= 0 or any(len(vector) != dimensions for vector in dense_vectors):
                        raise RuntimeError("Embedding vectors have inconsistent dimensions")
                    vectors = dense_vectors
                    actual_model = embedding_config["model"]
                    provider = "openrouter"
                    vector_format = "dense"
                except Exception as exc:
                    embedding_error = str(exc)[:500]

            if vector_format == "sparse":
                document_frequency: Counter[str] = Counter()
                for tokens in tokenized:
                    document_frequency.update(set(tokens))
                total = max(len(chunks), 1)
                idf = {
                    token: math.log((total + 1) / (frequency + 1)) + 1.0
                    for token, frequency in document_frequency.items()
                }
                vectors = [_sparse_vector(tokens, idf, self.dimensions) for tokens in tokenized]
                dimensions = self.dimensions

            with sqlite3.connect(self.path) as connection:
                connection.executescript(
                    """
                    PRAGMA journal_mode=WAL;
                    CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
                    CREATE TABLE chunks (
                        chunk_id TEXT PRIMARY KEY,
                        document_id TEXT NOT NULL,
                        title TEXT NOT NULL,
                        section TEXT NOT NULL,
                        source_path TEXT NOT NULL,
                        content TEXT NOT NULL,
                        vector_json TEXT NOT NULL,
                        word_count INTEGER NOT NULL,
                        estimated_pages REAL NOT NULL
                    );
                    CREATE INDEX idx_chunks_document_id ON chunks(document_id);
                    """
                )
                connection.executemany(
                    "INSERT INTO metadata(key, value) VALUES (?, ?)",
                    [
                        ("embedding_model", actual_model),
                        ("requested_embedding_model", requested_model),
                        ("embedding_provider", provider),
                        ("embedding_error", embedding_error),
                        ("vector_format", vector_format),
                        ("dimensions", str(dimensions)),
                        ("idf", json.dumps(idf, sort_keys=True)),
                        ("chunk_words", str(chunk_words)),
                        ("overlap_words", str(overlap_words)),
                    ],
                )
                rows = []
                for chunk, vector in zip(chunks, vectors, strict=True):
                    rows.append(
                        (
                            chunk["chunk_id"],
                            chunk["document_id"],
                            chunk["title"],
                            chunk["section"],
                            chunk["source_path"],
                            chunk["content"],
                            json.dumps(vector, sort_keys=isinstance(vector, dict)),
                            chunk["word_count"],
                            chunk["estimated_pages"],
                        )
                    )
                connection.executemany(
                    """INSERT INTO chunks(
                        chunk_id, document_id, title, section, source_path, content,
                        vector_json, word_count, estimated_pages
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    rows,
                )
                connection.commit()
            return self.stats()

    def ensure(self) -> dict[str, Any]:
        if not self.path.exists():
            return self.build()
        try:
            with sqlite3.connect(self.path) as connection:
                metadata = self._metadata(connection)
            if metadata.get("requested_embedding_model") != _requested_embedding_model():
                return self.build(force=True)
        except (sqlite3.Error, KeyError):
            return self.build(force=True)
        return self.stats()

    def _metadata(self, connection: sqlite3.Connection) -> dict[str, str]:
        return {row[0]: row[1] for row in connection.execute("SELECT key, value FROM metadata")}

    def search(
        self, query: str, *, limit: int = 4, document_prefix: str | None = None
    ) -> list[dict[str, Any]]:
        self.ensure()
        with sqlite3.connect(self.path) as connection:
            connection.row_factory = sqlite3.Row
            metadata = self._metadata(connection)
            vector_format = metadata.get("vector_format", "sparse")
            query_tokens = tokenize(query)
            query_vector: list[float] | dict[str, float] | None
            if vector_format == "dense":
                config = _embedding_config()
                if not config:
                    query_vector = None
                else:
                    try:
                        query_vector = _remote_embeddings([query], config)[0]
                    except Exception:
                        query_vector = None
            else:
                idf = json.loads(metadata.get("idf", "{}"))
                dimensions = int(metadata.get("dimensions", str(self.dimensions)))
                query_vector = _sparse_vector(query_tokens, idf, dimensions)

            sql = "SELECT * FROM chunks"
            params: tuple[Any, ...] = ()
            if document_prefix:
                sql += " WHERE document_id LIKE ?"
                params = (f"{document_prefix}%",)
            candidates = []
            query_lower = query.lower()
            for row in connection.execute(sql, params):
                lexical_tokens = set(tokenize(f"{row['title']} {row['section']} {row['content']}"))
                lexical_overlap = set(query_tokens) & lexical_tokens
                if vector_format == "sparse" and not lexical_overlap:
                    continue
                stored_vector = json.loads(row["vector_json"])
                if vector_format == "dense" and isinstance(query_vector, list) and isinstance(stored_vector, list):
                    score = _dense_cosine(query_vector, [float(value) for value in stored_vector])
                elif vector_format == "sparse" and isinstance(query_vector, dict) and isinstance(stored_vector, dict):
                    score = _sparse_cosine(query_vector, stored_vector)
                else:
                    score = 0.0

                title_section = f"{row['title']} {row['section']}".lower()
                lexical_hits = sum(1 for token in lexical_overlap if token in title_section)
                lexical_ratio = len(lexical_overlap) / max(len(set(query_tokens)), 1)
                phrase_bonus = 0.08 if query_lower in row["content"].lower() else 0.0
                score += lexical_ratio * 0.08 + lexical_hits * 0.025 + phrase_bonus
                if score <= 0:
                    continue
                content = row["content"]
                candidates.append(
                    {
                        "chunk_id": row["chunk_id"],
                        "document_id": row["document_id"],
                        "title": row["title"],
                        "section": row["section"],
                        "source_path": row["source_path"],
                        "snippet": content[:650] + ("…" if len(content) > 650 else ""),
                        "score": round(score, 4),
                    }
                )
            candidates.sort(key=lambda item: item["score"], reverse=True)
            return candidates[: max(1, min(limit, 10))]

    def get_section(self, document_id: str, section: str | None = None) -> list[dict[str, Any]]:
        self.ensure()
        with sqlite3.connect(self.path) as connection:
            connection.row_factory = sqlite3.Row
            if section:
                rows = connection.execute(
                    """SELECT * FROM chunks WHERE document_id = ? AND lower(section) LIKE ?
                       ORDER BY chunk_id""",
                    (document_id.upper(), f"%{section.lower()}%"),
                ).fetchall()
            else:
                rows = connection.execute(
                    "SELECT * FROM chunks WHERE document_id = ? ORDER BY chunk_id",
                    (document_id.upper(),),
                ).fetchall()
            return [
                {
                    "chunk_id": row["chunk_id"],
                    "document_id": row["document_id"],
                    "title": row["title"],
                    "section": row["section"],
                    "source_path": row["source_path"],
                    "snippet": row["content"],
                }
                for row in rows
            ]

    def stats(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"status": "missing", "path": str(self.path)}
        with sqlite3.connect(self.path) as connection:
            chunk_count = connection.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
            document_count = connection.execute("SELECT COUNT(DISTINCT document_id) FROM chunks").fetchone()[0]
            estimated_pages = connection.execute(
                "SELECT SUM(pages) FROM (SELECT document_id, MAX(estimated_pages) AS pages FROM chunks GROUP BY document_id)"
            ).fetchone()[0]
            metadata = self._metadata(connection)
        return {
            "status": "ready",
            "path": str(self.path),
            "documents": document_count,
            "chunks": chunk_count,
            "estimated_pages": round(float(estimated_pages or 0), 1),
            "embedding_model": metadata.get("embedding_model", "unknown"),
            "requested_embedding_model": metadata.get("requested_embedding_model", "unknown"),
            "embedding_provider": metadata.get("embedding_provider", "unknown"),
            "semantic_embeddings": metadata.get("vector_format") == "dense",
            "embedding_error": metadata.get("embedding_error") or None,
            "dimensions": int(metadata.get("dimensions", "0")),
            "chunk_words": int(metadata.get("chunk_words", "0")),
            "overlap_words": int(metadata.get("overlap_words", "0")),
        }


_INDEX: RagIndex | None = None


def get_index() -> RagIndex:
    global _INDEX
    if _INDEX is None:
        _INDEX = RagIndex()
    return _INDEX
