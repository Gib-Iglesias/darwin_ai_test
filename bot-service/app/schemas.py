"""
Pydantic v2 schemas for request validation and response serialization.

These schemas serve as the contract between the Connector Service and the
Bot Service, and are reflected automatically in the Swagger docs.
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class ExpenseCategory(str, Enum):
    """
    Predefined expense categories the LLM must classify into.
    Using an Enum enforces valid values at the schema level.
    """
    HOUSING = "Housing"
    TRANSPORTATION = "Transportation"
    FOOD = "Food"
    UTILITIES = "Utilities"
    INSURANCE = "Insurance"
    MEDICAL = "Medical/Healthcare"
    SAVINGS = "Savings"
    DEBT = "Debt"
    EDUCATION = "Education"
    ENTERTAINMENT = "Entertainment"
    OTHER = "Other"


class ProcessMessageRequest(BaseModel):
    """Payload sent by the Connector Service for each incoming Telegram message."""

    telegram_id: str = Field(
        ...,
        description="Telegram user ID as a string (e.g. '123456789').",
        examples=["123456789"],
    )
    text: str = Field(
        ...,
        description="Raw message text sent by the user.",
        examples=["Pizza 20 bucks"],
    )

    model_config = {"json_schema_extra": {"example": {"telegram_id": "123456789", "text": "Pizza 20 bucks"}}}


class ProcessMessageResponse(BaseModel):
    """
    Response returned after processing a message.
    `reply` is the text the Connector should forward to the Telegram user.
    `processed` indicates whether an expense was actually stored.
    """

    reply: str = Field(
        ...,
        description="Human-readable reply to send back to the Telegram user.",
        examples=["Food expense added ✅"],
    )
    processed: bool = Field(
        ...,
        description="True if a new expense row was inserted; False if the message was ignored.",
    )

    model_config = {
        "json_schema_extra": {
            "example": {"reply": "Food expense added ✅", "processed": True}
        }
    }


class HealthResponse(BaseModel):
    """Simple health-check payload."""

    status: str = Field(default="ok")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ExtractedExpense(BaseModel):
    """
    Internal schema produced by the LangChain agent.
    Not exposed in the API but used for type safety across modules.
    """

    is_expense: bool
    description: str = ""
    amount: float = 0.0
    category: ExpenseCategory = ExpenseCategory.OTHER
