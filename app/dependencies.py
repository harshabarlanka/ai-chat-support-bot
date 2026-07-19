import uuid
from fastapi import Depends, HTTPException, WebSocket, WebSocketException,status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.security import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def get_current_user(
        token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        user_id_str = decode_access_token(token)
        user_id = uuid.UUID(user_id_str)
    except (JWTError, ValueError):
        raise credentials_exception
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
    return user

def get_current_user_ws(websocket: WebSocket, token: str, db: Session) -> User:
    try: 
        user_id_str = decode_access_token(token)
        user_id = uuid.UUID(user_id_str)
    except(JWTError, ValueError):
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)
    
    return user
