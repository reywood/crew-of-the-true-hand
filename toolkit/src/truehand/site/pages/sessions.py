"""Session list and detail pages."""

import html
import re

from ...core.loaders import SESSION_LOCATIONS
from ...core.markdown import md_inline, md_to_html
from ...core.text import chunk_transcript, slugify
from ..layout import base_url, page
from ..linkify import linkify_html


def session_list_page(sessions, locations, link_map):
    loc_by_slug = {l.slug: l for l in locations}
    rows = []
    for s in sorted(sessions, key=lambda x: x.meta.get("date", x.slug), reverse=True):
        date = s.meta.get("date", s.slug)
        loc_slugs = SESSION_LOCATIONS.get(date, [])
        loc_chips = []
        for slug in loc_slugs:
            loc = loc_by_slug.get(slug)
            if loc:
                loc_chips.append(
                    f'<a class="session-row-loc" href="{loc.href}">{html.escape(loc.name)}</a>'
                )
        if not loc_chips:
            loc_chips.append(
                '<span class="session-row-loc session-row-loc-none">—</span>'
            )
        locs_html = "".join(loc_chips)
        audio_badge = ('<span class="session-row-audio" title="Audio recap available" aria-label="Audio recap available">&#9836;</span>'
                       if s.meta.get("has_audio") else '')
        rows.append(f"""
<li class="session-row">
  <div class="session-row-meta">
    <div class="session-row-date-line">
      <a class="session-row-date" href="{s.href}">{html.escape(date)}</a>{audio_badge}
    </div>
    <div class="session-row-locs">{locs_html}</div>
  </div>
  <p class="session-row-summary">{html.escape(s.summary or "")}</p>
</li>""")
    body = ('<h1>Sessions</h1>\n'
            '<p class="subhead"><em>Newest to oldest. Click a date to read the full account.</em></p>\n'
            '<p class="podcast-cta"><span class="copy-feed-wrap">'
            f'<a href="feed.xml" class="podcast-link js-copy-feed" data-feed-url="{base_url()}/feed.xml">'
            '<span aria-hidden="true">&#9836;</span> Subscribe to the podcast'
            '</a></span> <span class="podcast-cta-tail">— copies the feed link so you can paste it into your podcast app of choice.</span></p>\n'
            '<ol class="session-log">' + "".join(rows) + '</ol>')
    return page("Sessions", linkify_html(body, "sessions.html", link_map),
                current_nav="sessions.html",
                description='Every session of the campaign, newest first — each with a recap, illustrations, a narrated audio retelling, and the original notes and transcript.',
                canonical="sessions.html")


def _inject_beat_images(summary_html: str, date: str, beat_images: dict) -> str:
    """After each <h2>Title</h2> in the rendered summary, insert a
    <figure class="beat-image beat-{right,left}"> if we have an image whose
    slug matches slugify(title). Alternates float side for a book feel."""
    if not beat_images:
        return summary_html

    pattern = re.compile(r"(<h2>)(.*?)(</h2>)", re.DOTALL)
    side_iter = iter(["beat-right", "beat-left"] * 20)

    def replace(m):
        opener, inner, closer = m.groups()
        # inner is already HTML — strip tags AND unescape entities
        # (linkified h2s carry <a>…</a> and apostrophes render as &#x27;).
        title_text = re.sub(r"<[^>]+>", "", inner)
        title_text = html.unescape(title_text).strip()
        slug = slugify(title_text)
        img_path = beat_images.get(slug)
        if not img_path:
            return m.group(0)
        side = next(side_iter)
        img_name = img_path.name
        return (
            f'{opener}{inner}{closer}'
            f'<figure class="beat-image {side}">'
            f'<img src="images/sessions/{date}/{html.escape(img_name)}" '
            f'alt="{html.escape(title_text)}" loading="lazy">'
            f'</figure>'
        )

    return pattern.sub(replace, summary_html)


