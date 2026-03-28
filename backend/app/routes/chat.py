"""
/chat endpoint — conversational cybersecurity assistant.
"""
import logging

from fastapi import APIRouter, Depends, HTTPException, status

from app.models.schemas import ChatRequest, ChatResponse
from app.services.llm_service import LLMService, get_llm_service
from app.services.rag_service import RAGService, get_rag_service
from app.utils.formatter import clean_llm_text
from app.utils.prompt_builder import build_chat_prompt
from app.core.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat", tags=["Chat"])
settings = get_settings()


@router.post(
    "",
    response_model=ChatResponse,
    summary="Cybersecurity chat assistant",
    description=(
        "Send a message and receive a cybersecurity-expert response. "
        "Optionally set `mode` to `attacker`, `defender`, or `explain`."
    ),
)
async def chat(
    request: ChatRequest,
    llm: LLMService = Depends(get_llm_service),
    rag: RAGService = Depends(get_rag_service),
) -> ChatResponse:
    logger.info("Chat request — mode=%s, len=%d", request.mode, len(request.message))

    # 1. Retrieve relevant context from vector store
    try:
        context, sources = rag.build_context_block(request.message)
        context_used = bool(context.strip())
    except Exception as exc:
        logger.warning("RAG retrieval failed: %s", exc)
        context, sources, context_used = "", [], False

    # 2. Build prompt
    prompt = build_chat_prompt(
        user_message=request.message,
        context=context,
        mode=request.mode,
    )

    # 3. Generate response
    try:
        raw = await llm.generate_response(prompt)
    except ConnectionError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        )
    except TimeoutError as exc:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=str(exc),
        )
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )

    return ChatResponse(
        response=clean_llm_text(raw),
        context_used=context_used,
        sources=sources,
        model=settings.OLLAMA_MODEL,
        session_id=request.session_id,
    )
