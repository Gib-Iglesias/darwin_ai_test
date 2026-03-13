"""
Main entry point for the Bot Service.

Initializes the FastAPI application with full OpenAPI/Swagger documentation,
sets up the database connection pool on startup, and registers all routes.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.database import init_db, close_db
from app.routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage startup and shutdown events for the application."""
    await init_db()
    yield
    await close_db()


app = FastAPI(
    title="Darwin AI – Bot Service",
    description=(
        "Processes incoming Telegram messages, classifies them as expenses "
        "using LangChain + OpenAI, and persists the results to PostgreSQL.\n\n"
        "All endpoints (except `/health`) require a short-lived **JWT Bearer** "
        "token signed with the shared `JWT_SECRET`."
    ),
    version="1.0.0",
    contact={"name": "Darwin AI Engineering"},
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

app.include_router(router)


@app.exception_handler(Exception)
async def global_exception_handler(request, exc: Exception):
    """Catch-all handler so unhandled errors never leak stack traces."""
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error."},
    )
