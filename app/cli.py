#!/usr/bin/env python3
"""Ajax CLI — converse com o Ajax Super-Agent diretamente no terminal."""
from __future__ import annotations
import logging
import os
import sys
import threading
import time
from pathlib import Path

# Garante que agent_core esteja no path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__) / "backend" / ".env")

from agent_core import AjaxAgent, LLMRouter, Memory, Observer, RAGStore, get_default_tools

# Configurar logging para debug
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("ajax.cli")


def show_spinner(stop_event: threading.Event, message: str = "Processando"):
    """Mostra um spinner animado no terminal enquanto processa."""
    spinner = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    idx = 0
    while not stop_event.is_set():
        print(f"\r  {spinner[idx]} {message}...", end="", flush=True)
        idx = (idx + 1) % len(spinner)
        time.sleep(0.1)
    print("\r" + " " * (len(message) + 10) + "\r", end="")


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
    print("    /debug     - alternar modo debug (logs detalhados)")
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

    debug_mode = False

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

        if user_input.lower() == "/debug":
            debug_mode = not debug_mode
            level = logging.DEBUG if debug_mode else logging.INFO
            logging.getLogger().setLevel(level)
            print(f"\n[Modo debug: {'ON' if debug_mode else 'OFF'}]")
            print()
            continue

        print()
        
        # Spinner para dar feedback visual enquanto Ollama processa
        stop_spinner = threading.Event()
        spinner_thread = threading.Thread(target=show_spinner, args=(stop_spinner, "Ajax está pensando"))
        spinner_thread.start()

        # Stream da resposta
        full_response = ""
        try:
            for ev in agent.run_stream(session_id, user_input):
                # No primeiro token, para o spinner
                if not stop_spinner.is_set():
                    stop_spinner.set()
                    spinner_thread.join()
                    print("Ajax: ", end="", flush=True)

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
        except KeyboardInterrupt:
            stop_spinner.set()
            spinner_thread.join()
            print("\n[Interrompido pelo usuário]")
        finally:
            if not stop_spinner.is_set():
                stop_spinner.set()
                spinner_thread.join()

        print()
        print()


if __name__ == "__main__":
    main()

