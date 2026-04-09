from __future__ import annotations

from dotenv import load_dotenv
load_dotenv()

from datetime import datetime, UTC
from pathlib import Path
import uuid

from starlette.applications import Starlette
from starlette.routing import Mount

from mcp.server.fastmcp import FastMCP

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

# Mount at root of wherever the ASGI app mounts it
mcp = FastMCP("support-copilot-mcp")

DOCS_DIR = Path("data/docs")
INDEX_PATH = Path("data/faiss_index")

_vectorstore: FAISS | None = None


def load_markdown_docs() -> list[Document]:
    docs: list[Document] = []

    for path in DOCS_DIR.glob("*.md"):
        text = path.read_text(encoding="utf-8")
        docs.append(
            Document(
                page_content=text,
                metadata={"source": path.name},
            )
        )

    if not docs:
        raise ValueError(f"No markdown files found in {DOCS_DIR.resolve()}")

    return docs


def split_docs(docs: list[Document]) -> list[Document]:
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


@mcp.tool()
def retrieve_support_context(query: str, k: int = 4) -> str:
    """Retrieve relevant support-policy context from local markdown docs."""
    vectorstore = get_vectorstore()
    docs = vectorstore.similarity_search(query, k=k)

    if not docs:
        return "No relevant support documents found."

    parts: list[str] = []
    for i, doc in enumerate(docs, start=1):
        source = doc.metadata.get("source", "unknown")
        parts.append(f"[Chunk {i} | SOURCE: {source}]\n{doc.page_content}")

    return "\n\n".join(parts)


@mcp.tool()
def create_refund_ticket(user_query: str) -> str:
    ticket_id = f"refund-{uuid.uuid4().hex[:8]}"
    created_at = datetime.now(UTC).isoformat(timespec="seconds")
    return (
        f"Refund ticket created successfully.\n"
        f"Ticket ID: {ticket_id}\n"
        f"Created at: {created_at}\n"
        f"Reason: {user_query}"
    )


@mcp.tool()
def create_escalation_case(user_query: str) -> str:
    case_id = f"esc-{uuid.uuid4().hex[:8]}"
    created_at = datetime.now(UTC).isoformat(timespec="seconds")
    return (
        f"Escalation case created successfully.\n"
        f"Case ID: {case_id}\n"
        f"Created at: {created_at}\n"
        f"Summary: {user_query}"
    )

if __name__ == "__main__":
    get_vectorstore()  # optional warmup
    mcp.run(transport="streamable-http")