"""Web dashboard command."""

from __future__ import annotations

import asyncio

import typer

from carbonclaw.cli.main import app, console


@app.command()
def web(
    host: str = typer.Option("127.0.0.1", "--host", "-h"),
    port: int = typer.Option(8080, "--port", "-p"),
) -> None:
    """Launch the CarbonClaw web dashboard."""
    try:
        from carbonclaw.web.app import serve
    except ImportError as e:
        console.print(f"[red]Missing dependency:[/red] {e}")
        console.print("Install with: [bold]uv add fastapi uvicorn[/bold]")
        raise typer.Exit(1)

    console.print(f"[green]CarbonClaw web dashboard starting at http://{host}:{port}[/green]")
    asyncio.run(serve(host=host, port=port))
