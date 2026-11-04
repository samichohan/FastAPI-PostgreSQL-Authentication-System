"""
routes/auth.py
--------------
The authentication endpoints:
  POST /auth/signup  -> register a new user
  POST /auth/login   -> get a JWT token
  GET  /auth/me      -> get the logged-in user's profile (protected)
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.schemas import (
    LoginRequest,
    ProfileResponse,
    SignupRequest,
    SignupResponse,
    TokenResponse,
)
from app.security import (
    create_access_token,
    fake_verify,
    get_current_user,
    hash_password,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/signup", response_model=SignupResponse, status_code=status.HTTP_201_CREATED)
def signup(data: SignupRequest, db: Session = Depends(get_db)):
    # 1. Passwords must match (400 as required by the assignment)
    if data.password != data.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password and confirm password do not match.",
        )

    # 2. Reject duplicate email
    existing = db.scalar(select(User).where(User.email == data.email))
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already registered.",
        )

    # 3. Hash the password and save the user (plain password is never stored)
    user = User(
        full_name=data.full_name,
        email=data.email,
        password_hash=hash_password(data.password),
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        # Two requests with the same email at the same moment: the DB unique
        # constraint protects us, we just turn it into a clean error.
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already registered.",
        )
    db.refresh(user)

    return SignupResponse(message="User registered successfully.", user=user)


@router.post("/login", response_model=TokenResponse, status_code=status.HTTP_200_OK)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == data.email))

    if user is None:
        fake_verify()  # keep response time similar to a real check
        valid = False
    else:
        valid = verify_password(data.password, user.password_hash)

    if not valid:
        # Same message for "wrong email" and "wrong password" on purpose,
        # so attackers can't find out which emails exist.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return TokenResponse(access_token=create_access_token(user.id), token_type="bearer")


@router.get("/me", response_model=ProfileResponse, status_code=status.HTTP_200_OK)
def read_me(current_user: User = Depends(get_current_user)):
    # get_current_user already verified the token and loaded the user.
    return current_user
