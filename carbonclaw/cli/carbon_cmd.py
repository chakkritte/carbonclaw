"""Carbon CLI: view and manage emission records."""

from __future__ import annotations

import typer
from rich.table import Table

from carbonclaw.cli.main import app, console
from carbonclaw.telemetry.carbon import CarbonStore


@app.command(name="carbon")
def carbon(
    clear: bool = typer.Option(False, "--clear", help="Clear all emission records."),
) -> None:
    """Show aggregated carbon emission records."""
    store = CarbonStore()

    if clear:
        store.clear()
        console.print("[dim]Emission records cleared.[/dim]")
        return

    records = store.records()
    total = store.total_emissions()
    
    if not records:
        console.print("[dim]No emission records found.[/dim]")
        return

    console.print(f"🌱 [bold green]CarbonClaw Sustainability Report[/bold green]")
    console.print(f"[bold]Total sessions tracked:[/bold] {len(records)}")
    console.print(f"[bold]Total emissions:[/bold] [bold white]{total:.6f} kg CO2[/bold white]")
    
    # Approximation
    driving_km = total * 5.0
    console.print(f"[bold]Environmental impact:[/bold] Equivalent to driving [bold]{driving_km:.2f} km[/bold] in a petrol car.")

    table = Table(title="Emissions by Session", show_header=True)
    table.add_column("Timestamp", style="dim")
    table.add_column("Project", style="cyan")
    table.add_column("Emissions (kg CO2)", justify="right", style="bold green")

    # Show last 20 records
    for r in records[-20:]:
        table.add_row(
            r.timestamp.split("T")[0],
            r.project_name,
            f"{r.emissions:.6f}",
        )
    console.print(table)


@app.command(name="tracker", hidden=True)
def tracker(
    clear: bool = typer.Option(False, "--clear", help="Clear all emission records."),
) -> None:
    """Alias for 'carbon' command."""
    carbon(clear=clear)
