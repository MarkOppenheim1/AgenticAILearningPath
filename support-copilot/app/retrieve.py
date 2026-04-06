# app/retrieve.py
from __future__ import annotations

from pathlib import Path
from typing import List

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from pathlib import Path

DOCS_DIR = Path("data/docs")
INDEX_PATH = "data/faiss_index"

_vectorstore: FAISS | None = None


def load_markdown_docs() -> List[Document]:
    """Load all markdown files from data/docs into LangChain Documents."""
    docs: List[Document] = []

    for path in DOCS_DIR.glob("*.md"):
        text = path.read_text(encoding="utf-8")
        docs.append(
            Document(
                page_content=text,
                metadata={"source": path.name}
            )
        )

    if not docs:
        raise ValueError(f"No markdown files found in {DOCS_DIR.resolve()}")

    return docs


def split_docs(docs: List[Document]) -> List[Document]:
    """Split documents into retrieval-friendly chunks."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=150,
        separators=["\n## ", "\n### ", "\n\n", "\n", " ", ""],
    )
    return splitter.split_documents(docs)


def build_vectorstore() -> FAISS:
    """Build a FAISS vector store from local markdown documents."""
    docs = load_markdown_docs()
    chunks = split_docs(docs)

    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    vectorstore = FAISS.from_documents(chunks, embeddings)

    vectorstore.save_local(INDEX_PATH)
    return vectorstore


def get_vectorstore() -> FAISS:
    global _vectorstore

    if _vectorstore is not None:
        return _vectorstore

    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

    if Path(INDEX_PATH).exists():
        _vectorstore = FAISS.load_local(
            INDEX_PATH,
            embeddings,
            allow_dangerous_deserialization=True
        )
    else:
        _vectorstore = build_vectorstore()

    return _vectorstore


def retrieve_chunks(query: str, k: int = 4) -> List[Document]:
    """Return the top-k most similar chunks."""
    vectorstore = get_vectorstore()
    return vectorstore.similarity_search(query, k=k)


def retrieve_context_strings(query: str, k: int = 4) -> List[str]:
    """
    Convenience wrapper for your graph state.
    Returns formatted strings with source names included.
    """
    docs = retrieve_chunks(query, k=k)

    results: List[str] = []
    for doc in docs:
        source = doc.metadata.get("source", "unknown")
        results.append(f"[SOURCE: {source}]\n{doc.page_content}")

    return results