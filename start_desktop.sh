#!/bin/bash
# Start AJAX Local - Desktop Edition (macOS/Linux)

echo ""
echo "========================================"
echo "  AJAX Super-Agent - Desktop Setup"
echo "========================================"
echo ""
echo "Este script vai iniciar 2 processos:"
echo "  1. Ollama (LLM + embeddings)"
echo "  2. Desktop App (CustomTkinter)"
echo ""

cd "$(dirname "$0")"

# Check if folder exists
if [ ! -d "app/ajax_desktop" ]; then
    echo "ERRO: Pasta app/ajax_desktop não encontrada"
    exit 1
fi

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "Encerrando processos..."
    kill $OLLAMA_PID $DESKTOP_PID 2>/dev/null
    exit 0
}

trap cleanup SIGINT

# Terminal 1: Ollama
echo "Iniciando Ollama..."
ollama serve &
OLLAMA_PID=$!
sleep 2

# Terminal 2: Desktop App
echo "Iniciando Desktop App..."
(cd app/ajax_desktop && python desktop_app.py) &
DESKTOP_PID=$!

echo ""
echo "✅ Tudo iniciado!"
echo ""
echo "Pressione Ctrl+C para encerrar"
echo ""

wait
