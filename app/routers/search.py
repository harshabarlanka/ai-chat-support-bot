from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.chunk import ChunkResult
from app.services.retrieval import retrieve_relevant_chunks

router = APIRouter(prefix="/search", tags=["search"])

class SearchRequest(BaseModel):
    query: str

@router.post("/", response_model=list[ChunkResult])
def search_document(
    request: SearchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return retrieve_relevant_chunks(db=db, user_id=current_user.id, query=request.query)
