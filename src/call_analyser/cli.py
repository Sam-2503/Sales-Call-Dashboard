"""Command-line entry point; stage-specific commands arrive with their stages."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import typer

from call_analyser.config import Settings
from call_analyser.playbook import chunk_playbook, extract_playbook, load_playbook_spec
from call_analyser.schemas import CallReport

app = typer.Typer(help="Evidence-backed sales-call analysis.")
playbook_app = typer.Typer(help="Inspect and index persistent playbooks.")
app.add_typer(playbook_app, name="playbook")


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


@playbook_app.command("inspect")
def inspect_playbook(
    spec_path: Path,
    json_output: bool = typer.Option(False, "--json", help="Print machine-readable output."),
) -> None:
    """Extract and summarize a playbook without network or embedding calls."""
    spec = load_playbook_spec(spec_path)
    extracted = extract_playbook(spec)
    chunks = chunk_playbook(extracted, spec)
    estimates = sorted(chunk.token_estimate for chunk in chunks)
    summary: dict[str, Any] = {
        "pdf_sha256": extracted.pdf_sha256,
        "page_count": extracted.page_count,
        "skipped_pages": extracted.skipped_pages,
        "empty_pages": extracted.empty_pages,
        "chapters": [
            {"title": chapter.title, "start_page": chapter.start_page, "end_page": chapter.end_page}
            for chapter in extracted.chapters
        ],
        "chunk_count": len(chunks),
        "token_estimates": {
            "min": min(estimates) if estimates else 0,
            "median": estimates[len(estimates) // 2] if estimates else 0,
            "p95": (
                estimates[min(len(estimates) - 1, int(len(estimates) * 0.95))]
                if estimates
                else 0
            ),
            "max": max(estimates) if estimates else 0,
            "estimated_total_embedding_tokens": sum(estimates),
        },
        "samples": [
            {
                "id": chunk.id,
                "chapter": chunk.chapter,
                "page_start": chunk.page_start,
                "page_end": chunk.page_end,
                "text": " ".join(chunk.text.split())[:240],
            }
            for chunk in chunks[:5]
        ],
    }
    if json_output:
        typer.echo(json.dumps(summary, indent=2, sort_keys=True))
    else:
        typer.echo(f"pages: {summary['page_count']}")
        typer.echo(f"chunks: {summary['chunk_count']}")
        typer.echo(
            f"estimated embedding tokens: "
            f"{summary['token_estimates']['estimated_total_embedding_tokens']}"
        )
        for chapter in summary["chapters"]:
            typer.echo(
                f"chapter: {chapter['title']} "
                f"(pages {chapter['start_page']}-{chapter['end_page']})"
            )
