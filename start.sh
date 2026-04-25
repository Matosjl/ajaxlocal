#!/bin/bash
# Start AJAX Local - Web Edition (macOS/Linux)

echo ""
echo "========================================"
echo "  AJAX Super-Agent - Local Setup"
echo "========================================"
echo "  Modelo: qwen2.5-coder:1.5b (Ollama)"
echo "  Capacidades: Fullstack, Mobile, Web"
echo "========================================"
echo ""
echo "Este script vai iniciar 3 processos:"
echo "  1. Ollama (LLM + embeddings)"
echo "  2. Backend FastAPI"
echo "  3. Frontend React"
echo ""

cd "$(dirname "$0")"

# Check if folders exist
if [ ! -d "app/backend" ]; then
    echo "ERRO: Pasta app/backend não encontrada"
    exit 1
fi

if [ ! -d "app/frontend" ]; then
    echo "ERRO: Pasta app/frontend não encontrada"
    exit 1
fi

# Check model
echo "Verificando modelo qwen2.5-coder:1.5b..."
if ! ollama list 2>/dev/null | grep -q "qwen2.5-coder:1.5b"; then
    echo "📥 Baixando qwen2.5-coder:1.5b (~986MB)..."
    ollama pull qwen2.5-coder:1.5b
fi
echo "✅ Modelo pronto"

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "Encerrando processos..."
    kill $OLLAMA_PID $BACKEND_PID $FRONTEND_PID 2>/dev/null
    exit 0
}

trap cleanup SIGINT

# Terminal 1: Ollama
echo "Iniciando Ollama..."
ollama serve &
OLLAMA_PID=$!
sleep 2

# Terminal 2: Backend
echo "Iniciando Backend..."
(cd app/backend && python server.py) &
BACKEND_PID=$!
sleep 2

# Terminal 3: Frontend
echo "Iniciando Frontend..."
(cd app/frontend && yarn start) &
FRONTEND_PID=$!

echo ""
echo "✅ Tudo iniciado!"
echo "   Backend: http://localhost:8000"
echo "   Frontend: http://localhost:3000"
echo "   Docs: http://localhost:8000/docs"
echo "   Modelo: qwen2.5-coder:1.5b (Ollama local)"
echo ""
echo "Pressione Ctrl+C para encerrar"
echo ""

wait
