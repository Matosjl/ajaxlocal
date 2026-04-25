# TODO - Melhorias no AJAX Super-Agent

## Concluído ✅

### 1. Tratamento de Erros (Timeout Ollama)
- [x] `app/agent_core/llm.py` — Adicionado try/except com mensagens amigáveis:
  - Timeout: "⏳ Ollama está demorando para responder..."
  - ConnectError: "🔌 Não foi possível conectar com Ollama..."
  - KeyboardInterrupt: "🛑 Requisição interrompida..."
- [x] Streaming também protegido contra timeouts

### 2. Fast-Path para Perguntas Triviais
- [x] `app/agent_core/planner.py` — Regex para detectar perguntas simples (oi, o que é, como funciona)
- [x] `app/agent_core/agent.py` — Quando `direct=True`, pula loop de ferramentas e chama LLM direto
- [x] `app/cli.py` — Esconde bloco de plano quando resposta é direta

### 3. Logs de Debug Claros
- [x] `app/agent_core/llm.py` — Logger `ajax.llm` com debug/info/error
- [x] `app/agent_core/agent.py` — Logger `ajax.agent` rastreando todo o fluxo
- [x] `app/agent_core/rag.py` — Logger `ajax.rag` com scores e filtros
- [x] `app/cli.py` — Comando `/debug` para alternar nível de log

### 4. Limpeza de Contexto RAG
- [x] `app/agent_core/rag.py` — Filtro de score mínimo (0.3) para evitar resultados irrelevantes
- [x] Logs mostram quantos resultados foram filtrados

## Teste
```bash
cd app
python cli.py
# Testar: "oi" → deve responder rápido sem ferramentas
# Testar: "o que faz criar_componente" → fast-path
# Testar: "/debug" → mostrar logs detalhados
```

