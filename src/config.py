"""
╔══════════════════════════════════════════════════════════════════════╗
║  FLISOL 2026 · Pereira                                               ║
║  De los datos al diálogo: pipeline de IA open-source con datos reales║
║  @camilo_data                                                        ║
╚══════════════════════════════════════════════════════════════════════╝
"""
from pathlib import Path
from dataclasses import dataclass


# ─────────────────────────────────────────────────────────────────────
#  Rutas del proyecto
# ─────────────────────────────────────────────────────────────────────
ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
CHROMA_DIR = DATA_DIR / "chroma"

for _d in (RAW_DIR, PROCESSED_DIR, CHROMA_DIR):
    _d.mkdir(parents=True, exist_ok=True)


# ─────────────────────────────────────────────────────────────────────
#  Fuentes de datos abiertos colombianos
#  Todos los endpoints son públicos (portal datos.gov.co · Socrata API)
# ─────────────────────────────────────────────────────────────────────
@dataclass(frozen=True)
class DataSource:
    name: str
    slug: str              # id del dataset en Socrata
    description: str
    limit: int = 5_000


DATA_SOURCES: list[DataSource] = [
    DataSource(
        name="Contratos SECOP II",
        slug="jbjy-vk9h",
        description=(
            "Contratos de compra pública del Estado colombiano. "
            "Incluye entidad, objeto, valor, proveedor y municipio."
        ),
        limit=5_000,
    ),
    DataSource(
        name="Proyectos de regalías",
        slug="2pnw-mmge",
        description=(
            "Proyectos financiados con regalías en municipios de Colombia. "
            "Cobertura: salud, educación, vías, agua potable."
        ),
        limit=3_000,
    ),
    DataSource(
        name="Establecimientos educativos",
        slug="qijw-htwa",
        description=(
            "Directorio de instituciones educativas oficiales y privadas "
            "por municipio y departamento."
        ),
        limit=2_000,
    ),
]


# ─────────────────────────────────────────────────────────────────────
#  Modelos y servicios (todos locales · 0 API keys)
# ─────────────────────────────────────────────────────────────────────
OLLAMA_HOST = "http://localhost:11434"
LLM_MODEL = "llama3.2:3b"                    # ligero, cabe en 8GB RAM
EMBEDDING_MODEL = "nomic-embed-text"         # 768 dim, rápido, multilingüe

CHROMA_COLLECTION = "colombia_abierta"

# Parámetros de chunking y retrieval
CHUNK_SIZE = 512            # tokens aprox por fragmento
CHUNK_OVERLAP = 64
TOP_K = 5                   # documentos recuperados por query


# ─────────────────────────────────────────────────────────────────────
#  Banner para la consola — porque un CLI bonito también vende la charla
# ─────────────────────────────────────────────────────────────────────
BANNER = r"""
  ╔═╗╦  ╦╔═╗╔═╗╦    ┌─┐┌─┐┬─┐┌─┐┬┬─┐┌─┐
  ╠╣ ║  ║╚═╗║ ║║    ├─┘├┤ ├┬┘├┤ │├┬┘├─┤
  ╚  ╩═╝╩╚═╝╚═╝╩═╝  ┴  └─┘┴└─└─┘┴┴└─┴ ┴
         2026  ·  datos libres · ia soberana
"""
