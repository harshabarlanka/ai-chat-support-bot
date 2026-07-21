import os

from mcp.server.fastmcp import FastMCP

from app.database import SessionLocal
from app.models.document import Document
from app.models.user import User
from app.services.chat import generate_answer
from app.services.retrieval import retrieve_relevant_chunks

mcp = FastMCP("AI Chat Support Bot")

MCP_USER_EMAIL = os.environ["MCP_USER_EMAIL"]


def _get_current_user(db):
    user = db.query(User).filter(User.email == MCP_USER_EMAIL).first()
    if user is None:
        raise ValueError(f"No user found with email {MCP_USER_EMAIL}")
    return user


@mcp.tool()
def list_documents() -> list[dict]:
    """List all documents uploaded by the user, with their processing status."""
    db = SessionLocal()
    try:
        user = _get_current_user(db)
        documents = db.query(Document).filter(Document.owner_id == user.id).all()
        return [{"id": str(d.id), "filename": d.filename, "status": d.status} for d in documents]
    finally:
        db.close()


@mcp.tool()
def search_documents(query: str) -> list[dict]:
    """Search the user's uploaded documents for relevant excerpts."""
    db = SessionLocal()
    try:
        user = _get_current_user(db)
        chunks = retrieve_relevant_chunks(db=db, user_id=user.id, query=query)
        return [{"document_id": str(c.document_id), "content": c.content} for c in chunks]
    finally:
        db.close()


@mcp.tool()
def ask_question(question: str) -> dict:
    """Ask a question and get an answer generated from the user's documents."""
    db = SessionLocal()
    try:
        user = _get_current_user(db)
        chunks = retrieve_relevant_chunks(db=db, user_id=user.id, query=question)
        answer = generate_answer(question=question, chunks=chunks)
        return {
            "answer": answer,
            "sources": [{"document_id": str(c.document_id), "content": c.content} for c in chunks],
        }
    finally:
        db.close()


if __name__ == "__main__":
    mcp.run(transport="stdio")