"""Tools — the agent's hands. File ops, shell, web, code analysis, code execution, RAG, SQL.

Every tool returns a dict {ok: bool, result: str, meta?: dict}.
All tools pass through Guardrails before execution.
"""
from __future__ import annotations
import json
import os
import re
import subprocess
import tempfile
import textwrap
import time
import uuid
from pathlib import Path
from typing import Callable, Optional

import httpx

from .guardrails import Guardrails


# ---------- Default sandbox ----------
DEFAULT_SANDBOX = "/app/agent_workspace"
Path(DEFAULT_SANDBOX).mkdir(parents=True, exist_ok=True)


def _ok(result: str, meta: Optional[dict] = None) -> dict:
    return {"ok": True, "result": result, "meta": meta or {}}


def _err(msg: str, meta: Optional[dict] = None) -> dict:
    return {"ok": False, "result": msg, "meta": meta or {}}


# =====================================================
# FILE OPERATIONS
# =====================================================
def tool_save_file(caminho: str, conteudo: str, sandbox: str = DEFAULT_SANDBOX) -> dict:
    """Salva texto em um arquivo dentro do sandbox."""
    target = caminho if os.path.isabs(caminho) else os.path.join(sandbox, caminho)
    ok, reason = Guardrails.validate_path(target, sandbox)
    if not ok:
        return _err(reason)
    try:
        Path(target).parent.mkdir(parents=True, exist_ok=True)
        Path(target).write_text(conteudo, encoding="utf-8")
        return _ok(f"Arquivo salvo: {target} ({len(conteudo)} bytes)")
    except Exception as e:
        return _err(f"Erro ao salvar: {e}")


def tool_read_file(caminho: str, sandbox: str = DEFAULT_SANDBOX, max_bytes: int = 200_000) -> dict:
    """Lê o conteúdo de um arquivo."""
    target = caminho if os.path.isabs(caminho) else os.path.join(sandbox, caminho)
    # Allow reading from outside sandbox for analysis (read-only)
    try:
        data = Path(target).read_text(encoding="utf-8", errors="replace")
        if len(data) > max_bytes:
            data = data[:max_bytes] + f"\n... [truncado em {max_bytes} bytes]"
        return _ok(data, {"path": target, "size": len(data)})
    except Exception as e:
        return _err(f"Erro ao ler: {e}")


def tool_list_files(diretorio: str = ".", sandbox: str = DEFAULT_SANDBOX) -> dict:
    """Lista arquivos e pastas em um diretório."""
    target = diretorio if os.path.isabs(diretorio) else os.path.join(sandbox, diretorio)
    try:
        items = []
        for p in sorted(Path(target).iterdir()):
            items.append({
                "name": p.name,
                "type": "dir" if p.is_dir() else "file",
                "size": p.stat().st_size if p.is_file() else None,
            })
        return _ok(json.dumps(items, indent=2, ensure_ascii=False), {"count": len(items)})
    except Exception as e:
        return _err(f"Erro ao listar: {e}")


# =====================================================
# SHELL
# =====================================================
def tool_shell(comando: str, timeout: int = 60) -> dict:
    """Executa um comando shell. Bloqueia comandos perigosos (rm -rf /, mkfs, fork bombs, etc)."""
    ok, reason = Guardrails.validate_shell(comando)
    if not ok:
        return _err(reason)
    try:
        r = subprocess.run(
            comando, shell=True, capture_output=True, text=True, timeout=timeout,
            cwd=DEFAULT_SANDBOX,
        )
        out = (r.stdout or "") + (("\n[stderr]\n" + r.stderr) if r.stderr else "")
        return _ok(out[:50_000], {"exit_code": r.returncode})
    except subprocess.TimeoutExpired:
        return _err(f"Comando excedeu o timeout de {timeout}s")
    except Exception as e:
        return _err(f"Erro: {e}")


