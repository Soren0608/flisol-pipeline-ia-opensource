"""
Indexación de documentos en ChromaDB usando embeddings generados por Ollama.

ChromaDB corre embebido (persiste en disco), Ollama corre local en :11434.
Resultado: base vectorial 100% offline, soberana y reproducible.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

import chromadb
import httpx
from chromadb.config import Settings

from src.config import (
    CHROMA_COLLECTION,
    CHROMA_DIR,
    EMBEDDING_MODEL,
    OLLAMA_HOST,
    PROCESSED_DIR,
)

log = logging.getLogger("flisol.index")


# ─────────────────────────────────────────────────────────────────────
#  Embedding function que llama a Ollama directamente
#  (evita dependencias pesadas como sentence-transformers)
# ─────────────────────────────────────────────────────────────────────
class OllamaEmbedder:
    """Genera embeddings locales vía el endpoint /api/embeddings de Ollama."""

    def __init__(self, host: str = OLLAMA_HOST, model: str = EMBEDDING_MODEL):
        self.host = host
        self.model = model
        self._client = httpx.Client(timeout=60.0)

    def __call__(self, input: list[str]) -> list[list[float]]:  # noqa: A002
        vectors: list[list[float]] = []
        for text in input:
            response = self._client.post(
                f"{self.host}/api/embeddings",
                json={"model": self.model, "prompt": text},
            )
            response.raise_for_status()
            vectors.append(response.json()["embedding"])
        return vectors

    # Chroma requiere estos metadatos
    def name(self) -> str:
        return f"ollama-{self.model}"


# ─────────────────────────────────────────────────────────────────────
#  Cliente ChromaDB persistente
# ─────────────────────────────────────────────────────────────────────
def get_client() -> chromadb.PersistentClient:
    return chromadb.PersistentClient(
        path=str(CHROMA_DIR),
        settings=Settings(anonymized_telemetry=False),
    )


def get_collection(reset: bool = False):
    """Obtiene (o recrea) la colección vectorial."""
    client = get_client()
    embedder = OllamaEmbedder()

    if reset:
        try:
            client.delete_collection(CHROMA_COLLECTION)
            log.info("🗑   Colección anterior eliminada")
        except Exception:
            pass

    return client.get_or_create_collection(
        name=CHROMA_COLLECTION,
        embedding_function=embedder,
        metadata={"description": "FLISOL 2026 · datos abiertos Colombia"},
    )


# ─────────────────────────────────────────────────────────────────────
#  Indexación por lotes — muestra progreso en vivo
# ─────────────────────────────────────────────────────────────────────
def index_all(batch_size: int = 32, reset: bool = True) -> int:
    docs_path = PROCESSED_DIR / "documents.jsonl"
    if not docs_path.exists():
        raise FileNotFoundError(f"No existe {docs_path}. Corre transform primero.")

    documents: list[dict] = [
        json.loads(line) for line in docs_path.read_text(encoding="utf-8").splitlines()
    ]
    log.info("🧠  Indexando %d documentos con %s", len(documents), EMBEDDING_MODEL)

    collection = get_collection(reset=reset)

    total = len(documents)
    for start in range(0, total, batch_size):
        batch = documents[start : start + batch_size]
        collection.add(
            ids=[d["id"] for d in batch],
            documents=[d["text"] for d in batch],
            metadatas=[{"source": d["source"], **d["metadata"]} for d in batch],
        )
        pct = min(100, int((start + len(batch)) / total * 100))
        bar = "█" * (pct // 2) + "░" * (50 - pct // 2)
        print(f"\r  {bar}  {pct:3d}% ({start + len(batch)}/{total})", end="", flush=True)

    print()  # newline después de la barra
    log.info("✅  Índice listo. %d vectores en ChromaDB", collection.count())
    return collection.count()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s │ %(message)s",
        datefmt="%H:%M:%S",
    )
    index_all()
