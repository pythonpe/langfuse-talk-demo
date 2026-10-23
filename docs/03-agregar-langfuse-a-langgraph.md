# Tutorial: observar el workflow multiagente con Langfuse

Este escenario muestra el mayor valor de la observabilidad: una respuesta final
depende de varias decisiones, búsquedas, validaciones y posibles iteraciones.

## 1. Instrumentación mínima

Importa el cliente y el callback:

```python
from langfuse import get_client
from langfuse.langchain import CallbackHandler

langfuse = get_client()
langfuse_handler = CallbackHandler()
```

El grafo no necesita modificarse. El callback se añade al invocarlo:

```python
result = workflow.invoke(
    initial_state,
    config={
        "callbacks": [langfuse_handler],
        "run_name": "educational-research-workflow",
        "metadata": {
            "langfuse_session_id": session_id,
            "langfuse_tags": ["demo", "multi-agent", "research"],
        },
    },
)
```

LangGraph propaga el callback hacia los nodos y hacia las llamadas de LangChain
que se ejecutan dentro de ellos.

## 2. Qué representa la traza

La traza raíz corresponde a una investigación completa. Dentro aparecen:

- `orchestrator`: creación de preguntas de investigación;
- `research_agent`: preparación de consultas;
- `web_search`: búsquedas y resultados de Tavily;
- `validation_agent`: evaluación estructurada;
- la transición condicional y, si procede, otra iteración;
- `report_generator`: generación directa del documento HTML completo.

El adaptador se ejecuta mediante un `RunnableLambda` llamado `web-search`, de
modo que las búsquedas también formen parte de la jerarquía observable.

## 3. Ejecutar

```bash
docker compose up -d
uv run python 03-educational-research/research_with_langfuse.py
```

Usa como tema:

```text
Impacto de la IA generativa en la educación secundaria
```

Después abre **Tracing > Traces** en <http://localhost:3000> y localiza
`educational-research-workflow`.

## 4. Demostrar el bucle

En la traza, revisa la salida de `validation_agent`:

```json
{
  "approved": false,
  "issues": ["Falta evidencia sobre privacidad"],
  "missing_topics": ["Privacidad de estudiantes"],
  "feedback": "Buscar fuentes adicionales",
  "confidence": 0.65
}
```

Si la evidencia no es suficiente, la arista condicional regresa a
`research_agent`. Las nuevas consultas reciben `missing_topics` y `feedback`.

## 5. Interpretar correctamente la validación

La aprobación del agente no demuestra que una afirmación sea verdadera. El
ejemplo combina dos capas:

1. Comprobaciones deterministas de URLs, duplicados, referencias y cobertura.
2. Una evaluación semántica del LLM sobre calidad, suficiencia y contradicciones.

`confidence` es una estimación heurística del agente. No es una probabilidad
calibrada ni sustituye la revisión humana o la verificación factual externa.

## 6. Cerrar el cliente

La CLI debe enviar los últimos eventos antes de terminar:

```python
finally:
    langfuse.shutdown()
```
