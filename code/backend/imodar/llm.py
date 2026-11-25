"""Client for the local Ollama LLM endpoint."""

from __future__ import annotations

import json
from typing import Any

import httpx

from . import config


class OllamaClient:
    def __init__(
        self,
        base_url: str = config.OLLAMA_URL,
        model: str = config.OLLAMA_MODEL,
        timeout_s: float = config.OLLAMA_TIMEOUT_S,
        think: bool = config.OLLAMA_THINK,
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_s = timeout_s
        self.think = think
        self._http = httpx.Client(base_url=self.base_url, timeout=self.timeout_s)

    def is_alive(self) -> bool:
        try:
            r = self._http.get("/api/tags", timeout=5.0)
            return r.status_code == 200
        except Exception:
            return False

    def list_models(self) -> list[str]:
        try:
            r = self._http.get("/api/tags", timeout=5.0)
            if r.status_code == 200:
                data = r.json()
                return [m["name"] for m in data.get("models", [])]
        except Exception:
            pass
        return [self.model]

    def chat(
        self,
        messages: list[dict[str, str]],
        json_schema: dict[str, Any] | None = None,
        temperature: float = 0.0,
        think: bool | None = None,
    ) -> str:
        """Call Ollama /api/chat.

        If json_schema is provided, sets 'format' to enforce structured JSON output.
        """
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
            },
        }

        # Thinking toggle (for models like qwen3 / deepseek that support it)
        use_think = self.think if think is None else think
        payload["think"] = use_think

        if json_schema is not None:
            payload["format"] = json_schema

        try:
            resp = self._http.post("/api/chat", json=payload)
            resp.raise_for_status()
            data = resp.json()
            content = data.get("message", {}).get("content", "")
            return content.strip()
        except httpx.HTTPError as e:
            raise RuntimeError(f"Ollama request failed ({self.base_url}): {e}") from e

    def chat_json(
        self,
        messages: list[dict[str, str]],
        json_schema: dict[str, Any],
        temperature: float = 0.0,
        think: bool | None = None,
    ) -> dict[str, Any]:
        raw = self.chat(messages, json_schema=json_schema, temperature=temperature, think=think)
        # Parse JSON; sometimes models wrap in markdown code blocks even with schema
        cleaned = raw
        if "```json" in cleaned:
            cleaned = cleaned.split("```json", 1)[1].split("```", 1)[0].strip()
        elif "```" in cleaned:
            cleaned = cleaned.split("```", 1)[1].split("```", 1)[0].strip()

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as err:
            raise ValueError(f"Model output is not valid JSON:\nRaw:\n{raw}") from err