# =====================================================
# CODE EXECUTION (sandboxed Python)
# =====================================================
def tool_run_python(codigo: str, timeout: int = 30) -> dict:
    """Executa código Python isolado em subprocess. Retorna stdout/stderr."""
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, dir=DEFAULT_SANDBOX) as f:
        f.write(codigo)
        path = f.name
    try:
        r = subprocess.run(
            ["python3", path], capture_output=True, text=True, timeout=timeout, cwd=DEFAULT_SANDBOX,
        )
        out = (r.stdout or "") + (("\n[stderr]\n" + r.stderr) if r.stderr else "")
        return _ok(out[:50_000], {"exit_code": r.returncode})
    except subprocess.TimeoutExpired:
        return _err(f"Execução excedeu {timeout}s")
    except Exception as e:
        return _err(f"Erro: {e}")
    finally:
        try:
            os.unlink(path)
        except Exception:
            pass


# =====================================================
# CODE ANALYSIS (lint-light)
# =====================================================
def tool_analyze_code(codigo: str, linguagem: str = "python") -> dict:
    """Análise estática rápida: contagem de linhas, funções, classes, possíveis problemas."""
    lines = codigo.splitlines()
    info = {
        "linguagem": linguagem,
        "total_linhas": len(lines),
        "linhas_codigo": sum(1 for ln in lines if ln.strip() and not ln.strip().startswith(("#", "//", "/*", "*"))),
        "linhas_comentario": sum(1 for ln in lines if ln.strip().startswith(("#", "//", "/*", "*"))),
    }
    if linguagem.lower() in ("python", "py"):
        info["funcoes"] = len(re.findall(r"^\s*def\s+\w+", codigo, re.MULTILINE))
        info["classes"] = len(re.findall(r"^\s*class\s+\w+", codigo, re.MULTILINE))
        info["imports"] = len(re.findall(r"^\s*(import|from)\s+", codigo, re.MULTILINE))
        problems = []
        if "except:" in codigo or "except Exception:" in codigo:
            problems.append("Uso de 'except' genérico — capture exceções específicas.")
        if re.search(r"\bprint\(", codigo):
            problems.append("Uso de print() — considere logging em produção.")
        if "eval(" in codigo or "exec(" in codigo:
            problems.append("Uso de eval/exec é perigoso — evite com input do usuário.")
        info["alertas"] = problems
    elif linguagem.lower() in ("c", "cpp", "c++"):
        info["funcoes"] = len(re.findall(r"^\s*\w[\w\s\*]+\s+\w+\s*\([^;]*\)\s*\{", codigo, re.MULTILINE))
        info["mallocs"] = codigo.count("malloc(")
        info["frees"] = codigo.count("free(")
        problems = []
        if codigo.count("malloc(") != codigo.count("free("):
            problems.append("Possível memory leak: número de malloc != free.")
        if "gets(" in codigo:
            problems.append("gets() é inseguro — use fgets().")
        info["alertas"] = problems
    elif linguagem.lower() in ("java", "csharp", "c#", "go"):
        info["funcoes"] = len(re.findall(r"^\s*(public|private|protected|func|static)\s+", codigo, re.MULTILINE))
        info["classes"] = len(re.findall(r"^\s*(public\s+)?(class|struct|interface)\s+\w+", codigo, re.MULTILINE))
        info["alertas"] = []
    return _ok(json.dumps(info, indent=2, ensure_ascii=False), info)


# =====================================================
# WEB FETCH
# =====================================================
def tool_web_fetch(url: str, max_bytes: int = 100_000) -> dict:
    """Faz GET de uma URL e retorna o conteúdo (texto)."""
    if not url.startswith(("http://", "https://")):
        return _err("URL inválida — precisa começar com http:// ou https://")
    try:
        with httpx.Client(timeout=15, follow_redirects=True, headers={"User-Agent": "AjaxAgent/1.0"}) as c:
            r = c.get(url)
            text = r.text[:max_bytes]
            return _ok(text, {"status": r.status_code, "url": str(r.url)})
    except Exception as e:
        return _err(f"Erro web: {e}")


