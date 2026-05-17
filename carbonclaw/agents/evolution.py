"""Tools and agents for self-evolution and rule learning."""

from __future__ import annotations

import json
from typing import Any, TYPE_CHECKING

import structlog

from carbonclaw.core.base import BaseAgent, BaseTool
from carbonclaw.agents.base import ReactAgent
from carbonclaw.core.models import Message, ToolResult

if TYPE_CHECKING:
    from carbonclaw.core.base import BaseMemory, BaseProvider

logger = structlog.get_logger()


class LearnRuleTool(BaseTool):
    """Tool for agents to learn and persist new rules/preferences."""

    name = "learn_rule"
    description = (
        "Permanently store a new rule, preference, or 'lesson learned' based on user feedback or self-reflection. "
        "Use this to evolve your behavior and avoid repeating mistakes."
    )
    input_schema = {
        "type": "object",
        "properties": {
            "rule": {"type": "string", "description": "The concise rule or lesson to learn."},
            "context": {"type": "string", "description": "Short explanation of why this rule was learned."},
        },
        "required": ["rule"],
    }

    def __init__(self, memory: BaseMemory) -> None:
        self.memory = memory

    async def execute(self, arguments: dict[str, Any]) -> ToolResult:
        rule = arguments.get("rule", "")
        context = arguments.get("context", "Learned from interaction.")
        
        await self.memory.store(
            content=rule,
            namespace="learned_rules",
            metadata={"source": "agent_learning", "reason": context},
        )
        
        logger.info("agent.learned_rule", rule=rule, reason=context)
        return ToolResult(
            tool_call_id="",
            name=self.name,
            content=f"Successfully learned rule: {rule}",
        )


class EvolutionAgent(ReactAgent):
    """Agent that reflects on past interactions to extract lessons and evolve."""

    name = "evolution"
    description = "Reflects on task history to improve system behavior."

    def __init__(
        self,
        provider: BaseProvider,
        tools: list[BaseTool],
        memory: BaseMemory,
        model: str | None = None,
    ) -> None:
        super().__init__(
            provider=provider,
            tools=tools,
            memory=memory,
            system_prompt=(
                "You are a Self-Evolution Agent. Your goal is to analyze agent interactions and extract 'lessons learned'. "
                "1. Analyze the provided message history for inefficiencies, errors, or user corrections. "
                "2. Formulate concise, actionable rules to prevent these issues in the future. "
                "3. Use the 'learn_rule' tool to save these rules permanently. "
                "Be critical but constructive. Only learn high-value rules that improve future performance."
            ),
            model=model,
            max_iterations=5,
        )

    async def reflect(self, history: list[Message]) -> None:
        """Analyze a conversation history and extract lessons."""
        history_text = "\n".join([f"{m.role}: {m.content}" for m in history if m.content])
        task = (
            f"Analyze the following interaction and learn any rules that would have improved performance:\n\n"
            f"{history_text}\n\n"
            "If no clear lessons are found, you don't need to do anything."
        )
        await self.run(task)
