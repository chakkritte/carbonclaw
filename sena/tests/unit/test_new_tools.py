"""Functional tests for newly added advanced tools."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, AsyncIterator, Optional

import pytest
from pydantic import BaseModel

from sena.core.base import BaseProvider, BaseMemory
from sena.core.models import (
    CompletionRequest,
    CompletionResponse,
    Message,
    StreamChunk,
    MemoryEntry,
)
from sena.tools.plan import EnterPlanModeTool
from sena.tools.ui import UpdateTopicTool
from sena.tools.skill import ActivateSkillTool
from sena.tools.agent import InvokeAgentTool

# --- Functional Mocks (Real logic, no synthetic return_value) ---

class FakeProvider(BaseProvider):
    """A provider that returns predictable responses without hitting an API."""
    async def complete(self, request: CompletionRequest) -> CompletionResponse:
        return CompletionResponse(
            message=Message(role="assistant", content="Delegated response from agent.")
        )
    
    async def stream(self, request: CompletionRequest) -> AsyncIterator[StreamChunk]:
        yield StreamChunk(content="Delegated response from agent.")
        yield StreamChunk(finish_reason="stop")

    async def list_models(self) -> list[str]:
        return ["fake-model"]

class FakeMemory(BaseMemory):
    """A memory that stores items in a local list."""
    def __init__(self):
        self.entries = []
    async def store(self, content: str, namespace: str = "default", metadata: dict[str, Any] | None = None) -> str:
        self.entries.append(content)
        return "id"
    async def retrieve(self, query: str, namespace: str = "default", limit: int = 5) -> list[MemoryEntry]:
        return []
    async def get(self, entry_id: str) -> MemoryEntry | None:
        return None
    async def delete(self, entry_id: str) -> bool:
        return True
    async def namespaces(self) -> list[str]:
        return ["default"]

# --- Tests ---

@pytest.mark.asyncio
async def test_enter_plan_mode_functional() -> None:
    tool = EnterPlanModeTool()
    result = await tool.execute({"reason": "Complex refactoring"})
    assert "PLANNING MODE ENABLED" in result.content
    assert "Complex refactoring" in result.content
    assert result.name == "enter_plan_mode"

@pytest.mark.asyncio
async def test_update_topic_functional() -> None:
    tool = UpdateTopicTool()
    result = await tool.execute(
        {"title": "Architecture", "strategic_intent": "Define the core layers."}
    )
    assert "Topic updated: Architecture" in result.content
    assert result.name == "update_topic"

@pytest.mark.asyncio
async def test_activate_skill_functional(tmp_path: Path) -> None:
    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()
    skill_content = "Verify API security headers."
    (skills_dir / "security.md").write_text(skill_content, encoding="utf-8")
    
    tool = ActivateSkillTool(skills_dir=skills_dir)
    result = await tool.execute({"name": "security"})
    assert "<activated_skill>" in result.content
    assert skill_content in result.content

@pytest.mark.asyncio
async def test_invoke_agent_functional() -> None:
    provider = FakeProvider(config={})
    memory = FakeMemory()
    tools = []
    
    tool = InvokeAgentTool(provider, memory, tools)
    
    # Test dispatch to 'generalist' which uses ReactAgent
    result = await tool.execute({"agent_name": "generalist", "prompt": "Help me code."})
    assert not result.is_error
    assert "Delegated response" in result.content
    assert result.name == "invoke_agent"

@pytest.mark.asyncio
async def test_invoke_agent_invalid_functional() -> None:
    provider = FakeProvider(config={})
    memory = FakeMemory()
    tools = []
    
    tool = InvokeAgentTool(provider, memory, tools)
    
    # Test invalid agent name
    result = await tool.execute({"agent_name": "invalid_agent", "prompt": "Do something"})
    assert result.is_error
    assert "Agent 'invalid_agent' not found" in result.content
