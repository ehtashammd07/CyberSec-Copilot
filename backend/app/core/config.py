from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # App
    APP_NAME: str = "CyberSec Copilot"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Ollama
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "phi"          # phi3, phi3.5, phi3-mini also supported
    OLLAMA_TIMEOUT: int = 120             # seconds

    # Embeddings
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    VECTOR_DIM: int = 384

    # FAISS / RAG
    VECTOR_STORE_PATH: str = "vector_store/faiss_index"
    DOCUMENTS_PATH: str = "vector_store/documents.json"
    DATASET_PATH: str = "dataset/cybersec_kb.json"
    TOP_K_RESULTS: int = 5

    # CORS
    ALLOWED_ORIGINS: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
