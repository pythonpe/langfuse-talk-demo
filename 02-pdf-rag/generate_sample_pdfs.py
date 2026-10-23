from pathlib import Path

from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer

DOCUMENTS_DIR = Path(__file__).parent / "documents"

DOCUMENTS = {
    "aprendizaje_basado_en_proyectos.pdf": {
        "title": "Guía práctica de aprendizaje basado en proyectos",
        "pages": [
            [
                (
                    "Qué es el aprendizaje basado en proyectos",
                    "El aprendizaje basado en proyectos (ABP) es una metodología "
                    "en la que el alumnado investiga y responde a una pregunta o "
                    "desafío auténtico. El resultado final es un producto público "
                    "que demuestra lo aprendido. El proyecto no es una actividad "
                    "añadida al final: es el vehículo principal del aprendizaje.",
                ),
                (
                    "Fases recomendadas",
                    "El proceso se organiza en cinco fases: planteamiento del reto, "
                    "investigación guiada, diseño de una solución, creación del "
                    "producto y presentación con reflexión final. Cada fase debe "
                    "tener un entregable breve y una oportunidad de retroalimentación.",
                ),
                (
                    "Rol docente y rol del alumnado",
                    "El docente diseña el reto, facilita recursos y formula preguntas. "
                    "El alumnado toma decisiones, distribuye responsabilidades, "
                    "documenta evidencias y revisa su trabajo. Los equipos eficaces "
                    "suelen tener entre tres y cinco integrantes.",
                ),
            ],
            [
                (
                    "Caso de ejemplo: proyecto Aula Verde",
                    "Aula Verde es un proyecto de ciencias para estudiantes de 13 a "
                    "14 años. Su reto es reducir el consumo de agua del centro "
                    "educativo. Dura seis semanas y se realiza en equipos de cuatro "
                    "personas. El producto final es una propuesta de ahorro respaldada "
                    "por mediciones y presentada ante el consejo escolar.",
                ),
                (
                    "Calendario de Aula Verde",
                    "La primera semana se dedica a formular hipótesis. Durante las "
                    "semanas dos y tres se mide el consumo. La cuarta semana se "
                    "analizan los datos; la quinta se diseña la propuesta; y la sexta "
                    "se presenta y evalúa el producto final.",
                ),
                (
                    "Evaluación del proyecto",
                    "La rúbrica de Aula Verde asigna 35 % a la calidad de las "
                    "evidencias, 30 % a la viabilidad de la propuesta, 20 % a la "
                    "comunicación y 15 % a la colaboración. Cada equipo completa "
                    "además una autoevaluación individual.",
                ),
            ],
        ],
    },
    "evaluacion_formativa.pdf": {
        "title": "Manual breve de evaluación formativa",
        "pages": [
            [
                (
                    "Propósito de la evaluación formativa",
                    "La evaluación formativa recoge evidencias durante el aprendizaje "
                    "para decidir cuál debe ser el siguiente paso. Su propósito no es "
                    "calificar, sino reducir la distancia entre la comprensión actual "
                    "y el objetivo. Requiere objetivos visibles, evidencias frecuentes "
                    "y ajustes oportunos de la enseñanza.",
                ),
                (
                    "Ciclo de trabajo",
                    "El ciclo tiene cuatro pasos: aclarar el objetivo, obtener una "
                    "evidencia, interpretarla y actuar. La acción puede consistir en "
                    "explicar de otra manera, ofrecer práctica adicional, formar "
                    "grupos temporales o permitir que el alumnado revise su producto.",
                ),
                (
                    "Técnicas rápidas",
                    "El ticket de salida pide una respuesta breve al terminar "
                    "la clase. "
                    "El semáforo usa verde, amarillo y rojo para expresar el nivel de "
                    "comprensión. Las pizarras individuales permiten observar las "
                    "respuestas de todo el grupo de forma simultánea.",
                ),
            ],
            [
                (
                    "Retroalimentación que ayuda a avanzar",
                    "Una retroalimentación útil responde tres preguntas: ¿hacia dónde "
                    "voy?, ¿cómo lo estoy haciendo? y ¿cuál es el siguiente paso? Debe "
                    "ser específica, comprensible y aplicable mientras todavía existe "
                    "tiempo para revisar el trabajo.",
                ),
                (
                    "Ejemplo de rutina semanal",
                    "El lunes se comparte el objetivo y un ejemplo de calidad. El "
                    "miércoles se aplica un ticket de salida de tres minutos. "
                    "El jueves "
                    "se forman grupos temporales según las necesidades detectadas. El "
                    "viernes cada estudiante revisa una producción y explica qué "
                    "cambió.",
                ),
                (
                    "Errores frecuentes",
                    "No toda corrección es formativa. Una nota sin orientación llega "
                    "demasiado tarde para mejorar. También conviene evitar comentarios "
                    "vagos como 'esfuérzate más' y recopilar datos que nunca se "
                    "utilizan "
                    "para adaptar la enseñanza.",
                ),
            ],
        ],
    },
}


def build_pdf(path: Path, title: str, pages: list[list[tuple[str, str]]]) -> None:
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "DocumentTitle",
        parent=styles["Title"],
        alignment=TA_CENTER,
        spaceAfter=24,
    )
    heading_style = styles["Heading2"]
    body_style = ParagraphStyle(
        "Body",
        parent=styles["BodyText"],
        leading=17,
        spaceAfter=14,
    )
    story = []

    for page_index, sections in enumerate(pages):
        if page_index == 0:
            story.extend([Paragraph(title, title_style), Spacer(1, 0.5 * cm)])
        for heading, body in sections:
            story.extend(
                [Paragraph(heading, heading_style), Paragraph(body, body_style)]
            )
        if page_index < len(pages) - 1:
            story.append(PageBreak())

    document = SimpleDocTemplate(
        str(path),
        pagesize=A4,
        rightMargin=2.5 * cm,
        leftMargin=2.5 * cm,
        topMargin=2.5 * cm,
        bottomMargin=2.5 * cm,
        title=title,
        author="Demo de observabilidad LLM",
    )
    document.build(story)


def main() -> None:
    DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)
    for filename, document in DOCUMENTS.items():
        path = DOCUMENTS_DIR / filename
        build_pdf(path, document["title"], document["pages"])
        print(f"Creado: {path}")


if __name__ == "__main__":
    main()
