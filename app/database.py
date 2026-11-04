"""
database.py
-----------
Creates the connection to PostgreSQL using SQLAlchemy.
Also provides `get_db`, a FastAPI dependency that gives each request
its own database session and closes it afterwards.
"""

from sqlalchemy import URL, create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings

# URL.create() safely handles special characters (like @ or #) in the password.
# "postgresql+psycopg" tells SQLAlchemy to use the Psycopg 3 driver.
DATABASE_URL = URL.create(
    drivername="postgresql+psycopg",
    username=settings.db_user,
    password=settings.db_password,
    host=settings.db_host,
    port=settings.db_port,
    database=settings.db_name,
)

# The engine manages the actual connections to PostgreSQL.
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# Each SessionLocal() call creates one database session (a "conversation" with the DB).
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    """All ORM models inherit from this class."""


def get_db():
    """Dependency: open a session for one request, always close it at the end."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
