"""Planning command."""

from __future__ import annotations

import asyncio

import typer
from rich.markdown import Markdown

from carbonclaw.agents.planner import PlannerAgent
from carbonclaw.cli.main import app, console
from carbonclaw.config.settings import CarbonClawConfig
from carbonclaw.memory.sqlite import SQLiteMemory
from carbonclaw.providers.registry import ProviderRegistry
from carbonclaw.tools.base import ToolRegistry
from carbonclaw.tools.file import FileReadTool
from carbonclaw.tools.git import GitTool
from carbonclaw.tools.shell import ShellTool


@app.command()
def plan(
    task: str = typer.Argument(..., help="Task to plan."),
    provider: str | None = typer.Option(None, "--provider", "-p"),
    model: str | None = typer.Option(None, "--model", "-m"),
) -> None:
    """Generate a step-by-step plan for a task."""
    config = CarbonClawConfig()
    provider_name = provider or config.default_provider
    model = model or config.default_model or "llama3.2"

    async def _execute() -> None:
        prov = ProviderRegistry.create(provider_name, config)
        mem = SQLiteMemory()
        tools = ToolRegistry()
        tools.register(ShellTool())
        tools.register(FileReadTool())
        tools.register(GitTool())

        agent = PlannerAgent(
            provider=prov,
            tools=tools.list_tools(),
            memory=mem,
            model=model,
        )

        console.print(f"[bold green]Planning:[/bold green] {task}\n")
        result = await agent.run(task)
        console.print(Markdown(result))

    asyncio.run(_execute())
