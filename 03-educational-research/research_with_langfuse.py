import os
from uuid import uuid4

from dotenv import load_dotenv
from langfuse import get_client
from langfuse.langchain import CallbackHandler
from search import TavilySearchAdapter
from workflow import ResearchWorkflow, create_model


def main() -> None:
    load_dotenv(override=True)
    if not os.getenv("OPENROUTER_API_KEY"):
        raise RuntimeError("Falta OPENROUTER_API_KEY en el archivo .env")
    if not os.getenv("TAVILY_API_KEY"):
        raise RuntimeError("Falta TAVILY_API_KEY en el archivo .env")

    topic = input("Tema educativo a investigar: ").strip()
    if not topic:
        raise RuntimeError("El tema no puede estar vacío")

    workflow = ResearchWorkflow(
        model=create_model(),
        search_adapter=TavilySearchAdapter(os.environ["TAVILY_API_KEY"]),
    ).compile()
    langfuse = get_client()
    langfuse_handler = CallbackHandler()
    session_id = str(uuid4())

    try:
        result = workflow.invoke(
            {
                "topic": topic,
                "max_iterations": int(os.getenv("MAX_RESEARCH_ITERATIONS", "2")),
            },
            config={
                "callbacks": [langfuse_handler],
                "run_name": "educational-research-workflow",
                "recursion_limit": 20,
                "metadata": {
                    "langfuse_session_id": session_id,
                    "langfuse_tags": ["demo", "multi-agent", "research"],
                },
            },
        )
        print(f"\nReporte disponible en: {result['report_path']}")
        print(f"Sesión de Langfuse: {session_id}")
    finally:
        langfuse.shutdown()


if __name__ == "__main__":
    main()
