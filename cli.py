"""Thin CLI entry point. All business logic lives in the doc_classifier package."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import click

from doc_classifier.processor import process_files


@click.group()
def cli() -> None:
    """doc-classifier: classify business documents from PDFs using an LLM."""


def _expand_paths(paths: tuple[str, ...]) -> list[str]:
    """Expand any directories in `paths` to the PDF files directly inside them."""
    expanded: list[str] = []
    for raw_path in paths:
        path = Path(raw_path)
        if path.is_dir():
            pdfs = sorted(path.glob("*.pdf"))
            if not pdfs:
                raise click.UsageError(f"No PDF files found in directory: {path}")
            expanded.extend(str(p) for p in pdfs)
        else:
            expanded.append(raw_path)
    return expanded


@cli.command()
@click.argument("files", nargs=-1, required=True, type=click.Path(exists=True))
@click.option("--contractor-id", default=None, help="Optional contractor ID to attach to each result.")
@click.option("--output", "output_path", default=None, type=click.Path(dir_okay=False), help="Write JSON array of results to this file instead of stdout.")
def upload(files: tuple[str, ...], contractor_id: str | None, output_path: str | None) -> None:
    """Upload one or more PDF files (or directories of PDFs) and classify each with an LLM."""
    file_paths = _expand_paths(files)
    results = process_files(file_paths, contractor_id=contractor_id)

    for result in results:
        click.echo(
            f"{result.file_name}: {result.document_type} "
            f"({result.document_type_confidence}% confidence)",
            err=True,
        )

    payload = [r.model_dump() for r in results]
    output_json = json.dumps(payload, indent=2)

    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(output_json)
        click.echo(f"Full results written to {output_path}", err=True)
    else:
        click.echo(output_json)

    if any(r.document_type == "error" for r in results):
        sys.exit(1)


if __name__ == "__main__":
    cli()
