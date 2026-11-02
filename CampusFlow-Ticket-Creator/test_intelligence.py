import json
from types import SimpleNamespace

import ai_assistant


def test_ticket_intelligence_returns_valid_classification(monkeypatch):
    expected_result = {
        "category": "Network",
        "priority": "High",
        "department": "ICT",
        "reason": "The library Wi-Fi connection is unavailable."
    }

    fake_response = SimpleNamespace(
        output_text=json.dumps(expected_result)
    )

    fake_client = SimpleNamespace(
        interactions=SimpleNamespace(
            create=lambda **kwargs: fake_response
        )
    )

    monkeypatch.setattr(
        ai_assistant,
        "get_gemini_client",
        lambda: fake_client
    )

    result = ai_assistant.get_ticket_intelligence(
        "The library Wi-Fi is not working."
    )

    assert result == expected_result


def test_ticket_intelligence_returns_none_without_client(monkeypatch):
    monkeypatch.setattr(
        ai_assistant,
        "get_gemini_client",
        lambda: None
    )

    result = ai_assistant.get_ticket_intelligence(
        "The library Wi-Fi is not working."
    )

    assert result is None


def test_ticket_intelligence_handles_invalid_json(monkeypatch):
    fake_response = SimpleNamespace(
        output_text="This is not valid JSON"
    )

    fake_client = SimpleNamespace(
        interactions=SimpleNamespace(
            create=lambda **kwargs: fake_response
        )
    )

    monkeypatch.setattr(
        ai_assistant,
        "get_gemini_client",
        lambda: fake_client
    )

    result = ai_assistant.get_ticket_intelligence(
        "The library Wi-Fi is not working."
    )

    assert result is None


def test_ticket_intelligence_rejects_missing_fields(monkeypatch):
    incomplete_result = {
        "category": "Network",
        "priority": "High"
    }

    fake_response = SimpleNamespace(
        output_text=json.dumps(incomplete_result)
    )

    fake_client = SimpleNamespace(
        interactions=SimpleNamespace(
            create=lambda **kwargs: fake_response
        )
    )

    monkeypatch.setattr(
        ai_assistant,
        "get_gemini_client",
        lambda: fake_client
    )

    result = ai_assistant.get_ticket_intelligence(
        "The library Wi-Fi is not working."
    )

    assert result is None


def test_ticket_intelligence_handles_empty_response(monkeypatch):
    fake_response = SimpleNamespace(
        output_text=""
    )

    fake_client = SimpleNamespace(
        interactions=SimpleNamespace(
            create=lambda **kwargs: fake_response
        )
    )

    monkeypatch.setattr(
        ai_assistant,
        "get_gemini_client",
        lambda: fake_client
    )

    result = ai_assistant.get_ticket_intelligence(
        "The library Wi-Fi is not working."
    )

    assert result is None
