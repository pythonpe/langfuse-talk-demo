from typing import Protocol

from tavily import TavilyClient


class SearchResult(dict):
    """Resultado normalizado entregado al workflow."""


class WebSearchAdapter(Protocol):
    """Interfaz sustituible para cualquier proveedor de búsqueda."""

    def search(self, query: str, max_results: int = 3) -> list[SearchResult]: ...


class TavilySearchAdapter:
    """Adaptador de Tavily aislado del resto de la aplicación."""

    def __init__(self, api_key: str) -> None:
        self.client = TavilyClient(api_key=api_key)

    def search(self, query: str, max_results: int = 3) -> list[SearchResult]:
        response = self.client.search(
            query=query,
            search_depth="basic",
            max_results=max_results,
            include_answer=False,
            include_raw_content=False,
        )
        return [
            SearchResult(
                url=result.get("url", ""),
                title=result.get("title", "Sin título"),
                snippet=result.get("content", ""),
                published_date=result.get("published_date"),
            )
            for result in response.get("results", [])
        ]
