#!/usr/bin/env bash
set -e

echo ""
echo "========================================"
echo "  AJAX Super-Agent - Setup qwen2.5-coder:1.5b"
echo "========================================"
echo ""

# 1. Verificar Ollama
echo "[1/4] Verificando Ollama..."
if ! command -v ollama &> /dev/null; then
    echo "❌ Ollama não encontrado. Instale em https://ollama.com/download"
    exit 1
fi
echo "✅ Ollama encontrado"

# 2. Iniciar Ollama se necessario
echo "[2/4] Iniciando Ollama..."
if ! pgrep -x "ollama" > /dev/null; then
    ollama serve &
    sleep 5
fi
echo "✅ Ollama rodando"

# 3. Baixar modelo
echo "[3/4] Baixando qwen2.5-coder:1.5b (~986MB)..."
ollama pull qwen2.5-coder:1.5b
echo "✅ Modelo qwen2.5-coder:1.5b instalado"

# 4. Atualizar RAG
echo "[4/4] Populando base de conhecimento (RAG)..."
cd "$(dirname "$0")/app/backend"
if [ -f "venv_backend/bin/python" ]; then
    venv_backend/bin/python seed_rag.py
else
    python3 seed_rag.py || python seed_rag.py
fi
echo "✅ RAG atualizado"

echo ""
echo "========================================"
echo "  ✅ Setup completo!"
echo "========================================"
echo ""
echo "Pronto para rodar. Execute:"
echo "  ./start.sh       (Web App)"
echo "  ./start_desktop.sh   (Desktop App)"
echo ""

