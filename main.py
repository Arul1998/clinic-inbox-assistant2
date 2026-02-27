import os
from functools import lru_cache
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from clinic_inbox_assistant.llm import LLMError, OpenAICompatibleClient, OpenAICompatibleConfig
from clinic_inbox_assistant.models import InboxAnalysisRequest, InboxAnalysisResponse
from clinic_inbox_assistant.pipeline import InboxAnalysisPipeline


class LLMSettings(BaseModel):
    api_key: str
    base_url: str
    model: str


@lru_cache(maxsize=1)
def get_llm_settings() -> LLMSettings:
    api_key = os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("LLM_BASE_URL") or os.getenv("OPENAI_BASE_URL") or "https://api.openai.com"
    model = os.getenv("LLM_MODEL") or os.getenv("OPENAI_MODEL") or "gpt-4o-mini"

    if not api_key:
        raise RuntimeError(
            "No LLM API key found. Set LLM_API_KEY or OPENAI_API_KEY in your environment."
        )

    return LLMSettings(api_key=api_key, base_url=base_url, model=model)


@lru_cache(maxsize=1)
def get_llm_client() -> OpenAICompatibleClient:
    settings = get_llm_settings()
    config = OpenAICompatibleConfig(
        api_key=settings.api_key,
        base_url=settings.base_url.rstrip("/"),
        model=settings.model,
    )
    return OpenAICompatibleClient(config)


def get_pipeline(
    llm_client: Annotated[OpenAICompatibleClient, Depends(get_llm_client)],
) -> InboxAnalysisPipeline:
    return InboxAnalysisPipeline(llm_client=llm_client)


app = FastAPI(
    title="Clinic Inbox Assistant",
    description=(
        "Prototype backend for a clinic inbox assistant inspired by the MedGemma Impact Challenge. "
        "Analyze patient messages, propose triage decisions, and draft safe replies for clinician review."
    ),
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.post("/analyze_message", response_model=InboxAnalysisResponse)
async def analyze_message(
    request: InboxAnalysisRequest,
    pipeline: Annotated[InboxAnalysisPipeline, Depends(get_pipeline)],
) -> InboxAnalysisResponse:
    try:
        return await pipeline.analyze(request)
    except LLMError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


__all__ = ["app"]

