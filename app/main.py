"""
main.py
-------
Entry point of the FastAPI application.
Run with:  uvicorn app.main:app --reload
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app import models  # noqa: F401  (import so SQLAlchemy knows the models)
from app.database import Base, engine
from app.routes import auth

logger = logging.getLogger("uvicorn.error")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # On startup: create the "users" table if it doesn't exist yet.
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Auth System API",
    description="User signup, login and JWT authentication with FastAPI + PostgreSQL.",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(auth.router)


@app.get("/", tags=["Health"])
def root():
    return {"message": "Auth System API is running. Open /docs to test it."}


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    # Log the real error on the server, but never show internals to the client.
    logger.exception("Unhandled error: %s", exc)
    return JSONResponse(status_code=500, content={"detail": "Internal server error."})
