from typing import TypedDict

from pydantic import BaseModel, Field


class ResearchPlan(BaseModel):
    """Plan de investigación producido por el orquestador."""

    topic: str
    research_questions: list[str] = Field(min_length=3, max_length=6)


class SearchPlan(BaseModel):
    """Consultas que ejecutará el agente de investigación."""

    queries: list[str] = Field(min_length=1, max_length=6)


class Source(BaseModel):
    """Fuente web conservada en el estado compartido."""

    source_id: str
    url: str
    title: str
    snippet: str
    published_date: str | None = None


class Finding(BaseModel):
    """Afirmación vinculada a una pregunta y a fuentes concretas."""

    research_question: str
    claim: str
    source_ids: list[str] = Field(min_length=1)


class Findings(BaseModel):
    """Resultado estructurado del agente de investigación."""

    findings: list[Finding]


class ValidationResult(BaseModel):
    """Evaluación heurística de la evidencia recopilada."""

    approved: bool
    issues: list[str]
    missing_topics: list[str]
    feedback: str
    confidence: float = Field(ge=0, le=1)


class ResearchState(TypedDict, total=False):
    topic: str
    research_questions: list[str]
    search_queries: list[str]
    sources: list[dict]
    findings: list[dict]
    validation: dict
    iteration: int
    max_iterations: int
    report_path: str
