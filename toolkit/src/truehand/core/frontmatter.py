"""The archive's frontmatter dialect.

This is NOT YAML — see toolkit/tests/test_frontmatter.py. Real YAML fails on
this corpus: campaign-state.md raises a ScannerError, `aliases: A, B` becomes
a scalar instead of a list in 48 files, and 103 date-shaped fields come back
as datetime.date instead of str.

`parse_frontmatter` is the dialect: it says what the file means. `Frontmatter`
and `Field` are how the rest of the archive reads it. The dialect decides
str-vs-list by whether a value contains a comma, which is right for the corpus
but leaves every reader holding a `str | list[str] | None`. Twenty call sites
used to hand-coerce that through seven near-duplicate helpers — `site/pages/
npcs.py` alone did it three times and three different ways, joining a list with
", " twice and taking `[0]` once. A Field is asked what shape you want instead
of tested for what shape it is.
"""

import re
from collections.abc import Mapping


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


class Field:
    """One frontmatter value, read by intent rather than by isinstance.

    The dialect's str-vs-list split is incidental to nearly every reader, so
    say what you want out of it:

      ``one()``   a single scalar — location, holder, type, origin
      ``many()``  every value — aliases, expertise tags, session dates
      ``prose()`` the source line rejoined — prose the comma-split fragmented
      ``tags()``  lowercased values, for tag matching
    """

    __slots__ = ("raw",)

    def __init__(self, raw=None):
        self.raw = raw

    def one(self, default: str = "") -> str:
        """The first scalar, stripped. `default` when there is nothing."""
        value = self.raw
        if isinstance(value, list):
            value = value[0] if value else ""
        return str(value).strip() if value else default

    def many(self) -> list[str]:
        """Every value, stripped, empties dropped. A bare scalar becomes a
        one-item list; a comma-bearing scalar is split (the dialect usually did
        that already, but campaign-state values reach here unparsed)."""
        value = self.raw
        if not value:
            return []
        if isinstance(value, list):
            return [str(v).strip() for v in value if str(v).strip()]
        return [v.strip() for v in str(value).split(",") if v.strip()]

    def prose(self) -> str:
        """The source line, rejoined.

        The dialect splits any comma-bearing value into a list, which is right
        for aliases and wrong for a sentence. campaign-state.md's objective is a
        paragraph, so it arrived as a list of fragments and a str-only guard
        silently discarded it — next.html rendered no objective at all. Joining
        with ", " reconstructs the line exactly, since the parser split on ","
        and stripped each segment.
        """
        return ", ".join(self.many())

    def tags(self) -> list[str]:
        """Lowercased values, for matching expertise against expertise_needed."""
        return [v.lower() for v in self.many()]

    def __bool__(self) -> bool:
        return bool(self.raw)

    def __repr__(self) -> str:
        return f"Field({self.raw!r})"


#: A Field with nothing in it. Returned for every key a file didn't set, so
#: readers never branch on absence.
EMPTY = Field()


class Frontmatter(Mapping):
    """An entity's frontmatter: a mapping of name -> Field, in file order.

    Lookup is total — a missing key yields an empty Field rather than None or a
    KeyError — so `meta["location"].one()` is safe on every entity whether or
    not that entity's file mentions a location.
    """

    __slots__ = ("_fields",)

    def __init__(self, values=None):
        self._fields = {k: Field(v) for k, v in (values or {}).items()}

    def __getitem__(self, key) -> Field:
        return self._fields.get(key, EMPTY)

    def get(self, key, default=None) -> Field:
        """Total, like __getitem__; `default` supplies the value when unset."""
        found = self._fields.get(key)
        return found if found is not None else Field(default)

    def __iter__(self):
        return iter(self._fields)

    def __len__(self) -> int:
        return len(self._fields)

    def __repr__(self) -> str:
        return f"Frontmatter({ {k: f.raw for k, f in self._fields.items()} !r})"
