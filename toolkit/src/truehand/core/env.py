"""Reading .env, and requiring keys from the environment.

Replaces four copied load_dotenv implementations. Three stripped surrounding
quotes from values; the fourth (generate-character-references.py) used
split("=", 1) and did not, so GEMINI_API_KEY="abc" would have yielded a key
with literal quote marks. It only ever worked because the repo's .env happens
to be unquoted. This is the quote-stripping behaviour.
"""

from __future__ import annotations

import os
from pathlib import Path

from ..errors import UserError


def load_dotenv(path: Path) -> None:
    """Load KEY=VALUE lines from *path*. Real environment variables win.

    Blank lines and ``#`` comments are skipped; surrounding single or double
    quotes are stripped from the value.
    """
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def require_env(name: str, *, why: str) -> str:
    """Return environment variable *name*, or raise with a usable message."""
    value = os.environ.get(name)
    if not value:
        raise UserError(
            f"{why} needs {name}, which is not set.\n"
            f"  Put it in the archive's .env file (one line: {name}=...) "
            f"or export it."
        )
    return value
