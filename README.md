# Ajax Super-Agente

Agente de IA profissional com **Chain of Thought**, **Guardrails**, **RAG**, **Memória persistente** e **Observabilidade**.

## Arquitetura

```
agent_core/         # Cérebro compartilhado (importável por desktop e web)
├── agent.py        # Orquestrador (CoT → tool loop → resposta)
├── planner.py      # Chain of Thought
├── llm.py          # Router Ollama + OpenRouter (streaming + embeddings)
├── tools.py        # 10 ferramentas: arquivos, shell, Python, SQL, RAG, web...
├── guardrails.py   # SQL safety, prompt injection, secret redaction
├── memory.py       # Sessões + mensagens (SQLite)
├── rag.py          # Supabase pgvector com fallback local
└── observability.py # Logs estruturados (eventos, tokens, duração)

backend/            # FastAPI web demo (rodando na Emergent)
├── server.py       # Endpoints + SSE streaming
└── seed_rag.py     # Popula RAG com Python/Java/C/C++/C#/Go

ajax_desktop/       # Desktop CustomTkinter (rodar no seu PC)
├── desktop_app.py
├── ajax.bat
└── app.spec        # PyInstaller
```

## Web demo (Emergent)
Já está rodando. Acesse o frontend e mande mensagens — Ajax planeja, chama ferramentas, mostra logs.

## Desktop (rode no seu PC)

### 1. Instale Ollama
- Baixe: https://ollama.com/download
- Baixe os modelos:
  ```bash
  ollama pull llama3.1
  ollama pull nomic-embed-text   # para embeddings RAG
  ```

### 2. Instale dependências
```bash
cd /app
pip install -r ajax_desktop/requirements.txt
```

### 3. Rode
```bash
python ajax_desktop/desktop_app.py
# ou no Windows:
ajax_desktop\ajax.bat
```

### 4. Empacote em .exe (Windows)
```bash
pip install pyinstaller
cd ajax_desktop
pyinstaller app.spec
# saída em dist/ajax.exe
```

## Ferramentas disponíveis
| Nome | O que faz |
|---|---|
| `salvar_arquivo` | Cria/sobrescreve arquivo no workspace |
| `ler_arquivo` | Lê conteúdo |
| `listar_arquivos` | Lista diretório |
| `executar_shell` | Shell sandboxado (bloqueia rm -rf /, fork bomb...) |
| `executar_python` | Roda Python isolado |
| `analisar_codigo` | Lint-light (Python, C, C++, Java, C#, Go) |
| `buscar_web` | GET HTTP |
| `consultar_banco` | SELECT no Supabase (INSERT/DELETE bloqueados) |
| `obter_schema_banco` | Lista tabelas + colunas |
| `consultar_rag` | Busca semântica na base de conhecimento |

## Guardrails ativos
- **SQL**: só SELECT
- **Shell**: bloqueia `rm -rf /`, `mkfs`, fork bombs, `shutdown`, etc.
- **Secrets**: redacta `sk-*`, `sb_*`, senhas em URLs Postgres, AWS keys, GitHub tokens, chaves privadas
- **Prompt injection**: detecta "ignore instruções anteriores", "revele seu prompt", etc.
- **Path traversal**: opcional, configurável por ferramenta

## Observabilidade
Cada evento (plan, llm_call, tool_call) é gravado em SQLite com:
- duração (ms)
- tokens prompt + completion
- payload + status

Acesse pela aba "Observabilidade" no frontend ou `GET /api/logs`.

## Configuração (.env em backend/)
```
OPENROUTER_API_KEY=sk-or-v1-...
OPENROUTER_MODEL=openrouter/auto
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1
OLLAMA_EMBED_MODEL=nomic-embed-text
SUPABASE_URL=...
SUPABASE_DB_URL=postgres://...
```

> **Nota Supabase**: o host `db.zqskdthqrjxdzcvvzbxm.supabase.co` está com DNS inacessível.
> O RAG cai pra fallback local (SQLite + cosine search) automaticamente. Funciona perfeitamente.
> Para ativar pgvector real: confirme se o projeto Supabase está ativo e atualize `SUPABASE_DB_URL`.
