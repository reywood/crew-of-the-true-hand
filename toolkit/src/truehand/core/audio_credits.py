"""What the show owes the music it uses.

`sessions/library/audio/CREDITS.md` records every asset's source and licence,
and the archive's rule is that it must do so *before* the asset can be used.
Which of those licences actually *require* attribution — CC-BY does, the
Pixabay Content License does not — is a legal fact about the show, not a
rendering choice, so it is decided once here rather than inside the RSS
renderer where it used to live behind a process-global cache keyed on nothing.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class AudioCredits:
    """The attribution the episodes carry, in CREDITS.md order."""

    #: Wording a licence obliges us to reproduce.
    required: tuple[str, ...] = ()
    #: Courtesy credits, given because it is decent, not because we must.
    voluntary: tuple[str, ...] = ()

    def __bool__(self) -> bool:
        return bool(self.required or self.voluntary)

    def as_text(self) -> str:
        """The block appended to every episode's description. Empty when there
        is nothing to credit."""
        if not self:
            return ""
        lines = ["Music & SFX credits:"]
        lines += [f"\u2022 {c}" for c in self.required]
        if self.voluntary:
            lines.append("Additional sound effects & ambience (Pixabay Content "
                         "License, attribution not required): "
                         + "; ".join(self.voluntary) + ".")
        return "\n".join(lines)

    @classmethod
    def load(cls, paths) -> AudioCredits:
        parsed = _parse(paths)
        return cls(required=tuple(parsed["required"]),
                   voluntary=tuple(parsed["voluntary"]))


def _parse(paths):
    """Parse sessions/library/audio/CREDITS.md into a list of asset dicts.

    Each asset is a ``## <name>`` section carrying a ``**License**:`` line.
    We split the required-attribution assets (CC-BY and friends, whose license
    is a license condition) from the voluntary ones (Pixabay Content License,
    where attribution is a courtesy, not a requirement).

    Returns a dict with two lists of plain-text credit strings:
      {"required": [...], "voluntary": [...]}
    Both are ordered as they appear in CREDITS.md.
    """
    result = {"required": [], "voluntary": []}
    try:
        text = paths.audio_credits.read_text(encoding="utf-8")
    except OSError:
        return result

    # Split into ``## <name>`` sections (skip the file's own preamble).
    sections = re.split(r"^##\s+(.+?)\s*$", text, flags=re.MULTILINE)
    # re.split with one capture group yields: [preamble, name1, body1, name2, body2, ...]
    for i in range(1, len(sections), 2):
        name = sections[i].strip()
        body = sections[i + 1] if i + 1 < len(sections) else ""

        lic_m = re.search(r"^\s*[-*]\s*\*\*License\*\*:\s*(.+?)\s*$",
                          body, flags=re.MULTILINE)
        license_line = lic_m.group(1).strip() if lic_m else ""
        # Strip markdown link syntax <...> from the trailing license URL.
        license_line = re.sub(r"\s*—\s*<[^>]+>\s*$", "", license_line).strip()

        # Attribution is required when the license itself demands it. Pixabay's
        # Content License does not; Creative Commons "Attribution" (CC BY) does.
        requires = bool(re.search(r"attribution", license_line, re.IGNORECASE)) \
            and "pixabay" not in license_line.lower()

        if requires:
            # Pull the required-attribution blockquote (the ``> ...`` lines that
            # follow the "Required attribution wording" note).
            quote_lines = []
            capture = False
            for ln in body.split("\n"):
                if re.search(r"required attribution wording", ln, re.IGNORECASE):
                    capture = True
                    continue
                if capture:
                    m = re.match(r"^\s*>\s?(.*)$", ln)
                    if m:
                        if m.group(1).strip():
                            quote_lines.append(m.group(1).strip())
                    elif quote_lines:
                        break
            wording = " — ".join(quote_lines) if quote_lines else name
            result["required"].append(f"{wording}  (used in {name})")
        else:
            # Voluntary credit: use the plain-text fallback line if present.
            fb_m = re.search(r"Plain-text fallback:\s*\*?(.+?)\*?\s*$",
                             body, flags=re.MULTILINE)
            if fb_m:
                result["voluntary"].append(fb_m.group(1).strip().rstrip("."))

    return result
