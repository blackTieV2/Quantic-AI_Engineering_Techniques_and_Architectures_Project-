from __future__ import annotations

import hashlib
import json
import math
import os
import re
import sqlite3
import tempfile
from collections import Counter
from pathlib import Path
from threading import Lock
from typing import Any

from rag.ingest import chunk_sections, load_policy_sections

ROOT = Path(__file__).resolve().parents[1]
POLICY_DIR = ROOT / "policies"
DEFAULT_INDEX_PATH = Path(tempfile.gettempdir()) / "atlas-rag" / "rag_index.sqlite3"
TOKEN_PATTERN = re.compile(r"[a-z0-9][a-z0-9-]{1,}")
STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "has", "have", "how", "i",
    "in", "is", "it", "of", "on", "or", "that", "the", "this", "to", "was", "what", "when", "with", "you",
}
_LOCK = Lock()


def index_path() -> Path:
    return Path(os.getenv("ATLAS_INDEX_PATH", str(DEFAULT_INDEX_PATH)))


def tokenize(text: str) -> list[str]:
    return [token for token in TOKEN_PATTERN.findall(text.lower()) if token not in STOP_WORDS]


def _bucket(token: str, dimensions: int) -> str:
    digest = hashlib.sha256(token.encode("utf-8")).digest()
    return str(int.from_bytes(digest[:4], "big") % dimensions)


def _vector(tokens: list[str], idf: dict[str, float], dimensions: int) -> dict[str, float]:
    counts = Counter(tokens)
    values: dict[str, float] = {}
    for token, count in counts.items():
        bucket = _bucket(token, dimensions)
        values[bucket] = values.get(bucket, 0.0) + (1.0 + math.log(count)) * idf.get(token, 1.0)
    norm = math.sqrt(sum(value * value for value in values.values())) or 1.0
    return {key: value / norm for key, value in values.items()}


def _cosine(left: dict[str, float], right: dict[str, float]) -> float:
    if len(left) > len(right):
        left, right = right, left
    return sum(value * right.get(key, 0.0) for key, value in left.items())


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
            document_frequency: Counter[str] = Counter()
            for tokens in tokenized:
                document_frequency.update(set(tokens))
            total = max(len(chunks), 1)
            idf = {
                token: math.log((total + 1) / (frequency + 1)) + 1.0
                for token, frequency in document_frequency.items()
            }
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
                        ("embedding_model", "atlas-hashing-tfidf-v1"),
                        ("dimensions", str(self.dimensions)),
                        ("idf", json.dumps(idf, sort_keys=True)),
                        ("chunk_words", str(chunk_words)),
                        ("overlap_words", str(overlap_words)),
                    ],
                )
                rows = []
                for chunk, tokens in zip(chunks, tokenized, strict=True):
                    rows.append(
                        (
                            chunk["chunk_id"],
                            chunk["document_id"],
                            chunk["title"],
                            chunk["section"],
                            chunk["source_path"],
                            chunk["content"],
                            json.dumps(_vector(tokens, idf, self.dimensions), sort_keys=True),
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
            idf = json.loads(metadata["idf"])
            dimensions = int(metadata["dimensions"])
            query_tokens = tokenize(query)
            query_vector = _vector(query_tokens, idf, dimensions)
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
                if not lexical_overlap:
                    continue
                vector = json.loads(row["vector_json"])
                score = _cosine(query_vector, vector)
                title_section = f"{row['title']} {row['section']}".lower()
                lexical_hits = sum(1 for token in lexical_overlap if token in title_section)
                phrase_bonus = 0.08 if query_lower in row["content"].lower() else 0.0
                score += lexical_hits * 0.035 + phrase_bonus
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
            "chunk_words": int(metadata.get("chunk_words", "0")),
            "overlap_words": int(metadata.get("overlap_words", "0")),
        }


_INDEX: RagIndex | None = None


def get_index() -> RagIndex:
    global _INDEX
    if _INDEX is None:
        _INDEX = RagIndex()
    return _INDEX
