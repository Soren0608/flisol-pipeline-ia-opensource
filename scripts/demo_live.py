"""
demo_live.py — Demo dramática para el escenario de FLISOL.

Corre esto en una terminal grande durante la charla. Está diseñado para:
  1. Mostrar cada paso del pipeline en vivo con animaciones en consola
  2. Pausar entre pasos para que tú narres
  3. Terminar levantando la UI lista para las preguntas del público

Uso:
    python demo_live.py
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import BANNER


# ─────────────────────────────────────────────────────────────────────
#  Utilidades de teatro
# ─────────────────────────────────────────────────────────────────────
class T:
    RESET, DIM, BOLD = "\033[0m", "\033[2m", "\033[1m"
    AMBER = "\033[38;5;214m"
    GREEN = "\033[38;5;114m"
    CYAN = "\033[38;5;80m"
    RED = "\033[38;5;203m"
    BLUE = "\033[38;5;75m"
    YELLOW = "\033[38;5;220m"
    GREY = "\033[38;5;244m"


def type_out(text: str, speed: float = 0.015, color: str = ""):
    """Imprime texto letra por letra — efecto cinematográfico."""
    for ch in text:
        sys.stdout.write(color + ch + T.RESET)
        sys.stdout.flush()
        time.sleep(speed)
    print()


def loading(label: str, seconds: float = 2.0, color: str = T.AMBER):
    """Barra de progreso animada."""
    frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    n_frames = int(seconds * 10)
    for i in range(n_frames):
        frame = frames[i % len(frames)]
        sys.stdout.write(f"\r  {color}{frame}{T.RESET} {label}")
        sys.stdout.flush()
        time.sleep(0.1)
    sys.stdout.write(f"\r  {T.GREEN}✓{T.RESET} {label}" + " " * 20 + "\n")


def section(title: str, number: str = ""):
    print()
    print(f"{T.AMBER}{'━' * 70}{T.RESET}")
    prefix = f"{T.DIM}{number}{T.RESET}  " if number else "  "
    print(f"{prefix}{T.BOLD}{title}{T.RESET}")
    print(f"{T.AMBER}{'━' * 70}{T.RESET}")
    time.sleep(0.5)


def pause(prompt: str = "⏎ continuar"):
    print(f"\n{T.DIM}  [{prompt}]{T.RESET}", end="", flush=True)
    input()


# ─────────────────────────────────────────────────────────────────────
#  Acto 1 — el enemigo
# ─────────────────────────────────────────────────────────────────────
def acto_1_el_enemigo():
    print(f"{T.AMBER}{BANNER}{T.RESET}")
    time.sleep(1)

    type_out("  escenario: una empresa colombiana.", color=T.GREY)
    time.sleep(0.3)
    type_out("  necesita consultar sus propios datos con IA.", color=T.GREY)
    time.sleep(0.5)
    type_out("  opción A ▸  OpenAI GPT-4  ═══  $4,200 USD/mes", color=T.RED)
    time.sleep(0.3)
    type_out("  opción A ▸  + datos sensibles enviados a EE.UU.", color=T.RED)
    time.sleep(0.3)
    type_out("  opción A ▸  + vendor lock-in", color=T.RED)
    time.sleep(0.8)
    print()
    type_out("  opción B ▸  esta charla.", color=T.GREEN)
    time.sleep(1.0)
    pause("empezamos")


# ─────────────────────────────────────────────────────────────────────
#  Acto 2 — el pipeline
# ─────────────────────────────────────────────────────────────────────
def acto_2_pipeline():
    section("INGESTA · datos.gov.co", "[1/3]")
    print(f"  {T.DIM}fuente: portal oficial de datos abiertos de Colombia{T.RESET}")
    print(f"  {T.DIM}protocolo: Socrata Open Data API (público, sin auth){T.RESET}\n")

    time.sleep(0.5)
    from src.ingest import ingest_all
    summary = ingest_all()
    print()
    for name, n in summary.items():
        print(f"    {T.GREEN}▸{T.RESET} {name:<35} {T.AMBER}{n:>6,}{T.RESET} registros")
    pause()

    section("TRANSFORMACIÓN · chunking semántico", "[2/3]")
    print(f"  {T.DIM}json tabular → prosa densa optimizada para embeddings{T.RESET}\n")
    time.sleep(0.5)
    from src.transform import transform_all
    docs = transform_all()
    print()
    print(f"    {T.GREEN}▸{T.RESET} {len(docs):,} documentos listos para indexar")
    pause()

    section("INDEXACIÓN · ChromaDB + Ollama embeddings", "[3/3]")
    print(f"  {T.DIM}modelo: nomic-embed-text (768 dimensiones · local){T.RESET}")
    print(f"  {T.DIM}destino: ChromaDB persistente en disco{T.RESET}\n")
    time.sleep(0.5)
    from src.index import index_all
    n = index_all()
    print(f"\n    {T.GREEN}✓{T.RESET} {n:,} vectores en ChromaDB · {T.BOLD}0 bytes enviados a la nube{T.RESET}")
    pause()


# ─────────────────────────────────────────────────────────────────────
#  Acto 3 — la prueba
# ─────────────────────────────────────────────────────────────────────
PREGUNTAS_DEMO = [
    "¿Qué contratos públicos se han firmado en el departamento de Risaralda?",
    "Muéstrame proyectos de regalías en el sector educación.",
    "¿Cuáles son los proveedores más recurrentes del Estado colombiano?",
]


def acto_3_rag_en_vivo():
    section("PRUEBA DE FUEGO · preguntas al sistema", "[RAG]")
    print(f"  {T.DIM}desconecta el wifi ahora. esto corre 100% local.{T.RESET}\n")
    pause("probar")

    from src.rag import ask

    for i, q in enumerate(PREGUNTAS_DEMO, 1):
        print(f"\n  {T.CYAN}❯{T.RESET} {T.BOLD}{q}{T.RESET}")
        time.sleep(0.3)
        loading("recuperando contexto...", 0.8, T.CYAN)
        loading("generando respuesta con Llama 3...", 1.5, T.AMBER)

        response = ask(q)
        print(f"\n  {T.AMBER}🤖{T.RESET}  ", end="")
        type_out(response.answer, speed=0.008, color=T.RESET)
        print(f"\n    {T.DIM}↳ {len(response.chunks)} fragmentos · "
              f"{response.latency_ms}ms · "
              f"{T.GREEN}$0.00 USD{T.DIM} (sí, cero){T.RESET}")

        if i < len(PREGUNTAS_DEMO):
            pause("siguiente")


# ─────────────────────────────────────────────────────────────────────
#  Acto 4 — el llamado a la acción
# ─────────────────────────────────────────────────────────────────────
def acto_4_cierre():
    section("EL RETO · 30 días", "[→]")
    time.sleep(0.3)
    type_out("  toma un dataset público de tu ciudad.", speed=0.02, color=T.YELLOW)
    type_out("  construye tu propio asistente soberano.", speed=0.02, color=T.YELLOW)
    type_out("  etiquétame en LinkedIn como @camilo_data.", speed=0.02, color=T.YELLOW)
    type_out("  juntos armamos el mapa de IAs locales de Colombia.", speed=0.02, color=T.AMBER)
    print()
    print(f"  {T.GREEN}{'═' * 66}{T.RESET}")
    print(f"  {T.GREEN}  código · github.com/camilo-data/flisol-rag{T.RESET}")
    print(f"  {T.GREEN}{'═' * 66}{T.RESET}")
    print()
    type_out("  ¿preguntas? pregúntenle primero a ella.", speed=0.02, color=T.CYAN)
    type_out("  lo que no sepa, lo respondo yo.", speed=0.02, color=T.CYAN)
    print()
    pause("levantar la UI")


# ─────────────────────────────────────────────────────────────────────
#  Main
# ─────────────────────────────────────────────────────────────────────
def main():
    try:
        acto_1_el_enemigo()
        acto_2_pipeline()
        acto_3_rag_en_vivo()
        acto_4_cierre()

        # levanta la UI para la sesión interactiva con el público
        print(f"\n  {T.AMBER}▸ levantando UI en http://localhost:7860 ...{T.RESET}\n")
        import uvicorn
        uvicorn.run("ui.server:app", host="0.0.0.0", port=7860, log_level="warning")

    except KeyboardInterrupt:
        print(f"\n\n{T.DIM}  fin de la demo · gracias FLISOL{T.RESET}\n")


if __name__ == "__main__":
    main()
