"""
DAG de Airflow: orquesta el pipeline de IA soberana de extremo a extremo.

    ingest → transform → index → validate

Schedule: diario a las 3am. Cada corrida actualiza la base vectorial
con los últimos datos de datos.gov.co.
"""
from __future__ import annotations

from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator

# Estos imports funcionan cuando el proyecto está en el PYTHONPATH de Airflow
from src.ingest import ingest_all
from src.transform import transform_all
from src.index import index_all
from src.rag import ask


# ─────────────────────────────────────────────────────────────────────
#  Configuración base
# ─────────────────────────────────────────────────────────────────────
default_args = {
    "owner": "camilo_data",
    "depends_on_past": False,
    "email_on_failure": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}


# ─────────────────────────────────────────────────────────────────────
#  Callables
# ─────────────────────────────────────────────────────────────────────
def task_ingest(**_) -> None:
    summary = ingest_all()
    print(f"📥  Ingesta completa: {summary}")


def task_transform(**_) -> None:
    docs = transform_all()
    print(f"🧩  Transformación completa: {len(docs)} documentos")


def task_index(**_) -> None:
    n = index_all(reset=True)
    print(f"🧠  Indexación completa: {n} vectores")


def task_smoke_test(**_) -> None:
    """Valida que el pipeline responde a una pregunta de control."""
    response = ask("¿Qué contratos públicos existen en Colombia?")
    assert response.answer, "El modelo no generó respuesta"
    assert response.chunks, "No se recuperaron fragmentos"
    print(f"✅  Smoke test OK · latencia {response.latency_ms}ms")


# ─────────────────────────────────────────────────────────────────────
#  Declaración del DAG
# ─────────────────────────────────────────────────────────────────────
with DAG(
    dag_id="flisol_rag_pipeline",
    description="Pipeline de IA open-source con datos abiertos colombianos",
    default_args=default_args,
    start_date=datetime(2026, 4, 1),
    schedule_interval="0 3 * * *",   # diario 3am
    catchup=False,
    tags=["flisol", "rag", "ollama", "chromadb", "datos-abiertos"],
) as dag:

    start = BashOperator(
        task_id="start",
        bash_command='echo "🚀  Iniciando pipeline FLISOL · $(date)"',
    )

    ingest = PythonOperator(
        task_id="ingest_datos_gov_co",
        python_callable=task_ingest,
    )

    transform = PythonOperator(
        task_id="transform_to_documents",
        python_callable=task_transform,
    )

    index = PythonOperator(
        task_id="index_to_chromadb",
        python_callable=task_index,
    )

    smoke_test = PythonOperator(
        task_id="smoke_test_rag",
        python_callable=task_smoke_test,
    )

    end = BashOperator(
        task_id="end",
        bash_command='echo "✅  Pipeline finalizado · $(date)"',
    )

    start >> ingest >> transform >> index >> smoke_test >> end
