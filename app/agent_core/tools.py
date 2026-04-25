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

# ---------- Obsidian vault ----------
DEFAULT_OBSIDIAN_VAULT = r"C:\Users\sealo\Desktop\COntinue\SUPERajax"


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
    """Executa um comando shell. Bloqueia comandos perigosos."""
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
# CODE EXECUTION
# =====================================================
def tool_run_python(codigo: str, timeout: int = 30) -> dict:
    """Executa código Python isolado em subprocess."""
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
# CODE ANALYSIS
# =====================================================
def tool_analyze_code(codigo: str, linguagem: str = "python") -> dict:
    """Análise estática rápida de código."""
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
            problems.append("Uso de 'except' genérico.")
        if re.search(r"\bprint\(", codigo):
            problems.append("Uso de print() — considere logging.")
        if "eval(" in codigo or "exec(" in codigo:
            problems.append("Uso de eval/exec é perigoso.")
        info["alertas"] = problems
    elif linguagem.lower() in ("c", "cpp", "c++"):
        info["funcoes"] = len(re.findall(r"^\s*\w[\w\s\*]+\s+\w+\s*\([^;]*\)\s*\{", codigo, re.MULTILINE))
        info["mallocs"] = codigo.count("malloc(")
        info["frees"] = codigo.count("free(")
        problems = []
        if codigo.count("malloc(") != codigo.count("free("):
            problems.append("Possível memory leak.")
        if "gets(" in codigo:
            problems.append("gets() é inseguro.")
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
    """Faz GET de uma URL e retorna o conteúdo."""
    if not url.startswith(("http://", "https://")):
        return _err("URL inválida.")
    try:
        with httpx.Client(timeout=15, follow_redirects=True, headers={"User-Agent": "AjaxAgent/1.0"}) as c:
            r = c.get(url)
            return _ok(r.text[:max_bytes], {"status": r.status_code})
    except Exception as e:
        return _err(f"Erro web: {e}")


# =====================================================
# SQL
# =====================================================
def tool_sql_query(query: str, db_url: Optional[str] = None) -> dict:
    """Executa SELECT no Postgres/Supabase."""
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
    """Retorna schema do banco."""
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
# OBSIDIAN INTEGRATION
# =====================================================
def tool_read_obsidian(nota: str, vault: str = DEFAULT_OBSIDIAN_VAULT) -> dict:
    """Lê uma nota do vault Obsidian."""
    target = os.path.join(vault, nota if nota.endswith(".md") else nota + ".md")
    try:
        data = Path(target).read_text(encoding="utf-8", errors="replace")
        return _ok(data, {"path": target, "size": len(data)})
    except Exception as e:
        return _err(f"Erro ao ler nota Obsidian: {e}")


def tool_write_obsidian(nota: str, conteudo: str, vault: str = DEFAULT_OBSIDIAN_VAULT) -> dict:
    """Escreve ou atualiza uma nota no vault Obsidian."""
    target = os.path.join(vault, nota if nota.endswith(".md") else nota + ".md")
    try:
        Path(target).parent.mkdir(parents=True, exist_ok=True)
        Path(target).write_text(conteudo, encoding="utf-8")
        return _ok(f"Nota salva: {target} ({len(conteudo)} bytes)", {"path": target})
    except Exception as e:
        return _err(f"Erro ao salvar nota: {e}")


def tool_append_obsidian(nota: str, conteudo: str, vault: str = DEFAULT_OBSIDIAN_VAULT) -> dict:
    """Adiciona log com timestamp ao final de uma nota."""
    target = os.path.join(vault, nota if nota.endswith(".md") else nota + ".md")
    try:
        Path(target).parent.mkdir(parents=True, exist_ok=True)
        ts = time.strftime("%Y-%m-%d %H:%M:%S")
        entry = f"\n\n## {ts}\n\n{conteudo}\n"
        with open(target, "a", encoding="utf-8") as f:
            f.write(entry)
        return _ok(f"Log adicionado: {target}", {"path": target})
    except Exception as e:
        return _err(f"Erro ao adicionar log: {e}")


