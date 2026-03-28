"""
Embedding Service
-----------------
Converts text → dense vectors via sentence-transformers and persists /
queries a FAISS index.
"""
import json
import logging
import os
from pathlib import Path
from typing import Optional

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class EmbeddingService:
    """Manages text embeddings and FAISS vector store."""

    def __init__(self):
        self.model_name = settings.EMBEDDING_MODEL
        self.vector_dim = settings.VECTOR_DIM
        self.index_path = Path(settings.VECTOR_STORE_PATH)
        self.docs_path = Path(settings.DOCUMENTS_PATH)

        self._model: Optional[SentenceTransformer] = None
        self._index: Optional[faiss.Index] = None
        self._documents: list[dict] = []

    # ── initialisation ───────────────────────────────────────────────────────

    def _load_model(self) -> SentenceTransformer:
        if self._model is None:
            logger.info("Loading embedding model: %s", self.model_name)
            self._model = SentenceTransformer(self.model_name)
        return self._model

    def _init_index(self) -> faiss.Index:
        """Return a new flat L2 index."""
        return faiss.IndexFlatL2(self.vector_dim)

    def load_or_create_index(self) -> None:
        """Load existing FAISS index + documents, or create empty ones."""
        index_file = self.index_path / "index.faiss"
        self.index_path.mkdir(parents=True, exist_ok=True)

        if index_file.exists() and self.docs_path.exists():
            logger.info("Loading existing FAISS index from %s", index_file)
            self._index = faiss.read_index(str(index_file))
            with open(self.docs_path, "r") as f:
                self._documents = json.load(f)
            logger.info("Loaded %d documents from vector store", len(self._documents))
        else:
            logger.info("No existing index found — initialising empty index")
            self._index = self._init_index()
            self._documents = []

    # ── encoding ─────────────────────────────────────────────────────────────

    def encode(self, texts: list[str]) -> np.ndarray:
        """
        Convert a list of strings to a float32 numpy array of shape (N, dim).
        """
        model = self._load_model()
        vectors = model.encode(
            texts,
            normalize_embeddings=True,
            show_progress_bar=False,
            batch_size=32,
        )
        return np.array(vectors, dtype=np.float32)

    # ── index management ─────────────────────────────────────────────────────

    def add_documents(self, documents: list[dict]) -> None:
        """
        Add documents to the FAISS index.

        Each document must have at least a ``text`` field.
        Optional fields: ``source``, ``title``, ``category``.
        """
        if not documents:
            return

        if self._index is None:
            self.load_or_create_index()

        texts = [doc["text"] for doc in documents]
        vectors = self.encode(texts)

        start_id = len(self._documents)
        self._index.add(vectors)
        self._documents.extend(documents)

        logger.info(
            "Added %d documents to index (total: %d)", len(documents), len(self._documents)
        )
        self._persist()

    def _persist(self) -> None:
        """Write index and documents to disk."""
        self.index_path.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self._index, str(self.index_path / "index.faiss"))
        self.docs_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.docs_path, "w") as f:
            json.dump(self._documents, f, indent=2)
        logger.debug("Persisted FAISS index (%d vectors)", self._index.ntotal)

    # ── similarity search ────────────────────────────────────────────────────

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        """
        Return *top_k* most relevant documents for *query*.

        Returns a list of dicts with original document fields plus:
          - ``score``  — L2 distance (lower = more similar)
          - ``rank``   — 1-indexed position
        """
        if self._index is None:
            self.load_or_create_index()

        if self._index.ntotal == 0:
            logger.warning("Vector store is empty — no results returned")
            return []

        query_vec = self.encode([query])
        distances, indices = self._index.search(query_vec, min(top_k, self._index.ntotal))

        results = []
        for rank, (idx, dist) in enumerate(zip(indices[0], distances[0]), start=1):
            if idx == -1:
                continue
            doc = dict(self._documents[idx])
            doc["score"] = float(dist)
            doc["rank"] = rank
            results.append(doc)

        return results

    # ── properties ───────────────────────────────────────────────────────────

    @property
    def is_loaded(self) -> bool:
        return self._index is not None and self._index.ntotal > 0

    @property
    def document_count(self) -> int:
        return len(self._documents)


# ── singleton ─────────────────────────────────────────────────────────────────

_embedding_service: EmbeddingService | None = None


def get_embedding_service() -> EmbeddingService:
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
