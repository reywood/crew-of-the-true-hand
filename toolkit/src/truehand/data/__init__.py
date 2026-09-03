"""Campaign and presentation data held as TOML rather than Python source.

These are values the archive's authors edit as part of writing the campaign —
which sessions happened where, where each location sits on the chart — so they
do not belong in code. Read with stdlib `tomllib`, so this costs no dependency.
"""

from __future__ import annotations

import tomllib
from functools import cache
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent


@cache
def load(name: str) -> dict:
    """Parse `<name>.toml` from this package. Cached — these never change at runtime."""
    return tomllib.loads((DATA_DIR / f"{name}.toml").read_text(encoding="utf-8"))
