"""Locating the campaign archive, and every path derived from it.

This is the ONLY place the repository root is computed. The scripts this
package replaced each carried their own ``ROOT = Path(__file__).resolve()
.parent.parent`` — six copies, all of which depended on the file sitting
exactly one directory below the root. Packaged code cannot rely on that, so
the root is discovered by walking up for marker files instead.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from .errors import UserError

#: A directory is a campaign archive only if ALL of these exist.
#:
#: Deliberately not ``pyproject.toml``: an upward walk from ``toolkit/src/
#: truehand/`` would stop at ``toolkit/`` and never reach the archive. And
#: deliberately not ``.git``: that binds the tool to a VCS it does not use and
#: breaks on an exported copy.
MARKERS: tuple[str, ...] = ("campaign-state.md", "quests.md", "sessions")

#: Overrides the upward walk entirely.
ROOT_ENV_VAR = "TRUEHAND_ROOT"


def is_archive_root(path: Path) -> bool:
    """True if every marker is present in *path*."""
    return all((path / marker).exists() for marker in MARKERS)


def find_root(start: Path | None = None) -> Path:
    """Locate the campaign archive root.

    ``TRUEHAND_ROOT`` wins if set; otherwise walk up from *start* (default:
    the current working directory).
    """
    override = os.environ.get(ROOT_ENV_VAR)
    if override:
        root = Path(override).expanduser().resolve()
        if not is_archive_root(root):
            raise UserError(
                f"{ROOT_ENV_VAR}={override} is not a campaign archive "
                f"(needs {', '.join(MARKERS)})"
            )
        return root

    begin = (start or Path.cwd()).resolve()
    for candidate in (begin, *begin.parents):
        if is_archive_root(candidate):
            return candidate
    raise UserError(
        f"not inside a campaign archive (looked for {', '.join(MARKERS)} "
        f"in {begin} and its parents); pass --root or set {ROOT_ENV_VAR}"
    )


@dataclass(frozen=True, slots=True)
class Paths:
    """Every path the toolkit reads or writes, derived from one root.

    Passed as the first argument to the loaders so they can be pointed at a
    fixture archive in tests rather than the real one.
    """

    root: Path

    @classmethod
    def at(cls, root: Path) -> Paths:
        return cls(Path(root).resolve())

    @classmethod
    def discover(cls, start: Path | None = None) -> Paths:
        return cls.at(find_root(start))

    # -- content ---------------------------------------------------------
    @property
    def characters(self) -> Path:
        return self.root / "characters"

    @property
    def character_references(self) -> Path:
        return self.characters / "references"

    @property
    def battle_cards(self) -> Path:
        return self.root / "battle-cards"

    @property
    def npcs(self) -> Path:
        return self.root / "npcs"

    @property
    def locations(self) -> Path:
        return self.root / "locations"

    @property
    def items(self) -> Path:
        return self.root / "items"

    @property
    def sessions(self) -> Path:
        return self.root / "sessions"

    @property
    def audio_library(self) -> Path:
        return self.sessions / "library" / "audio"

    @property
    def audio_credits(self) -> Path:
        return self.audio_library / "CREDITS.md"

    @property
    def quests_file(self) -> Path:
        return self.root / "quests.md"

    @property
    def campaign_state_file(self) -> Path:
        return self.root / "campaign-state.md"

    @property
    def env_file(self) -> Path:
        return self.root / ".env"

    # -- website (content and output; these stay outside the package) -----
    @property
    def web(self) -> Path:
        return self.root / "website"

    @property
    def static(self) -> Path:
        return self.web / "static"

    @property
    def site(self) -> Path:
        return self.web / "site"

    # -- per-session helpers ---------------------------------------------
    def session(self, date: str) -> Path:
        return self.sessions / date

    def session_audio(self, date: str) -> Path:
        return self.session(date) / "audio"

    def session_images(self, date: str) -> Path:
        return self.session(date) / "images"

    def session_summary(self, date: str) -> Path:
        return self.session(date) / "summary.md"
