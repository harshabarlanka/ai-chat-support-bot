import uuid
from pydantic import BaseModel

class ChunkResult(BaseModel):
    id: uuid.UUID
    document_id: uuid.UUID
    chunk_index: int
    content: str

    model_config = {"from_attributes": True}