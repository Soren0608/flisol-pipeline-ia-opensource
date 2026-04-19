"""
Motor RAG: recupera contexto de ChromaDB y genera respuesta con Llama 3.

Este es el módulo que demuestra en vivo cómo funciona un sistema de
Retrieval-Augmented Generation extremo a extremo, sin servicios externos.
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass

import httpx

from src.config import LLM_MODEL, OLLAMA_HOST, TOP_K
from src.index import get_collection

log = logging.getLogger("flisol.rag")


# ─────────────────────────────────────────────────────────────────────
#  Estructuras de respuesta
# ─────────────────────────────────────────────────────────────────────
@dataclass
class RetrievedChunk:
    text: str
    source: str
    metadata: dict
    distance: float


@dataclass
class RagResponse:
    question: str
    answer: str
    chunks: list[RetrievedChunk]
    latency_ms: int
    tokens_estimate: int


# ─────────────────────────────────────────────────────────────────────
#  Prompt — pieza clave: fuerza al modelo a usar SOLO el contexto
# ─────────────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """Eres un asistente experto en datos abiertos de Colombia.
Respondes preguntas utilizando EXCLUSIVAMENTE la información del contexto entregado.

Reglas:
1. Si la respuesta no está en el contexto, di claramente: "No tengo esa información en los datos disponibles."
2. Cita la fuente entre corchetes al final de cada afirmación, así: [Fuente: nombre]
3. Responde en español, de forma clara y concisa.
4. Cuando haya cifras, preséntalas con separadores de miles.
5. Nunca inventes datos, nombres ni cifras.
"""

USER_TEMPLATE = """CONTEXTO:
{context}

PREGUNTA DEL USUARIO:
{question}

RESPUESTA:"""


# ─────────────────────────────────────────────────────────────────────
#  Retrieval
# ─────────────────────────────────────────────────────────────────────
def retrieve(question: str, k: int = TOP_K) -> list[RetrievedChunk]:
    """Busca los k fragmentos más similares a la pregunta."""
    collection = get_collection(reset=False)
    results = collection.query(query_texts=[question], n_results=k)

    chunks: list[RetrievedChunk] = []
    for text, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        chunks.append(
            RetrievedChunk(
                text=text,
                source=meta.get("source", "desconocida"),
                metadata=meta,
                distance=float(dist),
            )
        )
    return chunks


def build_context(chunks: list[RetrievedChunk]) -> str:
    """Formatea los chunks recuperados en un bloque de contexto numerado."""
    lines = []
    for i, c in enumerate(chunks, 1):
        lines.append(f"[{i}] ({c.source}) {c.text}")
    return "\n\n".join(lines)


# ─────────────────────────────────────────────────────────────────────
#  Generación con Ollama (streaming desactivado para simplicidad)
# ─────────────────────────────────────────────────────────────────────
def generate(question: str, context: str, model: str = LLM_MODEL) -> str:
    prompt = USER_TEMPLATE.format(context=context, question=question)

    with httpx.Client(timeout=120.0) as client:
        response = client.post(
            f"{OLLAMA_HOST}/api/chat",
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                "stream": False,
                "options": {
                    "temperature": 0.2,   # bajo = más determinista
                    "top_p": 0.9,
                    "num_ctx": 4096,
                },
            },
        )
        response.raise_for_status()
    return response.json()["message"]["content"].strip()


def generate_stream(question: str, context: str, model: str = LLM_MODEL):
    """Generador que produce tokens a medida que llegan (para UIs en vivo)."""
    prompt = USER_TEMPLATE.format(context=context, question=question)

    with httpx.Client(timeout=None) as client:
        with client.stream(
            "POST",
            f"{OLLAMA_HOST}/api/chat",
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                "stream": True,
                "options": {"temperature": 0.2, "num_ctx": 4096},
            },
        ) as response:
            for line in response.iter_lines():
                if not line:
                    continue
                import json as _json
                data = _json.loads(line)
                if data.get("done"):
                    break
                token = data.get("message", {}).get("content", "")
                if token:
                    yield token


# ─────────────────────────────────────────────────────────────────────
#  Orquestador público
# ─────────────────────────────────────────────────────────────────────
def ask(question: str, k: int = TOP_K) -> RagResponse:
    """Pipeline RAG completo: retrieve → augment → generate."""
    started = time.perf_counter()

    chunks = retrieve(question, k=k)
    context = build_context(chunks)
    answer = generate(question, context)

    latency_ms = int((time.perf_counter() - started) * 1000)
    tokens_estimate = len(answer.split()) + len(context.split())

    return RagResponse(
        question=question,
        answer=answer,
        chunks=chunks,
        latency_ms=latency_ms,
        tokens_estimate=tokens_estimate,
    )


# ─────────────────────────────────────────────────────────────────────
#  CLI para demos rápidas
# ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    preguntas_demo = [
        "¿Qué contratos públicos se han firmado en Pereira recientemente?",
        "¿Cuáles son los proyectos de regalías en el sector educación?",
        "Dame ejemplos de instituciones educativas en Risaralda.",
    ]

    for q in preguntas_demo:
        print(f"\n❓  {q}")
        r = ask(q)
        print(f"\n🤖  {r.answer}")
        print(f"\n⚡  {r.latency_ms}ms · {len(r.chunks)} fragmentos recuperados")
        print("─" * 60)
