"""The ``truehand`` command.

Thin by design: parse flags, build a :class:`~truehand.paths.Paths`, hand off
to a pipeline. No domain logic lives here.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Annotated

import typer

from .. import __version__
from ..errors import TrueHandError
from ..paths import Paths

app = typer.Typer(
    name="truehand",
    help="Tooling for the Crew of the True Hand campaign archive.",
    no_args_is_help=True,
    add_completion=True,
)


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"truehand {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    ctx: typer.Context,
    root: Annotated[
        Path | None,
        typer.Option(
            "--root",
            help="Campaign archive root. Defaults to $TRUEHAND_ROOT, else an "
            "upward search from the current directory.",
        ),
    ] = None,
    _version: Annotated[
        bool,
        typer.Option("--version", callback=_version_callback, is_eager=True,
                     help="Show the version and exit."),
    ] = False,
) -> None:
    """Resolve the archive root once, for every subcommand."""
    ctx.obj = Paths.at(root) if root is not None else None


def resolve_paths(ctx: typer.Context) -> Paths:
    """The archive for this invocation, discovered lazily.

    Deferred out of the callback so ``--help`` and ``--version`` work from
    anywhere, not only from inside an archive.
    """
    if ctx.obj is None:
        ctx.obj = Paths.discover()
    return ctx.obj


from .site import site_app  # imported here: it needs `app` to exist first

app.add_typer(site_app, name="site")


def run() -> None:
    """Console-script wrapper: map our exceptions onto exit codes."""
    try:
        app()
    except TrueHandError as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(exc.exit_code) from exc
