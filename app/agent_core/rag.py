"""RAG Store — Supabase pgvector with graceful local fallback (SQLite + cosine search)."""
from __future__ import annotations
import json
import logging
import os
import sqlite3
import threading
import uuid
from pathlib import Path
from typing import Optional

logger = logging.getLogger("ajax.rag")


class RAGStore:
    """Vector store that prefers Supabase pgvector but falls back to local SQLite + cosine."""

    def __init__(
        self,
        supabase_url: Optional[str] = None,
        supabase_key: Optional[str] = None,
        database_url: Optional[str] = None,
        local_db_path: str = "/app/agent_core/data/rag.db",
        embedding_dim: int = 384,
        min_score_threshold: float = 0.3,  # Filtra resultados com score muito baixo
    ):
        self.supabase_url = supabase_url or os.environ.get("SUPABASE_URL")
        self.supabase_key = supabase_key or os.environ.get("SUPABASE_KEY")
        self.database_url = database_url or os.environ.get("SUPABASE_DB_URL")
        self.embedding_dim = embedding_dim
        self.min_score_threshold = min_score_threshold
        self.backend = "local"
        self.engine = None

        logger.info(f"[RAGStore] Inicializando... dim={embedding_dim} min_score={min_score_threshold}")

        # Try Supabase pgvector via direct DB connection
        if self.database_url:
            try:
                from sqlalchemy import create_engine, text
                self.engine = create_engine(self.database_url, pool_pre_ping=True)
                with self.engine.connect() as conn:
                    conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
                    conn.execute(text(f"""
                        CREATE TABLE IF NOT EXISTS ajax_rag_documents (
                            id UUID PRIMARY KEY,
                            collection TEXT NOT NULL,
                            content TEXT NOT NULL,
                            metadata JSONB DEFAULT '{{}}',
                            embedding vector({embedding_dim})
                        )
                    """))
                    conn.execute(text(
                        "CREATE INDEX IF NOT EXISTS ajax_rag_collection_idx ON ajax_rag_documents(collection)"
                    ))
                    conn.commit()
                self.backend = "supabase"
                logger.info("[RAGStore] Backend: Supabase pgvector")
            except Exception as e:
                logger.warning(f"[RAGStore] Supabase indisponível, usando fallback local: {e}")
                self.engine = None
        else:
            logger.info("[RAGStore] SUPABASE_DB_URL não configurado, usando SQLite local")

        # Local fallback
        Path(local_db_path).parent.mkdir(parents=True, exist_ok=True)
        self.local_db_path = local_db_path
        self._lock = threading.Lock()
        self._init_local()

    def _init_local(self):
        with self._lock, sqlite3.connect(self.local_db_path) as c:
            c.execute("""
                CREATE TABLE IF NOT EXISTS rag_docs (
                    id TEXT PRIMARY KEY,
                    collection TEXT,
                    content TEXT,
                    metadata TEXT,
                    embedding TEXT
                )
            """)
            c.execute("CREATE INDEX IF NOT EXISTS rag_collection_idx ON rag_docs(collection)")
        logger.info(f"[RAGStore] SQLite local pronto: {self.local_db_path}")

    def add(self, content: str, embedding: list[float], collection: str = "default", metadata: Optional[dict] = None) -> str:
        doc_id = str(uuid.uuid4())
        meta = metadata or {}
        content_preview = content[:80].replace('\n', ' ')
        logger.debug(f"[RAGStore.add] collection={collection} preview='{content_preview}...'")
        
        if self.backend == "supabase" and self.engine is not None:
            try:
                from sqlalchemy import text
                with self.engine.connect() as conn:
                    emb_str = "[" + ",".join(str(float(x)) for x in embedding) + "]"
                    conn.execute(
                        text("INSERT INTO ajax_rag_documents(id, collection, content, metadata, embedding) "
                             "VALUES(:id, :col, :content, CAST(:meta AS JSONB), CAST(:emb AS vector))"),
                        {"id": doc_id, "col": collection, "content": content,
                         "meta": json.dumps(meta), "emb": emb_str},
                    )
                    conn.commit()
                logger.info(f"[RAGStore.add] Documento inserido no Supabase: {doc_id[:8]}...")
                return doc_id
            except Exception as e:
                logger.warning(f"[RAGStore.add] insert supabase falhou, fallback local: {e}")
        # local
        with self._lock, sqlite3.connect(self.local_db_path) as c:
            c.execute(
                "INSERT INTO rag_docs VALUES(?,?,?,?,?)",
                (doc_id, collection, content, json.dumps(meta), json.dumps(embedding)),
            )
        logger.info(f"[RAGStore.add] Documento inserido no SQLite: {doc_id[:8]}...")
        return doc_id

    def search(self, embedding: list[float], collection: Optional[str] = None, top_k: int = 5) -> list[dict]:
        logger.info(f"[RAGStore.search] collection={collection} top_k={top_k}")
        
        if self.backend == "supabase" and self.engine is not None:
            try:
                from sqlalchemy import text
                emb_str = "[" + ",".join(str(float(x)) for x in embedding) + "]"
                with self.engine.connect() as conn:
                    where = "WHERE collection=:col" if collection else ""
                    params = {"emb": emb_str, "k": top_k}
                    if collection:
                        params["col"] = collection
                    rows = conn.execute(
                        text(f"""
                            SELECT id, collection, content, metadata,
                                   1 - (embedding <=> CAST(:emb AS vector)) AS score
                            FROM ajax_rag_documents
                            {where}
                            ORDER BY embedding <=> CAST(:emb AS vector)
                            LIMIT :k
                        """),
                        params,
                    ).fetchall()
                    results = [
                        {"id": str(r[0]), "collection": r[1], "content": r[2],
                         "metadata": r[3] if isinstance(r[3], dict) else json.loads(r[3] or "{}"),
                         "score": float(r[4])}
                        for r in rows
                    ]
                    # Filtra por score mínimo
                    filtered = [r for r in results if r["score"] >= self.min_score_threshold]
                    logger.info(f"[RAGStore.search] Supabase: {len(results)} resultados, {len(filtered)} após filtro (score>={self.min_score_threshold})")
                    return filtered
            except Exception as e:
                logger.warning(f"[RAGStore.search] search supabase falhou, fallback local: {e}")

        # Local cosine search
        with self._lock, sqlite3.connect(self.local_db_path) as c:
            if collection:
                rows = c.execute("SELECT id,collection,content,metadata,embedding FROM rag_docs WHERE collection=?", (collection,)).fetchall()
            else:
                rows = c.execute("SELECT id,collection,content,metadata,embedding FROM rag_docs").fetchall()
        
        scored = []
        for r in rows:
            emb = json.loads(r[4])
            score = self._cosine(embedding, emb)
            scored.append({
                "id": r[0], "collection": r[1], "content": r[2],
                "metadata": json.loads(r[3] or "{}"), "score": score,
            })
        scored.sort(key=lambda x: x["score"], reverse=True)
        
        # Filtra por score mínimo
        filtered = [r for r in scored[:top_k] if r["score"] >= self.min_score_threshold]
        logger.info(f"[RAGStore.search] SQLite: {len(scored)} docs, top_k={top_k}, {len(filtered)} após filtro (score>={self.min_score_threshold})")
        
        # Log dos scores para debug
        for i, r in enumerate(filtered[:3], 1):
            preview = r["content"][:60].replace('\n', ' ')
            logger.debug(f"[RAGStore.search]   [{i}] score={r['score']:.3f} '{preview}...'")
        
        return filtered

    @staticmethod
    def _cosine(a: list[float], b: list[float]) -> float:
        if not a or not b:
            return 0.0
        n = min(len(a), len(b))
        dot = sum(a[i] * b[i] for i in range(n))
        na = sum(x * x for x in a[:n]) ** 0.5 or 1.0
        nb = sum(x * x for x in b[:n]) ** 0.5 or 1.0
        return dot / (na * nb)

    def list_collections(self) -> list[dict]:
        if self.backend == "supabase" and self.engine is not None:
            try:
                from sqlalchemy import text
                with self.engine.connect() as conn:
                    rows = conn.execute(text(
                        "SELECT collection, COUNT(*) FROM ajax_rag_documents GROUP BY collection"
                    )).fetchall()
                return [{"name": r[0], "count": int(r[1])} for r in rows]
            except Exception:
                pass
        with self._lock, sqlite3.connect(self.local_db_path) as c:
            rows = c.execute("SELECT collection, COUNT(*) FROM rag_docs GROUP BY collection").fetchall()
            return [{"name": r[0], "count": int(r[1])} for r in rows]

    def clear_collection(self, collection: str):
        logger.info(f"[RAGStore.clear_collection] Limpando collection='{collection}'")
        if self.backend == "supabase" and self.engine is not None:
            try:
                from sqlalchemy import text
                with self.engine.connect() as conn:
                    conn.execute(text("DELETE FROM ajax_rag_documents WHERE collection=:c"), {"c": collection})
                    conn.commit()
            except Exception as e:
                logger.warning(f"[RAGStore.clear_collection] Erro no Supabase: {e}")
        with self._lock, sqlite3.connect(self.local_db_path) as c:
            c.execute("DELETE FROM rag_docs WHERE collection=?", (collection,))
        logger.info(f"[RAGStore.clear_collection] Collection '{collection}' limpa")

