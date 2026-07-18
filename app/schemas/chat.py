import uuid

from pydantic import BaseModel

from app.schemas.chunk import ChunkResult


class ChatRequest(BaseModel):
    question: str


class ChatResponse(BaseModel):
    answer: str
    sources: list[ChunkResult]