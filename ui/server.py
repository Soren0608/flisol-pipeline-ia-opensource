"""
Servidor FastAPI que sirve la UI y expone el RAG con streaming SSE.

Arquitectura:
    Browser ←─ SSE ─→ FastAPI ─→ ChromaDB (retrieval)
                              ─→ Ollama    (generation)
"""
from __future__ import annotations

import asyncio
import json
import logging
import time
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from src.rag import retrieve, build_context, generate_stream

log = logging.getLogger("flisol.server")
logging.basicConfig(level=logging.INFO, format="%(asctime)s │ %(message)s", datefmt="%H:%M:%S")

app = FastAPI(title="FLISOL · Colombia Abierta")

UI_DIR = Path(__file__).resolve().parent


# ─────────────────────────────────────────────────────────────────────
#  Modelo de request
# ─────────────────────────────────────────────────────────────────────
class Question(BaseModel):
    question: str


# ─────────────────────────────────────────────────────────────────────
#  Endpoint principal con streaming (Server-Sent Events)
#  Cada token llega en tiempo real a la UI → efecto "typing" en vivo
# ─────────────────────────────────────────────────────────────────────
@app.post("/ask")
async def ask_stream(q: Question):
    """Stream RAG: envía fragments recuperados primero, luego tokens del LLM."""

    async def event_generator():
        started = time.perf_counter()

        # 1. Retrieval
        chunks = retrieve(q.question)
        yield _sse("chunks", {
            "items": [
                {
                    "source": c.source,
                    "text": c.text[:260] + ("…" if len(c.text) > 260 else ""),
                    "distance": round(c.distance, 4),
                    "municipio": c.metadata.get("municipio", ""),
                }
                for c in chunks
            ]
        })

        # 2. Generation streaming
        context = build_context(chunks)
        full = []
        for token in generate_stream(q.question, context):
            full.append(token)
            yield _sse("token", {"t": token})
            await asyncio.sleep(0)  # cede control al event loop

        latency_ms = int((time.perf_counter() - started) * 1000)
        yield _sse("done", {
            "latency_ms": latency_ms,
            "chars": sum(len(x) for x in full),
            "chunks": len(chunks),
        })

    return StreamingResponse(event_generator(), media_type="text/event-stream")


def _sse(event: str, data: dict) -> str:
    """Formato Server-Sent Events."""
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


# ─────────────────────────────────────────────────────────────────────
#  Stats globales: dólares ahorrados vs OpenAI
#  Cálculo: GPT-4o ≈ $2.50/1M input + $10/1M output tokens
# ─────────────────────────────────────────────────────────────────────
_stats = {"queries": 0, "tokens": 0, "saved_usd": 0.0}


@app.get("/stats")
async def stats():
    return _stats


@app.post("/stats/increment")
async def increment_stats(payload: dict):
    tokens = int(payload.get("tokens", 0))
    _stats["queries"] += 1
    _stats["tokens"] += tokens
    # estimación conservadora: mitad input, mitad output
    _stats["saved_usd"] += (tokens / 2) * 2.5e-6 + (tokens / 2) * 1e-5
    return _stats


# ─────────────────────────────────────────────────────────────────────
#  Servir la UI estática
# ─────────────────────────────────────────────────────────────────────
@app.get("/")
async def index():
    return FileResponse(UI_DIR / "index.html")


if (UI_DIR / "static").exists():
    app.mount("/static", StaticFiles(directory=UI_DIR / "static"), name="static")


# ─────────────────────────────────────────────────────────────────────
#  Entry point
# ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860, log_level="info")
