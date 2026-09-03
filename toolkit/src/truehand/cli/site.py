"""``truehand site`` — build the static campaign site."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from ..site.build import DEFAULT_BASE_URL, build_site
from .app import resolve_paths

site_app = typer.Typer(help="Build the static campaign site.", no_args_is_help=True)


@site_app.command("build")
def build(
    ctx: typer.Context,
    out: Annotated[
        Path | None,
        typer.Option("--out", help="Output directory. Defaults to website/site."),
    ] = None,
    base_url: Annotated[
        str,
        typer.Option("--base-url", help="Public base URL for absolute links in the feed."),
    ] = DEFAULT_BASE_URL,
) -> None:
    """Regenerate website/site/ from the archive sources."""
    paths = resolve_paths(ctx)
    result = build_site(paths, base_url=base_url, out_dir=out)
    counts = result["counts"]
    typer.echo(f"  Podcast feed: /feed.xml with {result['episodes']} episodes")
    typer.echo(f"Generated {result['total']} pages into {result['out_dir']}")
    typer.echo(
        f"  PCs: {counts['pcs']}, NPCs: {counts['npcs']}, "
        f"Locations: {counts['locations']}, Items: {counts['items']}, "
        f"Quests: {counts['quests']}, Sessions: {counts['sessions']}"
    )
