"""TUI command entry point."""

from __future__ import annotations

import asyncio
from typing import Any

import typer
from rich.console import Console

from carbonclaw.cli.main import app, console
from carbonclaw.config.settings import CarbonClawConfig
from carbonclaw.ui.tui import CarbonClawApp


@app.command()
def tui(
    provider: str | None = typer.Option(None, "--provider", "-p"),
    model: str | None = typer.Option(None, "--model", "-m"),
) -> None:
    """Launch the full-screen Textual TUI."""
    config = CarbonClawConfig()
    provider_name = provider or config.default_provider
    model = model or config.default_model or "llama3.2"

    try:
        app_instance = CarbonClawApp(provider_name=provider_name, model=model)
        app_instance.run()
    except Exception as e:
        console.print(f"[red]TUI Error:[/red] {e}")
