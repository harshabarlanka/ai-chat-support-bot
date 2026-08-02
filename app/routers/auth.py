from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.schemas.user import RefreshRequest, TokenPair, UserCreate, UserResponse
from app.security import (
    create_access_token,
    generate_refresh_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def issue_token_pair(db: Session, user_id) -> TokenPair:
    access_token = create_access_token(subject=str(user_id))

    raw_refresh_token = generate_refresh_token()
    refresh_token_row = RefreshToken(
        user_id=user_id,
        token_hash=hash_refresh_token(raw_refresh_token),
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days),
    )
    db.add(refresh_token_row)
    db.commit()

    return TokenPair(access_token=access_token, refresh_token=raw_refresh_token)


@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def signup(user_in: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == user_in.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )

    user = User(email=user_in.email, hashed_password=hash_password(user_in.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=TokenPair)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    return issue_token_pair(db, user.id)


@router.post("/refresh", response_model=TokenPair)
def refresh(request: RefreshRequest, db: Session = Depends(get_db)):
    token_hash = hash_refresh_token(request.refresh_token)

    stored_token = db.query(RefreshToken).filter(RefreshToken.token_hash == token_hash).first()

    invalid_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token"
    )

    if stored_token is None or stored_token.revoked:
        raise invalid_exception

    if stored_token.expires_at < datetime.now(timezone.utc):
        raise invalid_exception

    # Rotate: revoke the old refresh token, issue a brand-new pair
    stored_token.revoked = True
    db.commit()

    return issue_token_pair(db, stored_token.user_id)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(request: RefreshRequest, db: Session = Depends(get_db)):
    token_hash = hash_refresh_token(request.refresh_token)
    stored_token = db.query(RefreshToken).filter(RefreshToken.token_hash == token_hash).first()

    if stored_token is not None:
        stored_token.revoked = True
        db.commit()

    return None