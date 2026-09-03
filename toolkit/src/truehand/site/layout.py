"""Page chrome: nav, <head>, share metadata, and the static-asset cache buster."""

import hashlib
import html
import os

from ..core.text import share_text

DEFAULT_BASE_URL = os.environ.get(
    "_BASE_URL",
    "https://crewofthetruehand.com",
).rstrip("/")


_STATIC_DIR = None


_BASE_URL = DEFAULT_BASE_URL


_STATIC_VER_CACHE = {}


def base_url():
    """The public base URL for absolute links.

    An accessor, not a module constant re-exported by value: configure() runs
    after the other modules have been imported, so a `from .layout import
    _BASE_URL` elsewhere would freeze the default and silently ignore
    --base-url.
    """
    return _BASE_URL


def configure(static_dir, base_url):
    """Set the ambient presentation config. Called once by build_site()."""
    global _STATIC_DIR, _BASE_URL
    _STATIC_DIR = static_dir
    _BASE_URL = base_url
    _STATIC_VER_CACHE.clear()


def static_url(name):
    """Return static/<name> with a content-hash cache-buster (?v=…) so browsers
    refetch the asset only when its bytes actually change. Falls back to the
    bare path if the source file is missing."""
    if name not in _STATIC_VER_CACHE:
        src = _STATIC_DIR / name
        try:
            digest = hashlib.sha256(src.read_bytes()).hexdigest()[:8]
        except OSError:
            digest = None
        _STATIC_VER_CACHE[name] = digest
    digest = _STATIC_VER_CACHE[name]
    return f"static/{name}?v={digest}" if digest else f"static/{name}"


NAV = [
    ("index.html", "Home"),
    ("next.html", "Prep"),
    ("sessions.html", "Sessions"),
    ("characters.html", "Characters"),
    ("npcs.html", "NPCs"),
    ("locations.html", "Locations"),
    ("items.html", "Items"),
    ("quests.html", "Quests"),
]


def render_nav(current=None):
    items = []
    for href, label in NAV:
        cls = ' class="active"' if href == current else ""
        items.append(f'<a href="{href}"{cls}>{label}</a>')
    return '<nav class="site-nav">' + "".join(items) + "</nav>"


SITE_NAME = "Crew of the True Hand"


DEFAULT_SHARE_IMAGE = "static/podcast-cover.jpg"


DEFAULT_SHARE_DESC = (
    "A D&D 5e campaign archive: session recaps, the crew, the folk they've met, "
    "the places they've been, and the threads still hanging."
)


def _abs_url(path):
    return f"{_BASE_URL}/{path.lstrip('/')}" if path else ""


def share_meta(title, description, image, canonical, og_type, audio=None):
    """Open Graph + Twitter Card tags, so links unfurl in Discord/Slack/iMessage."""
    desc = share_text(description) or DEFAULT_SHARE_DESC
    img = _abs_url(image or DEFAULT_SHARE_IMAGE)
    # No site-name suffix here: og:site_name is rendered on its own line above
    # the title in Discord/Slack, so repeating it just eats the title's width.
    full_title = title
    t = [
        f'<meta name="description" content="{html.escape(desc)}">',
        f'<meta property="og:site_name" content="{html.escape(SITE_NAME)}">',
        f'<meta property="og:type" content="{og_type}">',
        f'<meta property="og:title" content="{html.escape(full_title)}">',
        f'<meta property="og:description" content="{html.escape(desc)}">',
        f'<meta property="og:image" content="{html.escape(img)}">',
        '<meta name="twitter:card" content="summary_large_image">',
        f'<meta name="twitter:title" content="{html.escape(full_title)}">',
        f'<meta name="twitter:description" content="{html.escape(desc)}">',
        f'<meta name="twitter:image" content="{html.escape(img)}">',
        # Discord tints the left edge of the embed with this.
        '<meta name="theme-color" content="#c19a4a">',
    ]
    if canonical:
        t.insert(1, f'<link rel="canonical" href="{html.escape(_abs_url(canonical))}">')
        t.insert(2, f'<meta property="og:url" content="{html.escape(_abs_url(canonical))}">')
    if audio:
        t.append(f'<meta property="og:audio" content="{html.escape(_abs_url(audio))}">')
        t.append('<meta property="og:audio:type" content="audio/mpeg">')
    return "\n".join(t)


def page(title, body, current_nav=None, breadcrumb=None,
         description=None, image=None, canonical=None,
         og_type="website", audio=None, share_title=None):
    nav = render_nav(current_nav)
    bc = f'<div class="breadcrumb">{breadcrumb}</div>' if breadcrumb else ""
    meta = share_meta(share_title or title, description, image,
                      canonical, og_type, audio)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)} — Crew of the True Hand</title>
{meta}
<link rel="alternate" type="application/rss+xml" title="Tales of the True Hand" href="feed.xml">
<link rel="stylesheet" href="{static_url('style.css')}">
<script defer src="{static_url('podcast-subscribe.js')}"></script>
<script defer src="{static_url('search.js')}"></script>
</head>
<body>
<header class="site-header">
  <div class="site-title"><a href="index.html"><span class="anchor">⚓</span> Crew of the <em>True Hand</em></a></div>
  {nav}
  <div class="site-search-wrap">
    <input type="search" id="site-search" placeholder="Search the archive…" autocomplete="off" aria-label="Search the archive">
    <div id="search-results" class="search-results" hidden></div>
  </div>
</header>
<main class="content">
{bc}
{body}
</main>
<footer class="site-footer">
  <div class="rope-divider"></div>
  <p>Tales from the sea and the giant-haunted North.</p>
</footer>
</body>
</html>
"""
