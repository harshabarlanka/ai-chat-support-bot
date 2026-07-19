import uuid

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, get_current_user_ws
from app.models.chat_message import ChatMessage
from app.models.chat_session import ChatSession
from app.models.user import User
from app.schemas.chat import ChatRequest, ChatResponse
from app.schemas.chat_message import ChatMessageResponse
from app.services.chat import generate_answer, generate_answer_stream
from app.services.conversation import rewrite_query
from app.services.retrieval import retrieve_relevant_chunks

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/", response_model=ChatResponse)
def chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    chunks = retrieve_relevant_chunks(db=db, user_id=current_user.id, query=request.question)
    answer = generate_answer(question=request.question, chunks=chunks)
    return ChatResponse(answer=answer, sources=chunks)


@router.get("/sessions/{session_id}/messages", response_model=list[ChatMessageResponse])
def get_session_messages(
    session_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session = (
        db.query(ChatSession)
        .filter(ChatSession.id == session_id, ChatSession.owner_id == current_user.id)
        .first()
    )
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    return (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at)
        .all()
    )


def get_or_create_session(db: Session, user_id: uuid.UUID, session_id: uuid.UUID | None) -> ChatSession:
    if session_id is not None:
        session = (
            db.query(ChatSession)
            .filter(ChatSession.id == session_id, ChatSession.owner_id == user_id)
            .first()
        )
        if session is not None:
            return session

    session = ChatSession(id=uuid.uuid4(), owner_id=user_id)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@router.websocket("/ws")
async def chat_websocket(
    websocket: WebSocket,
    token: str,
    session_id: uuid.UUID | None = None,
    db: Session = Depends(get_db),
):
    current_user = get_current_user_ws(websocket, token, db)

    await websocket.accept()

    session = get_or_create_session(db, current_user.id, session_id)
    await websocket.send_json({"type": "session", "session_id": str(session.id)})

    try:
        while True:
            question = await websocket.receive_text()

            history = (
                db.query(ChatMessage)
                .filter(ChatMessage.session_id == session.id)
                .order_by(ChatMessage.created_at)
                .all()
            )

            standalone_question = rewrite_query(question, history)

            chunks = retrieve_relevant_chunks(
                db=db, user_id=current_user.id, query=standalone_question
            )

            db.add(ChatMessage(id=uuid.uuid4(), session_id=session.id, role="user", content=question))
            db.commit()

            full_answer_parts = []
            for text_piece in generate_answer_stream(
                question=standalone_question, chunks=chunks, history=history
            ):
                full_answer_parts.append(text_piece)
                await websocket.send_json({"type": "token", "content": text_piece})

            full_answer = "".join(full_answer_parts)
            db.add(
                ChatMessage(
                    id=uuid.uuid4(), session_id=session.id, role="assistant", content=full_answer
                )
            )
            db.commit()

            await websocket.send_json({"type": "done"})

    except WebSocketDisconnect:
        pass