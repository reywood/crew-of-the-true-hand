#!/usr/bin/env python3
"""
Scan session summaries for entity mentions and write the discovered
session dates into each NPC and location markdown file's frontmatter
as a `sessions:` field.

Usage:
    python3 scripts/update-entity-sessions.py            # update all NPCs + locations
    python3 scripts/update-entity-sessions.py --dry-run  # print what would change

Design:
- Reads each session's summary at `summaries/YYYY-MM-DD.md`.
- For each entity, matches against every alias in its `aliases:` field,
  word-boundary + case-sensitive (proper nouns work best that way).
- Writes back a `sessions: 2025-09-23, 2025-11-12, ...` line into the
  frontmatter, sorted ascending. Replaces an existing `sessions:` field
  if present.
- If no aliases match, the `sessions:` field is removed entirely.

The website generator (website/generate.py) reads the `sessions:` field
and surfaces it as clickable chips on the detail page. Re-run this script
whenever a new summary is added (or aliases change) so entity pages stay
in sync with the sessions their subjects actually appear in.
"""

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SUMMARIES_DIR = ROOT / "summaries"
NPC_DIR = ROOT / "npcs"
LOC_DIR = ROOT / "locations"
ITEM_DIR = ROOT / "items"


def parse_frontmatter(text: str):
    """Match the generator's parse_frontmatter behavior: return (dict, body).
    Comma-separated values become lists."""
    if not text.startswith("---"):
        return {}, text
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n?", text, re.DOTALL)
    if not m:
        return {}, text
    body = text[m.end():]
    fm = {}
    for line in m.group(1).split("\n"):
        if ":" not in line:
            continue
        k, _, v = line.partition(":")
        k, v = k.strip(), v.strip()
        fm[k] = v
    return fm, body


def parse_aliases_field(raw):
    """The aliases: field is a raw string like "Fiz, Hisfiz, Spinfizzler"."""
    if not raw:
        return []
    return [a.strip() for a in raw.split(",") if a.strip()]


def load_session_summaries():
    """Return {date: full_summary_text} for every summary on disk."""
    out = {}
    if not SUMMARIES_DIR.exists():
        return out
    for p in sorted(SUMMARIES_DIR.glob("*.md")):
        out[p.stem] = p.read_text(encoding="utf-8")
    return out


def find_sessions(aliases, session_texts):
    """Return sorted list of session dates whose summaries mention any alias
    (word-boundary + case-sensitive)."""
    if not aliases:
        return []
    pattern = re.compile(
        r"\b(?:" + "|".join(re.escape(a) for a in aliases) + r")\b"
    )
    hits = [date for date, text in session_texts.items() if pattern.search(text)]
    return sorted(hits)


def write_sessions_field(path: Path, sessions: list, dry_run: bool) -> str:
    """Update `sessions:` in path's frontmatter. Returns a change tag:
    'unchanged', 'updated', 'removed', or 'added'."""
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return "unchanged"  # no frontmatter, skip
    m = re.match(r"^(---\s*\n)(.*?)(\n---\s*\n?)", text, re.DOTALL)
    if not m:
        return "unchanged"
    open_delim, fm_body, close_delim = m.groups()
    rest = text[m.end():]

    # Split the frontmatter into lines so we can add/replace the sessions line
    # while preserving the order of other fields.
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
        if fm_lines[existing_idx].strip() == new_line:
            tag = "unchanged"
        else:
            fm_lines[existing_idx] = new_line
            tag = "updated"
    elif existing_idx is None and new_line is not None:
        # Insert the sessions field just after the aliases field if we can
        # find it, otherwise append to the frontmatter tail.
        insert_at = len(fm_lines)
        for i, line in enumerate(fm_lines):
            if re.match(r"^\s*aliases\s*:", line):
                insert_at = i + 1
                break
        fm_lines.insert(insert_at, new_line)
        tag = "added"

    if tag == "unchanged":
        return tag

    if not dry_run:
        new_fm_body = "\n".join(fm_lines)
        path.write_text(open_delim + new_fm_body + close_delim + rest,
                        encoding="utf-8")
    return tag


def process_dir(directory: Path, session_texts: dict, dry_run: bool) -> dict:
    counts = {"unchanged": 0, "updated": 0, "removed": 0, "added": 0}
    for entity_path in sorted(directory.glob("*.md")):
        text = entity_path.read_text(encoding="utf-8")
        fm, _ = parse_frontmatter(text)
        aliases_raw = fm.get("aliases", "")
        # aliases may have come back as a list from the "," split. Normalize.
        if isinstance(aliases_raw, list):
            aliases = [a for a in aliases_raw if a]
        else:
            aliases = parse_aliases_field(aliases_raw)
        if not aliases:
            # Fall back to filename-derived name so at least something is checked
            aliases = [entity_path.stem.replace("-", " ").title()]

        sessions = find_sessions(aliases, session_texts)
        tag = write_sessions_field(entity_path, sessions, dry_run)
        counts[tag] += 1
        if tag != "unchanged":
            hits = ", ".join(sessions) if sessions else "(none)"
            print(f"  {tag:8s} {entity_path.name:40s} -> {hits}")
    return counts


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--dry-run", action="store_true",
                        help="Print changes without writing files.")
    args = parser.parse_args()

    session_texts = load_session_summaries()
    if not session_texts:
        print("ERROR: no summaries found under summaries/.", file=sys.stderr)
        return 1

    print(f"Scanning {len(session_texts)} session summaries.\n")

    print("NPCs:")
    npc_counts = process_dir(NPC_DIR, session_texts, args.dry_run)
    print(f"  {sum(npc_counts.values())} files, "
          f"{npc_counts['updated'] + npc_counts['added'] + npc_counts['removed']} changes\n")

    print("Locations:")
    loc_counts = process_dir(LOC_DIR, session_texts, args.dry_run)
    print(f"  {sum(loc_counts.values())} files, "
          f"{loc_counts['updated'] + loc_counts['added'] + loc_counts['removed']} changes\n")

    print("Items:")
    item_counts = process_dir(ITEM_DIR, session_texts, args.dry_run) if ITEM_DIR.exists() else {"unchanged": 0, "updated": 0, "removed": 0, "added": 0}
    print(f"  {sum(item_counts.values())} files, "
          f"{item_counts['updated'] + item_counts['added'] + item_counts['removed']} changes\n")

    if args.dry_run:
        print("(dry run — no files written)")
    else:
        print("Next: python3 website/generate.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