# =====================================================
# SQL (Supabase / Postgres) — SELECT only
# =====================================================
def tool_sql_query(query: str, db_url: Optional[str] = None) -> dict:
    """Executa SELECT no Postgres/Supabase. Bloqueia INSERT/UPDATE/DELETE/DROP."""
    ok, reason = Guardrails.validate_sql(query)
    if not ok:
        return _err(reason)
    db_url = db_url or os.environ.get("SUPABASE_DB_URL")
    if not db_url:
        return _err("SUPABASE_DB_URL não configurado.")
    try:
        from sqlalchemy import create_engine, text
        engine = create_engine(db_url, pool_pre_ping=True)
        with engine.connect() as conn:
            result = conn.execute(text(query))
            rows = result.fetchall()
            cols = list(result.keys())
            data = [dict(zip(cols, row)) for row in rows]
        return _ok(json.dumps(data, indent=2, default=str, ensure_ascii=False)[:50_000], {"rows": len(data)})
    except Exception as e:
        return _err(f"Erro SQL: {e}")


def tool_get_database_schema(db_url: Optional[str] = None) -> dict:
    """Retorna schema (tabelas e colunas) do banco — útil pro agente planejar SQL."""
    db_url = db_url or os.environ.get("SUPABASE_DB_URL")
    if not db_url:
        return _err("SUPABASE_DB_URL não configurado.")
    try:
        from sqlalchemy import create_engine, text
        engine = create_engine(db_url, pool_pre_ping=True)
        with engine.connect() as conn:
            rows = conn.execute(text("""
                SELECT table_name, column_name, data_type
                FROM information_schema.columns
                WHERE table_schema = 'public'
                ORDER BY table_name, ordinal_position
            """)).fetchall()
        schema: dict[str, list] = {}
        for t, c, dt in rows:
            schema.setdefault(t, []).append(f"{c} ({dt})")
        return _ok(json.dumps(schema, indent=2, ensure_ascii=False), {"tables": len(schema)})
    except Exception as e:
        return _err(f"Erro schema: {e}")


# =====================================================
# RAG SEARCH
# =====================================================
def make_tool_rag_search(rag_store, llm_router) -> Callable:
    def tool_rag_search(consulta: str, colecao: str = "programacao", top_k: int = 4) -> dict:
        """Busca semântica na base de conhecimento (RAG)."""
        try:
            emb = llm_router.embed([consulta])[0]
            results = rag_store.search(emb, collection=colecao, top_k=top_k)
            if not results:
                return _ok("Nenhum trecho encontrado na base de conhecimento.")
            out = []
            for i, r in enumerate(results, 1):
                meta = r.get("metadata", {})
                title = meta.get("titulo") or meta.get("title") or r["id"][:8]
                out.append(f"[{i}] ({title}) score={r['score']:.3f}\n{r['content']}")
            return _ok("\n\n".join(out), {"count": len(results)})
        except Exception as e:
            return _err(f"Erro RAG: {e}")
    return tool_rag_search


# =====================================================
# REGISTRY
# =====================================================
class ToolRegistry:
    """Registry of tools, exposing OpenAI-compatible schemas + dispatchers."""

    def __init__(self):
        self._tools: dict[str, dict] = {}

    def register(self, name: str, func: Callable, description: str, parameters: dict):
        self._tools[name] = {
            "func": func,
            "schema": {
                "type": "function",
                "function": {
                    "name": name,
                    "description": description,
                    "parameters": parameters,
                },
            },
        }

    def names(self) -> list[str]:
        return list(self._tools.keys())

    def schemas(self) -> list[dict]:
        return [t["schema"] for t in self._tools.values()]

    def dispatch(self, name: str, arguments: dict) -> dict:
        if name not in self._tools:
            return _err(f"Ferramenta '{name}' não existe.")
        try:
            return self._tools[name]["func"](**arguments)
        except TypeError as e:
            return _err(f"Argumentos inválidos: {e}")
        except Exception as e:
            return _err(f"Erro na ferramenta {name}: {e}")


