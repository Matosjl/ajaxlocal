"""Ajax Desktop — CustomTkinter GUI for the local super-agent.

Roda no PC do usuário com Ollama local (ou OpenRouter como fallback).
Compartilha o mesmo agent_core do backend web.
"""
from __future__ import annotations
import os
import sys
import threading
from pathlib import Path

# Add project root to path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import customtkinter as ctk
from dotenv import load_dotenv

load_dotenv(ROOT / "backend" / ".env")

from agent_core import (
    AjaxAgent, LLMRouter, Memory, Observer, RAGStore, get_default_tools,
)


# ---------------- Setup ----------------
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")


class AjaxDesktopApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("AJAX — Super-Agente Local")
        self.geometry("1100x780")
        self.configure(fg_color="#0a0a0c")

        # ----- Agent setup (default = Ollama local) -----
        self.provider_var = ctk.StringVar(value=os.environ.get("AJAX_DEFAULT_PROVIDER", "ollama"))
        self.model_var = ctk.StringVar(value=os.environ.get("OLLAMA_MODEL", "llama3.1"))
        self.memory = Memory(db_path=str(ROOT / "agent_core" / "data" / "memory_desktop.db"))
        self.observer = Observer(db_path=str(ROOT / "agent_core" / "data" / "observability_desktop.db"))
        self.rag = RAGStore(database_url=os.environ.get("SUPABASE_DB_URL"))
        self.session = self.memory.create_session("Desktop session")

        self._build_ui()
        self._rebuild_agent()

    # ----- UI -----
    def _build_ui(self):
        # Header
        header = ctk.CTkFrame(self, fg_color="#0d0d10", corner_radius=0, height=64)
        header.pack(fill="x")
        header.pack_propagate(False)

        title = ctk.CTkLabel(
            header, text="🤖  AJAX  ·  super-agente local",
            font=("Segoe UI", 18, "bold"), text_color="#fb923c",
        )
        title.pack(side="left", padx=20, pady=18)

        # Provider selector
        ctk.CTkLabel(header, text="Provider:", font=("Segoe UI", 12), text_color="#a1a1aa").pack(side="left", padx=(20, 6))
        self.provider_menu = ctk.CTkOptionMenu(
            header, values=["ollama", "openrouter"], variable=self.provider_var,
            command=lambda _: self._rebuild_agent(),
            fg_color="#1f1f23", button_color="#fb923c", button_hover_color="#ea580c",
            text_color="#e8e8ea", width=110,
        )
        self.provider_menu.pack(side="left")

        ctk.CTkLabel(header, text="Modelo:", font=("Segoe UI", 12), text_color="#a1a1aa").pack(side="left", padx=(15, 6))
        self.model_entry = ctk.CTkEntry(
            header, textvariable=self.model_var, width=200,
            fg_color="#1f1f23", border_color="#2a2a2e", text_color="#e8e8ea",
        )
        self.model_entry.pack(side="left")
        self.model_entry.bind("<Return>", lambda _: self._rebuild_agent())

        self.status_label = ctk.CTkLabel(header, text="●  pronto", font=("Segoe UI", 11), text_color="#10b981")
        self.status_label.pack(side="right", padx=20)

        # Chat area (scrollable)
        self.chat_frame = ctk.CTkScrollableFrame(
            self, fg_color="#0a0a0c", scrollbar_button_color="#27272a",
        )
        self.chat_frame.pack(fill="both", expand=True, padx=20, pady=(15, 5))

        # Welcome
        self._add_system_message(
            "Olá, chefe. Sou o **Ajax**. Posso planejar, ler/escrever arquivos, "
            "executar comandos, rodar Python/SQL, buscar na minha base de conhecimento "
            "(Python, Java, C, C++, C#, Go) e desenvolver código pra você. Manda ver."
        )

        # Composer
        composer = ctk.CTkFrame(self, fg_color="#0d0d10", corner_radius=0, height=110)
        composer.pack(fill="x", side="bottom")
        composer.pack_propagate(False)

        self.entry = ctk.CTkTextbox(
            composer, height=70, fg_color="#1a1a1e", text_color="#e8e8ea",
            border_color="#2a2a2e", border_width=1, font=("Segoe UI", 13),
        )
        self.entry.pack(side="left", fill="x", expand=True, padx=(20, 8), pady=20)
        self.entry.bind("<Control-Return>", lambda _: self._send())
        self.entry.bind("<Return>", self._on_enter)

        self.send_btn = ctk.CTkButton(
            composer, text="ENVIAR", command=self._send, width=110, height=70,
            fg_color="#fb923c", hover_color="#ea580c", text_color="#0a0a0c",
            font=("Segoe UI", 13, "bold"),
        )
        self.send_btn.pack(side="right", padx=(0, 20), pady=20)

    def _on_enter(self, event):
        if event.state & 0x0001:  # Shift
            return
        self._send()
        return "break"

    def _rebuild_agent(self):
        provider = self.provider_var.get()
        model = self.model_var.get().strip()
        try:
            llm = LLMRouter(
                provider=provider,
                model=model,
                openrouter_key=os.environ.get("OPENROUTER_API_KEY", ""),
                ollama_url=os.environ.get("OLLAMA_URL", "http://localhost:11434"),
            )
            tools = get_default_tools(self.rag, llm)
            self.agent = AjaxAgent(
                llm=llm, memory=self.memory, observer=self.observer,
                rag=self.rag, tools=tools,
            )
            self._set_status(f"●  {provider} · {model}", "#10b981")
        except Exception as e:
            self._set_status(f"●  erro: {e}", "#ef4444")

    def _set_status(self, text, color):
        self.status_label.configure(text=text, text_color=color)

    # ----- Send / receive -----
    def _send(self):
        text = self.entry.get("1.0", "end").strip()
        if not text:
            return
        self.entry.delete("1.0", "end")
        self._add_user_message(text)
        self._set_status("●  pensando...", "#fb923c")
        self.send_btn.configure(state="disabled")

        threading.Thread(target=self._run_agent, args=(text,), daemon=True).start()

    def _run_agent(self, text: str):
        try:
            asst_frame = self._add_assistant_placeholder()
            for ev in self.agent.run_stream(self.session["id"], text):
                self.after(0, lambda e=ev, f=asst_frame: self._handle_event(f, e))
            self.after(0, lambda: self._set_status("●  pronto", "#10b981"))
        except Exception as e:
            self.after(0, lambda: self._add_system_message(f"❌ Erro: {e}", error=True))
            self.after(0, lambda: self._set_status("●  erro", "#ef4444"))
        finally:
            self.after(0, lambda: self.send_btn.configure(state="normal"))

    def _handle_event(self, frame, ev):
        t = ev.get("type")
        if t == "plan":
            self._append_to_assistant(frame, "🧠 PLANO:", "#fb923c", bold=True)
            self._append_to_assistant(frame, ev["content"], "#a1a1aa")
        elif t == "injection_warning":
            self._append_to_assistant(frame, f"⚠️ {ev['message']}", "#ef4444")
        elif t == "tool_call":
            self._append_to_assistant(frame, f"🔧 {ev['name']}({ev['arguments'][:120]})", "#fb923c", bold=True)
        elif t == "tool_result":
            ok = "✅" if ev.get("ok") else "❌"
            preview = (ev.get("content") or "")[:300].replace("\n", " ")
            self._append_to_assistant(frame, f"   {ok} {preview}", "#71717a")
        elif t == "token":
            self._append_to_assistant(frame, ev["content"], "#e8e8ea", inline=True)
        elif t == "final":
            pass  # already streamed via tokens
        elif t == "error":
            self._append_to_assistant(frame, f"❌ {ev['message']}", "#ef4444")

    # ----- UI helpers -----
    def _add_user_message(self, text: str):
        bubble = ctk.CTkFrame(self.chat_frame, fg_color="#fb923c", corner_radius=12)
        bubble.pack(anchor="e", padx=10, pady=6, fill=None)
        lbl = ctk.CTkLabel(
            bubble, text=text, text_color="#0a0a0c", font=("Segoe UI", 12),
            wraplength=700, justify="left",
        )
        lbl.pack(padx=14, pady=10)

    def _add_assistant_placeholder(self):
        bubble = ctk.CTkFrame(self.chat_frame, fg_color="#1a1a1e", corner_radius=12, border_width=1, border_color="#27272a")
        bubble.pack(anchor="w", padx=10, pady=6, fill="x")
        header = ctk.CTkLabel(bubble, text="🤖 Ajax", text_color="#fb923c", font=("Segoe UI", 11, "bold"))
        header.pack(anchor="w", padx=14, pady=(8, 0))
        return bubble

    def _append_to_assistant(self, bubble, text: str, color: str, bold: bool = False, inline: bool = False):
        font = ("Segoe UI", 12, "bold") if bold else ("Segoe UI", 12)
        if inline and bubble.winfo_children() and isinstance(bubble.winfo_children()[-1], ctk.CTkLabel):
            last = bubble.winfo_children()[-1]
            current = last.cget("text") or ""
            last.configure(text=current + text)
        else:
            lbl = ctk.CTkLabel(
                bubble, text=text, text_color=color, font=font,
                wraplength=850, justify="left", anchor="w",
            )
            lbl.pack(anchor="w", padx=14, pady=2, fill="x")
        self._scroll_bottom()

    def _add_system_message(self, text: str, error: bool = False):
        color = "#ef4444" if error else "#a1a1aa"
        lbl = ctk.CTkLabel(
            self.chat_frame, text=text, text_color=color, font=("Segoe UI", 12, "italic"),
            wraplength=900, justify="center",
        )
        lbl.pack(pady=20)
        self._scroll_bottom()

    def _scroll_bottom(self):
        self.chat_frame._parent_canvas.yview_moveto(1.0)


def main():
    app = AjaxDesktopApp()
    app.mainloop()


if __name__ == "__main__":
    main()
