"""
API routes for the Bot Service.

Endpoints:
  GET  /health            – Liveness probe (no auth required).
  POST /process-message   – Core endpoint; requires JWT Bearer token.
"""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.agent import analyze_message
from app.auth import verify_jwt
from app.database import get_session
from app.models import Expense, User
from app.schemas import (
    HealthResponse,
    ProcessMessageRequest,
    ProcessMessageResponse,
)

router = APIRouter()


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health Check",
    description=(
        "Returns the current service status and UTC timestamp. "
        "Use this endpoint to verify the service is running before sending messages."
    ),
    tags=["Monitoring"],
)
async def health_check() -> HealthResponse:
    return HealthResponse(status="ok", timestamp=datetime.now(timezone.utc))


# ---------------------------------------------------------------------------
# Process message
# ---------------------------------------------------------------------------


@router.post(
    "/process-message",
    response_model=ProcessMessageResponse,
    summary="Process Telegram Message",
    description=(
        "Receives a raw Telegram message from the Connector Service, runs it "
        "through the LangChain agent to determine if it's an expense, and — "
        "if so — categorizes it and persists it to PostgreSQL.\n\n"
        "**Auth:** Requires a short-lived JWT Bearer token signed with `JWT_SECRET`.\n\n"
        "**Ignored cases (processed=false):**\n"
        "- Sender's `telegram_id` is not in the `users` whitelist.\n"
        "- Message text is not classified as an expense by the LLM."
    ),
    responses={
        200: {"description": "Message processed (expense added or ignored)."},
        401: {"description": "Missing or invalid JWT token."},
        500: {"description": "Unexpected server error."},
    },
    tags=["Bot"],
)
async def process_message(
    body: ProcessMessageRequest,
    db: AsyncSession = Depends(get_session),
    _token: dict = Depends(verify_jwt),   # Enforces JWT auth; payload unused here
) -> ProcessMessageResponse:
    """
    Core processing pipeline:
      1. Verify the sender is a whitelisted user.
      2. Send the message to the LangChain agent for classification.
      3. If it's an expense, insert a row into the `expenses` table.
      4. Return the reply text and a `processed` flag.
    """

    # ── Step 1: Whitelist check ──────────────────────────────────────────────
    result = await db.execute(
        select(User).where(User.telegram_id == body.telegram_id)
    )
    user: User | None = result.scalar_one_or_none()

    if user is None:
        # User not whitelisted – silently ignore (return processed=False)
        return ProcessMessageResponse(
            reply="",
            processed=False,
        )

    # ── Step 2: LangChain agent classification ───────────────────────────────
    expense = await analyze_message(body.text)

    if not expense.is_expense:
        # Non-expense message – silently ignore
        return ProcessMessageResponse(
            reply="",
            processed=False,
        )

    # ── Step 3: Persist expense ──────────────────────────────────────────────
    new_expense = Expense(
        user_id=user.id,
        description=expense.description,
        # Cast to PostgreSQL MONEY-compatible string
        amount=str(expense.amount),
        category=expense.category.value,
        added_at=datetime.now(timezone.utc).replace(tzinfo=None),
    )
    db.add(new_expense)
    await db.commit()

    # ── Step 4: Build reply ──────────────────────────────────────────────────
    reply = f"{expense.category.value} expense added ✅"

    return ProcessMessageResponse(reply=reply, processed=True)
