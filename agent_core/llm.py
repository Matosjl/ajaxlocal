"""LLM Router — unified streaming interface for Ollama (local) and OpenRouter (cloud)."""
from __future__ import annotations
import os
import json
import time
from typing import AsyncIterator, Optional
import httpx
from openai import OpenAI


class LLMRouter:
    """Unified LLM client supporting both Ollama and OpenRouter with streaming + tool calls."""

    def __init__(
        self,
        provider: str = "openrouter",
        model: Optional[str] = None,
        openrouter_key: Optional[str] = None,
        ollama_url: str = "http://localhost:11434",
    ):
        self.provider = provider
        self.ollama_url = ollama_url.rstrip("/")
        self.openrouter_key = openrouter_key or os.environ.get("OPENROUTER_API_KEY", "")

        # Default models per provider
        if not model:
            if provider == "ollama":
                model = os.environ.get("OLLAMA_MODEL", "llama3.1")
            else:
                model = os.environ.get("OPENROUTER_MODEL", "openrouter/auto")
        self.model = model

        if provider == "openrouter":
            self.client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=self.openrouter_key or "missing",
            )
        else:
            self.client = None

    # ---------- Sync chat with tools (used by agent loop) ----------
    def chat(self, messages: list, tools: Optional[list] = None, temperature: float = 0.3) -> dict:
        """Returns {content, tool_calls, raw, usage} after a single round."""
        t0 = time.time()
        if self.provider == "openrouter":
            kwargs = {"model": self.model, "messages": messages, "temperature": temperature}
            if tools:
                kwargs["tools"] = tools
                kwargs["tool_choice"] = "auto"
            resp = self.client.chat.completions.create(**kwargs)
            msg = resp.choices[0].message
            usage = getattr(resp, "usage", None)
            return {
                "content": msg.content or "",
                "tool_calls": [
                    {
                        "id": tc.id,
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    }
                    for tc in (msg.tool_calls or [])
                ],
                "elapsed": time.time() - t0,
                "usage": {
                    "prompt_tokens": getattr(usage, "prompt_tokens", 0) if usage else 0,
                    "completion_tokens": getattr(usage, "completion_tokens", 0) if usage else 0,
                } if usage else {},
                "raw_message": msg,
            }
        else:
            # Ollama path
            return self._ollama_chat(messages, tools, temperature, t0)

    def _ollama_chat(self, messages: list, tools: Optional[list], temperature: float, t0: float) -> dict:
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": temperature},
        }
        if tools:
            payload["tools"] = tools
        with httpx.Client(timeout=180) as c:
            r = c.post(f"{self.ollama_url}/api/chat", json=payload)
            r.raise_for_status()
            data = r.json()
        msg = data.get("message", {})
        tool_calls = []
        for tc in msg.get("tool_calls", []) or []:
            fn = tc.get("function", {})
            tool_calls.append({
                "id": tc.get("id", f"call_{int(time.time()*1000)}"),
                "name": fn.get("name"),
                "arguments": json.dumps(fn.get("arguments", {})),
            })
        return {
            "content": msg.get("content", ""),
            "tool_calls": tool_calls,
            "elapsed": time.time() - t0,
            "usage": {
                "prompt_tokens": data.get("prompt_eval_count", 0),
                "completion_tokens": data.get("eval_count", 0),
            },
            "raw_message": msg,
        }

    # ---------- Streaming text generation (final answer) ----------
    def stream(self, messages: list, temperature: float = 0.3) -> AsyncIterator[str]:
        """Synchronous generator yielding text chunks."""
        if self.provider == "openrouter":
            stream = self.client.chat.completions.create(
                model=self.model, messages=messages, stream=True, temperature=temperature,
            )
            for chunk in stream:
                delta = chunk.choices[0].delta.content if chunk.choices else None
                if delta:
                    yield delta
        else:
            payload = {
                "model": self.model,
                "messages": messages,
                "stream": True,
                "options": {"temperature": temperature},
            }
            with httpx.stream("POST", f"{self.ollama_url}/api/chat", json=payload, timeout=180) as r:
                for line in r.iter_lines():
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                    except Exception:
                        continue
                    chunk = obj.get("message", {}).get("content", "")
                    if chunk:
                        yield chunk
                    if obj.get("done"):
                        break

    # ---------- Embeddings (for RAG) ----------
    def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings. Uses a tiny local fallback if no provider available."""
        if self.provider == "openrouter":
            # OpenRouter doesn't expose embeddings natively; we use a separate OpenAI-compatible
            # endpoint via OpenRouter's free embedding or a basic hash fallback.
            # For reliability, use a simple deterministic hash-based embedding (384d).
            return [self._hash_embed(t) for t in texts]
        else:
            try:
                with httpx.Client(timeout=60) as c:
                    out = []
                    for t in texts:
                        r = c.post(
                            f"{self.ollama_url}/api/embeddings",
                            json={"model": os.environ.get("OLLAMA_EMBED_MODEL", "nomic-embed-text"), "prompt": t},
                        )
                        r.raise_for_status()
                        out.append(r.json().get("embedding", []))
                    return out
            except Exception:
                return [self._hash_embed(t) for t in texts]

    @staticmethod
    def _hash_embed(text: str, dim: int = 384) -> list[float]:
        """Deterministic hash-based embedding fallback (works without external API)."""
        import hashlib
        import struct
        vec = [0.0] * dim
        for i, word in enumerate(text.lower().split()):
            h = hashlib.sha256(word.encode()).digest()
            for j in range(dim):
                vec[j] += struct.unpack("b", h[j % 32:j % 32 + 1])[0] / 128.0
        # Normalize
        norm = sum(v * v for v in vec) ** 0.5 or 1.0
        return [v / norm for v in vec]
