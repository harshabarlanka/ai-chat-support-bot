import uuid

from pydantic import BaseModel

from app.schemas.chunk import ChunkResult


class ChatRequest(BaseModel):
    question: str


class ChatResponse(BaseModel):
    answer: str
    sources: list[ChunkResult]

class ChatComparisonResponse(BaseModel):
    question: str
    vector_answer: str
    vector_sources: list[ChunkResult]
    graph_answer: str
    graph_sources: list[ChunkResult]