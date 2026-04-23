"""Planner — Chain of Thought planning before tool execution.

A professional agent THINKS before acting. The planner produces a step-by-step
plan describing what tools will be called and why, BEFORE any tool is invoked.
"""
from __future__ import annotations
from typing import Optional


PLANNER_SYSTEM = """Você é o módulo de PLANEJAMENTO do Ajax, um agente de IA profissional.

Sua única função: dado um pedido do usuário e a lista de ferramentas disponíveis, escrever um PLANO claro
em até 5 passos numerados, antes de qualquer ferramenta ser chamada.

Regras CRÍTICAS:
1. NUNCA execute nada. Apenas planeje.
2. Pense como um engenheiro sênior: "Para responder isso, eu preciso primeiro X, depois Y, depois Z".
3. Para cada passo, mencione QUAL ferramenta usar e POR QUE.
4. Se a pergunta for trivial (cumprimento, dúvida conceitual, conversa), responda apenas: "DIRETO: <breve justificativa>"
5. Se precisar de informações que você não tem, planeje uma chamada de ferramenta para obtê-las.
6. Idioma: sempre Português do Brasil.
7. Seja conciso — máximo 5 passos.

Formato OBRIGATÓRIO:
PLANO:
1. [ferramenta] — descrição curta do que vai fazer e por quê
2. ...
3. ...

Exemplo BOM:
PLANO:
1. consultar_rag — buscar documentação sobre "decoradores em Python" pra dar uma resposta precisa
2. responder_final — sintetizar a resposta com exemplos de código

Exemplo de resposta direta:
DIRETO: pergunta conceitual simples, posso responder sem ferramentas.
"""


class Planner:
    def __init__(self, llm_router, observer=None):
        self.llm = llm_router
        self.observer = observer

    def plan(self, user_input: str, tool_names: list[str], session_id: str = "global") -> dict:
        """Returns {plan: str, direct: bool, raw: dict}."""
        tools_str = ", ".join(tool_names) if tool_names else "(nenhuma)"
        messages = [
            {"role": "system", "content": PLANNER_SYSTEM},
            {"role": "user", "content": (
                f"Ferramentas disponíveis: {tools_str}\n\n"
                f"Pedido do usuário:\n\"\"\"\n{user_input}\n\"\"\"\n\n"
                "Escreva o PLANO."
            )},
        ]
        result = self.llm.chat(messages, tools=None, temperature=0.2)
        content = (result.get("content") or "").strip()
        direct = content.upper().startswith("DIRETO")
        if self.observer:
            self.observer.log(
                session_id=session_id,
                type_="plan",
                name="cot_planner",
                duration_ms=int(result.get("elapsed", 0) * 1000),
                prompt_tokens=result.get("usage", {}).get("prompt_tokens", 0),
                completion_tokens=result.get("usage", {}).get("completion_tokens", 0),
                payload={"plan": content, "direct": direct},
            )
        return {"plan": content, "direct": direct, "raw": result}
