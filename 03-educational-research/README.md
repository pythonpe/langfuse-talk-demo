# Investigación educativa multiagente

Workflow de LangGraph que planifica una investigación, busca fuentes web con
Tavily, valida las evidencias y solicita al modelo un reporte HTML completo.

## Grafo

```text
START -> orchestrator -> research_agent -> web_search -> validation_agent
                              ^                               |
                              +--------- evidencia NO --------+
                                                              |
                                                    evidencia SÍ o límite
                                                              |
                                                              v
                                                     report_generator -> END
```

El límite predeterminado es de dos iteraciones para controlar tiempo y coste.
Si no se obtiene aprobación, el reporte se genera indicando esa limitación.

## Configuración

Añade a `.env`:

```dotenv
TAVILY_API_KEY=tvly-...
MAX_RESEARCH_ITERATIONS=2
```

## Ejecutar sin observabilidad

```bash
uv run python 03-educational-research/research.py
```

## Ejecutar con Langfuse

```bash
docker compose up -d
uv run python 03-educational-research/research_with_langfuse.py
```

Tema sugerido:

```text
Impacto de la IA generativa en la educación secundaria
```

Los reportes se guardan en `03-educational-research/outputs/reports/`.

## Adaptador de búsqueda

`search.py` define el protocolo `WebSearchAdapter`. El workflow solo depende de
ese contrato, por lo que Tavily puede reemplazarse por un buscador simulado:

```python
class FakeSearchAdapter:
    def search(self, query: str, max_results: int = 3) -> list[dict]:
        return [{"url": "https://example.org", "title": "Ejemplo", ...}]
```

Esto permite hacer pruebas sin red ni consumo de API sin modificar el grafo.
