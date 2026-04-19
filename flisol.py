#!/usr/bin/env python3
"""
flisol.py — Orquestador principal del pipeline RAG soberano.

Uso:
    python flisol.py setup      # descarga modelos ollama
    python flisol.py ingest     # datos.gov.co → raw/
    python flisol.py transform  # raw/ → documents.jsonl
    python flisol.py index      # documents → chromadb
    python flisol.py all        # ingest + transform + index
    python flisol.py serve      # levanta FastAPI + UI
    python flisol.py ask "tu pregunta"  # demo rápida en terminal
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from src.config import BANNER, LLM_MODEL, EMBEDDING_MODEL   # noqa: E402


# ─────────────────────────────────────────────────────────────────────
#  Salida con estilo
# ─────────────────────────────────────────────────────────────────────
class c:  # colores ANSI
    RESET = "\033[0m"
    DIM = "\033[2m"
    BOLD = "\033[1m"
    AMBER = "\033[38;5;214m"
    GREEN = "\033[38;5;114m"
    RED = "\033[38;5;203m"
    BLUE = "\033[38;5;75m"
    GREY = "\033[38;5;244m"


def banner():
    print(f"{c.AMBER}{BANNER}{c.RESET}")


def step(label: str):
    print(f"\n{c.AMBER}▸{c.RESET} {c.BOLD}{label}{c.RESET}")
    print(f"{c.DIM}{'─' * 60}{c.RESET}")


def ok(msg: str):
    print(f"  {c.GREEN}✓{c.RESET} {msg}")


def warn(msg: str):
    print(f"  {c.RED}!{c.RESET} {msg}")


# ─────────────────────────────────────────────────────────────────────
#  Comandos
# ─────────────────────────────────────────────────────────────────────
def cmd_setup(_args):
    banner()
    step("Verificando Ollama")
    try:
        subprocess.run(["ollama", "--version"], check=True, capture_output=True)
        ok("Ollama detectado")
    except (FileNotFoundError, subprocess.CalledProcessError):
        warn("Ollama no está instalado.")
        print(f"  {c.DIM}→ https://ollama.com/download{c.RESET}")
        sys.exit(1)

    step(f"Descargando modelos · {LLM_MODEL} + {EMBEDDING_MODEL}")
    for model in (LLM_MODEL, EMBEDDING_MODEL):
        print(f"  {c.BLUE}pull{c.RESET} {model}")
        subprocess.run(["ollama", "pull", model], check=True)
        ok(f"{model} listo")

    step("Todo preparado")
    print(f"  Ahora corre: {c.AMBER}python flisol.py all{c.RESET}")


def cmd_ingest(_args):
    banner()
    step("Ingestando datos.gov.co")
    from src.ingest import ingest_all
    ingest_all()


def cmd_transform(_args):
    banner()
    step("Transformando registros → documentos")
    from src.transform import transform_all
    transform_all()


def cmd_index(_args):
    banner()
    step(f"Indexando en ChromaDB con {EMBEDDING_MODEL}")
    from src.index import index_all
    index_all()


def cmd_all(args):
    banner()
    t0 = time.perf_counter()

    step("1/3 · INGESTA")
    from src.ingest import ingest_all
    ingest_all()

    step("2/3 · TRANSFORMACIÓN")
    from src.transform import transform_all
    transform_all()

    step("3/3 · INDEXACIÓN")
    from src.index import index_all
    index_all()

    elapsed = time.perf_counter() - t0
    print(f"\n{c.GREEN}{'═' * 60}{c.RESET}")
    print(f"{c.GREEN}  PIPELINE COMPLETO EN {elapsed:.1f}s · listo para demo{c.RESET}")
    print(f"{c.GREEN}{'═' * 60}{c.RESET}")
    print(f"\n  Levanta la UI con: {c.AMBER}python flisol.py serve{c.RESET}\n")


def cmd_serve(_args):
    banner()
    step("Levantando FastAPI en http://localhost:7860")
    import uvicorn
    uvicorn.run(
        "ui.server:app",
        host="0.0.0.0",
        port=7860,
        log_level="info",
        reload=False,
    )


def cmd_ask(args):
    banner()
    from src.rag import ask
    step(f"Pregunta: {args.question}")
    r = ask(args.question)
    print(f"\n{c.AMBER}🤖  Respuesta:{c.RESET}\n")
    print(r.answer)
    print(f"\n{c.DIM}─ {len(r.chunks)} fragmentos · {r.latency_ms}ms · {r.tokens_estimate} tokens ─{c.RESET}\n")


# ─────────────────────────────────────────────────────────────────────
#  CLI
# ─────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="FLISOL 2026 · Pipeline RAG soberano",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="github.com/camilo-data/flisol-rag",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("setup", help="verifica ollama y descarga modelos").set_defaults(fn=cmd_setup)
    sub.add_parser("ingest", help="descarga datasets de datos.gov.co").set_defaults(fn=cmd_ingest)
    sub.add_parser("transform", help="convierte raw json en documentos").set_defaults(fn=cmd_transform)
    sub.add_parser("index", help="indexa documentos en chromadb").set_defaults(fn=cmd_index)
    sub.add_parser("all", help="corre ingest + transform + index").set_defaults(fn=cmd_all)
    sub.add_parser("serve", help="levanta la UI en :7860").set_defaults(fn=cmd_serve)

    p_ask = sub.add_parser("ask", help="pregunta rápida por CLI")
    p_ask.add_argument("question", help="pregunta entre comillas")
    p_ask.set_defaults(fn=cmd_ask)

    args = parser.parse_args()
    args.fn(args)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{c.DIM}interrumpido{c.RESET}")
