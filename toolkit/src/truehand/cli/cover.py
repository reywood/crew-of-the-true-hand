"""``truehand cover`` — the podcast cover art."""

from __future__ import annotations

from typing import Annotated

import typer

from ..adapters.images import DEFAULT_IMAGE_MODEL, GeminiImageBackend
from ..core.env import load_dotenv
from ..pipelines import podcast_cover
from .app import resolve_paths

cover_app = typer.Typer(help="Podcast cover art.", no_args_is_help=True)


@cover_app.command("build")
def build(
    ctx: typer.Context,
    force: Annotated[bool, typer.Option("--force", help="Regenerate even if the cover exists.")] = False,
    model: Annotated[str, typer.Option("--model", help="Gemini image model.")] = DEFAULT_IMAGE_MODEL,
) -> None:
    """Generate website/static/podcast-cover.jpg (1400x1400)."""
    paths = resolve_paths(ctx)
    load_dotenv(paths.env_file)
    result = podcast_cover.generate(paths, GeminiImageBackend(), force=force, model=model)
    for slug in result.missing_portraits:
        typer.secho(f"  WARN: portrait missing for {slug}", fg="yellow", err=True)
    typer.echo(f"{result.status}: {result.path} ({result.detail})")
    if result.status == "written":
        typer.echo("Next: truehand site build")
