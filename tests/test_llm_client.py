"""Unit tests for NVIDIA NIM LLM client."""

import pytest
from unittest.mock import patch, MagicMock
from llm_client import NIMClient, NIMError


def test_nim_missing_key():
    client = NIMClient(api_key="")
    with pytest.raises(NIMError, match="NVIDIA_API_KEY is not configured"):
        client.chat_completion([{"role": "user", "content": "hello"}])


def test_nim_successful_completion():
    client = NIMClient(api_key="test_key")
    mock_resp = MagicMock()
    mock_resp.ok = True
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": "READY",
                    "tool_calls": None
                }
            }
        ]
    }
    with patch("requests.post", return_value=mock_resp):
        msg = client.chat_completion([{"role": "user", "content": "hello"}])
        assert msg["role"] == "assistant"
        assert msg["content"] == "READY"


def test_nim_tool_calls_response():
    client = NIMClient(api_key="test_key")
    mock_resp = MagicMock()
    mock_resp.ok = True
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": "call_123",
                            "type": "function",
                            "function": {
                                "name": "search_flights",
                                "arguments": '{"origin": "DEL", "destination": "BOM", "travel_date": "2026-09-24"}'
                            }
                        }
                    ]
                }
            }
        ]
    }
    with patch("requests.post", return_value=mock_resp):
        msg = client.chat_completion([{"role": "user", "content": "Find flight DEL to BOM on Sep 24"}])
        assert "tool_calls" in msg
        assert len(msg["tool_calls"]) == 1
        assert msg["tool_calls"][0]["function"]["name"] == "search_flights"


def test_nim_410_error_handling():
    client = NIMClient(api_key="test_key", model="meta/llama-3.3-70b-instruct")
    mock_resp = MagicMock()
    mock_resp.ok = False
    mock_resp.status_code = 410
    mock_resp.text = "Model deprecated"
    with patch("requests.post", return_value=mock_resp):
        with pytest.raises(NIMError, match="deprecated or gone"):
            client.chat_completion([{"role": "user", "content": "hello"}])
