from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat import generate_answer
from app.services.retrieval import retrieve_relevant_chunks

router = APIRouter(prefix="/chat",tags=["chat"])

@router.post("/", response_model=ChatResponse)
def chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    chunks = retrieve_relevant_chunks(db=db, user_id=current_user.id, query=request.question)
    answer = generate_answer(question=request.question, chunks=chunks)
    return ChatResponse(answer=answer,sources=chunks)