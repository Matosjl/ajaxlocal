"""Guardrails — security trilhos for SQL safety, prompt injection, and secret redaction."""
from __future__ import annotations
import re
from typing import Optional

# SQL: only SELECT statements allowed
SELECT_ONLY_PATTERN = re.compile(r"^\s*SELECT\b", re.IGNORECASE)
SQL_BLOCKED = ("INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE", "TRUNCATE", "GRANT", "REVOKE", "EXEC", "EXECUTE")

# Shell: dangerous commands
SHELL_BLOCKED_PATTERNS = [
    r"\brm\s+-rf\s+/\b",
    r"\bmkfs\b",
    r"\bdd\s+if=",
    r":\(\)\s*\{.*:\|:.*&\s*\}",  # fork bomb
    r"\bshutdown\b",
    r"\breboot\b",
    r">\s*/dev/sd",
]

# Secret patterns (redact in outputs)
SECRET_PATTERNS = [
    (re.compile(r"sk-[A-Za-z0-9_\-]{20,}"), "[REDACTED_API_KEY]"),
    (re.compile(r"sk-or-v1-[A-Za-z0-9]{30,}"), "[REDACTED_OPENROUTER_KEY]"),
    (re.compile(r"sb_(secret|publishable)_[A-Za-z0-9_\-]{20,}"), "[REDACTED_SUPABASE_KEY]"),
    (re.compile(r"postgres(?:ql)?://[^:]+:([^@]+)@"), r"postgres://[USER]:[REDACTED_PASSWORD]@"),
    (re.compile(r"AKIA[0-9A-Z]{16}"), "[REDACTED_AWS_KEY]"),
    (re.compile(r"ghp_[A-Za-z0-9]{30,}"), "[REDACTED_GITHUB_TOKEN]"),
    (re.compile(r"-----BEGIN [A-Z ]+PRIVATE KEY-----[\s\S]+?-----END [A-Z ]+PRIVATE KEY-----"), "[REDACTED_PRIVATE_KEY]"),
]

# Prompt injection signals
INJECTION_SIGNALS = [
    r"ignore (the|all|previous|above) (instructions|prompts?|rules?)",
    r"reveal (your|the) (system )?prompt",
    r"print (the|your) (system|developer) (prompt|message)",
    r"you are now (a|an) (different|new)",
    r"DAN mode",
    r"jailbreak",
    r"forget everything",
]
INJECTION_REGEX = re.compile("|".join(INJECTION_SIGNALS), re.IGNORECASE)


class Guardrails:
    """Validates inputs/outputs. Returns (allowed, reason)."""

    @staticmethod
    def validate_sql(query: str) -> tuple[bool, Optional[str]]:
        if not SELECT_ONLY_PATTERN.match(query or ""):
            return False, "ERRO DE SEGURANÇA: apenas comandos SELECT são permitidos."
        upper = (query or "").upper()
        for kw in SQL_BLOCKED:
            if re.search(rf"\b{kw}\b", upper):
                return False, f"ERRO DE SEGURANÇA: comando '{kw}' bloqueado."
        return True, None

    @staticmethod
    def validate_shell(command: str) -> tuple[bool, Optional[str]]:
        for pat in SHELL_BLOCKED_PATTERNS:
            if re.search(pat, command or "", re.IGNORECASE):
                return False, f"ERRO DE SEGURANÇA: comando bloqueado ('{pat}')."
        return True, None

    @staticmethod
    def validate_path(path: str, allowed_root: Optional[str] = None) -> tuple[bool, Optional[str]]:
        """Optional sandboxing: ensure path stays inside allowed_root."""
        if not allowed_root:
            return True, None
        import os
        try:
            real = os.path.realpath(path)
            root = os.path.realpath(allowed_root)
            if not real.startswith(root):
                return False, f"ERRO DE SEGURANÇA: caminho '{path}' fora do diretório permitido."
        except Exception as e:
            return False, f"ERRO ao validar caminho: {e}"
        return True, None

    @staticmethod
    def redact_secrets(text: str) -> str:
        if not text:
            return text
        out = text
        for pattern, replacement in SECRET_PATTERNS:
            out = pattern.sub(replacement, out)
        return out

    @staticmethod
    def detect_injection(user_input: str) -> tuple[bool, Optional[str]]:
        if user_input and INJECTION_REGEX.search(user_input):
            return True, "Tentativa de prompt injection detectada — instruções do sistema permanecem ativas."
        return False, None
