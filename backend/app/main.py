"""
CyberSec Copilot — FastAPI Application Entry Point
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.models.schemas import HealthResponse
from app.routes import chat, analyze
from app.services.llm_service import get_llm_service
from app.services.rag_service import get_rag_service

# ── logging ───────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)
settings = get_settings()


# ── lifespan ──────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown hooks."""
    logger.info("🚀 Starting %s v%s …", settings.APP_NAME, settings.APP_VERSION)

    # Warm up RAG (loads or builds FAISS index)
    rag = get_rag_service()
    await rag.initialise()

    # Quick Ollama connectivity check (non-blocking if offline)
    llm = get_llm_service()
    if await llm.is_available():
        logger.info("✅ Ollama connected — model: %s", settings.OLLAMA_MODEL)
    else:
        logger.warning(
            "⚠️  Ollama not reachable at %s. "
            "Start with: ollama serve && ollama pull %s",
            settings.OLLAMA_BASE_URL,
            settings.OLLAMA_MODEL,
        )

    yield  # ── application runs ──

    # Graceful shutdown
    await llm.close()
    logger.info("👋 CyberSec Copilot shut down cleanly.")


# ── app factory ───────────────────────────────────────────────────────────────

def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description=(
            "AI-powered cybersecurity assistant with RAG-backed knowledge, "
            "threat analysis, and Ollama LLM integration."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routers
    app.include_router(chat.router, prefix="/api/v1")
    app.include_router(analyze.router, prefix="/api/v1")

    # Health check
    @app.get(
        "/health",
        response_model=HealthResponse,
        tags=["System"],
        summary="Health check",
    )
    async def health() -> HealthResponse:
        llm = get_llm_service()
        rag = get_rag_service()
        return HealthResponse(
            status="ok",
            version=settings.APP_VERSION,
            ollama_connected=await llm.is_available(),
            vector_store_loaded=rag.embedding.is_loaded,
        )

    # Root
    @app.get("/", tags=["System"])
    async def root():
        return JSONResponse(
            {"message": f"Welcome to {settings.APP_NAME}", "docs": "/docs"}
        )

    return app


app = create_app()


# ── dev entrypoint ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info",
    )
