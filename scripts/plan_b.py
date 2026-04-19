"""
plan_b.py — Modo offline de emergencia con respuestas cacheadas.

SI ALGO FALLA EN VIVO (sin wifi, sin ollama, sin chromadb):
    python scripts/plan_b.py

Carga respuestas pre-generadas y simula el streaming para que la demo
siga viéndose real. El público no sabe la diferencia.
"""
from __future__ import annotations

import asyncio
import json
import sys
import time
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


# ─────────────────────────────────────────────────────────────────────
#  Respuestas cacheadas (pre-generadas la noche anterior)
# ─────────────────────────────────────────────────────────────────────
CACHED = {
    "default": {
        "answer": (
            "Según los datos disponibles de datos.gov.co, existen múltiples "
            "contratos y proyectos públicos registrados en el sistema. Para "
            "una respuesta más precisa, es necesario consultar los fragmentos "
            "recuperados de la base vectorial [Fuente: datos.gov.co]."
        ),
        "chunks": [
            {"source": "Contratos SECOP II", "text": "Ejemplo de contrato público registrado.", "distance": 0.32, "municipio": "Pereira"},
        ],
    },
    "pereira": {
        "answer": (
            "En Pereira se han registrado contratos públicos por parte de la "
            "Alcaldía Municipal en sectores como obras públicas, salud y "
            "educación. Entre los proveedores recurrentes figuran empresas "
            "locales y nacionales [Fuente: Contratos SECOP II]."
        ),
        "chunks": [
            {"source": "Contratos SECOP II", "text": "Contrato público firmado por Alcaldía de Pereira en Pereira, Risaralda. Objeto: mantenimiento de vías urbanas.", "distance": 0.21, "municipio": "Pereira"},
            {"source": "Contratos SECOP II", "text": "Contrato público firmado por Secretaría de Salud en Pereira, Risaralda. Objeto: dotación de insumos hospitalarios.", "distance": 0.28, "municipio": "Pereira"},
        ],
    },
    "educacion": {
        "answer": (
            "Los proyectos de regalías en el sector educación cubren "
            "construcción y mejoramiento de infraestructura escolar, dotación "
            "de equipos tecnológicos y programas de alimentación en zonas "
            "rurales [Fuente: Proyectos de regalías]."
        ),
        "chunks": [
            {"source": "Proyectos de regalías", "text": "Proyecto 'Construcción sede educativa rural' en el sector educación, ejecutado en La Virginia, Risaralda.", "distance": 0.19, "municipio": "La Virginia"},
        ],
    },
}


def match_cache(question: str) -> dict:
    q = question.lower()
    if "pereira" in q or "alcald" in q:
        return CACHED["pereira"]
    if "educaci" in q or "escuela" in q or "instituci" in q:
        return CACHED["educacion"]
    return CACHED["default"]


# ─────────────────────────────────────────────────────────────────────
#  Servidor idéntico al real (misma API) pero offline
# ─────────────────────────────────────────────────────────────────────
app = FastAPI(title="FLISOL · Plan B (offline)")

UI_DIR = ROOT / "ui"


class Question(BaseModel):
    question: str


@app.post("/ask")
async def ask_stream(q: Question):
    data = match_cache(q.question)

    async def gen():
        # Fake retrieval
        yield _sse("chunks", {"items": data["chunks"]})
        await asyncio.sleep(0.6)  # simula latencia de búsqueda

        # Fake token streaming
        for word in data["answer"].split(" "):
            yield _sse("token", {"t": word + " "})
            await asyncio.sleep(0.04)  # velocidad de "typing" realista

        yield _sse("done", {"latency_ms": 1850, "chars": len(data["answer"]), "chunks": len(data["chunks"])})

    return StreamingResponse(gen(), media_type="text/event-stream")


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


@app.get("/")
async def index():
    return FileResponse(UI_DIR / "index.html")


if __name__ == "__main__":
    import uvicorn
    print("\n  ⚠  MODO PLAN B (offline) · respuestas cacheadas\n")
    uvicorn.run(app, host="0.0.0.0", port=7860, log_level="warning")
