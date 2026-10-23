# Tutorial: observar el chat RAG con Langfuse

Esta guía parte de [`02-pdf-rag/rag_chat.py`](../02-pdf-rag/rag_chat.py) y
explica los cambios presentes en
[`rag_chat_with_langfuse.py`](../02-pdf-rag/rag_chat_with_langfuse.py).

Antes de comenzar, completa el tutorial del primer escenario para levantar
Langfuse y configurar `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY` y
`LANGFUSE_BASE_URL` en `.env`.

## 1. Qué interesa observar en un sistema RAG

Una respuesta RAG tiene al menos dos operaciones relevantes:

1. **Retrieval:** transforma la pregunta en un embedding y recupera fragmentos.
2. **Generation:** envía la pregunta y el contexto recuperado al LLM.

Observar solamente la llamada al modelo no permite saber si una respuesta
incorrecta se debe al LLM o a documentos poco relevantes. Por eso el retriever
forma parte de la cadena LCEL y recibe el mismo callback que el modelo.

## 2. Importar e inicializar Langfuse

Añade los imports:

```python
from uuid import uuid4

from langfuse import get_client
from langfuse.langchain import CallbackHandler
```

Después de crear la cadena:

```python
chain = create_chain()
langfuse = get_client()
langfuse_handler = CallbackHandler()
session_id = str(uuid4())
```

## 3. Instrumentar la cadena completa

La versión sin observabilidad utiliza:

```python
answer = chain.invoke({"question": question, "history": history})
```

Añade el callback y los metadatos:

```python
answer = chain.invoke(
    {"question": question, "history": history},
    config={
        "callbacks": [langfuse_handler],
        "run_name": "pdf-rag-turn",
        "metadata": {
            "langfuse_session_id": session_id,
            "langfuse_tags": ["demo", "pdf-rag"],
        },
    },
)
```

La configuración se propaga por los componentes de LangChain. Langfuse puede
mostrar la jerarquía completa del turno: preparación de entradas, retriever,
prompt, llamada al modelo y parser de salida.

## 4. Garantizar el envío de trazas

Envuelve el bucle en `try/finally` y cierra el cliente:

```python
try:
    # Bucle del chat
    ...
finally:
    langfuse.shutdown()
```

## 5. Ejecutar la demostración

```bash
docker compose up -d
uv run python 02-pdf-rag/ingest.py
uv run python 02-pdf-rag/rag_chat_with_langfuse.py
```

Pregunta:

```text
¿Cuánto dura el proyecto Aula Verde y cuál es su producto final?
```

Después abre **Tracing > Traces** en <http://localhost:3000> y localiza
`pdf-rag-turn`.

## 6. Qué revisar en Langfuse

- Los fragmentos retornados por el retriever.
- El archivo y la página almacenados en los metadatos.
- El contexto final incluido en el system prompt.
- La respuesta y sus citas.
- La latencia de recuperación frente a la generación.
- Los tokens de entrada, que ahora incluyen el contexto documental.
- La agrupación de varios turnos bajo una misma sesión.

Para ilustrar un fallo de recuperación, pregunta por un asunto ausente, como la
fotosíntesis. La traza permite comprobar qué fragmentos se recuperaron y por qué
el prompt obliga al modelo a reconocer que no tiene evidencia suficiente.
