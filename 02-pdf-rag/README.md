# Chat RAG sobre documentos PDF

Este escenario carga PDFs, divide su contenido en fragmentos, genera embeddings
locales, los almacena en Chroma y utiliza los fragmentos relevantes para
responder preguntas.

## Flujo

```text
PDFs -> PyPDFLoader -> fragmentos -> embeddings locales -> Chroma
                                                              |
pregunta -> embedding -> recuperación ------------------------+
                                                              |
                                     prompt + contexto -> LLM -> respuesta
```

## 1. Preparar los servicios

Desde la raíz:

```bash
docker compose up -d chroma
```

Para ejecutar también la variante observable:

```bash
docker compose up -d
```

## 2. Generar nuevamente los PDFs (opcional)

El repositorio ya contiene los dos documentos generados. Para recrearlos:

```bash
uv run python 02-pdf-rag/generate_sample_pdfs.py
```

## 3. Ingerir los documentos

```bash
uv run python 02-pdf-rag/ingest.py
```

La primera ejecución descarga el modelo multilingüe de embeddings. Cada
ejecución reemplaza el contenido de la colección para evitar duplicados.

## 4. Ejecutar el chat

Sin observabilidad:

```bash
uv run python 02-pdf-rag/rag_chat.py
```

Con Langfuse:

```bash
uv run python 02-pdf-rag/rag_chat_with_langfuse.py
```

Preguntas sugeridas:

```text
¿Cuánto dura el proyecto Aula Verde y cuál es su producto final?
¿Qué porcentaje de la rúbrica corresponde a la viabilidad?
¿Qué tres preguntas debe responder una retroalimentación útil?
¿Qué dice el documento sobre la fotosíntesis?
```

La última pregunta permite demostrar que el modelo debe reconocer cuándo la
respuesta no está en los documentos.
