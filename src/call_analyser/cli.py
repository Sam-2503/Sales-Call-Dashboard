"""Command-line entry point; stage-specific commands arrive with their stages."""

from __future__ import annotations

import json

import typer

from call_analyser.config import Settings

app = typer.Typer(help="Evidence-backed sales-call analysis.")


@app.callback()
def main() -> None:
    """Expose a command group so stage commands can be added over time."""


@app.command("settings")
def show_settings() -> None:
    """Print effective non-secret configuration."""
    payload = Settings().model_dump(exclude={"gemini_api_key"}, mode="json")
    typer.echo(json.dumps(payload, indent=2, sort_keys=True, default=str))
