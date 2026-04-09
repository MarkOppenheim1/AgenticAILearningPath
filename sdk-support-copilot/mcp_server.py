from __future__ import annotations

from dotenv import load_dotenv
load_dotenv()

import logging
import os
import sys
import uuid
from datetime import datetime, UTC
from pathlib import Path

from starlette.requests import Request
from starlette.responses import JSONResponse

from mcp.server.fastmcp import FastMCP
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

# -----------------------------------------------------------------------------
# Logging
# -----------------------------------------------------------------------------

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    stream=sys.stderr,  # important: stderr, not stdout
)

logger = logging.getLogger("support_copilot_mcp")

# -----------------------------------------------------------------------------
# MCP server
# -----------------------------------------------------------------------------

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

    logger.info("Loaded %s markdown docs from %s", len(docs), DOCS_DIR.resolve())
    return docs


def split_docs(docs: list[Document]) -> list[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=150,
        separators=["\n## ", "\n### ", "\n\n", "\n", " ", ""],
    )
    chunks = splitter.split_documents(docs)
    logger.info("Split docs into %s chunks", len(chunks))
    return chunks


def build_vectorstore() -> FAISS:
    logger.info("Building FAISS vector store")
    docs = load_markdown_docs()
    chunks = split_docs(docs)

    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    vectorstore = FAISS.from_documents(chunks, embeddings)

    INDEX_PATH.mkdir(parents=True, exist_ok=True)
    vectorstore.save_local(str(INDEX_PATH))
    logger.info("Saved FAISS index to %s", INDEX_PATH.resolve())

    return vectorstore


def get_vectorstore() -> FAISS:
    global _vectorstore

    if _vectorstore is not None:
        return _vectorstore

    logger.info("Initializing vector store")
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

    faiss_file = INDEX_PATH / "index.faiss"
    pkl_file = INDEX_PATH / "index.pkl"

    if faiss_file.exists() and pkl_file.exists():
        logger.info("Loading FAISS index from disk")
        _vectorstore = FAISS.load_local(
            str(INDEX_PATH),
            embeddings,
            allow_dangerous_deserialization=True,
        )
    else:
        logger.info("No FAISS index found on disk; building a new one")
        _vectorstore = build_vectorstore()

    return _vectorstore


# -----------------------------------------------------------------------------
# MCP tools
# -----------------------------------------------------------------------------

@mcp.tool()
def retrieve_support_context(query: str, k: int = 4) -> str:
    """Retrieve relevant support-policy context from local markdown docs."""
    logger.info("Tool called: retrieve_support_context | query=%r | k=%s", query, k)

    vectorstore = get_vectorstore()
    docs = vectorstore.similarity_search(query, k=k)

    if not docs:
        logger.warning("No relevant support documents found for query=%r", query)
        return "No relevant support documents found."

    parts: list[str] = []
    for i, doc in enumerate(docs, start=1):
        source = doc.metadata.get("source", "unknown")
        parts.append(f"[Chunk {i} | SOURCE: {source}]\n{doc.page_content}")

    logger.info("Returning %s retrieved chunks for query=%r", len(docs), query)
    return "\n\n".join(parts)


@mcp.tool()
def create_refund_ticket(user_query: str) -> str:
    """Create a simulated refund ticket."""
    logger.info("Tool called: create_refund_ticket | user_query=%r", user_query)

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
    """Create a simulated escalation case."""
    logger.info("Tool called: create_escalation_case | user_query=%r", user_query)

    case_id = f"esc-{uuid.uuid4().hex[:8]}"
    created_at = datetime.now(UTC).isoformat(timespec="seconds")

    return (
        f"Escalation case created successfully.\n"
        f"Case ID: {case_id}\n"
        f"Created at: {created_at}\n"
        f"Summary: {user_query}"
    )


# -----------------------------------------------------------------------------
# Custom HTTP routes
# -----------------------------------------------------------------------------

@mcp.custom_route("/health", methods=["GET"])
async def health(_: Request) -> JSONResponse:
    return JSONResponse(
        {
            "status": "ok",
            "server": "support-copilot-mcp",
        }
    )


@mcp.custom_route("/ready", methods=["GET"])
async def ready(_: Request) -> JSONResponse:
    try:
        get_vectorstore()
        return JSONResponse(
            {
                "status": "ready",
                "vectorstore": "loaded",
            }
        )
    except Exception as e:
        logger.exception("Readiness check failed")
        return JSONResponse(
            {
                "status": "not_ready",
                "error": str(e),
            },
            status_code=503,
        )


if __name__ == "__main__":
    logger.info("Starting MCP server")
    get_vectorstore()  # optional warmup
    mcp.run(transport="streamable-http")