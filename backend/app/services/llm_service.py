"""
LLM Service — Ollama integration (phi / phi3 / phi3.5)
Provides async generate_response() optimised for Microsoft Phi models.
Phi is a small but capable model — prompts are kept concise for best results.
"""
import httpx
import logging
from typing import AsyncGenerator

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class LLMService:
    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL
        self.model = settings.OLLAMA_MODEL
        self.timeout = settings.OLLAMA_TIMEOUT
        self._client: httpx.AsyncClient | None = None

    # ── lifecycle ────────────────────────────────────────────────────────────

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=httpx.Timeout(self.timeout),
            )
        return self._client

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    # ── health ───────────────────────────────────────────────────────────────

    async def is_available(self) -> bool:
        try:
            client = await self._get_client()
            resp = await client.get("/api/tags")
            return resp.status_code == 200
        except Exception:
            return False

    # ── core generation ──────────────────────────────────────────────────────

    async def generate_response(self, prompt: str) -> str:
        """
        Send prompt to Ollama Phi and return full text response.

        Phi-specific tuning:
          - temperature 0.2  (lower = more factual, phi benefits from this)
          - num_predict 1024 (phi is efficient; 1024 tokens is plenty)
          - repeat_penalty 1.1 (reduces phi's tendency to repeat phrases)

        Raises:
            ConnectionError  — Ollama not reachable
            RuntimeError     — Non-200 response
            TimeoutError     — Request timed out
        """
        client = await self._get_client()

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.2,       # phi is more precise at low temp
                "top_p": 0.9,
                "num_predict": 1024,      # phi is concise, 1024 is enough
                "repeat_penalty": 1.1,    # prevent phi from looping
                "stop": ["<|end|>", "<|user|>", "User:", "Human:"],  # phi stop tokens
            },
        }

        try:
            resp = await client.post("/api/generate", json=payload)
        except httpx.ConnectError as exc:
            logger.error("Ollama not reachable at %s", self.base_url)
            raise ConnectionError(
                f"Cannot connect to Ollama at {self.base_url}. "
                "Is Ollama running? (check system tray)"
            ) from exc
        except httpx.TimeoutException as exc:
            logger.error("Ollama request timed out after %ss", self.timeout)
            raise TimeoutError(
                f"Phi model did not respond within {self.timeout}s. "
                "Try reducing prompt length or restarting Ollama."
            ) from exc

        if resp.status_code != 200:
            logger.error("Ollama error %s: %s", resp.status_code, resp.text)
            raise RuntimeError(
                f"Ollama returned HTTP {resp.status_code}: {resp.text[:200]}"
            )

        data = resp.json()
        text: str = data.get("response", "").strip()

        if not text:
            raise RuntimeError("Phi returned an empty response.")

        logger.debug("LLM response (%d chars)", len(text))
        return text

    # ── streaming variant ────────────────────────────────────────────────────

    async def stream_response(self, prompt: str) -> AsyncGenerator[str, None]:
        """Yield response tokens one chunk at a time."""
        client = await self._get_client()

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": True,
            "options": {
                "temperature": 0.2,
                "top_p": 0.9,
                "repeat_penalty": 1.1,
                "stop": ["<|end|>", "<|user|>", "User:", "Human:"],
            },
        }

        try:
            async with client.stream("POST", "/api/generate", json=payload) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if line:
                        import json as _json
                        chunk = _json.loads(line)
                        token: str = chunk.get("response", "")
                        if token:
                            yield token
                        if chunk.get("done"):
                            break
        except httpx.ConnectError as exc:
            raise ConnectionError("Cannot connect to Ollama.") from exc


# ── singleton ─────────────────────────────────────────────────────────────────

_llm_service: LLMService | None = None


def get_llm_service() -> LLMService:
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service
