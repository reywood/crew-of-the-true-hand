"""Refreshing the ``sessions:`` frontmatter field on NPCs, locations and items.

Scans every session summary and records, in each entity's frontmatter, the
sessions whose summary mentions one of its aliases. The site renders that as
the "Mentioned in sessions" chip row.

Was scripts/update-entity-sessions.py, which carried its own cut-down copy of
parse_frontmatter that understood neither YAML-style bullet lists nor the
comma-splitting its own docstring claimed. It now uses the canonical parser in
core/frontmatter.py, which makes the previously dead ``isinstance(..., list)``
branch below actually reachable.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from ..core.frontmatter import parse_frontmatter

#: Change tags, in the order they are reported.
TAGS = ("added", "updated", "removed", "unchanged")


@dataclass
class SyncResult:
    """What happened to one directory of entity files."""

    directory: Path
    counts: dict[str, int] = field(default_factory=lambda: dict.fromkeys(TAGS, 0))
    changes: list[tuple[str, str, list[str]]] = field(default_factory=list)

    @property
    def changed(self) -> int:
        return sum(self.counts[t] for t in TAGS if t != "unchanged")

    @property
    def total(self) -> int:
        return sum(self.counts.values())


def parse_aliases_field(raw) -> list[str]:
    """Normalize an ``aliases:`` value to a list.

    The canonical parser returns a list when the value is comma-separated or a
    bullet list, and a plain string otherwise.
    """
    if not raw:
        return []
    if isinstance(raw, list):
        return [a.strip() for a in raw if str(a).strip()]
    return [a.strip() for a in str(raw).split(",") if a.strip()]


def load_session_summaries(paths) -> dict[str, str]:
    """Return ``{date: summary_text}`` for every session summary on disk."""
    out: dict[str, str] = {}
    if not paths.sessions.exists():
        return out
    for p in sorted(paths.sessions.glob("*/summary.md")):
        out[p.parent.name] = p.read_text(encoding="utf-8")
    return out


def find_sessions(aliases: list[str], session_texts: dict[str, str]) -> list[str]:
    """Session dates whose summary mentions any alias (word-boundary, case-sensitive)."""
    if not aliases:
        return []
    pattern = re.compile(r"\b(?:" + "|".join(re.escape(a) for a in aliases) + r")\b")
    return sorted(date for date, text in session_texts.items() if pattern.search(text))


def write_sessions_field(path: Path, sessions: list[str], dry_run: bool) -> str:
    """Update ``sessions:`` in *path*'s frontmatter.

    Returns one of 'unchanged', 'updated', 'removed', 'added'. Files without
    frontmatter are left alone.
    """
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return "unchanged"
    m = re.match(r"^(---\s*\n)(.*?)(\n---\s*\n?)", text, re.DOTALL)
    if not m:
        return "unchanged"
    open_delim, fm_body, close_delim = m.groups()
    rest = text[m.end():]

    # Work line-wise so the order of the other fields is preserved.
    fm_lines = fm_body.split("\n")
    new_line = f"sessions: {', '.join(sessions)}" if sessions else None

    existing_idx = None
    for i, line in enumerate(fm_lines):
        if re.match(r"^\s*sessions\s*:", line):
            existing_idx = i
            break

    tag = "unchanged"
    if existing_idx is not None and new_line is None:
        del fm_lines[existing_idx]
        tag = "removed"
    elif existing_idx is not None and new_line is not None:
        if fm_lines[existing_idx].strip() != new_line:
            fm_lines[existing_idx] = new_line
            tag = "updated"
    elif existing_idx is None and new_line is not None:
        # Sit the field just after aliases: when there is one, else append.
        insert_at = len(fm_lines)
        for i, line in enumerate(fm_lines):
            if re.match(r"^\s*aliases\s*:", line):
                insert_at = i + 1
                break
        fm_lines.insert(insert_at, new_line)
        tag = "added"

    if tag != "unchanged" and not dry_run:
        path.write_text(open_delim + "\n".join(fm_lines) + close_delim + rest,
                        encoding="utf-8")
    return tag


def sync_directory(directory: Path, session_texts: dict[str, str],
                   dry_run: bool) -> SyncResult:
    """Refresh every ``*.md`` in *directory*."""
    result = SyncResult(directory=directory)
    for entity_path in sorted(directory.glob("*.md")):
        fm, _ = parse_frontmatter(entity_path.read_text(encoding="utf-8"))
        aliases = parse_aliases_field(fm.get("aliases", ""))
        if not aliases:
            # Nothing declared: fall back to the filename so the entity is at
            # least checked against something.
            aliases = [entity_path.stem.replace("-", " ").title()]

        sessions = find_sessions(aliases, session_texts)
        tag = write_sessions_field(entity_path, sessions, dry_run)
        result.counts[tag] += 1
        if tag != "unchanged":
            result.changes.append((tag, entity_path.name, sessions))
    return result


def sync(paths, *, dry_run: bool = False) -> list[SyncResult]:
    """Refresh npcs/, locations/ and items/ against every session summary."""
    session_texts = load_session_summaries(paths)
    return [
        sync_directory(d, session_texts, dry_run)
        for d in (paths.npcs, paths.locations, paths.items)
    ]
