"""``truehand entities`` — keep entity frontmatter in step with the summaries."""

from __future__ import annotations

from typing import Annotated

import typer

from ..pipelines.entity_sessions import sync
from .app import resolve_paths

entities_app = typer.Typer(help="Maintain NPC / location / item frontmatter.",
                           no_args_is_help=True)


@entities_app.command("sync")
def sync_command(
    ctx: typer.Context,
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run", help="Report what would change without writing."),
    ] = False,
) -> None:
    """Refresh each entity's `sessions:` field from the session summaries."""
    paths = resolve_paths(ctx)
    results = sync(paths, dry_run=dry_run)
    for result in results:
        for tag, name, sessions in result.changes:
            hits = ", ".join(sessions) if sessions else "(none)"
            typer.echo(f"  {tag:8s} {name:40s} -> {hits}")
        counts = result.counts
        typer.echo(
            f"{result.directory.name}: {result.total} files, "
            + ", ".join(f"{counts[t]} {t}" for t in ("added", "updated", "removed", "unchanged"))
        )
    if dry_run:
        typer.echo("(dry run — nothing written)")
