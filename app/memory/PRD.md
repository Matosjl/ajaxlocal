# Ajax Super-Agent — PRD

## Problem Statement (original, user language preserved)
Transformar o agente de IA local Ajax num super-agente capaz de:
- Automações de PC (ferramentas de arquivos, shell, Python, web, SQL)
- RAG para ensinar programação (Go, Python, Java, C#, C++, C)
- Ler, analisar e resolver arquivos
- Desenvolver apps, landing pages, código, aplicações web
- Chain of Thought (planejar antes de executar)
- Guardrails (SQL só SELECT, prompt injection, sanitização de secrets)
- Memória e contexto de estado
- Observabilidade (logs estruturados, tokens, duração)
- UX adaptativa (Markdown, Streaming)
- Usar Supabase como banco

## User Choices
- **Interface**: Desktop local (CustomTkinter + Ollama) + Web demo (Emergent React/FastAPI)
- **LLM**: OpenRouter (keeping existing key) com opção Ollama local no desktop
- **Tools**: Sandboxadas
- **RAG**: Supabase pgvector com fallback local
- **Mobile**: acesso pelo celular com digitação
- **Branding**: sem marca d'água Emergent; créditos **Jose Lorenzo — (51) 98152-1264 WhatsApp**

## Architecture
```
/app/agent_core/        # Cérebro compartilhado
  ├ agent.py            # Orquestrador (plan → tools → reply)
  ├ planner.py          # Chain of Thought
  ├ llm.py              # OpenRouter + Ollama router, streaming, embeddings
  ├ tools.py            # 10 ferramentas + ToolRegistry
  ├ guardrails.py       # SQL/shell/secrets/injection
  ├ memory.py           # SQLite sessions + messages
  ├ rag.py              # Supabase pgvector + fallback SQLite
  └ observability.py    # Structured event log

/app/backend/           # FastAPI web wrapper
  ├ server.py           # /api/chat/stream (SSE), /api/sessions, /api/tools, /api/rag, /api/logs
  └ seed_rag.py         # 24 docs de programação indexados

/app/ajax_desktop/      # Desktop CustomTkinter (user's PC)
  ├ desktop_app.py
  ├ ajax.bat
  └ app.spec            # PyInstaller

/app/frontend/          # React chat UI (mobile responsive)
  └ src/pages/AjaxChat.jsx
```

## Implemented (2026-02)

### Iteration 1 — Super-Agent Core (first finish)
- ✅ **Chain of Thought planner** — plano gerado antes de qualquer tool call
- ✅ **10 ferramentas**: salvar_arquivo, ler_arquivo, listar_arquivos, executar_shell, executar_python, analisar_codigo (Python/C/C++/Java/C#/Go), buscar_web, consultar_banco, obter_schema_banco, consultar_rag
- ✅ **Guardrails**: SQL SELECT-only, shell dangerous command block, secret redaction (sk-*, sb_*, postgres passwords, AWS, GitHub, PEM), prompt injection detection
- ✅ **Memory**: multi-session, SQLite, OpenAI-compatible message format
- ✅ **Observability**: every plan/llm_call/tool_call logged with duration + tokens + status
- ✅ **RAG**: 24 docs de Python/Java/C/C++/C#/Go, Supabase pgvector com fallback local SQLite
- ✅ **LLM Router**: OpenRouter + Ollama unificados (chat + stream + embed)
- ✅ **Streaming UX** via SSE (Server-Sent Events)
- ✅ **FastAPI backend** com SSE + tools + RAG + logs endpoints
- ✅ **React frontend** com markdown, code highlighting, plan disclosure, tool call cards, sessions sidebar, logs tab, RAG tab
- ✅ **Desktop CustomTkinter** app (para PC do usuário com Ollama)
- ✅ **Desktop packaging**: .bat launcher + PyInstaller spec

### Iteration 2 — Mobile + Branding (current)
- ✅ **Mobile responsive**: sidebar colapsável, viewport-aware, textarea com font-size:16px (evita zoom iOS), safe-area insets (notch)
- ✅ **Hamburger menu** no topo para abrir sidebar no mobile
- ✅ **Emergent watermark hidden** via CSS
- ✅ **Developer credits**: José Lorenzo + WhatsApp (5551981521264) como link direto `wa.me`
- ✅ **Fix guardrail crítico**: `rm -rf /` agora é bloqueado (regex antigo tinha `\b` após `/` que falhava)

## Known Status
- Supabase pgvector: host DNS do projeto fornecido está inacessível desta rede. Sistema cai automaticamente pro SQLite local (funciona 100%). Para ativar pgvector real, confirmar que o projeto Supabase está ativo e atualizar SUPABASE_DB_URL.
- Ollama: não disponível no sandbox web. Desktop app no PC do usuário usa Ollama como default.

## Backend Testing
- **18/19 tests passed** inicialmente
- **1 critical bug** encontrado (rm -rf / bypass) → **FIXED** e validado via curl

## Next Action Items (P0 → P2)
- P1: Adicionar exportação de conversa (JSON/MD)
- P1: Dark/light theme toggle
- P2: Integração de STT (fala pra texto) para celular
- P2: Push notifications pra resultados longos
- P2: Criar landing page marketing para o Ajax
