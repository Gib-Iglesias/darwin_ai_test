"""
Unit tests for the LangChain agent (app/agent.py).

These tests inject a FakeListChatModel to simulate LLM responses without
making real API calls, keeping the test suite fast and free.
"""

import json

import pytest
from langchain_core.language_models.fake import FakeListChatModel

import app.agent as agent_module
from app.agent import analyze_message
from app.schemas import ExpenseCategory


def _patch_llm(monkeypatch, response_dict: dict):
    """Helper to swap the agent's LLM with a fake that returns `response_dict`."""
    fake = FakeListChatModel(responses=[json.dumps(response_dict)])
    monkeypatch.setattr(agent_module, "_llm", fake)
    monkeypatch.setattr(agent_module, "_chain", agent_module._prompt | agent_module._llm)


@pytest.mark.asyncio
async def test_expense_message_classified_correctly(monkeypatch):
    _patch_llm(monkeypatch, {
        "is_expense": True,
        "description": "Pizza",
        "amount": 20.0,
        "category": "Food",
    })
    result = await analyze_message("Pizza 20 bucks")
    assert result.is_expense is True
    assert result.description == "Pizza"
    assert result.amount == 20.0
    assert result.category == ExpenseCategory.FOOD


@pytest.mark.asyncio
async def test_greeting_not_classified_as_expense(monkeypatch):
    _patch_llm(monkeypatch, {
        "is_expense": False,
        "description": "",
        "amount": 0.0,
        "category": "Other",
    })
    result = await analyze_message("Hey! How are you?")
    assert result.is_expense is False


@pytest.mark.asyncio
async def test_unknown_category_falls_back_to_other(monkeypatch):
    _patch_llm(monkeypatch, {
        "is_expense": True,
        "description": "Something weird",
        "amount": 5.0,
        "category": "NotARealCategory",
    })
    result = await analyze_message("Something weird 5 bucks")
    assert result.category == ExpenseCategory.OTHER


@pytest.mark.asyncio
async def test_invalid_json_response_treated_as_non_expense(monkeypatch):
    """If the LLM returns garbage, the agent should not crash."""
    fake = FakeListChatModel(responses=["this is not json at all"])
    monkeypatch.setattr(agent_module, "_llm", fake)
    monkeypatch.setattr(agent_module, "_chain", agent_module._prompt | agent_module._llm)

    result = await analyze_message("Some message")
    assert result.is_expense is False


@pytest.mark.asyncio
async def test_all_categories_are_valid():
    """Ensure every ExpenseCategory value is a non-empty string."""
    for cat in ExpenseCategory:
        assert isinstance(cat.value, str)
        assert len(cat.value) > 0
