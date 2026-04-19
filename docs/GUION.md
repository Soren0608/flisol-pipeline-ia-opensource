# 🎬 Guion de charla · FLISOL Pereira 2026

**Título:** Tu IA, tus datos, tu máquina — construyendo un ChatGPT colombiano en 45 minutos
**Duración:** 45 min
**Ponente:** Camilo · [@camilo_data](https://linkedin.com/in/camilo-data)

---

## ⏱️ Timing general

| Bloque | Min | Acumulado |
|---|---|---|
| Gancho de apertura | 3 | 3 |
| El problema real | 5 | 8 |
| Demo a ciegas | 7 | 15 |
| Ingeniería inversa | 15 | 30 |
| Preguntas del público | 8 | 38 |
| Cierre + reto | 5 | 43 |
| Q&A buffer | 2 | 45 |

---

## 🎭 Bloque 1 · Gancho (0:00 – 3:00)

**Acción en escenario:** entras sin presentarte. La UI ya está proyectada.

> *"Buenos días. Antes que nada, una pregunta."*

Escribes en vivo en la UI:
`¿Qué contratos ha firmado la alcaldía de Pereira este año?`

La IA responde con datos reales citando fuentes.

> *"Esto que acaban de ver es real. Son datos del portal de datos abiertos de Colombia, datos.gov.co. Pero aquí viene lo importante..."*

**GESTO DRAMÁTICO:** desconectas el wifi del portátil. Muestras la configuración de red.

> *"... lo acabo de hacer sin internet. Sin API key de OpenAI. Sin enviar un solo byte a un servidor en Virginia, Oregón o Dublín. Todo corre aquí."*

Señalas tu laptop.

> *"En los próximos 42 minutos, les voy a enseñar exactamente cómo. Y al final, van a tener el código para replicarlo esta misma noche."*

**Te presentas ahora, no antes.** Una línea, máximo.

> *"Soy Camilo, Data Engineer. Colombiano. Esto es FLISOL."*

---

## 🎭 Bloque 2 · El problema (3:00 – 8:00)

Cambias a un slide simple con una sola cifra grande.

### Slide: **$4,200 USD / mes**

> *"Esto es lo que gasta en promedio una empresa colombiana mediana en APIs de LLMs hoy. Cuatro mil dólares al mes. Dieciséis millones de pesos. Por leer sus propios datos."*

Pausa.

> *"Pero el dinero no es lo más grave. Lo grave es esto:"*

### Slide: **mapa de Colombia → flecha hacia EE.UU.**

> *"Cada consulta que hacen a GPT-4 manda sus datos — contratos, nóminas, información de clientes — a servidores en Estados Unidos. Y la Ley Patriot les da al FBI acceso a esos datos sin orden judicial."*

Pausa larga.

> *"La pregunta no es si puedes usar IA. La pregunta es quién controla tus datos cuando la usas."*

Cambias de tono, más optimista.

> *"La buena noticia: en 2026 ya no hace falta vender esa soberanía. Y en los próximos 35 minutos se los demuestro."*

---

## 🎭 Bloque 3 · Demo a ciegas (8:00 – 15:00)

**Filosofía:** en vez de explicar teoría primero, corres el pipeline completo. Que vean la magia funcionar antes de entender.

Abres terminal y ejecutas:

```bash
python scripts/demo_live.py
```

El script es teatral: banner animado, cada paso con loading spinners, respuestas en streaming. Tú narras por encima.

**Paso 1 — Ingesta:**
> *"Primero descargo datos públicos del portal de datos.gov.co. Contratos públicos, regalías, educación. Cinco mil contratos reales. Sin pagar. Sin pedir permiso. Son públicos."*

**Paso 2 — Transformación:**
> *"Ahora convierto esos datos tabulares en texto. ¿Por qué? Porque los modelos de lenguaje piensan en palabras, no en filas de Excel."*

**Paso 3 — Indexación:**
> *"Cada texto se convierte en un vector de 768 dimensiones. Esa matemática es lo que permite buscar por significado, no por palabras clave."*

**Paso 4 — Query en vivo:**
> *"Y ahora la magia:"*

Haces 2-3 preguntas preparadas. Streaming token por token. El público ve los fragmentos recuperados.

---

## 🎭 Bloque 4 · Ingeniería inversa (15:00 – 30:00)

Ahora sí la teoría. Pero al revés.

> *"Acaban de ver un sistema RAG funcionando. Vamos a destriparlo pieza por pieza."*

Abres el código en el editor (VS Code con tema oscuro, font grande).

### 4.1 · ¿Qué es RAG? (2 min)

Un slide único:

```
RAG = Retrieval-Augmented Generation

   pregunta → [buscar contexto] → [generar respuesta con ese contexto]
```

> *"Sin RAG: el modelo inventa cosas. Con RAG: el modelo usa TUS datos como fuente. La diferencia entre un estudiante que responde de memoria y uno que consulta un libro."*

### 4.2 · El retrieval (3 min)

Abres `src/rag.py`. Muestras la función `retrieve()`. 10 líneas.

> *"Esto es toda la magia. ChromaDB hace la búsqueda por similitud coseno. En 50 milisegundos me devuelve los 5 fragmentos más parecidos a mi pregunta."*

### 4.3 · Los embeddings (3 min)

Abres `src/index.py`.

> *"Pero, ¿cómo se parecen un texto y otro? Ahí entran los embeddings. Nomic-embed-text convierte cualquier texto en un punto en un espacio de 768 dimensiones. Textos con significado parecido quedan cerca en ese espacio."*

Muestras una visualización simple (slide).

### 4.4 · La generación (4 min)

Abres `src/rag.py`, función `generate_stream()`.

> *"El modelo que usamos es Llama 3.2, 3 mil millones de parámetros. Corre en mi laptop con 8GB de RAM. Es público, Meta lo liberó. Ollama es el wrapper que lo hace fácil de usar."*

Muestras el prompt que arma el sistema:

```
CONTEXTO: [los 5 fragmentos recuperados]
PREGUNTA: [lo que pidió el usuario]
RESPUESTA:
```

> *"Tan simple como eso."*

### 4.5 · Comparativa honesta (3 min)

Aquí ganas credibilidad. Slide con tabla comparando open-source vs propietario:

| | Open Source | OpenAI |
|---|---|---|
| Costo/mes | $0 | $4,200+ |
| Velocidad | media | alta |
| Calidad | 80% | 100% |
| Privacidad | 🟢 | 🔴 |
| Soberanía | 🟢 | 🔴 |

> *"No les voy a mentir: GPT-4 es mejor modelo. Pero el 80% de los casos de uso empresariales no necesitan ese 20% extra. Y ese 20% no justifica vender la soberanía de tus datos."*

---

## 🎭 Bloque 5 · Preguntas del público (30:00 – 38:00)

Esta es **LA parte memorable**.

> *"Acabamos de ver el sistema. Ahora rómpanlo. Quiero 3 preguntas del público. Las hago en vivo. Si falla, les muestro cómo debuggear RAG en vivo. Si funciona, aplauden."*

Abres un Slido (proyectado al lado) donde la gente manda preguntas desde el celular.

Tomas 3. Las escribes en la UI. Algunas van a fallar (el modelo dirá "no tengo esa información"). **Eso es parte del show.**

> *"Fíjense. Cuando el modelo no sabe, ADMITE que no sabe. Eso es lo que diferencia a un sistema RAG bien hecho de ChatGPT, que a veces inventa."*

---

## 🎭 Bloque 6 · Cierre (38:00 – 43:00)

Momento épico. Bajas el volumen del escenario.

> *"Hace 20 años, solo las corporaciones podían correr bases de datos relacionales. Hoy cualquiera corre PostgreSQL en su portátil."*

> *"Hace 10 años, solo las corporaciones podían hacer machine learning. Hoy cualquiera corre scikit-learn."*

> *"Hoy les estoy diciendo que solo las corporaciones dominan la IA generativa."*

Pausa larga.

> *"En 5 años eso va a ser ridículo."*

> *"Pero el cambio no lo hacen ellos. Lo hacemos nosotros."*

### Slide final: **EL RETO 30/30**

> *"En los próximos 30 días, quiero que cada uno de ustedes tome un dataset público de su ciudad. De su alcaldía. De su secretaría de salud. De la universidad. Y construyan su propio asistente soberano."*

> *"Etiquétenme en LinkedIn como @camilo_data. Entre todos armamos un mapa de IAs locales de Colombia. Una por ciudad. Una por universidad. Una por empresa."*

> *"El código está ahí:"*

**Slide con URL grande del repo.**

> *"MIT license. Hagan con él lo que quieran."*

---

## 🎭 Bloque 7 · Q&A (43:00 – 45:00)

> *"¿Preguntas?"*

> *"Pero con un twist. Pregúntenle primero a ella."*

Señalas la UI.

> *"Lo que ella no sepa, lo respondo yo."*

---

## 🎒 Checklist pre-charla

- [ ] Laptop cargada al 100% + cargador en escenario
- [ ] Ollama corriendo con llama3.2 y nomic-embed-text ya descargados
- [ ] Pipeline corrido previamente (`make all`) → ChromaDB con datos
- [ ] UI probada en resolución del proyector
- [ ] Slido o similar abierto en una pestaña aparte
- [ ] Plan B: `python scripts/plan_b.py` listo por si falla ollama
- [ ] Repo de GitHub público y URL corta copiada
- [ ] Camiseta con algo tipo "mis datos no viajan a EE.UU." 👕
- [ ] Respirar

---

## 🎤 Frases-bomba para cerrar momentos

- *"El software libre no es un hobby. Es soberanía tecnológica."*
- *"Si no pagas por el producto, el producto eres tú. Tus datos."*
- *"La nube de alguien más no es magia, es el servidor de alguien más."*
- *"RAG no es opcional. Es la forma honesta de usar IA generativa."*
- *"Un modelo que no puede decir 'no sé' es un mentiroso con esteroides."*

---

**github.com/camilo-data/flisol-rag**