def tool_list_obsidian(pasta: str = "", vault: str = DEFAULT_OBSIDIAN_VAULT) -> dict:
    """Lista notas do vault Obsidian."""
    target = os.path.join(vault, pasta) if pasta else vault
    try:
        items = []
        for p in sorted(Path(target).rglob("*.md")):
            rel = p.relative_to(vault)
            items.append({"name": str(rel), "type": "file", "size": p.stat().st_size})
        return _ok(json.dumps(items[:100], indent=2, ensure_ascii=False), {"count": len(items)})
    except Exception as e:
        return _err(f"Erro ao listar vault: {e}")


def tool_map_project_to_obsidian(vault: str = DEFAULT_OBSIDIAN_VAULT) -> dict:
    """Mapeia o código do Ajax para o Obsidian em formato de grafo/cérebro."""
    try:
        import ast
        project_dir = Path(__file__).parent.parent  # app/
        notes_created = []
        
        brain_note = os.path.join(vault, "01_BRAIN", "Cerebro Ajax.md")
        os.makedirs(os.path.dirname(brain_note), exist_ok=True)
        
        modules = []
        for py_file in sorted(project_dir.rglob("*.py")):
            if "__pycache__" in str(py_file):
                continue
            rel_path = py_file.relative_to(project_dir)
            module_name = str(rel_path).replace(os.sep, ".").replace(".py", "")
            modules.append({"name": module_name, "path": str(rel_path), "file": py_file})
        
        for mod in modules:
            try:
                content = mod["file"].read_text(encoding="utf-8", errors="replace")
                classes = []
                functions = []
                imports = []
                try:
                    tree = ast.parse(content)
                    for node in ast.walk(tree):
                        if isinstance(node, ast.ClassDef):
                            classes.append(node.name)
                        elif isinstance(node, ast.FunctionDef):
                            functions.append(node.name)
                        elif isinstance(node, ast.Import):
                            for alias in node.names:
                                imports.append(alias.name)
                        elif isinstance(node, ast.ImportFrom):
                            imports.append(node.module or "")
                except:
                    pass
                
                safe_name = mod["name"].replace(".", " - ")
                note_path = os.path.join(vault, "02_PROJECTS", f"{safe_name}.md")
                os.makedirs(os.path.dirname(note_path), exist_ok=True)
                
                links = []
                for imp in imports:
                    if "agent_core" in str(imp) or "backend" in str(imp) or "frontend" in str(imp):
                        links.append(f"[[{str(imp).replace('.', ' - ')}]]")
                
                note_content = f"""# {safe_name}

**Arquivo:** `{mod['path']}`

## Classes
{chr(10).join(f"- [[{c}]]" for c in classes) if classes else "- Nenhuma"}

## Funções
{chr(10).join(f"- `{f}()`" for f in functions[:20]) if functions else "- Nenhuma"}
{'\\n*... e mais funções*' if len(functions) > 20 else ''}

## Dependências
{chr(10).join(f"- {l}" for l in set(links)) if links else "- Nenhuma interna"}

## Código
```python
{content[:1500]}{'\\n... (truncado)' if len(content) > 1500 else ''}
```

---
*Mapeado pelo Ajax*
"""
                Path(note_path).write_text(note_content, encoding="utf-8")
                notes_created.append(safe_name)
            except Exception as e:
                notes_created.append(f"ERRO: {mod['name']}")
        
        brain_content = f"""# Cérebro Ajax

```mermaid
graph TD
    A[CLI] --> B[Agent Core]
    B --> C[LLM Router]
    B --> D[Memory]
    B --> E[Tools]
    B --> F[RAG]
    B --> G[Planner]
    C --> H[Ollama]
    C --> I[OpenRouter]
    E --> J[Obsidian]
    E --> K[File System]
    E --> L[Database]
```

## Módulos ({len(notes_created)})

{chr(10).join(f"- [[{n}]]" for n in notes_created[:50])}

## Tags
#ajax #agente-ia #sistema

---
*Gerado: {time.strftime("%Y-%m-%d %H:%M:%S")}*
"""
        Path(brain_note).write_text(brain_content, encoding="utf-8")
        
        return _ok(
            f"Grafo criado! {len(notes_created)} notas\nCérebro: {brain_note}",
            {"notes_created": len(notes_created)}
        )
    except Exception as e:
        return _err(f"Erro ao mapear: {e}")


