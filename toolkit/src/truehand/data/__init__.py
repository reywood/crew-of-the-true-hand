"""Campaign and show data held as TOML rather than Python source.

These are values the archive's authors edit as part of writing the campaign or
producing an episode, not program logic, so they do not belong in code:

  ``party``              the four PCs — names, aliases, one-line blurbs
  ``session_locations``  which locations each session took place in
  ``map``                where each location sits on the chart
  ``npc_standing``       how the crew stands with each NPC, as chip vocabulary
  ``quest_dependencies`` which quest advances which
  ``audio_direction``    delivery presets, cue-to-asset maps and mix levels

Read with stdlib `tomllib`, so this costs no dependency.
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
