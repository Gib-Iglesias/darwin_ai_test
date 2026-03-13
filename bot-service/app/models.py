"""
SQLAlchemy ORM models that mirror the database DDL specified in the test.

We use the async-compatible DeclarativeBase from SQLAlchemy 2.x so that
all DB operations are non-blocking and work with FastAPI's async handlers.
"""

from datetime import datetime

from sqlalchemy import ForeignKey, String, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""
    pass


class User(Base):
    """
    Whitelisted Telegram users.

    Only users with a row in this table are allowed to interact with the bot.
    New users can be added directly via SQL or a future admin endpoint.
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    telegram_id: Mapped[str] = mapped_column(String, unique=True, nullable=False)

    # Relationship – allows `user.expenses` for convenience
    expenses: Mapped[list["Expense"]] = relationship(back_populates="user")

    def __repr__(self) -> str:
        return f"<User id={self.id} telegram_id={self.telegram_id!r}>"


class Expense(Base):
    """
    Individual expense records linked to a whitelisted user.

    The `amount` column uses PostgreSQL's MONEY type via a raw server_default
    cast; SQLAlchemy stores it as a string on the Python side. We keep it as
    a float in Python and let the DB handle the MONEY formatting.
    """

    __tablename__ = "expenses"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False)
    # PostgreSQL MONEY is stored as numeric here; SQLAlchemy maps it via String
    amount: Mapped[str] = mapped_column(
        String,
        nullable=False,
        comment="Stored as PostgreSQL MONEY type (e.g. '$20.00')",
    )
    category: Mapped[str] = mapped_column(String, nullable=False)
    added_at: Mapped[datetime] = mapped_column(
        nullable=False,
        server_default=text("NOW()"),
    )

    # Back-reference to the owning user
    user: Mapped["User"] = relationship(back_populates="expenses")

    def __repr__(self) -> str:
        return (
            f"<Expense id={self.id} category={self.category!r} "
            f"amount={self.amount!r} user_id={self.user_id}>"
        )
