"""CarbonClaw agents for various tasks."""

from carbonclaw.core.base import BaseAgent
from carbonclaw.agents.base import ReactAgent
from carbonclaw.agents.coding import CodingAgent
from carbonclaw.agents.docs import DocsAgent
from carbonclaw.agents.planner import PlannerAgent
from carbonclaw.agents.qa import QAAgent
from carbonclaw.agents.review import ReviewAgent
from carbonclaw.agents.supervisor import SupervisorAgent

__all__ = [
    "BaseAgent",
    "ReactAgent",
    "CodingAgent",
    "DocsAgent",
    "PlannerAgent",
    "QAAgent",
    "ReviewAgent",
    "SupervisorAgent",
]
