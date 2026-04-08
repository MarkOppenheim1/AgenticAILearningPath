from __future__ import annotations

from pathlib import Path
from typing import List

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

DOCS_DIR = Path("data/docs")
INDEX_PATH = Path("data/faiss_index")

_vectorstore: FAISS | None = None


def load_markdown_docs() -> List[Document]:
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
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=150,
        separators=["\n## ", "\n### ", "\n\n", "\n", " ", ""],
    )
    return splitter.split_documents(docs)


def build_vectorstore() -> FAISS:
    docs = load_markdown_docs()
    chunks = split_docs(docs)

    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    vectorstore = FAISS.from_documents(chunks, embeddings)

    INDEX_PATH.mkdir(parents=True, exist_ok=True)
    vectorstore.save_local(str(INDEX_PATH))
    return vectorstore


def get_vectorstore() -> FAISS:
    global _vectorstore

    if _vectorstore is not None:
        return _vectorstore

    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

    faiss_file = INDEX_PATH / "index.faiss"
    pkl_file = INDEX_PATH / "index.pkl"

    if faiss_file.exists() and pkl_file.exists():
        _vectorstore = FAISS.load_local(
            str(INDEX_PATH),
            embeddings,
            allow_dangerous_deserialization=True,
        )
    else:
        _vectorstore = build_vectorstore()

    return _vectorstore


def retrieve_support_context(query: str, k: int = 4) -> str:
    vectorstore = get_vectorstore()
    docs = vectorstore.similarity_search(query, k=k)

    if not docs:
        return "No relevant support documents found."

    parts: list[str] = []
    for i, doc in enumerate(docs, start=1):
        source = doc.metadata.get("source", "unknown")
        parts.append(
            f"[Chunk {i} | SOURCE: {source}]\n{doc.page_content}"
        )

    return "\n\n".join(parts)