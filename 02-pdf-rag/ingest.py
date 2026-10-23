import hashlib
import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader

DOCUMENTS_DIR = Path(__file__).parent / "documents"


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


def create_vector_store() -> Chroma:
    return Chroma(
        collection_name=os.getenv("CHROMA_COLLECTION", "educational_documents"),
        embedding_function=create_embeddings(),
        host=os.getenv("CHROMA_HOST", "localhost"),
        port=int(os.getenv("CHROMA_PORT", "8000")),
    )


def load_pdfs() -> list[Document]:
    pdf_paths = sorted(DOCUMENTS_DIR.glob("*.pdf"))
    if not pdf_paths:
        raise RuntimeError(f"No se encontraron archivos PDF en {DOCUMENTS_DIR}")

    pages = []
    for pdf_path in pdf_paths:
        reader = PdfReader(pdf_path)
        pdf_pages = [
            Document(
                page_content=page.extract_text() or "",
                metadata={"source": pdf_path.name, "page": page_number},
            )
            for page_number, page in enumerate(reader.pages)
        ]
        pages.extend(pdf_pages)
        print(f"Cargado: {pdf_path.name} ({len(pdf_pages)} páginas)")
    return pages


def document_id(document) -> str:
    identity = (
        f"{document.metadata['source']}:{document.metadata.get('page', 0)}:"
        f"{document.metadata.get('start_index', 0)}"
    )
    return hashlib.sha256(identity.encode()).hexdigest()


def main() -> None:
    load_dotenv(override=True)
    pages = load_pdfs()
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=700,
        chunk_overlap=100,
        add_start_index=True,
    )
    chunks = splitter.split_documents(pages)

    print(f"Fragmentos generados: {len(chunks)}")
    print("Cargando el modelo local de embeddings...")
    vector_store = create_vector_store()
    vector_store.reset_collection()
    vector_store.add_documents(chunks, ids=[document_id(chunk) for chunk in chunks])

    print(
        f"Ingesta completada en la colección "
        f"'{os.getenv('CHROMA_COLLECTION', 'educational_documents')}'."
    )


if __name__ == "__main__":
    main()
