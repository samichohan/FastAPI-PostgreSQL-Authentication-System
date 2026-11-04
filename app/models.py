"""
models.py
---------
SQLAlchemy ORM models = Python classes that map to database tables.
"""

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    # unique=True -> no duplicate emails, index=True -> fast lookups by email
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    # We store ONLY the Argon2 hash, never the real password
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
