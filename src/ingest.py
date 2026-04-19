"""
Ingesta de datos abiertos colombianos vía Socrata Open Data API.

Fuente: https://www.datos.gov.co/
No requiere autenticación para consultas públicas.
"""
from __future__ import annotations

import json
import logging
import time
from pathlib import Path

import httpx

from src.config import DATA_SOURCES, RAW_DIR, DataSource

log = logging.getLogger("flisol.ingest")

SOCRATA_BASE = "https://www.datos.gov.co/resource"


def fetch_dataset(source: DataSource, timeout: float = 30.0) -> list[dict]:
    """Descarga un dataset completo como lista de registros JSON."""
    url = f"{SOCRATA_BASE}/{source.slug}.json"
    params = {"$limit": source.limit}

    log.info("⬇  Descargando %s (%s)", source.name, source.slug)
    started = time.perf_counter()

    with httpx.Client(timeout=timeout, follow_redirects=True) as client:
        response = client.get(url, params=params)
        response.raise_for_status()
        records = response.json()

    elapsed = time.perf_counter() - started
    log.info("✓  %d registros en %.2fs", len(records), elapsed)
    return records


def save_raw(source: DataSource, records: list[dict]) -> Path:
    """Persiste el JSON crudo para reproducibilidad."""
    path = RAW_DIR / f"{source.slug}.json"
    path.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    log.info("💾  Guardado en %s", path.relative_to(RAW_DIR.parent.parent))
    return path


def ingest_all() -> dict[str, int]:
    """Pipeline de ingesta completo. Devuelve resumen {dataset: n_registros}."""
    summary: dict[str, int] = {}

    for source in DATA_SOURCES:
        try:
            records = fetch_dataset(source)
            save_raw(source, records)
            summary[source.name] = len(records)
        except httpx.HTTPError as err:
            log.error("✗  Error en %s: %s", source.name, err)
            summary[source.name] = 0

    total = sum(summary.values())
    log.info("━" * 54)
    log.info("📊  TOTAL INGESTADO: %d registros de %d fuentes", total, len(summary))
    return summary


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s │ %(message)s",
        datefmt="%H:%M:%S",
    )
    ingest_all()
