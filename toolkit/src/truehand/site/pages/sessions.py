"""Session list and detail pages."""

import html
import re

from ...core.markdown import md_inline, md_to_html
from ...core.text import chunk_transcript
from ..layout import base_url, page
from ..linkify import linkify_html


def session_list_page(sessions, locations, link_map):
    loc_by_slug = {l.slug: l for l in locations}
    rows = []
    for s in sorted(sessions, key=lambda x: x.date, reverse=True):
        date = s.date
        loc_chips = []
        for slug in s.locations:
            loc = loc_by_slug.get(slug)
            if loc:
                loc_chips.append(
                    f'<a class="session-row-loc" href="{loc.href}">{html.escape(loc.name)}</a>'
                )
        if not loc_chips:
            loc_chips.append('<span class="session-row-loc session-row-loc-none">—</span>')
        locs_html = "".join(loc_chips)
        audio_badge = (
            '<span class="session-row-audio" title="Audio recap available" aria-label="Audio recap available">&#9836;</span>'
            if s.has_audio
            else ""
        )
        rows.append(f"""
<li class="session-row">
  <div class="session-row-meta">
    <div class="session-row-date-line">
      <a class="session-row-date" href="{s.href}">{html.escape(date)}</a>{audio_badge}
    </div>
    <div class="session-row-locs">{locs_html}</div>
  </div>
  <p class="session-row-summary">{html.escape(s.blurb)}</p>
</li>""")
    body = (
        "<h1>Sessions</h1>\n"
        '<p class="subhead"><em>Newest to oldest. Click a date to read the full account.</em></p>\n'
        '<p class="podcast-cta"><span class="copy-feed-wrap">'
        f'<a href="feed.xml" class="podcast-link js-copy-feed" data-feed-url="{base_url()}/feed.xml">'
        '<span aria-hidden="true">&#9836;</span> Subscribe to the podcast'
        '</a></span> <span class="podcast-cta-tail">— copies the feed link so you can paste it into your podcast app of choice.</span></p>\n'
        '<ol class="session-log">' + "".join(rows) + "</ol>"
    )
    return page(
        "Sessions",
        linkify_html(body, "sessions.html", link_map),
        current_nav="sessions.html",
        description="Every session of the campaign, newest first — each with a recap, illustrations, a narrated audio retelling, and the original notes and transcript.",
        canonical="sessions.html",
    )


def _inject_beat_images(summary_html: str, session) -> str:
    """After each <h2> in the rendered summary, insert a
    <figure class="beat-image beat-{right,left}"> if that beat has an image.
    Alternates float side (across illustrated beats only) for a book feel.

    The <h2> elements render one-for-one from the summary's Beats, in order, so
    the beats are zipped onto them directly. This used to strip tags and
    unescape entities out of each rendered <h2> to recover a title and re-slug
    it — reconstructing, from HTML, knowledge the model already had.
    """
    if not session.artifacts.beats:
        return summary_html

    beats = iter(session.summary.beats)
    side_iter = iter(["beat-right", "beat-left"] * 20)

    def replace(m):
        beat = next(beats, None)
        if beat is None:
            return m.group(0)
        img_path = session.beat_image(beat)
        if not img_path:
            return m.group(0)
        return (
            f"{m.group(0)}"
            f'<figure class="beat-image {next(side_iter)}">'
            f'<img src="images/sessions/{session.date}/{html.escape(img_path.name)}" '
            f'alt="{html.escape(beat.title)}" loading="lazy">'
            f"</figure>"
        )

    return re.sub(r"<h2>.*?</h2>", replace, summary_html, flags=re.DOTALL)


def detail_page_session(s, link_map, prev=None, nxt=None):
    summary_html = (
        md_to_html(s.summary.raw)
        if s.summary
        else "<p><em>No summary available for this session.</em></p>"
    )
    summary_html = _inject_beat_images(summary_html, s)

    note_text = s.notes
    notes_section = ""
    if note_text:
        notes_section = f"""
<section class="session-notes">
  <details>
    <summary>Original session notes (Fiz's POV)</summary>
    <div class="notes-body">{md_to_html(note_text)}</div>
  </details>
</section>"""

    transcript_text = s.transcript
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
    if s.has_audio:
        audio_html = (
            f'  <figure class="session-audio">\n'
            f'    <figcaption><span class="session-audio-badge no-link">Tales of the True Hand</span>'
            f' <span class="session-audio-caption no-link">Listen to this session as told by Vandal Lovelace.</span></figcaption>\n'
            f'    <audio controls preload="none" src="audio/sessions/{html.escape(s.audio_name)}"></audio>\n'
            f"  </figure>\n"
        )

    hero_html = ""
    if s.has_hero:
        hero_html = (
            f'  <figure class="session-hero">'
            f'<img src="images/sessions/{html.escape(s.hero_name)}" '
            f'alt="Illustration for {html.escape(s.name)}" loading="lazy">'
            f"</figure>\n"
        )

    carried_html = ""
    if s.carried:
        items = "".join(f"<li>{md_inline(it)}</li>" for it in s.carried)
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
    subtitle = s.artifacts.episode_title
    share_title = f"{s.name} — {subtitle}" if subtitle else s.name
    return page(
        share_title,
        body,
        current_nav="sessions.html",
        breadcrumb=bc,
        description=s.blurb,
        image=f"images/sessions/{s.hero_name}" if s.has_hero else None,
        canonical=s.href,
        og_type="article",
        audio=f"audio/sessions/{s.audio_name}" if s.has_audio else None,
    )


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
        if entity.blurb:
            pieces.append(f'<span class="session-pager-brief">{html.escape(entity.blurb)}</span>')
        return (
            f'<a class="session-pager-link {direction}" '
            f'href="{entity.href}" rel="{rel}">' + "".join(pieces) + "</a>"
        )

    return (
        '\n<nav class="session-pager" aria-label="Session navigation">\n'
        f"  {slot(prev, 'prev', 'Previous session')}\n"
        f"  {slot(nxt, 'next', 'Next session')}\n"
        "</nav>\n"
    )
