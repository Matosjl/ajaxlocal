"""Ajax Super-Agent — FastAPI server with SSE streaming."""
from __future__ import annotations
import asyncio
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from fastapi import APIRouter, FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from starlette.middleware.cors import CORSMiddleware

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

# Add parent to path so we can import agent_core
sys.path.insert(0, str(ROOT_DIR.parent))

from agent_core import (  # noqa: E402
    AjaxAgent, LLMRouter, Memory, Observer, RAGStore, get_default_tools,
)

# ---------------- Setup ----------------
OPENROUTER_KEY = os.environ.get("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.environ.get("OPENROUTER_MODEL", "openrouter/auto")
SUPABASE_DB_URL = os.environ.get("SUPABASE_DB_URL", "")

# Singletons
memory = Memory()
observer = Observer()
rag = RAGStore(database_url=SUPABASE_DB_URL or None)

def make_router(provider: str = "openrouter", model: str | None = None) -> LLMRouter:
    if provider == "ollama":
        return LLMRouter(provider="ollama", model=model or os.environ.get("OLLAMA_MODEL", "llama3.1"),
                         ollama_url=os.environ.get("OLLAMA_URL", "http://localhost:11434"))
    return LLMRouter(provider="openrouter", model=model or OPENROUTER_MODEL, openrouter_key=OPENROUTER_KEY)

def make_agent(provider: str = "openrouter", model: str | None = None) -> AjaxAgent:
    llm = make_router(provider, model)
    tools = get_default_tools(rag, llm)
    return AjaxAgent(llm=llm, memory=memory, observer=observer, rag=rag, tools=tools)

app = FastAPI(title="Ajax Super-Agent")
api = APIRouter(prefix="/api")


# ---------------- Models ----------------
class SessionCreate(BaseModel):
    title: str = Field(default="Nova conversa")
    provider: str = Field(default="openrouter")
    model: str | None = None


class SessionUpdate(BaseModel):
    title: str | None = None
    provider: str | None = None
    model: str | None = None


class ChatRequest(BaseModel):
    session_id: str
    message: str
    provider: str = "openrouter"
    model: str | None = None


class ToolExecuteRequest(BaseModel):
    name: str
    arguments: dict = {}


class RAGIngestRequest(BaseModel):
    items: list[dict]  # [{content, metadata, collection}]
    collection: str = "programacao"


class RAGSearchRequest(BaseModel):
    query: str
    collection: str = "programacao"
    top_k: int = 5


# ---------------- Routes ----------------
@api.get("/")
def root():
    return {"name": "Ajax Super-Agent", "status": "ok",
            "providers": ["openrouter", "ollama"],
            "rag_backend": rag.backend,
            "default_model": OPENROUTER_MODEL}


@api.get("/health")
def health():
    return {
        "ok": True,
        "rag_backend": rag.backend,
        "openrouter_configured": bool(OPENROUTER_KEY),
        "supabase_db_configured": bool(SUPABASE_DB_URL),
    }


# ---- Sessions ----
@api.post("/sessions")
def create_session(body: SessionCreate):
    s = memory.create_session(body.title, body.provider, body.model or OPENROUTER_MODEL)
    return s


@api.get("/sessions")
def list_sessions():
    return memory.list_sessions()


@api.get("/sessions/{sid}")
def get_session(sid: str):
    s = memory.get_session(sid)
    if not s:
        raise HTTPException(404, "session not found")
    return s


@api.patch("/sessions/{sid}")
def update_session(sid: str, body: SessionUpdate):
    fields = {k: v for k, v in body.model_dump().items() if v is not None}
    if fields:
        memory.update_session(sid, **fields)
    return memory.get_session(sid)


@api.delete("/sessions/{sid}")
def delete_session(sid: str):
    memory.delete_session(sid)
    return {"ok": True}


@api.get("/sessions/{sid}/messages")
def get_messages(sid: str):
    return memory.get_messages(sid)


# ---- Chat (SSE streaming) ----
@api.post("/chat/stream")
async def chat_stream(body: ChatRequest):
    if not memory.get_session(body.session_id):
        raise HTTPException(404, "session not found")

    agent = make_agent(body.provider, body.model)

    async def event_stream():
        loop = asyncio.get_event_loop()
        # Run blocking generator in thread, push events through queue
        queue: asyncio.Queue = asyncio.Queue()

        def producer():
            try:
                for ev in agent.run_stream(body.session_id, body.message):
                    asyncio.run_coroutine_threadsafe(queue.put(ev), loop)
            except Exception as e:
                asyncio.run_coroutine_threadsafe(
                    queue.put({"type": "error", "message": str(e)}), loop)
            finally:
                asyncio.run_coroutine_threadsafe(queue.put(None), loop)

        loop.run_in_executor(None, producer)

        while True:
            ev = await queue.get()
            if ev is None:
                break
            yield f"data: {json.dumps(ev, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@api.post("/chat")
async def chat_sync(body: ChatRequest):
    """Non-streaming version (returns all events + final)."""
    if not memory.get_session(body.session_id):
        raise HTTPException(404, "session not found")
    agent = make_agent(body.provider, body.model)
    result = await asyncio.get_event_loop().run_in_executor(
        None, agent.run, body.session_id, body.message)
    return result


# ---- Tools ----
@api.get("/tools")
def list_tools():
    llm = make_router("openrouter")
    reg = get_default_tools(rag, llm)
    return [s["function"] for s in reg.schemas()]


@api.post("/tools/execute")
def execute_tool(body: ToolExecuteRequest):
    llm = make_router("openrouter")
    reg = get_default_tools(rag, llm)
    return reg.dispatch(body.name, body.arguments)


# ---- RAG ----
@api.get("/rag/collections")
def rag_collections():
    return rag.list_collections()


@api.post("/rag/search")
def rag_search(body: RAGSearchRequest):
    llm = make_router("openrouter")
    emb = llm.embed([body.query])[0]
    return rag.search(emb, collection=body.collection, top_k=body.top_k)


@api.post("/rag/ingest")
def rag_ingest(body: RAGIngestRequest):
    llm = make_router("openrouter")
    contents = [it["content"] for it in body.items]
    embs = llm.embed(contents)
    ids = []
    for it, emb in zip(body.items, embs):
        ids.append(rag.add(
            it["content"], emb,
            collection=it.get("collection", body.collection),
            metadata=it.get("metadata", {}),
        ))
    return {"inserted": len(ids), "backend": rag.backend}


@api.delete("/rag/collections/{name}")
def rag_clear(name: str):
    rag.clear_collection(name)
    return {"ok": True}


# ---- Observability ----
@api.get("/logs")
def get_logs(session_id: str | None = None, limit: int = 100):
    return observer.list_events(session_id=session_id, limit=limit)


@api.get("/stats")
def get_stats(session_id: str | None = None):
    return observer.stats(session_id=session_id)


# ---- Mount ----
app.include_router(api)
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
