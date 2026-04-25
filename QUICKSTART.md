# 🚀 Quick Start - AJAX Super-Agent

## ⚡ 3 Formas de Rodar Tudo

### 1️⃣ **Windows - Double-click (Recomendado)**
```
run.bat
```
Ou procure o arquivo `run.bat` e abra com duplo-clique.

---

### 2️⃣ **Command Line (Windows)**
```bash
run.bat
```

---

### 3️⃣ **macOS / Linux - Terminal**
```bash
chmod +x run.sh
./run.sh
```

---

### 4️⃣ **npm (Todas as plataformas)**
```bash
npm install
npm run ajax
```

---

## 🔧 Setup Único (Primeira Vez)

Antes de rodar pela primeira vez, inicialize a base de RAG:

**Windows:**
```bash
INIT_RAG.bat
```

**macOS / Linux:**
```bash
chmod +x init_rag.sh
./init_rag.sh
```

---

## 📍 O que vai abrir

Quando você rodar `run`:

| Serviço | URL | Descrição |
|---------|-----|-----------|
| **Frontend** | http://localhost:3000 | Interface React |
| **Backend** | http://localhost:8000 | FastAPI server |
| **Docs** | http://localhost:8000/docs | API documentation |
| **Ollama** | http://localhost:11434 | LLM local (background) |

---

## 🐛 Se algo der errado

**Frontend não abre?**
- Certifique-se que tem Node.js + Yarn instalados
- Rode: `cd app/frontend && yarn install`

**Backend não responde?**
- Certifique-se que Ollama está rodando
- Verifique a porta 8000: `netstat -an | find "8000"` (Windows) ou `lsof -i :8000` (Mac/Linux)

**Ollama não inicia?**
- Instale Ollama: https://ollama.com
- Puxe os modelos: `ollama pull llama3.1` e `ollama pull nomic-embed-text`

---

## 📦 Comandos Individuais

```bash
# Rodar só o backend
cd app/backend && python server.py

# Rodar só o frontend
cd app/frontend && yarn start

# Inicializar RAG
cd app/backend && python seed_rag.py

# Ou com npm
npm run backend
npm run frontend
npm run init-rag
```

---

**Pronto! 🎉 Tudo configurado para rodar com um único comando!**
