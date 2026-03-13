"""
LangChain agent responsible for two tasks:
  1. Deciding whether a message describes an expense.
  2. Extracting the amount, description, and category if it does.

We use a single structured-output call with Pydantic to get both decisions
in one LLM round-trip, keeping latency and cost low.

In test/CI environments (`OPENAI_API_KEY=test`), a `FakeListLLM` is returned
instead, so no real API calls are made.
"""

import json
import os

from langchain.chat_models import init_chat_model
from langchain_core.language_models.fake_chat_models import FakeListChatModel
from langchain_core.prompts import ChatPromptTemplate

from app.schemas import ExpenseCategory, ExtractedExpense

# ---------------------------------------------------------------------------
# Prompt
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = """You are a personal finance assistant. Your job is to parse
short user messages and determine if they describe an expense.

If the message IS an expense:
  - Set is_expense to true.
  - Extract a short description (e.g. "Pizza").
  - Extract the numeric amount (e.g. 20.0). If no amount is found, use 0.
  - Choose the best category from this exact list:
    Housing, Transportation, Food, Utilities, Insurance,
    Medical/Healthcare, Savings, Debt, Education, Entertainment, Other.

If the message is NOT an expense (e.g. greetings, questions, random text):
  - Set is_expense to false.
  - Leave description, amount, and category at their default values.

Respond ONLY with a valid JSON object matching this schema:
{{
  "is_expense": bool,
  "description": string,
  "amount": float,
  "category": string   // one of the categories above
}}
Do not include any explanation or markdown fences."""

_HUMAN_TEMPLATE = "Message: {text}"

_prompt = ChatPromptTemplate.from_messages(
    [("system", _SYSTEM_PROMPT), ("human", _HUMAN_TEMPLATE)]
)


# ---------------------------------------------------------------------------
# Model factory
# ---------------------------------------------------------------------------

def _build_llm():
    """
    Return a real OpenAI chat model or a deterministic FakeLLM for tests.

    The `OPENAI_API_KEY=test` convention avoids an extra env var while keeping
    test setup straightforward.
    """
    if os.getenv("OPENAI_API_KEY", "") == "test":
        # Fake responses cycle through this list. Tests should override as needed.
        fake_response = json.dumps({
            "is_expense": True,
            "description": "Pizza",
            "amount": 20.0,
            "category": "Food",
        })
        return FakeListChatModel(responses=[fake_response])

    provider = os.getenv("LLM_PROVIDER", "openai").lower()
    model_name = os.getenv("LLM_MODEL", "gpt-4o-mini")
    
    # Load the matching API key depending on the chosen provider
    if provider == "google-genai":
        api_key = os.getenv("GEMINI_API_KEY")
    elif provider == "anthropic":
        api_key = os.getenv("ANTHROPIC_API_KEY")
    else:
        api_key = os.getenv("OPENAI_API_KEY")

    # If the user still forgot to furnish the key, let langchain error out normally,
    # or return a clear error. We'll let LangChain handle it.
    
    return init_chat_model(
        model=model_name,
        model_provider=provider,
        api_key=api_key,
        temperature=0,          # Deterministic output for classification tasks
        max_tokens=256,
    )


# Build the LLM once at module import – avoids re-initialising on every request.
_llm = _build_llm()

# Chain: prompt → LLM → raw string response
_chain = _prompt | _llm


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def analyze_message(text: str) -> ExtractedExpense:
    """
    Run the LangChain chain and return a typed `ExtractedExpense`.

    The function is async so it integrates cleanly with FastAPI's event loop.
    LangChain's `ainvoke` uses a thread-pool internally for sync LLM backends,
    so concurrent requests don't block each other.

    Args:
        text: Raw message text from the Telegram user.

    Returns:
        An `ExtractedExpense` instance. Check `is_expense` before persisting.
    """
    result = await _chain.ainvoke({"text": text})

    # `result` is an AIMessage; extract the string content
    raw_content: str = result.content if hasattr(result, "content") else str(result)

    try:
        data = json.loads(raw_content)
    except json.JSONDecodeError:
        # If the LLM produced unparseable output, treat as non-expense
        return ExtractedExpense(is_expense=False)

    # Validate category against the enum; fall back to Other if unrecognized
    raw_category = data.get("category", "Other")
    try:
        category = ExpenseCategory(raw_category)
    except ValueError:
        category = ExpenseCategory.OTHER

    return ExtractedExpense(
        is_expense=bool(data.get("is_expense", False)),
        description=str(data.get("description", "")),
        amount=float(data.get("amount", 0.0)),
        category=category,
    )
