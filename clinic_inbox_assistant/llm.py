from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional

import httpx
from pydantic import BaseModel


class LLMError(RuntimeError):
    pass


class LLMClient(ABC):
    @abstractmethod
    async def generate(self, prompt: str, **kwargs: Any) -> str:
        ...


@dataclass
class OpenAICompatibleConfig:
    api_key: str
    base_url: str
    model: str
    timeout: float = 30.0


class OpenAICompatibleClient(LLMClient):
    """
    Minimal client for any OpenAI-compatible chat completion API.

    This allows you to point the app at:
    - A hosted provider (e.g., OpenAI, DeepSeek, etc.)
    - Your own deployment of MedGemma or other models via an OpenAI-style server
    """

    def __init__(self, config: OpenAICompatibleConfig):
        self._config = config
        self._client = httpx.AsyncClient(
            base_url=config.base_url,
            headers={"Authorization": f"Bearer {config.api_key}"},
            timeout=config.timeout,
        )

    async def generate(self, prompt: str, **kwargs: Any) -> str:
        payload: Dict[str, Any] = {
            "model": self._config.model,
            "messages": [{"role": "user", "content": prompt}],
        }
        payload.update(kwargs)

        try:
            response = await self._client.post("/v1/chat/completions", json=payload)
        except httpx.HTTPError as exc:
            raise LLMError(f"Error calling LLM API: {exc}") from exc

        if response.status_code != 200:
            raise LLMError(
                f"LLM API returned status {response.status_code}: {response.text}"
            )

        data = response.json()
        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMError(f"Unexpected LLM response format: {data}") from exc


class AnalysisPrompt(BaseModel):
    system_instructions: str
    message_body: str
    thread_context: Optional[str] = None


def build_analysis_prompt(payload: AnalysisPrompt) -> str:
    """Create a single prompt string for the LLM."""
    parts = [
        payload.system_instructions.strip(),
        "",
        "---- PATIENT MESSAGE ----",
        payload.message_body.strip(),
    ]
    if payload.thread_context:
        parts.extend(
            [
                "",
                "---- PREVIOUS THREAD CONTEXT ----",
                payload.thread_context.strip(),
            ]
        )
    parts.append("")
    parts.append(
        "Return a concise analysis in structured JSON with keys: "
        "urgency, categories, clinician_summary, draft_patient_reply, "
        "safety_flags, escalate."
    )
    return "\n".join(parts)

