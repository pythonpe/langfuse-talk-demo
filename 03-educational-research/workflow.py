import json
import re
import unicodedata
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal
from urllib.parse import urlparse

from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda
from langchain_openrouter import ChatOpenRouter
from langgraph.graph import END, START, StateGraph
from models import (
    Finding,
    Findings,
    ResearchPlan,
    ResearchState,
    SearchPlan,
    Source,
    ValidationResult,
)
from search import WebSearchAdapter

OUTPUT_DIR = Path(__file__).parent / "outputs" / "reports"


def valid_web_url(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def unique_strings(items: list[str]) -> list[str]:
    return list(dict.fromkeys(item.strip() for item in items if item.strip()))


def extract_html(text: str) -> str:
    normalized = text.lower()
    start = normalized.find("<!doctype html")
    if start == -1:
        start = normalized.find("<html")
    end = normalized.rfind("</html>")
    if start == -1 or end == -1 or end < start:
        raise ValueError("El modelo no devolvió un documento HTML completo")
    return text[start : end + len("</html>")]


def create_model() -> ChatOpenRouter:
    import os

    return ChatOpenRouter(
        model=os.getenv("OPENROUTER_MODEL", "deepseek/deepseek-v4.1-flash"),
        api_key=os.environ["OPENROUTER_API_KEY"],
        temperature=0.1,
    )


class ResearchWorkflow:
    def __init__(self, model: ChatOpenRouter, search_adapter: WebSearchAdapter) -> None:
        self.plan_model = model.with_structured_output(
            ResearchPlan, method="function_calling", strict=True
        )
        self.search_plan_model = model.with_structured_output(
            SearchPlan, method="function_calling", strict=True
        )
        self.findings_model = model.with_structured_output(
            Findings, method="function_calling", strict=True
        )
        self.validation_model = model.with_structured_output(
            ValidationResult, method="function_calling", strict=True
        )
        self.report_model = model | StrOutputParser()
        self.search_tool = RunnableLambda(
            lambda query: search_adapter.search(query), name="web-search"
        )

    def orchestrator(self, state: ResearchState) -> dict:
        print("[Orchestrator] Interpretando el tema y creando el plan...")
        plan = self.plan_model.invoke(
            """Actúa como orquestador de una investigación educativa.
            Descompón el tema en entre 3 y 6 preguntas concretas que cubran evidencia,
            beneficios, riesgos y recomendaciones. Conserva el tema original.

            Tema: """
            + state["topic"],
            config={"run_name": "orchestrator-plan"},
        )
        return {
            "topic": plan.topic,
            "research_questions": unique_strings(plan.research_questions),
            "sources": [],
            "findings": [],
            "iteration": 0,
            "validation": {},
        }

    def research_agent(self, state: ResearchState) -> dict:
        iteration = state.get("iteration", 0) + 1
        print(f"[Research Agent] Preparando búsquedas, iteración {iteration}...")
        validation = state.get("validation", {})
        search_plan = self.search_plan_model.invoke(
            """Actúa como investigador educativo. Genera consultas web precisas y
            variadas. Prioriza organismos públicos, universidades y revisiones
            sistemáticas. En una nueva iteración, atiende las observaciones
            del validador. No generes más de seis consultas.

            Tema: {topic}
            Preguntas: {questions}
            Temas faltantes: {missing}
            Feedback: {feedback}
            """.format(
                topic=state["topic"],
                questions=json.dumps(state["research_questions"], ensure_ascii=False),
                missing=json.dumps(
                    validation.get("missing_topics", []), ensure_ascii=False
                ),
                feedback=validation.get("feedback", "Primera investigación"),
            ),
            config={"run_name": "research-search-plan"},
        )
        return {
            "search_queries": unique_strings(search_plan.queries),
            "iteration": iteration,
        }

    def web_search(self, state: ResearchState) -> dict:
        queries = state["search_queries"]
        print(f"[Web Search] Ejecutando {len(queries)} consultas...")
        batches = self.search_tool.batch(queries)

        sources = [Source.model_validate(source) for source in state.get("sources", [])]
        known_urls = {source.url for source in sources}
        for results in batches:
            for result in results:
                url = str(result.get("url", "")).strip()
                if not valid_web_url(url) or url in known_urls:
                    continue
                sources.append(
                    Source(
                        source_id=f"S{len(sources) + 1}",
                        url=url,
                        title=str(result.get("title") or "Sin título"),
                        snippet=str(result.get("snippet") or "")[:1500],
                        published_date=result.get("published_date"),
                    )
                )
                known_urls.add(url)

        print(f"[Web Search] Fuentes únicas acumuladas: {len(sources)}")
        source_payload = [source.model_dump() for source in sources]
        extracted = self.findings_model.invoke(
            """Extrae hallazgos respaldados exclusivamente por las fuentes dadas.
            Cada hallazgo debe usar exactamente una pregunta de investigación y
            citar identificadores existentes. No inventes fuentes ni afirmaciones que no
            aparezcan en los fragmentos.

            Preguntas:
            {questions}

            Fuentes:
            {sources}
            """.format(
                questions=json.dumps(state["research_questions"], ensure_ascii=False),
                sources=json.dumps(source_payload, ensure_ascii=False),
            ),
            config={"run_name": "research-consolidate-findings"},
        )

        allowed_questions = set(state["research_questions"])
        allowed_sources = {source.source_id for source in sources}
        findings = []
        for finding in extracted.findings:
            source_ids = unique_strings(
                [item for item in finding.source_ids if item in allowed_sources]
            )
            if finding.research_question not in allowed_questions or not source_ids:
                continue
            findings.append(
                Finding(
                    research_question=finding.research_question,
                    claim=finding.claim,
                    source_ids=source_ids,
                ).model_dump()
            )

        return {"sources": source_payload, "findings": findings}

    def validation_agent(self, state: ResearchState) -> dict:
        print("[Validation Agent] Evaluando cobertura y referencias...")
        deterministic_issues = self._deterministic_checks(state)
        assessment = self.validation_model.invoke(
            """Actúa como validador crítico de una investigación educativa.
            Evalúa cobertura, suficiencia, contradicciones y respaldo de las
            afirmaciones. Tu confidence es una estimación heurística, no una
            calibrada. No declares veracidad factual independiente.

            Plan: {questions}
            Fuentes: {sources}
            Hallazgos: {findings}
            Comprobaciones deterministas: {issues}
            """.format(
                questions=json.dumps(state["research_questions"], ensure_ascii=False),
                sources=json.dumps(state["sources"], ensure_ascii=False),
                findings=json.dumps(state["findings"], ensure_ascii=False),
                issues=json.dumps(deterministic_issues, ensure_ascii=False),
            ),
            config={"run_name": "validation-assessment"},
        )

        issues = unique_strings(deterministic_issues + assessment.issues)
        approved = assessment.approved and not issues
        result = ValidationResult(
            approved=approved,
            issues=issues,
            missing_topics=unique_strings(assessment.missing_topics),
            feedback=assessment.feedback,
            confidence=assessment.confidence,
        )
        status = "aprobada" if approved else "requiere más investigación"
        print(
            f"[Validation Agent] Evidencia {status}; "
            f"confianza heurística: {result.confidence:.2f}"
        )
        return {"validation": result.model_dump()}

    def _deterministic_checks(self, state: ResearchState) -> list[str]:
        issues = []
        sources = [Source.model_validate(source) for source in state["sources"]]
        source_ids = {source.source_id for source in sources}
        urls = [source.url for source in sources]

        if len(urls) != len(set(urls)):
            issues.append("Existen fuentes duplicadas por URL")
        if any(not valid_web_url(url) for url in urls):
            issues.append("Existen fuentes con URL no válida")

        covered_questions = set()
        for finding_data in state["findings"]:
            finding = Finding.model_validate(finding_data)
            if not set(finding.source_ids).issubset(source_ids):
                issues.append("Existen hallazgos con referencias inexistentes")
            if finding.source_ids:
                covered_questions.add(finding.research_question)

        for question in state["research_questions"]:
            if question not in covered_questions:
                issues.append(f"Falta evidencia para: {question}")
        if len(sources) < 3:
            issues.append("Se requieren al menos tres fuentes web válidas")
        return unique_strings(issues)

    def route_after_validation(
        self, state: ResearchState
    ) -> Literal["research_agent", "report_generator"]:
        validation = state["validation"]
        if validation["approved"]:
            return "report_generator"
        if state["iteration"] >= state["max_iterations"]:
            print("[Orchestrator] Límite de iteraciones alcanzado; generando reporte.")
            return "report_generator"
        return "research_agent"

    def report_generator(self, state: ResearchState) -> dict:
        print("[Report Generator] Redactando y guardando el reporte HTML...")
        report_html = self.report_model.invoke(
            """Genera un documento HTML5 completo y autocontenido en español.
            **Devuelve exclusivamente HTML**, comenzando con <!doctype html>, sin
            bloques de Markdown ni explicaciones adicionales. Usa únicamente los
            hallazgos y fuentes proporcionados. Cita sus identificadores, por
            ejemplo [S1], y crea enlaces usando solamente las URLs recibidas.

            Incluye: título, resumen ejecutivo, introducción, preguntas de
            investigación, hallazgos, beneficios, riesgos y limitaciones,
            recomendaciones, conclusiones y referencias. Incluye CSS en <style>.
            Indica el resultado de la validación y aclara que la validación por
            LLM no equivale a una verificación factual independiente.

            Tema: {topic}
            Preguntas: {questions}
            Hallazgos: {findings}
            Validación: {validation}
            Fuentes: {sources}
            """.format(
                topic=state["topic"],
                questions=json.dumps(state["research_questions"], ensure_ascii=False),
                findings=json.dumps(state["findings"], ensure_ascii=False),
                validation=json.dumps(state["validation"], ensure_ascii=False),
                sources=json.dumps(state["sources"], ensure_ascii=False),
            ),
            config={"run_name": "report-content-generation"},
        )
        path = self._write_html(state["topic"], extract_html(report_html))
        print(f"[Report Generator] Reporte creado: {path}")
        return {"report_path": str(path)}

    def _write_html(self, topic: str, report_html: str) -> Path:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
        normalized = unicodedata.normalize("NFKD", topic)
        slug = re.sub(
            r"[^a-z0-9]+", "-", normalized.encode("ascii", "ignore").decode().lower()
        ).strip("-")
        path = OUTPUT_DIR / f"{slug or 'reporte'}-{timestamp}.html"
        path.write_text(report_html, encoding="utf-8")
        return path

    def compile(self):
        builder = StateGraph(ResearchState)
        builder.add_node("orchestrator", self.orchestrator)
        builder.add_node("research_agent", self.research_agent)
        builder.add_node("web_search", self.web_search)
        builder.add_node("validation_agent", self.validation_agent)
        builder.add_node("report_generator", self.report_generator)

        builder.add_edge(START, "orchestrator")
        builder.add_edge("orchestrator", "research_agent")
        builder.add_edge("research_agent", "web_search")
        builder.add_edge("web_search", "validation_agent")
        builder.add_conditional_edges(
            "validation_agent",
            self.route_after_validation,
            {
                "research_agent": "research_agent",
                "report_generator": "report_generator",
            },
        )
        builder.add_edge("report_generator", END)
        return builder.compile()
