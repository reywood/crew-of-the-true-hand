"""Small pure text helpers shared across the whole toolkit."""

import html
import re
from pathlib import Path


def slugify(s):
    s = s.replace("'", "").replace("’", "")
    s = re.sub(r"[^\w\s-]", "", s.lower())
    s = re.sub(r"[\s_-]+", "-", s).strip("-")
    return s


def read(p):
    return Path(p).read_text(encoding="utf-8", errors="replace")


def share_text(raw, limit=280):
    """Flatten markdown/HTML to a single plain line for a link preview.

    Discord, Slack and iMessage show roughly 2–4 lines of description, so this
    strips markup, collapses whitespace, and truncates on a word boundary.
    """
    if not raw:
        return ""
    txt = re.sub(r"<[^>]+>", "", str(raw))            # tags
    txt = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", txt)     # images
    txt = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", txt)  # links → text
    txt = re.sub(r"[*_`#>]+", "", txt)                 # emphasis / headings
    txt = html.unescape(txt)
    txt = re.sub(r"\s+", " ", txt).strip()
    if len(txt) > limit:
        txt = txt[:limit].rsplit(" ", 1)[0].rstrip(",.;:—- ") + "…"
    return txt


def chunk_transcript(text):
    text = text.strip()
    if not text:
        return []
    text_n = re.sub(r"\s+", " ", text)
    sentences = re.split(r"(?<=[.!?])\s+", text_n)
    out = []
    for i in range(0, len(sentences), 6):
        chunk = " ".join(sentences[i:i+6]).strip()
        if chunk:
            out.append(chunk)
    return out


def _normalize_tag_list(value):
    """Coerce a frontmatter field (string, list, or None) to a lowercased,
    stripped list of tag strings."""
    if not value:
        return []
    if isinstance(value, str):
        parts = [p.strip() for p in value.split(",")]
    else:
        parts = [str(p).strip() for p in value]
    return [p.lower() for p in parts if p]


def _norm_heading(h):
    return h.strip().rstrip(":").replace("’", "'").lower()


def _extract_session_dates(value):
    """Normalize a frontmatter sessions field into a list of YYYY-MM-DD."""
    if not value:
        return []
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    return [s.strip() for s in str(value).split(",") if s.strip()]


def _hms(seconds):
    if seconds <= 0:
        return "00:00"
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


def _extract_in_brief(summary_md):
    for ln in (summary_md or "").split("\n"):
        s = ln.strip()
        if s.startswith("*In brief:") and s.endswith("*"):
            return s[len("*In brief:"):-1].strip()
    return ""


def _clean_blurb(text, limit=200):
    """A short plain-text blurb for a node: strip markdown emphasis/links/code."""
    if not text:
        return ""
    s = text.strip().split("\n", 1)[0].strip()
    s = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", s)   # [txt](url) -> txt
    s = re.sub(r"[*`_]", "", s)                        # emphasis / code marks
    s = re.sub(r"\s+", " ", s).strip()
    if len(s) > limit:
        s = s[:limit].rsplit(" ", 1)[0] + "…"
    return s
