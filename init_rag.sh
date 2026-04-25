#!/bin/bash
# Initialize RAG Database

echo ""
echo "========================================"
echo "  Inicializando RAG Database"
echo "========================================"
echo ""
echo "Isto vai popular a base de conhecimento do RAG"
echo "com materiais de Python, Java, C, C++, C#, Go"
echo ""

cd "$(dirname "$0")"

if [ ! -d "app/backend" ]; then
    echo "ERRO: Pasta app/backend não encontrada"
    exit 1
fi

cd app/backend
echo "Executando seed_rag.py..."
python -m backend.seed_rag

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ RAG inicializado com sucesso!"
    echo ""
else
    echo ""
    echo "❌ Erro ao inicializar RAG"
    echo ""
fi
