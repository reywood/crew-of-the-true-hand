"""Importing an optional dependency, with an actionable error if it is absent.

Typer is the package's only hard dependency: the site build has to work in a
venv with nothing else installed. Every adapter that needs google-genai,
elevenlabs or Pillow resolves it through require() at call time rather than
importing at module scope, so `truehand --help` and `truehand site build`
never touch them.
"""

from __future__ import annotations

import importlib
from types import ModuleType

from ..errors import MissingDependency


def require(module: str, *, extra: str, why: str) -> ModuleType:
    """Import *module*, or raise MissingDependency naming the extra to install."""
    try:
        return importlib.import_module(module)
    except ImportError as exc:
        raise MissingDependency(
            f"{why} needs the '{module}' package, which is not installed.\n"
            f"  Install it with:  .venv/bin/pip install -e 'toolkit[{extra}]'"
        ) from exc
