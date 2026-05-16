"""One-shot task execution."""

from __future__ import annotations

import asyncio

import typer

from sena.agents.coding import CodingAgent
from sena.cli.main import app, cli_approval_callback, console
from sena.config.settings import SenaConfig
from sena.memory.sqlite import SQLiteMemory
from sena.providers.registry import ProviderRegistry
from sena.tools.base import ToolRegistry
from sena.tools.browser import BrowserTool
from sena.tools.file import FilePatchTool, FileReadTool, FileWriteTool
from sena.tools.git import GitTool
from sena.tools.mcp import register_mcp_tools
from sena.tools.shell import ShellTool


@app.command()
def run(
    task: str = typer.Argument(..., help="The task for the agent to execute."),
    provider: str | None = typer.Option(None, "--provider", "-p", help="LLM provider to use."),
    model: str | None = typer.Option(None, "--model", "-m", help="Model ID to use."),
) -> None:
    """Run a one-shot task using the coding agent."""
    config = SenaConfig()
    provider_name = provider or config.default_provider
    model = model or config.default_model

    async def _execute() -> None:
        prov = ProviderRegistry.create(provider_name, config)
        mem = SQLiteMemory()
        tools = ToolRegistry()
        tools.register(ShellTool())
        tools.register(BrowserTool())
        tools.register(FileReadTool())
        tools.register(FileWriteTool())
        tools.register(FilePatchTool())
        tools.register(GitTool())

        # Register MCP tools
        mcp_clients = await register_mcp_tools(tools, config)

        agent = CodingAgent(
            provider=prov,
            tools=tools.list_tools(),
            memory=mem,
            model=model,
            approval_callback=cli_approval_callback,
        )

        try:
            console.print(f"[bold green]Running:[/bold green] {task}\n")
            async for text in agent.stream_run(task):
                console.print(text, end="")
            console.print()
        finally:
            # Disconnect MCP clients
            for client in mcp_clients:
                await client.disconnect()

    asyncio.run(_execute())

