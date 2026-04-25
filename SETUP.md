# 🚀 Setup AJAX Local

## Pré-requisitos
- Python 3.9+
- Node.js 18+
- Yarn 1.22+

## ⚡ Instalação Rápida

### 1️⃣ Instale Ollama (para embeddings e LLM local)
```bash
# https://ollama.com/download
ollama pull qwen2.5-coder:1.5b
ollama pull nomic-embed-text
```

### 2️⃣ Configure variáveis de ambiente

**Backend** - Edite `app/backend/.env`:
```bash
# Use Ollama (gratuito, local) OU OpenRouter (com custo, mais rápido)
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5-coder:1.5b
OLLAMA_EMBED_MODEL=nomic-embed-text

# Se usar OpenRouter:
# OPENROUTER_API_KEY=sk-or-v1-seu-token (https://openrouter.ai)
```

**Frontend** - `app/frontend/.env` (já criado):
```bash
REACT_APP_API_URL=http://localhost:8000
```

**Desktop** - `app/ajax_desktop/.env` (já criado):
```bash
OLLAMA_URL=http://localhost:11434
```

### 3️⃣ Instale dependências

```bash
# Backend
cd app/backend
pip install -r requirements.txt

# Frontend
cd app/frontend
yarn install

# Desktop (opcional)
cd app/ajax_desktop
pip install -r requirements.txt
```

### 4️⃣ Inicialize o RAG Database

**Windows:**
```bash
INIT_RAG.bat
```

**macOS/Linux:**
```bash
chmod +x init_rag.sh
./init_rag.sh
```

Isso popula a base de conhecimento com Python, Java, C, C++, C#, Go. Execute uma única vez (ou sempre que quiser resetar).

## 🎯 Rodando

⚠️ **Antes de rodar: execute `INIT_RAG.bat` ou `./init_rag.sh` uma vez para popular o RAG**

### Opção A: Web (Backend + Frontend)

**Terminal 1 - Ollama** (deixa rodando):
```bash
ollama serve
```

**Terminal 2 - Backend**:
```bash
cd app/backend
python server.py
# Acesso: http://localhost:8000
# Docs: http://localhost:8000/docs
```

**Terminal 3 - Frontend**:
```bash
cd app/frontend
yarn start
# Abre: http://localhost:3000
```

### Opção B: Desktop App

```bash
# Terminal 1 - Ollama
ollama serve

# Terminal 2 - Desktop
cd app/ajax_desktop
python desktop_app.py
```

## ✅ Testes

```bash
# Backend tests
cd app/backend
pytest tests/

# Frontend tests
cd app/frontend
yarn test
```

## 📦 Build para Produção

**Frontend**:
```bash
cd app/frontend
yarn build
```

**Desktop .exe** (Windows):
```bash
cd app/ajax_desktop
pip install pyinstaller
pyinstaller app.spec
# Saída: dist/ajax.exe
```

## 🐛 Troubleshooting

| Problema | Solução |
|----------|---------|
| `ModuleNotFoundError: agent_core` | Verifique se está na pasta `app/` ao rodar |
| `Connection refused localhost:8000` | Backend não está rodando - execute `python server.py` |
| `Ollama not responding` | Verifique se `ollama serve` está rodando na porta 11434 |
| `CORS error` | Verifique `REACT_APP_API_URL` em `app/frontend/.env` |

## 📚 Arquitetura

```
app/
├── agent_core/          # Motor IA compartilhado
├── backend/             # FastAPI + SSE streaming
├── frontend/            # React 19 + Tailwind
├── ajax_desktop/        # CustomTkinter desktop app
└── agent_workspace/     # Workspace de trabalho
```

## 🔐 Variáveis de Ambiente

Ver `.env.example` em cada pasta para todas as opções disponíveis.

---

**Pronto!** 🎉 Qualquer dúvida, leia o README.md principal.
