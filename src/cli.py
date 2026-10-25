"""Command-line entry point; stage-specific commands arrive with their stages."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Annotated, Any

import typer

from config import Settings
from evaluation import evaluate_cases, load_cases
from pipeline import AnalyseInput, analyse_call
from playbook import (
    chunk_playbook,
    extract_playbook,
    index_playbook,
    load_playbook_spec,
    open_playbook,
)
from playbook.eval import evaluate_retrieval, load_queries
from playbook.retriever import PlaybookRetriever
from schemas import CallReport

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


@app.command("evaluate")
def evaluate_command(
    cases: Annotated[Path, typer.Option("--cases")],
) -> None:
    """Evaluate saved reports against an offline YAML case set."""
    summary = evaluate_cases(load_cases(cases), cases.parent)
    typer.echo(summary.model_dump_json(indent=2))


@app.command("analyse")
def analyse_command(
    audio_path: Path,
    rubric_path: Annotated[Path, typer.Option("--rubric")] = Path("rubrics/sales_v1.yaml"),
    playbook_path: Annotated[Path | None, typer.Option("--playbook")] = None,
    fake: Annotated[
        bool, typer.Option("--fake", help="Use the offline synthetic transcriber.")
    ] = False,
    no_grounding: Annotated[bool, typer.Option("--no-grounding")] = False,
    output: Annotated[Path | None, typer.Option("--output", "-o")] = None,
) -> None:
    """Analyse one call and print or save its schema-valid JSON report."""
    report = asyncio.run(
        analyse_call.ainvoke(
            AnalyseInput(
                audio_path=audio_path,
                rubric_path=rubric_path,
                playbook_path=playbook_path,
                grounding=not no_grounding,
                fake=fake,
            )
        )
    )
    rendered = report.model_dump_json(indent=2)
    if output is None:
        typer.echo(rendered)
    else:
        output.write_text(rendered + "\n")


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


@playbook_app.command("index")
def index_playbook_command(
    spec_path: Path,
    rebuild: bool = typer.Option(False, "--rebuild"),
    yes: bool = typer.Option(False, "--yes"),
) -> None:
    """Build or resume a persistent playbook index."""
    spec = load_playbook_spec(spec_path)
    manifest = index_playbook(spec, rebuild=rebuild, yes=yes)
    typer.echo(
        f"{manifest['status']}: {manifest['actual_chunk_count']}/"
        f"{manifest['expected_chunk_count']} chunks"
    )


@playbook_app.command("status")
def playbook_status(spec_path: Path) -> None:
    """Print the manifest and live collection count."""
    from playbook.index import manifest_path, open_playbook

    spec = load_playbook_spec(spec_path)
    path = manifest_path(spec, Settings())
    manifest = json.loads(path.read_text()) if path.exists() else {"status": "missing"}
    live_count = None
    if manifest.get("status") == "complete":
        live_count = open_playbook(spec).count()
    typer.echo(json.dumps({"manifest": manifest, "live_collection_count": live_count}, indent=2))


@playbook_app.command("query")
def query_playbook(
    spec_path: Path,
    query: str,
    k: int = typer.Option(5, min=1),
    full: bool = typer.Option(False, "--full"),
) -> None:
    """Query an indexed playbook and print scored citations."""
    spec = load_playbook_spec(spec_path)
    retriever = PlaybookRetriever(index=open_playbook(spec), top_k=k)
    for document in retriever.invoke(query):
        excerpt = document.page_content if full else " ".join(document.page_content.split())[:200]
        typer.echo(
            f"[{document.metadata['score']:.3f}] {document.metadata.get('chapter')} "
            f"pp. {document.metadata.get('page_start')}-{document.metadata.get('page_end')} "
            f"{document.metadata.get('passage_id')}\n{excerpt}\n"
        )


@playbook_app.command("eval-retrieval")
def eval_retrieval(
    spec_path: Path,
    queries: Annotated[Path, typer.Option(..., "--queries")],
) -> None:
    """Evaluate retrieval against chapter/page references in a YAML file."""
    spec = load_playbook_spec(spec_path)
    retriever = PlaybookRetriever(index=open_playbook(spec))
    typer.echo(json.dumps(evaluate_retrieval(retriever, load_queries(queries)), indent=2))
