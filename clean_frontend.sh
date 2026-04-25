#!/bin/bash
# Clean and reinstall frontend dependencies

echo ""
echo "========================================"
echo "  Limpando Frontend"
echo "========================================"
echo ""

cd "$(dirname "$0")/app/frontend"

echo "Removendo node_modules..."
rm -rf node_modules
rm -f yarn.lock package-lock.json

echo ""
echo "Reinstalando dependências..."
yarn install

echo ""
echo "✅ Frontend limpo e reinstalado!"
echo ""