def detail_page_session(s, link_map, prev=None, nxt=None):
    summary_md = s.meta.get("summary_md", "")
    summary_html = (md_to_html(summary_md) if summary_md
                    else "<p><em>No summary available for this session.</em></p>")
    summary_html = _inject_beat_images(
        summary_html, s.meta.get("date", s.slug),
        s.meta.get("beat_images") or {},
    )

    note_text = s.body or ""
    notes_section = ""
    if note_text:
        notes_section = f"""
<section class="session-notes">
  <details>
    <summary>Original session notes (Fiz's POV)</summary>
    <div class="notes-body">{md_to_html(note_text)}</div>
  </details>
</section>"""

    transcript_text = s.meta.get("transcript", "")
    transcript_blocks = chunk_transcript(transcript_text)
    if transcript_blocks:
        ts_inner = "".join(f"<p>{html.escape(p)}</p>" for p in transcript_blocks)
        ts_section = f"""
<section class="raw-transcript">
  <details>
    <summary>Raw transcript ({len(transcript_blocks)} chunks of auto-transcribed audio)</summary>
    <p class="muted small">Lightly chunked. Expect overlap with table chatter.</p>
    <div class="transcript-body">{ts_inner}</div>
  </details>
</section>"""
    else:
        ts_section = ""

    audio_html = ""
    if s.meta.get("has_audio"):
        audio_name = s.meta.get("audio_name", f"{s.meta.get('date', s.slug)}.mp3")
        audio_html = (
            f'  <figure class="session-audio">\n'
            f'    <figcaption><span class="session-audio-badge no-link">Tales of the True Hand</span>'
            f' <span class="session-audio-caption no-link">Listen to this session as told by Vandal Lovelace.</span></figcaption>\n'
            f'    <audio controls preload="none" src="audio/sessions/{html.escape(audio_name)}"></audio>\n'
            f'  </figure>\n'
        )

    hero_html = ""
    if s.meta.get("has_image"):
        img_name = s.meta.get("image_name", f"{s.meta.get('date', s.slug)}.jpg")
        hero_html = (
            f'  <figure class="session-hero">'
            f'<img src="images/sessions/{html.escape(img_name)}" '
            f'alt="Illustration for {html.escape(s.name)}" loading="lazy">'
            f'</figure>\n'
        )

    carried = s.meta.get("carried") or []
    carried_html = ""
    if carried:
        items = "".join(f'<li>{md_inline(it)}</li>' for it in carried)
        carried_html = f"""
  <aside class="carried">
    <h2>Items acquired</h2>
    <ul>{items}</ul>
  </aside>
"""

    body = f"""<article class="detail">
  <h1>{html.escape(s.name)}</h1>
{audio_html}{hero_html}{carried_html}  <section class="session-summary">
  {summary_html}
  </section>
  {notes_section}
  {ts_section}
</article>"""
    body = linkify_html(body, s.href, link_map)
    # Prev/next chronological navigation. `sessions` is ordered oldest→newest,
    # so `prev` is the earlier session and `nxt` the later one. Built outside
    # linkify so the neighbour dates don't get turned into entity self-links.
    body += _session_pager(prev, nxt)
    bc = f'<a href="sessions.html">Sessions</a> &rsaquo; {html.escape(s.name)}'
    img_name = s.meta.get("image_name") or ""
    audio_name = s.meta.get("audio_name") or ""
    subtitle = s.meta.get("audio_subtitle") or ""
    share_title = f"{s.name} — {subtitle}" if subtitle else s.name
    return page(share_title, body, current_nav="sessions.html", breadcrumb=bc,
                description=s.summary,
                image=f"images/sessions/{img_name}" if img_name else None,
                canonical=s.href, og_type="article",
                audio=f"audio/sessions/{audio_name}" if audio_name else None)


def _session_pager(prev, nxt):
    """Bottom-of-page 'Previous / Next session' navigation for a detail page.

    Always renders both slots so the flex row keeps Previous left and Next
    right even when one end is missing (an empty span holds the slot).
    """
    if prev is None and nxt is None:
        return ""

    def slot(entity, direction, label):
        if entity is None:
            return '<span class="session-pager-link empty" aria-hidden="true"></span>'
        rel = "prev" if direction == "prev" else "next"
        arrow = "‹" if direction == "prev" else "›"
        pieces = [
            f'<span class="session-pager-dir">{arrow}&nbsp;{label}</span>',
            f'<span class="session-pager-title">{html.escape(entity.name)}</span>',
        ]
        if entity.summary:
            pieces.append(
                f'<span class="session-pager-brief">{html.escape(entity.summary)}</span>')
        return (f'<a class="session-pager-link {direction}" '
                f'href="{entity.href}" rel="{rel}">' + "".join(pieces) + '</a>')

    return (
        '\n<nav class="session-pager" aria-label="Session navigation">\n'
        f'  {slot(prev, "prev", "Previous session")}\n'
        f'  {slot(nxt, "next", "Next session")}\n'
        '</nav>\n'
    )
