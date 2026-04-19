"""
Transformación de registros crudos a documentos listos para embedding.

Cada fuente tiene un formateador específico que convierte el JSON tabular
en texto narrativo denso, optimizado para que el modelo de embeddings
capture el contexto semántico.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from src.config import DATA_SOURCES, PROCESSED_DIR, RAW_DIR, CHUNK_SIZE, CHUNK_OVERLAP

log = logging.getLogger("flisol.transform")


# ─────────────────────────────────────────────────────────────────────
#  Estructura del documento
# ─────────────────────────────────────────────────────────────────────
@dataclass
class Document:
    """Unidad mínima que entra a la base vectorial."""
    id: str
    text: str
    source: str
    metadata: dict = field(default_factory=dict)


# ─────────────────────────────────────────────────────────────────────
#  Formateadores por fuente — convierten filas tabulares en prosa
# ─────────────────────────────────────────────────────────────────────
def _get(record: dict, *keys: str, default: str = "N/D") -> str:
    """Obtiene el primer valor no vacío de varias llaves posibles."""
    for k in keys:
        v = record.get(k)
        if v not in (None, "", "N/A"):
            return str(v).strip()
    return default


def format_secop(record: dict, idx: int) -> Document:
    entidad = _get(record, "nombre_entidad", "entidad")
    objeto = _get(record, "descripcion_del_proceso", "objeto_del_contrato")
    valor = _get(record, "valor_del_contrato", "cuantia_contrato")
    proveedor = _get(record, "proveedor_adjudicado", "nom_raz_social_contratista")
    municipio = _get(record, "ciudad", "municipio_entidad")
    departamento = _get(record, "departamento", "departamento_entidad")
    fecha = _get(record, "fecha_de_firma", "fecha_firma")

    text = (
        f"Contrato público firmado por {entidad} en {municipio}, {departamento}. "
        f"Objeto: {objeto}. "
        f"Proveedor adjudicado: {proveedor}. "
        f"Valor del contrato: {valor} COP. "
        f"Fecha de firma: {fecha}."
    )
    return Document(
        id=f"secop-{idx}",
        text=text,
        source="Contratos SECOP II",
        metadata={
            "entidad": entidad,
            "municipio": municipio,
            "departamento": departamento,
            "valor": valor,
        },
    )


def format_regalias(record: dict, idx: int) -> Document:
    nombre = _get(record, "nombre_proyecto", "nombre_del_proyecto")
    sector = _get(record, "sector", "sector_inversion")
    municipio = _get(record, "municipio", "municipio_ejecucion")
    departamento = _get(record, "departamento", "departamento_ejecucion")
    valor = _get(record, "valor_total", "valor_proyecto")
    estado = _get(record, "estado_proyecto", "estado")

    text = (
        f"Proyecto de regalías '{nombre}' en el sector {sector}, "
        f"ejecutado en {municipio}, {departamento}. "
        f"Valor total: {valor} COP. Estado actual: {estado}."
    )
    return Document(
        id=f"regalias-{idx}",
        text=text,
        source="Proyectos de regalías",
        metadata={
            "sector": sector,
            "municipio": municipio,
            "departamento": departamento,
            "estado": estado,
        },
    )


def format_educacion(record: dict, idx: int) -> Document:
    nombre = _get(record, "nombre_establecimiento", "nombre_institucion")
    municipio = _get(record, "municipio")
    departamento = _get(record, "departamento")
    sector = _get(record, "sector", "naturaleza")
    zona = _get(record, "zona")
    niveles = _get(record, "niveles", "niveles_educativos")

    text = (
        f"Institución educativa '{nombre}' ubicada en {municipio}, {departamento}. "
        f"Sector: {sector}. Zona: {zona}. "
        f"Niveles ofrecidos: {niveles}."
    )
    return Document(
        id=f"edu-{idx}",
        text=text,
        source="Establecimientos educativos",
        metadata={
            "municipio": municipio,
            "departamento": departamento,
            "sector": sector,
            "zona": zona,
        },
    )


FORMATTERS: dict[str, Callable[[dict, int], Document]] = {
    "jbjy-vk9h": format_secop,
    "2pnw-mmge": format_regalias,
    "qijw-htwa": format_educacion,
}


# ─────────────────────────────────────────────────────────────────────
#  Chunking con solapamiento por palabras
#  (simple, rápido, suficiente para registros cortos)
# ─────────────────────────────────────────────────────────────────────
def chunk_text(text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    words = text.split()
    if len(words) <= size:
        return [text]

    chunks: list[str] = []
    step = size - overlap
    for start in range(0, len(words), step):
        chunk = " ".join(words[start : start + size])
        if chunk:
            chunks.append(chunk)
        if start + size >= len(words):
            break
    return chunks


# ─────────────────────────────────────────────────────────────────────
#  Orquestador
# ─────────────────────────────────────────────────────────────────────
def transform_all() -> list[Document]:
    """Lee los JSON crudos y devuelve una lista unificada de Documents."""
    documents: list[Document] = []

    for source in DATA_SOURCES:
        raw_path = RAW_DIR / f"{source.slug}.json"
        if not raw_path.exists():
            log.warning("⚠  Falta %s — omitido", raw_path.name)
            continue

        records = json.loads(raw_path.read_text(encoding="utf-8"))
        formatter = FORMATTERS.get(source.slug)
        if formatter is None:
            log.warning("⚠  Sin formateador para %s", source.slug)
            continue

        for i, record in enumerate(records):
            doc = formatter(record, i)
            for j, chunk in enumerate(chunk_text(doc.text)):
                documents.append(
                    Document(
                        id=f"{doc.id}-c{j}",
                        text=chunk,
                        source=doc.source,
                        metadata=doc.metadata,
                    )
                )

        log.info("✓  %s → %d documentos procesados", source.name, len(records))

    # Persistir para auditoría
    out = PROCESSED_DIR / "documents.jsonl"
    with out.open("w", encoding="utf-8") as f:
        for d in documents:
            f.write(json.dumps(d.__dict__, ensure_ascii=False) + "\n")

    log.info("━" * 54)
    log.info("🧩  TOTAL DE DOCUMENTOS: %d", len(documents))
    log.info("💾  Guardados en %s", out.relative_to(RAW_DIR.parent.parent))
    return documents


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s │ %(message)s",
        datefmt="%H:%M:%S",
    )
    transform_all()
