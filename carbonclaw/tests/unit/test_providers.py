"""Unit tests for provider message normalization."""

from __future__ import annotations

import json
import pytest

from carbonclaw.core.models import Message, ToolCall
from carbonclaw.providers.base import _message_to_anthropic, _message_to_openai


def test_message_to_openai_text() -> None:
    msg = Message(role="user", content="hello")
    out = _message_to_openai(msg)
    assert out == {"role": "user", "content": "hello"}


def test_message_to_openai_tool_call() -> None:
    msg = Message(
        role="assistant",
        content="",
        tool_calls=[ToolCall(id="1", name="shell", arguments={"command": "ls"})],
    )
    out = _message_to_openai(msg)
    assert out["role"] == "assistant"
    assert len(out["tool_calls"]) == 1
    assert out["tool_calls"][0]["function"]["name"] == "shell"
    assert json.loads(out["tool_calls"][0]["function"]["arguments"]) == {"command": "ls"}


def test_message_to_anthropic_system() -> None:
    msg = Message(role="system", content="You are CarbonClaw.")
    out = _message_to_anthropic(msg)
    assert out == {"role": "system", "content": "You are CarbonClaw."}


def test_message_to_anthropic_tool_result() -> None:
    msg = Message(role="tool", content="output", tool_call_id="tc1", name="shell")
    out = _message_to_anthropic(msg)
    assert out["role"] == "user"
    assert out["content"][0]["type"] == "tool_result"


@pytest.mark.asyncio
async def test_llamacpp_provider_complete() -> None:
    from unittest.mock import MagicMock, patch
    from carbonclaw.core.models import CompletionRequest
    from carbonclaw.providers.llamacpp import LlamaCppProvider

    provider = LlamaCppProvider(model_path="dummy.gguf")
    
    mock_llm = MagicMock()
    mock_llm.create_chat_completion.return_value = {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": "Hello from mock llama.cpp!"
                }
            }
        ]
    }
    
    with patch("carbonclaw.providers.llamacpp.LlamaCppProvider._get_llm") as mock_get:
        mock_get.return_value = mock_llm
        
        req = CompletionRequest(
            messages=[Message(role="user", content="Hi")],
            model="dummy.gguf"
        )
        
        resp = await provider.complete(req)
        assert resp.message.content == "Hello from mock llama.cpp!"
