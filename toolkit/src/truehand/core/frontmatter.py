"""The archive's frontmatter dialect.

This is NOT YAML — see toolkit/tests/test_frontmatter.py. Real YAML fails on
this corpus: campaign-state.md raises a ScannerError, `aliases: A, B` becomes
a scalar instead of a list in 48 files, and 103 date-shaped fields come back
as datetime.date instead of str."""

import re


def parse_frontmatter(text):
    """Minimal YAML-ish frontmatter parser.

    Handles two list forms in addition to plain scalar values:
      - Inline comma-list:   aliases: Foo, Bar, Baz
      - YAML-style bullets:  carried:
                             - Item one
                             - Item two

    A field with no value on its own line and dashed bullets on the
    following lines becomes a list. Anything else is a scalar (or an
    inline comma-list)."""
    if not text.startswith("---"):
        return {}, text
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n?", text, re.DOTALL)
    if not m:
        return {}, text
    body = text[m.end():]
    fm = {}
    lines = m.group(1).split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]
        if ":" not in line:
            i += 1
            continue
        k, _, v = line.partition(":")
        k, v = k.strip(), v.strip()
        # Empty value + following bullet lines = list.
        if not v:
            items = []
            j = i + 1
            while j < len(lines):
                nxt = lines[j].lstrip()
                if nxt.startswith("- "):
                    items.append(nxt[2:].strip())
                    j += 1
                elif nxt.startswith("-") and len(nxt) > 1 and nxt[1] != " ":
                    # tolerate "-item" with no space
                    items.append(nxt[1:].strip())
                    j += 1
                else:
                    break
            fm[k] = items
            i = j
            continue
        if "," in v:
            v = [x.strip() for x in v.split(",") if x.strip()]
        fm[k] = v
        i += 1
    return fm, body
