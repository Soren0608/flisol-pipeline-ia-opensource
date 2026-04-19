# 🧠 Cómo funciona · línea por línea

Este documento es tu compañero de lectura después de la charla. Toma el código del repo y te explica **por qué** cada pieza está ahí, no solo qué hace.

---

## 1. Ingesta · `src/ingest.py`

### La idea

Los datos abiertos del Estado colombiano están expuestos vía la API **Socrata**, el mismo protocolo que usan ciudades como Nueva York o Chicago. Cada dataset tiene un `slug` único y se consulta con HTTP GET.

```python
url = f"{SOCRATA_BASE}/{source.slug}.json"
params = {"$limit": source.limit}
response = client.get(url, params=params)
```

### Por qué httpx y no requests

`httpx` es la versión moderna de `requests`. Misma API pero con soporte nativo para async, HTTP/2 y timeouts más granulares. Si mañana quieres paralelizar 10 descargas simultáneas, solo cambias `Client` por `AsyncClient`.

### Por qué guardamos el JSON crudo

Dos razones: **reproducibilidad** (puedes rehacer la transformación sin volver a descargar) y **auditoría** (si el pipeline falla, ves qué llegó vs qué se procesó).

---

## 2. Transformación · `src/transform.py`

### El problema central

Los datos tabulares no son buenos para embeddings. Un embedding de la fila:

```
{ "entidad": "Alcaldía de Pereira", "valor": "450000000", ... }
```

da un vector mediocre. En cambio, el embedding de:

```
"Contrato público firmado por la Alcaldía de Pereira, Risaralda.
Objeto: mantenimiento de vías. Valor: $450.000.000 COP."
```

captura mucho mejor el significado semántico.

### La función `format_*`

Cada fuente tiene su propio formateador porque cada tabla tiene su propio esquema. El patrón es siempre el mismo:

```python
def format_X(record, idx) -> Document:
    # 1. Extraer campos con defaults seguros
    campo = _get(record, "nombre_preferido", "nombre_alternativo")
    # 2. Componer prosa narrativa
    text = f"Contexto natural con {campo}..."
    # 3. Empaquetar en Document con metadata útil para filtrar después
    return Document(id=..., text=..., source=..., metadata={...})
```

### Chunking

Para registros cortos (menos de 512 palabras) no hace falta partir. Para textos largos, el solapamiento (`overlap=64`) garantiza que ideas que están a caballo entre dos chunks se capturen en ambos.

---

## 3. Embeddings · `src/index.py`

### Qué es un embedding

Una función mágica que convierte texto en un punto en un espacio de alta dimensión. Textos similares en significado terminan cerca en ese espacio.

```
"vías dañadas en Pereira"  →  [0.23, -0.11, 0.88, ...]  (768 números)
"mal estado de carreteras"  →  [0.21, -0.09, 0.85, ...]  ← vecino cercano
"receta de arepa"           →  [-0.55, 0.77, 0.12, ...]  ← muy lejos
```

### Por qué nomic-embed-text

Tres razones:
- **Open-source real** (Apache 2.0, pesos descargables)
- **Bueno en español** (entrenado multilingüe)
- **Rápido**: 768 dimensiones es un buen balance velocidad/calidad

Alternativas: `mxbai-embed-large` (1024 dim, más lento pero mejor), `all-MiniLM-L6-v2` (384 dim, más rápido pero peor en español).

### Por qué ChromaDB

- **Embebido**: no necesitas levantar un servidor separado (a diferencia de Qdrant, Weaviate, Milvus)
- **Persistente**: guarda en disco, sobrevive reinicios
- **API simple**: `add()`, `query()`, y listo

Para producción con millones de vectores, probablemente quieras Qdrant. Para esta demo, Chroma es perfecto.

### La clase `OllamaEmbedder`

Chroma permite pasar tu propia función de embedding. La nuestra simplemente llama al endpoint `/api/embeddings` de Ollama. Ventaja: cero dependencias pesadas (nada de `torch`, `transformers` ni `sentence-transformers`).

```python
def __call__(self, input: list[str]) -> list[list[float]]:
    vectors = []
    for text in input:
        response = self._client.post(
            f"{self.host}/api/embeddings",
            json={"model": self.model, "prompt": text}
        )
        vectors.append(response.json()["embedding"])
    return vectors
```

---

## 4. El corazón · `src/rag.py`

### La anatomía de una respuesta RAG

```
usuario pregunta
    │
    ▼
[1] RETRIEVE
    ├─ embedding de la pregunta
    ├─ búsqueda k-NN en ChromaDB
    └─ top-k chunks más similares
    │
    ▼
[2] AUGMENT
    └─ construir prompt con el contexto
    │
    ▼
[3] GENERATE
    └─ enviar prompt a Llama 3
    │
    ▼
respuesta
```

### El prompt: donde está el truco

Este es el prompt real del sistema:

```
Eres un asistente experto en datos abiertos de Colombia.
Respondes preguntas utilizando EXCLUSIVAMENTE la información del contexto entregado.

Reglas:
1. Si la respuesta no está en el contexto, di claramente: "No tengo esa información..."
2. Cita la fuente entre corchetes al final de cada afirmación
3. Responde en español, de forma clara y concisa
4. Cuando haya cifras, preséntalas con separadores de miles
5. Nunca inventes datos, nombres ni cifras
```

**Cada línea de este prompt previene un modo de falla específico:**
- La línea 1 previene que el modelo use su conocimiento previo en vez del contexto
- La línea 2 previene alucinaciones y da trazabilidad
- La línea 5 es redundante pero refuerza

### Por qué temperature=0.2

Para datos factuales queremos determinismo. Temperature alto (0.7-1.0) es para creatividad. Para respuestas que deben citar hechos, 0.0-0.3 es lo correcto.

### Streaming vs no-streaming

Para la UI usamos `generate_stream()` que yield tokens a medida que llegan. Para CLI usamos `generate()` que espera la respuesta completa. El streaming cambia la percepción de velocidad: un usuario que ve texto apareciendo tolera esperas 3x más largas que uno que mira una pantalla en blanco.

---

## 5. El servidor · `ui/server.py`

### Server-Sent Events vs WebSockets

Para streaming de un LLM, SSE es la elección correcta:
- **Unidireccional** (solo servidor → cliente): suficiente
- **HTTP estándar**: atraviesa proxies y firewalls sin drama
- **Reconnect automático**: el navegador lo hace solo
- **Simple**: no hace falta librería, funciona con `fetch()` + `ReadableStream`

Formato del evento:

```
event: token
data: {"t": "Hola"}

event: token
data: {"t": " mundo"}

event: done
data: {"latency_ms": 1240}
```

### Por qué FastAPI

Tres ventajas reales sobre Flask/Django:
- **Async nativo** (crucial para streaming)
- **Validación con Pydantic** (el `Question` BaseModel)
- **Docs automáticas** en `/docs`

---

## 6. Orquestación · `dags/flisol_rag_dag.py`

### Por qué Airflow para un pipeline de 3 pasos

Para **un solo** pipeline, Airflow es overkill. Un `cron` con bash funcionaría. Pero Airflow brilla cuando tienes:
- Retry logic con backoff exponencial
- Dependencias entre tareas (si una falla, las siguientes no corren)
- UI web para ver el historial
- Alertas por email / Slack
- Backfill automático

Y lo más importante: es **estándar en la industria**. Aprenderlo una vez te sirve en cualquier empresa de datos.

### El patrón del DAG

```python
start >> ingest >> transform >> index >> smoke_test >> end
```

El `>>` es azúcar sintáctica para `start.set_downstream(ingest)`. Define el grafo de dependencias. Airflow resuelve el orden, gestiona reintentos, registra métricas.

### El smoke test al final

Patrón importante: **siempre valida que el pipeline produjo algo usable**. El smoke test hace una pregunta de control. Si el RAG no responde, la tarea falla y te avisa. Mejor enterarte a las 3am que cuando un usuario pregunte.

---

## 7. Decisiones que parecen raras pero no lo son

### ¿Por qué no LangChain?

LangChain añade 50+ dependencias y abstracciones que cambian cada 3 meses. Para un RAG de producción, código directo como el nuestro es más mantenible. LangChain brilla cuando tienes flujos agénticos complejos con múltiples herramientas.

### ¿Por qué no un framework frontend?

La UI son ~500 líneas de HTML+CSS+JS vanilla. Agregar React sumaría 300KB de JS y un build step. Para una charla donde quiero mostrar "esto es simple", vanilla gana.

### ¿Por qué Python 3.11 y no 3.12?

Airflow todavía soporta mejor 3.11. En 2026 ya puedes moverte a 3.12 sin drama para este proyecto específico.

### ¿Por qué no Docker?

Para producción, sí. Para una demo en FLISOL donde queremos que la gente clone y corra en su laptop en 5 minutos, Docker añade fricción innecesaria. `make install && make all` basta.

---

## 8. Siguiente nivel — si quieres llevarlo más lejos

1. **Reranker**: después del retrieval inicial, usa un modelo pequeño (cross-encoder) para reordenar los top-20 a los mejores top-5. Mejora la calidad 15-30%.

2. **Query rewriting**: antes de buscar, pídele al LLM que reformule la pregunta en varias variantes. Busca con las 3 y funde resultados.

3. **Hybrid search**: combina búsqueda semántica (embeddings) con búsqueda lexical (BM25). ChromaDB no lo tiene nativo, tendrías que usar Qdrant o implementarlo manual.

4. **Citations granulares**: en vez de citar "Fuente: SECOP II", cita "Fuente: SECOP II / contrato CO1.PCCNTR.12345". Requiere propagar IDs desde la transformación.

5. **Feedback loop**: registra qué respuestas el usuario marcó como buenas/malas. Usa eso para ajustar el prompt o entrenar un reranker.

6. **Guardrails**: detecta cuando la pregunta es sobre algo fuera del scope (ej: "¿cómo hackeo una cuenta?") y rechaza antes de generar.

---

**github.com/camilo-data/flisol-rag**
