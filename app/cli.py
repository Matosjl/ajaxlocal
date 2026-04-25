#!/usr/bin/env python3
"""Ajax CLI — converse com o Ajax Super-Agent diretamente no terminal."""
from __future__ import annotations
import os
import sys
from pathlib import Path

# Garante que agent_core esteja no path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__) / "backend" / ".env")

from agent_core import AjaxAgent, LLMRouter, Memory, Observer, RAGStore, get_default_tools


def main():
    print("=" * 50)
    print("  AJAX Super-Agent - CLI")
    print("  Modelo:", os.environ.get("OLLAMA_MODEL", "qwen2.5-coder:1.5b"))
    print("  Provider: Ollama (local)")
    print("=" * 50)
    print("  Comandos especiais:")
    print("    /sair      - encerrar")
    print("    /limpar    - nova conversa")
    print("    /ferramentas - listar ferramentas disponiveis")
    print("=" * 50)
    print()

    # Setup
    memory = Memory()
    observer = Observer()
    rag = RAGStore(database_url=os.environ.get("SUPABASE_DB_URL") or None)
    
    llm = LLMRouter(
        provider="ollama",
        model=os.environ.get("OLLAMA_MODEL", "qwen2.5-coder:1.5b"),
        ollama_url=os.environ.get("OLLAMA_URL", "http://localhost:11434"),
    )
    tools = get_default_tools(rag, llm)
    agent = AjaxAgent(llm=llm, memory=memory, observer=observer, rag=rag, tools=tools)

    # Cria sessao
    session = memory.create_session("CLI Session", provider="ollama", model=llm.model)
    session_id = session["id"]
    print(f"[Sessao: {session_id[:8]}...]")
    print()

    while True:
        try:
            user_input = input("Voce: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\nSaindo...")
            break

        if not user_input:
            continue

        if user_input.lower() == "/sair":
            print("Ate logo!")
            break

        if user_input.lower() == "/limpar":
            session = memory.create_session("CLI Session", provider="ollama", model=llm.model)
            session_id = session["id"]
            print(f"[Nova sessao: {session_id[:8]}...]")
            print()
            continue

        if user_input.lower() == "/ferramentas":
            print("\nFerramentas disponiveis:")
            for name in tools.names():
                print(f"  - {name}")
            print()
            continue

        print()
        print("Ajax: ", end="", flush=True)

        # Stream da resposta
        full_response = ""
        for ev in agent.run_stream(session_id, user_input):
            if ev["type"] == "token":
                print(ev["content"], end="", flush=True)
                full_response += ev["content"]
            elif ev["type"] == "plan":
                if not ev.get("direct"):
                    print(f"\n[Plano: {ev['content'][:60]}...]")
                    print()
            elif ev["type"] == "tool_call":
                print(f"\n[Ferramenta: {ev['name']}({ev['arguments']})]")
            elif ev["type"] == "tool_result":
                print(f"\n[Resultado: {ev['content'][:100]}...]")
            elif ev["type"] == "error":
                print(f"\n[Erro: {ev['message']}]")

        print()
        print()


if __name__ == "__main__":
    main()

