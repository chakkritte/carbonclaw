"""Unit tests for JSON repair utility."""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock

from carbonclaw.utils.json_repair import repair_json
from carbonclaw.core.errors import ToolCallParseError


@pytest.mark.asyncio
async def test_repair_valid_json() -> None:
    raw = '{"command": "ls", "args": ["-l"]}'
    result = await repair_json(raw)
    assert result == {"command": "ls", "args": ["-l"]}


@pytest.mark.asyncio
async def test_repair_markdown_fences() -> None:
    raw = "```json\n{\"command\": \"ls\"}\n```"
    result = await repair_json(raw)
    assert result == {"command": "ls"}


@pytest.mark.asyncio
async def test_repair_trailing_comma() -> None:
    raw = '{"command": "ls",}'
    result = await repair_json(raw)
    assert result == {"command": "ls"}
    
    raw_arr = '[1, 2, 3,]'
    result_arr = await repair_json(raw_arr)
    assert result_arr == [1, 2, 3]


@pytest.mark.asyncio
async def test_repair_unquoted_keys() -> None:
    raw = '{command: "ls", args: ["-l"]}'
    result = await repair_json(raw)
    assert result == {"command": "ls", "args": ["-l"]}


@pytest.mark.asyncio
async def test_repair_llm_fallback() -> None:
    raw = "completely broken {{"
    
    mock_provider = MagicMock()
    mock_response = MagicMock()
    mock_response.message.content = '{"command": "fixed"}'
    mock_provider.complete = AsyncMock(return_value=mock_response)
    
    result = await repair_json(raw, provider=mock_provider, model="test-model")
    assert result == {"command": "fixed"}
    mock_provider.complete.assert_called_once()


@pytest.mark.asyncio
async def test_repair_fail_raises_error() -> None:
    raw = "completely broken {{"
    with pytest.raises(ToolCallParseError):
        await repair_json(raw)
