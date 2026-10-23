import os

from dotenv import load_dotenv
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
    result = workflow.invoke(
        {
            "topic": topic,
            "max_iterations": int(os.getenv("MAX_RESEARCH_ITERATIONS", "2")),
        },
        config={"recursion_limit": 20},
    )
    print(f"\nReporte disponible en: {result['report_path']}")


if __name__ == "__main__":
    main()
