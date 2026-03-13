"""
Integration-style tests for the Bot Service HTTP endpoints.

All tests use an in-memory SQLite DB (via conftest fixtures) and a FakeLLM
(triggered by OPENAI_API_KEY=test), so no external services are required.
"""

import pytest
from httpx import AsyncClient


# ---------------------------------------------------------------------------
# /health
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_health_returns_ok(app_client: AsyncClient):
    response = await app_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "timestamp" in data


# ---------------------------------------------------------------------------
# /process-message – auth guards
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_process_message_no_token_returns_401(app_client: AsyncClient):
    response = await app_client.post(
        "/process-message",
        json={"telegram_id": "123456789", "text": "Pizza 20 bucks"},
    )
    assert response.status_code == 403  # HTTPBearer returns 403 when header absent


@pytest.mark.asyncio
async def test_process_message_expired_token_returns_401(
    app_client: AsyncClient, expired_token: str
):
    response = await app_client.post(
        "/process-message",
        json={"telegram_id": "123456789", "text": "Pizza 20 bucks"},
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_process_message_wrong_secret_returns_401(
    app_client: AsyncClient, wrong_secret_token: str
):
    response = await app_client.post(
        "/process-message",
        json={"telegram_id": "123456789", "text": "Pizza 20 bucks"},
        headers={"Authorization": f"Bearer {wrong_secret_token}"},
    )
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# /process-message – whitelist guard
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_unknown_user_is_ignored(app_client: AsyncClient, valid_token: str):
    """A telegram_id not in the users table should return processed=False."""
    response = await app_client.post(
        "/process-message",
        json={"telegram_id": "999999999", "text": "Pizza 20 bucks"},
        headers={"Authorization": f"Bearer {valid_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["processed"] is False
    assert data["reply"] == ""


# ---------------------------------------------------------------------------
# /process-message – expense flow
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_expense_message_is_processed(
    app_client: AsyncClient, valid_token: str, sample_user
):
    """
    A whitelisted user sending an expense message should get a success reply.
    The FakeLLM returns Food/20.0/Pizza by default (see conftest).
    """
    response = await app_client.post(
        "/process-message",
        json={"telegram_id": "123456789", "text": "Pizza 20 bucks"},
        headers={"Authorization": f"Bearer {valid_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["processed"] is True
    assert "expense added ✅" in data["reply"]


@pytest.mark.asyncio
async def test_non_expense_message_is_ignored(
    app_client: AsyncClient, valid_token: str, sample_user, monkeypatch
):
    """
    When the agent returns is_expense=False the endpoint should silently ignore
    the message and return processed=False.
    """
    import json as _json
    from langchain_core.language_models.fake import FakeListChatModel
    import app.agent as agent_module

    fake_non_expense = _json.dumps({
        "is_expense": False,
        "description": "",
        "amount": 0.0,
        "category": "Other",
    })
    # Swap the chain's LLM for one that returns a non-expense response
    monkeypatch.setattr(
        agent_module,
        "_llm",
        FakeListChatModel(responses=[fake_non_expense]),
    )
    # Rebuild the chain with the patched LLM
    monkeypatch.setattr(
        agent_module,
        "_chain",
        agent_module._prompt | agent_module._llm,
    )

    response = await app_client.post(
        "/process-message",
        json={"telegram_id": "123456789", "text": "Hey, how are you?"},
        headers={"Authorization": f"Bearer {valid_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["processed"] is False