# =====================================================
# SCAFFOLDING
# =====================================================
SCAFFOLD_TEMPLATES = {
    "react": {
        "files": {
            "package.json": '{"name": "{{name}}", "version": "0.1.0", "private": true, "dependencies": {"react": "^19.0.0", "react-dom": "^19.0.0", "react-scripts": "5.0.1"}, "scripts": {"start": "react-scripts start", "build": "react-scripts build"}}',
            "public/index.html": '<!DOCTYPE html><html lang="pt-BR"><head><meta charset="utf-8" /><title>{{name}}</title></head><body><div id="root"></div></body></html>',
            "src/index.js": "import React from 'react'; import ReactDOM from 'react-dom/client'; import App from './App'; const root = ReactDOM.createRoot(document.getElementById('root')); root.render(<App />);",
            "src/App.js": "export default function App() { return <div><h1>{{name}}</h1></div>; }",
        },
        "run_cmd": "npm install && npm start",
    },
    "nextjs": {
        "files": {
            "package.json": '{"name": "{{name}}", "version": "0.1.0", "private": true, "scripts": {"dev": "next dev"}, "dependencies": {"next": "^15.0.0", "react": "^19.0.0"}}',
            "app/page.tsx": "export default function Home() { return <main><h1>{{name}}</h1></main>; }",
        },
        "run_cmd": "npm install && npm run dev",
    },
    "fastapi": {
        "files": {
            "main.py": "from fastapi import FastAPI\napp = FastAPI(title='{{name}}')\n@app.get('/')\ndef read_root():\n    return {'message': 'Bem-vindo'}",
            "requirements.txt": "fastapi==0.110.1\nuvicorn==0.25.0\n",
        },
        "run_cmd": "pip install -r requirements.txt && uvicorn main:app --reload",
    },
}


def tool_scaffold_project(tipo: str, nome: str, sandbox: str = DEFAULT_SANDBOX) -> dict:
    """Gera estrutura de projeto completo."""
    tipo = tipo.lower().strip()
    if tipo not in SCAFFOLD_TEMPLATES:
        return _err(f"Tipo '{tipo}' não suportado. Use: {', '.join(SCAFFOLD_TEMPLATES.keys())}")
    template = SCAFFOLD_TEMPLATES[tipo]
    project_dir = os.path.join(sandbox, nome)
    ok, reason = Guardrails.validate_path(project_dir, sandbox)
    if not ok:
        return _err(reason)
    try:
        Path(project_dir).mkdir(parents=True, exist_ok=True)
        created = []
        for rel_path, content_template in template["files"].items():
            file_path = os.path.join(project_dir, rel_path)
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            content = content_template.replace("{{name}}", nome)
            Path(file_path).write_text(content, encoding="utf-8")
            created.append(rel_path)
        return _ok(
            f"Projeto '{nome}' ({tipo}) criado!\nArquivos: {', '.join(created)}",
            {"project": nome, "tipo": tipo, "arquivos": created}
        )
    except Exception as e:
        return _err(f"Erro ao scaffold: {e}")


def tool_create_component(nome: str, tipo: str = "react", props: str = "", sandbox: str = DEFAULT_SANDBOX) -> dict:
    """Gera um componente React, React Native ou Flutter."""
    tipo = tipo.lower().strip()
    safe_name = "".join(c for c in nome if c.isalnum() or c in "_-").strip("-_")
    if not safe_name:
        return _err("Nome inválido.")
    file_name = safe_name
    if tipo == "react":
        ext = "jsx"
        code = f"import React from 'react';\n\nexport default function {safe_name}({{ {props} }}) {{\n  return (\n    <div><h2>{safe_name}</h2></div>\n  );\n}}\n"
    elif tipo == "react-native":
        ext = "js"
        code = f"import React from 'react';\nimport {{ View, Text }} from 'react-native';\n\nexport default function {safe_name}() {{\n  return <View><Text>{safe_name}</Text></View>;\n}}\n"
    elif tipo == "flutter":
        ext = "dart"
        file_name = safe_name.lower()
        code = f"import 'package:flutter/material.dart';\n\nclass {safe_name} extends StatelessWidget {{\n  @override\n  Widget build(BuildContext context) {{\n    return Text('{safe_name}');\n  }}\n}}\n"
    else:
        return _err(f"Tipo '{tipo}' não suportado.")
    
    out_path = os.path.join(sandbox, f"{file_name}.{ext}")
    try:
        Path(out_path).write_text(code, encoding="utf-8")
        return _ok(f"Componente salvo: {out_path}", {"path": out_path})
    except Exception as e:
        return _err(f"Erro: {e}")


