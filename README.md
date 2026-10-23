# Demos de aplicaciones LLM con observabilidad

Proyecto didáctico para construir tres ejemplos progresivos con LangChain,
LangGraph y Langfuse.

## Ejemplos

1. [`01-basic-chat`](01-basic-chat/README.md): chat por turnos con y sin Langfuse.
2. [`02-pdf-rag`](02-pdf-rag/README.md): chat RAG sobre documentos PDF.
3. [`03-educational-research`](03-educational-research/README.md): workflow
   multiagente de investigación educativa.

## Preparación

```bash
cp .env.example .env
uv sync
```

Después, añade tu `OPENROUTER_API_KEY` a `.env`.

## Calidad de código

```bash
uv run ruff format .
uv run ruff check .
```

La guía para añadir observabilidad al primer chat está en
[`docs/01-agregar-langfuse-al-chat.md`](docs/01-agregar-langfuse-al-chat.md).
