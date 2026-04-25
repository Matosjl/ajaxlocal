#!/usr/bin/env python3
"""Teste rápido para validar o fast-path de perguntas triviais."""
from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from agent_core.planner import _TRIVIAL_RE


def test_trivial_detection():
    """Testa se o regex detecta corretamente perguntas triviais."""
    trivial_cases = [
        "oi",
        "olá",
        "e ai",
        "eae",
        "hey",
        "hello",
        "o que é criar_componente",
        "o que faz criar_componente",
        "qual é a função do criar_componente",
        "como funciona o salvar_arquivo",
        "defina o que é RAG",
    ]
    
    non_trivial_cases = [
        "crie um projeto react",
        "execute o comando ls -la",
        "analise esse código python",
        "busque na web sobre fastapi",
        "salve um arquivo com conteúdo xyz",
    ]
    
    print("Testando detecção de perguntas triviais:")
    all_pass = True
    
    for case in trivial_cases:
        match = _TRIVIAL_RE.search(case)
        status = "✅" if match else "❌"
        if not match:
            all_pass = False
        print(f"  {status} '{case}' → {'TRIVIAL' if match else 'NÃO TRIVIAL'}")
    
    print("\nTestando detecção de perguntas NÃO triviais:")
    for case in non_trivial_cases:
        match = _TRIVIAL_RE.search(case)
        status = "✅" if not match else "❌"
        if match:
            all_pass = False
        print(f"  {status} '{case}' → {'TRIVIAL' if match else 'NÃO TRIVIAL'}")
    
    print(f"\n{'✅ Todos os testes passaram!' if all_pass else '❌ Alguns testes falharam!'}")
    return all_pass


if __name__ == "__main__":
    success = test_trivial_detection()
    sys.exit(0 if success else 1)