# =====================================================
# RAG SEARCH
# =====================================================
def make_tool_rag_search(rag_store, llm_router) -> Callable:
    def tool_rag_search(consulta: str, colecao: str = "programacao", top_k: int = 4) -> dict:
        """Busca semântica na base de conhecimento."""
        try:
            emb = llm_router.embed([consulta])[0]
            results = rag_store.search(emb, collection=colecao, top_k=top_k)
            if not results:
                return _ok("Nenhum trecho encontrado.")
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
    """Registry of tools."""

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
    """Constrói registry com todas as ferramentas."""
    reg = ToolRegistry()
    reg.register("salvar_arquivo", tool_save_file, "Salva arquivo no workspace.",
        {"type": "object", "properties": {"caminho": {"type": "string"}, "conteudo": {"type": "string"}}, "required": ["caminho", "conteudo"]})
    reg.register("ler_arquivo", tool_read_file, "Lê arquivo do disco.",
        {"type": "object", "properties": {"caminho": {"type": "string"}}, "required": ["caminho"]})
    reg.register("listar_arquivos", tool_list_files, "Lista arquivos.",
        {"type": "object", "properties": {"diretorio": {"type": "string"}}, "required": []})
    reg.register("executar_shell", tool_shell, "Executa comando shell.",
        {"type": "object", "properties": {"comando": {"type": "string"}, "timeout": {"type": "integer"}}, "required": ["comando"]})
    reg.register("executar_python", tool_run_python, "Executa Python sandbox.",
        {"type": "object", "properties": {"codigo": {"type": "string"}, "timeout": {"type": "integer"}}, "required": ["codigo"]})
    reg.register("analisar_codigo", tool_analyze_code, "Análise estática.",
        {"type": "object", "properties": {"codigo": {"type": "string"}, "linguagem": {"type": "string"}}, "required": ["codigo", "linguagem"]})
    reg.register("buscar_web", tool_web_fetch, "Busca URL.",
        {"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"]})
    reg.register("consultar_banco", tool_sql_query, "SELECT no banco.",
        {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]})
    reg.register("obter_schema_banco", tool_get_database_schema, "Schema do banco.",
        {"type": "object", "properties": {}, "required": []})
    if rag_store and llm_router:
        reg.register("consultar_rag", make_tool_rag_search(rag_store, llm_router), "Busca RAG.",
            {"type": "object", "properties": {"consulta": {"type": "string"}}, "required": ["consulta"]})
    reg.register("scaffold_projeto", tool_scaffold_project, "Gera projeto.",
        {"type": "object", "properties": {"tipo": {"type": "string"}, "nome": {"type": "string"}}, "required": ["tipo", "nome"]})
    reg.register("criar_componente", tool_create_component, "Gera componente.",
        {"type": "object", "properties": {"nome": {"type": "string"}, "tipo": {"type": "string"}, "props": {"type": "string"}}, "required": ["nome"]})
    # Obsidian tools
    reg.register("ler_obsidian", tool_read_obsidian, "Lê nota do Obsidian.",
        {"type": "object", "properties": {"nota": {"type": "string"}}, "required": ["nota"]})
    reg.register("escrever_obsidian", tool_write_obsidian, "Escreve nota no Obsidian.",
        {"type": "object", "properties": {"nota": {"type": "string"}, "conteudo": {"type": "string"}}, "required": ["nota", "conteudo"]})
    reg.register("adicionar_log_obsidian", tool_append_obsidian, "Adiciona log no Obsidian.",
        {"type": "object", "properties": {"nota": {"type": "string"}, "conteudo": {"type": "string"}}, "required": ["nota", "conteudo"]})
    reg.register("listar_obsidian", tool_list_obsidian, "Lista notas do Obsidian.",
        {"type": "object", "properties": {"pasta": {"type": "string"}}, "required": []})
    reg.register("mapear_projeto_obsidian", tool_map_project_to_obsidian, "Mapeia código para grafo no Obsidian.",
        {"type": "object", "properties": {}, "required": []})
    return reg
