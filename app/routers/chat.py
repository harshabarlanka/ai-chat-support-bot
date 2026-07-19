from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, get_current_user_ws
from app.models.user import User
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat import generate_answer, generate_answer_stream
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

@router.websocket("/ws")
async def chat_websocket(websocket: WebSocket, token: str, db: Session=Depends(get_db)):
    current_user = get_current_user_ws(websocket, token, db)
    await websocket.accept()
    try:
        while True:
            question = await websocket.receive_text()
            chunks = retrieve_relevant_chunks(db=db,user_id=current_user.id, query=question)
            for text_piece in generate_answer_stream(question=question, chunks=chunks):
                await websocket.send_json({"type":"token", "content":text_piece})
            await websocket.send_json({"type":"done"})
    except WebSocketDisconnect:
        pass
