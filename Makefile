# ╔══════════════════════════════════════════════════════════════╗
# ║  FLISOL 2026 · Pereira · @camilo_data                        ║
# ║  Make targets para la demo en vivo                           ║
# ╚══════════════════════════════════════════════════════════════╝

.PHONY: help install setup ingest transform index all serve ask clean check

PYTHON := python3

help:
	@echo ""
	@echo "  ╔═╗╦  ╦╔═╗╔═╗╦    rag soberano"
	@echo "  ╠╣ ║  ║╚═╗║ ║║    comandos:"
	@echo "  ╚  ╩═╝╩╚═╝╚═╝╩═╝  "
	@echo ""
	@echo "  make install    → instala dependencias python"
	@echo "  make setup      → verifica ollama y descarga modelos"
	@echo "  make all        → corre ingest + transform + index"
	@echo "  make serve      → levanta la UI en :7860"
	@echo "  make ask Q='..' → pregunta rápida por CLI"
	@echo "  make check      → verifica que todo esté listo"
	@echo "  make clean      → borra data/ y chroma/"
	@echo ""

install:
	$(PYTHON) -m pip install -r requirements.txt

setup:
	$(PYTHON) flisol.py setup

ingest:
	$(PYTHON) flisol.py ingest

transform:
	$(PYTHON) flisol.py transform

index:
	$(PYTHON) flisol.py index

all:
	$(PYTHON) flisol.py all

serve:
	$(PYTHON) flisol.py serve

ask:
	@$(PYTHON) flisol.py ask "$(Q)"

check:
	@echo "▸ Verificando Ollama..."
	@ollama list || echo "  ! Ollama no responde"
	@echo ""
	@echo "▸ Verificando datos..."
	@ls -la data/raw/ 2>/dev/null || echo "  ! data/raw/ vacío"
	@echo ""
	@echo "▸ Verificando ChromaDB..."
	@ls -la data/chroma/ 2>/dev/null || echo "  ! data/chroma/ vacío"

clean:
	rm -rf data/raw/* data/processed/* data/chroma/*
	@echo "✓ workspace limpio"
