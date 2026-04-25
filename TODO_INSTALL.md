# Instalação de Dependências - TODO

## Progresso

- [x] Step 1: Root dependencies (`npm install`) - DONE
- [x] Step 2: Frontend dependencies (`yarn install`) - DONE
- [x] Step 3: Backend dependencies (`pip install -r requirements.txt`) - DONE
- [x] Step 4: Desktop venv creation + dependencies - DONE
- [x] Step 5: Configurar qwen2.5-coder:1.5b como modelo padrão - DONE
- [x] Step 6: Expandir RAG com fullstack/mobile/web - DONE
- [x] Step 7: Adicionar ferramentas de scaffolding - DONE
- [x] Step 8: Report results - DONE

## Resumo da Instalação

| Componente | Status | Detalhes |
|------------|--------|----------|
| **Root** | ✅ | `concurrently` instalado |
| **Frontend** | ✅ | Todos os pacotes yarn atualizados |
| **Backend** | ✅ | ~137 pacotes Python instalados no venv |
| **Desktop** | ✅ | venv criado + 7 pacotes instalados |
| **Modelo** | ✅ | `qwen2.5-coder:1.5b` configurado como padrão |
| **RAG** | ✅ | Expandido com React, Next.js, TypeScript, React Native, Flutter, PWA, FastAPI, Docker, SEO |
| **Tools** | ✅ | `scaffold_projeto` e `criar_componente` adicionados |

## 🎯 Modelo Recomendado: qwen2.5-coder:1.5b

O projeto agora usa **qwen2.5-coder:1.5b** como modelo padrão no Ollama:

- **Tamanho:** ~986 MB (ideal para máquinas com pouca RAM)
- **Capacidades:** Excelente para código Python, JavaScript, TypeScript, Dart, Flutter, React, Next.js
- **RAM necessária:** ~1.2 GB livres (funciona na sua máquina!)

### Como configurar

**Windows:**
```bash
setup_qwen.bat
```

**macOS / Linux:**
```bash
chmod +x setup_qwen.sh
./setup_qwen.sh
```

Isso baixa o modelo e atualiza a base de conhecimento (RAG) automaticamente.

### Alternativas (se quiser testar outros modelos)

**Opção A — OpenRouter (cloud):**
No frontend, selecione:
- Provider: **OpenRouter**
- Modelo: `google/gemini-2.0-flash-001`

**Opção B — Outros modelos Ollama:**
- Provider: **Ollama**
- Modelo: `deepseek-r1:1.5b` (1.1 GB)
- Modelo: `qwen2.5-coder:7b` (4.7 GB — só se tiver RAM suficiente)

