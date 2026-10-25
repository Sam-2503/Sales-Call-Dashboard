"""Command-line entry point; stage-specific commands arrive with their stages."""

from __future__ import annotations

import json
from pathlib import Path

import typer

from call_analyser.config import Settings
from call_analyser.schemas import CallReport

app = typer.Typer(help="Evidence-backed sales-call analysis.")


@app.callback()
def main() -> None:
    """Provide a command group even while only Stage 1 commands exist."""


@app.command("settings")
def show_settings() -> None:
    """Print effective non-secret configuration."""
    payload = Settings().model_dump(exclude={"gemini_api_key"}, mode="json")
    typer.echo(json.dumps(payload, indent=2, sort_keys=True, default=str))


@app.command("export-schema")
def export_schema(output: Path = Path("schemas/call_report.schema.json")) -> None:
    """Write a deterministic JSON Schema for the public report contract."""
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(CallReport.model_json_schema(), indent=2, sort_keys=True) + "\n")
