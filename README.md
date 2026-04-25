# AJAX Local - Quick Start

## 🎯 Comece Aqui

### 1️⃣ Initialize RAG (apenas primeira vez)

**Windows:**
```bash
INIT_RAG.bat
```

**macOS / Linux:**
```bash
chmod +x init_rag.sh
./init_rag.sh
```

### 2️⃣ Rodar a Aplicação

**Windows**
```bash
# Web App (Backend + Frontend)
START.bat

# OU Desktop App
START_DESKTOP.bat
```

**macOS / Linux**
```bash
# Web App
chmod +x start.sh
./start.sh

# OU Desktop App
chmod +x start_desktop.sh
./start_desktop.sh
```

---

## 📋 Setup Manual (se preferir)

### 1. Ollama (precisa estar rodando)
```bash
ollama serve
```

### 2. Backend
```bash
cd app/backend
python server.py
# http://localhost:8000
```

### 3. Frontend
```bash
cd app/frontend
yarn start
# http://localhost:3000
```

---

## 📚 Documentação Completa
Veja `SETUP.md` para instruções detalhadas

## 🐛 Precisa de Help?
Leia o README.md em `app/`

---

**Tudo pronto!** 🚀
