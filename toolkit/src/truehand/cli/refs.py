"""``truehand refs`` — the per-PC character reference plates."""

from __future__ import annotations

from typing import Annotated

import typer

from ..adapters.images import DEFAULT_IMAGE_MODEL, GeminiImageBackend
from ..content.pc_identity import PC_SLUGS
from ..core.env import load_dotenv
from ..errors import OperationFailed
from ..pipelines import character_refs
from .app import resolve_paths

refs_app = typer.Typer(help="Character reference plates.", no_args_is_help=True)


@refs_app.command("build")
def build(
    ctx: typer.Context,
    only: Annotated[str | None, typer.Option("--only", help=f"One PC slug: {', '.join(PC_SLUGS)}.")] = None,
    plate: Annotated[int | None, typer.Option("--plate", min=1, max=2, help="Render only plate 1 or 2.")] = None,
    force: Annotated[bool, typer.Option("--force", help="Regenerate even if the plate exists.")] = False,
    model: Annotated[str, typer.Option("--model", help="Gemini image model.")] = DEFAULT_IMAGE_MODEL,
) -> None:
    """Generate characters/references/<slug>-ref-<n>.jpg."""
    paths = resolve_paths(ctx)
    load_dotenv(paths.env_file)
    results = character_refs.generate(paths, GeminiImageBackend(), only=only,
                                      plate=plate, force=force, model=model)
    failures = 0
    for r in results:
        if r.status == "failed":
            failures += 1
            typer.secho(f"  ERROR {r.slug} plate {r.plate}: {r.detail}", fg="red", err=True)
        else:
            typer.echo(f"  {r.status:8s} {r.slug} plate {r.plate}: {r.path.name} {r.detail}")
    if failures:
        raise OperationFailed(f"{failures} plate(s) failed")