def get_default_tools(rag_store=None, llm_router=None) -> ToolRegistry:
    """Constrói registry com todas as ferramentas padrão."""
    reg = ToolRegistry()
    reg.register(
        "salvar_arquivo", tool_save_file,
        "Salva texto em um arquivo dentro do workspace do agente. Use para gerar código, configs, docs.",
        {
            "type": "object",
            "properties": {
                "caminho": {"type": "string", "description": "Caminho relativo ou absoluto do arquivo"},
                "conteudo": {"type": "string", "description": "Conteúdo a ser escrito"},
            },
            "required": ["caminho", "conteudo"],
        },
    )
    reg.register(
        "ler_arquivo", tool_read_file,
        "Lê um arquivo do disco para análise.",
        {
            "type": "object",
            "properties": {"caminho": {"type": "string"}},
            "required": ["caminho"],
        },
    )
    reg.register(
        "listar_arquivos", tool_list_files,
        "Lista arquivos de um diretório.",
        {
            "type": "object",
            "properties": {"diretorio": {"type": "string", "description": "Diretório a listar (padrão '.')"}},
            "required": [],
        },
    )
    reg.register(
        "executar_shell", tool_shell,
        "Executa um comando shell sandboxado. Bloqueia comandos perigosos.",
        {
            "type": "object",
            "properties": {
                "comando": {"type": "string"},
                "timeout": {"type": "integer", "description": "Timeout em segundos (padrão 60)"},
            },
            "required": ["comando"],
        },
    )
    reg.register(
        "executar_python", tool_run_python,
        "Executa código Python em sandbox. Use para testar trechos, calcular, processar dados.",
        {
            "type": "object",
            "properties": {
                "codigo": {"type": "string", "description": "Código Python completo a executar"},
                "timeout": {"type": "integer"},
            },
            "required": ["codigo"],
        },
    )
    reg.register(
        "analisar_codigo", tool_analyze_code,
        "Análise estática de código. Suporta Python, C, C++, Java, C#, Go.",
        {
            "type": "object",
            "properties": {
                "codigo": {"type": "string"},
                "linguagem": {"type": "string", "enum": ["python", "c", "cpp", "java", "csharp", "go"]},
            },
            "required": ["codigo", "linguagem"],
        },
    )
    reg.register(
        "buscar_web", tool_web_fetch,
        "Busca conteúdo de uma URL pública.",
        {
            "type": "object",
            "properties": {"url": {"type": "string"}},
            "required": ["url"],
        },
    )
    reg.register(
        "consultar_banco", tool_sql_query,
        "Executa SELECT no banco Supabase/Postgres. INSERT/UPDATE/DELETE bloqueados.",
        {
            "type": "object",
            "properties": {"query": {"type": "string", "description": "Consulta SQL SELECT"}},
            "required": ["query"],
        },
    )
    reg.register(
        "obter_schema_banco", tool_get_database_schema,
        "Retorna schema (tabelas+colunas) do banco. SEMPRE use antes de inventar SQL.",
        {"type": "object", "properties": {}, "required": []},
    )
    if rag_store and llm_router:
        reg.register(
            "consultar_rag", make_tool_rag_search(rag_store, llm_router),
            "Busca na base de conhecimento de programação (Python, Java, C, C++, C#, Go). "
            "Use SEMPRE que a pergunta envolver dúvida técnica de programação.",
            {
                "type": "object",
                "properties": {
                    "consulta": {"type": "string"},
                    "colecao": {"type": "string", "description": "Coleção (padrão 'programacao')"},
                    "top_k": {"type": "integer"},
                },
                "required": ["consulta"],
            },
        )
    return reg
