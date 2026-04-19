<div align="center">

# 🇨🇴 colombia_abierta

### _De los datos al diálogo_
#### Pipeline de IA open-source con datos reales colombianos

**FLISOL 2026 · Pereira · [@camilo_data](https://linkedin.com/in/camilo-data)**

`python` · `airflow` · `chromadb` · `ollama` · `llama 3` · `fastapi`

---

> _Tu IA. Tus datos. Tu máquina._
> _Sin API keys. Sin nube. Sin que un solo byte salga de Colombia._

</div>

## 🎯 Qué es esto

Un pipeline completo de **Retrieval-Augmented Generation (RAG)** que corre 100% en tu máquina, usando únicamente herramientas open-source y datos abiertos del portal [datos.gov.co](https://www.datos.gov.co).

Haces preguntas en lenguaje natural sobre contratación pública, regalías y educación en Colombia — y un LLM local te responde citando las fuentes.

**Cero servicios de pago. Cero dependencia de Big Tech. Cero datos enviados a EE.UU.**

## 🏗️ Arquitectura

```
datos.gov.co  ──►  ingest  ──►  transform  ──►  chunk  ──►  embed  ──►  chromadb
                                                                             │
                                                                             ▼
         usuario  ──►  FastAPI  ──►  retrieve top-k  ──►  Llama 3  ──►  respuesta
                                                             ▲
                                                          Ollama
                                                        (localhost)
```

Todo orquestado por **Apache Airflow** con un DAG que se corre diario a las 3am.

## 🚀 Quick start (4 comandos)

```bash
# 1. Clonar e instalar
git clone https://github.com/camilo-data/flisol-rag
cd flisol-rag
make install

# 2. Descargar modelos de Ollama (una sola vez)
make setup

# 3. Correr el pipeline completo (ingest → transform → index)
make all

# 4. Levantar la UI
make serve
# → abre http://localhost:7860
```

## 🧪 Probar desde CLI

```bash
make ask Q="¿Qué contratos ha firmado la alcaldía de Pereira?"
```

## 📁 Estructura

```
flisol-rag/
├── flisol.py              # CLI orquestador
├── Makefile               # comandos rápidos
├── requirements.txt
│
├── src/
│   ├── config.py          # rutas, modelos, fuentes
│   ├── ingest.py          # datos.gov.co → raw/
│   ├── transform.py       # raw → documentos (con chunking)
│   ├── index.py           # embeddings + chromadb
│   └── rag.py             # retrieval + generación con llama 3
│
├── dags/
│   └── flisol_rag_dag.py  # orquestación con airflow
│
├── ui/
│   ├── server.py          # FastAPI con streaming SSE
│   └── index.html         # UI terminal brutalista
│
└── data/
    ├── raw/               # json crudo de datos.gov.co
    ├── processed/         # documentos listos para embedding
    └── chroma/            # base vectorial persistente
```

## 💡 Fuentes de datos

| Dataset | Slug Socrata | Registros |
|---|---|---|
| Contratos SECOP II | `jbjy-vk9h` | ~5,000 |
| Proyectos de regalías | `2pnw-mmge` | ~3,000 |
| Establecimientos educativos | `qijw-htwa` | ~2,000 |

Todas son fuentes públicas, sin autenticación. Cambia o agrega las que quieras en `src/config.py`.

## 🎨 Por qué cada herramienta

| Componente | Elección | Por qué |
|---|---|---|
| **LLM** | Llama 3.2 · 3B | cabe en 8GB RAM, multilingüe, respuestas rápidas |
| **Embeddings** | nomic-embed-text | 768 dim, buen español, corre local |
| **Vector DB** | ChromaDB | embebido, persistente, 0 config |
| **Runtime LLM** | Ollama | `curl` simple, modelos intercambiables |
| **Orquestación** | Airflow | estándar de la industria para pipelines |
| **UI** | FastAPI + vanilla JS | streaming SSE, 0 frameworks |

## 🧠 Cómo replicar con tus propios datos

1. Agrega tu fuente a `DATA_SOURCES` en `src/config.py`.
2. Escribe un formateador en `src/transform.py` (mira `format_secop` de referencia).
3. Corre `make all`.
4. Listo — tu dato ahora es consultable en lenguaje natural.

## 🏴 El reto de FLISOL 2026

En los próximos 30 días:

> Toma un dataset público de tu municipio o departamento. Úsalo para construir tu propio asistente soberano. Etiquétame en LinkedIn como [@camilo_data](https://linkedin.com/in/camilo-data) y juntos armamos un **mapa de IAs locales de Colombia**, una por ciudad.

## 📜 Licencia

MIT — haz con esto lo que quieras. Aprende, fórkealo, destrózalo, mejóralo.

---

<div align="center">

**hecho con ☕ en Cartago, Valle del Cauca**

`@camilo_data`

</div>
