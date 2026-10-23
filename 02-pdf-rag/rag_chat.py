import logging
import os
from operator import itemgetter
from pathlib import Path

from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableParallel
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_openrouter import ChatOpenRouter

SYSTEM_PROMPT = """Eres un asistente que responde preguntas sobre documentos educativos.
Usa exclusivamente el CONTEXTO recuperado para responder.
Si el contexto no contiene la respuesta, indica que no aparece en los documentos.
Cita las fuentes con el formato [archivo, página N].

CONTEXTO:
{context}"""


def create_embeddings() -> HuggingFaceEmbeddings:
    os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
    logging.getLogger("torch.distributed.elastic.multiprocessing.redirects").setLevel(
        logging.ERROR
    )
    return HuggingFaceEmbeddings(
        model_name=os.getenv(
            "EMBEDDING_MODEL",
            "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        ),
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )


def format_documents(documents: list[Document]) -> str:
    sections = []
    for document in documents:
        source = Path(document.metadata.get("source", "desconocido")).name
        page = int(document.metadata.get("page", 0)) + 1
        sections.append(f"[{source}, página {page}]\n{document.page_content}")
    return "\n\n".join(sections)


def create_chain():
    vector_store = Chroma(
        collection_name=os.getenv("CHROMA_COLLECTION", "educational_documents"),
        embedding_function=create_embeddings(),
        host=os.getenv("CHROMA_HOST", "localhost"),
        port=int(os.getenv("CHROMA_PORT", "8000")),
    )
    retriever = vector_store.as_retriever(search_kwargs={"k": 4})
    model = ChatOpenRouter(
        model=os.getenv("OPENROUTER_MODEL", "deepseek/deepseek-v4.1-flash"),
        api_key=os.environ["OPENROUTER_API_KEY"],
        temperature=0.1,
    )
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT),
            MessagesPlaceholder("history"),
            ("human", "{question}"),
        ]
    )
    inputs = RunnableParallel(
        context=itemgetter("question") | retriever | format_documents,
        question=itemgetter("question"),
        history=itemgetter("history"),
    )
    return inputs | prompt | model | StrOutputParser()


def main() -> None:
    load_dotenv(override=True)
    if not os.getenv("OPENROUTER_API_KEY"):
        raise RuntimeError("Falta OPENROUTER_API_KEY en el archivo .env")

    print("Cargando el modelo local de embeddings...")
    chain = create_chain()
    history: list[BaseMessage] = []

    print("Chat RAG sobre documentos PDF")
    print("Escribe 'salir' para terminar.\n")

    while True:
        try:
            question = input("Tú: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nHasta luego.")
            break

        if question.lower() in {"salir", "exit", "quit"}:
            print("Hasta luego.")
            break
        if not question:
            continue

        try:
            answer = chain.invoke({"question": question, "history": history})
        except Exception as error:
            print(f"Error al responder: {error}")
            continue

        history.extend([HumanMessage(content=question), AIMessage(content=answer)])
        print(f"Asistente: {answer}\n")


if __name__ == "__main__":
    main()
