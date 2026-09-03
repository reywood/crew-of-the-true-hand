"""The prep hub (next.html) and the open-threads board (threads.html)."""

import html
import re

from ...core.graph import _meta_first
from ...core.loaders import SESSION_LOCATIONS, chip_for
from ...core.markdown import md_inline
from ...core.text import _norm_heading
from ..layout import page
from ..linkify import linkify_html
from .index import _render_quest_li, _top_active_quests

FORWARD_HEADINGS = {"what's next", "whats next", "next steps", "loose ends", "loose end"}


def extract_forward_sections(summary_md):
    """Return [(heading, [bullet, ...]), ...] for a session summary's
    forward-looking sections (What's next / Loose ends / Next steps), in
    document order. Tolerates the known casing/punctuation variants."""
    if not summary_md:
        return []
    out, cur_head, cur_bullets = [], None, None
    for raw in summary_md.split("\n"):
        line = raw.rstrip()
        m = re.match(r"^##\s+(.*)$", line)
        if m:
            if cur_head is not None and cur_bullets:
                out.append((cur_head, cur_bullets))
            head = m.group(1).strip()
            if _norm_heading(head) in FORWARD_HEADINGS:
                cur_head, cur_bullets = head, []
            else:
                cur_head, cur_bullets = None, None
            continue
        if cur_bullets is not None:
            bm = re.match(r"^\s*[-*]\s+(.*)$", line)
            if bm:
                cur_bullets.append(bm.group(1).strip())
    if cur_head is not None and cur_bullets:
        out.append((cur_head, cur_bullets))
    return out


def _current_location(state, sessions, locations):
    """Resolve the party's current location: the campaign-state override if set,
    else the most recent session that has a SESSION_LOCATIONS entry (walking back
    past in-transit sessions). Returns (location_entity_or_None, as_of_date)."""
    loc_by_slug = {l.slug: l for l in locations}
    dates = sorted((s.meta.get("date", s.slug) for s in sessions), reverse=True)
    as_of = dates[0] if dates else ""
    slug = state.get("current_location")
    if not slug:
        for d in dates:
            here = SESSION_LOCATIONS.get(d, [])
            if here:
                slug = here[0]
                break
    return (loc_by_slug.get(slug) if slug else None), as_of


def _npc_at_location(npc, loc):
    val = npc.meta.get("location", "")
    if isinstance(val, list):
        val = " ".join(val)
    val = (val or "").lower()
    if not val:
        return False
    return loc.name.lower() in val or loc.slug.replace("-", " ") in val


def prep_page(pcs, npcs, locations, items, quests, sessions, state,
              session_lookup, link_map):
    """The pre-session briefing hub. Composes existing rollups (current location,
    latest recap, top quests, loose threads, location leads, item→expert leads,
    open questions, crew holdings) into one 'what do I need to know / do next' page."""
    loc, as_of = _current_location(state, sessions, locations)
    latest = session_lookup.get(as_of)
    parts = [
        "<h1>Where We Left Off</h1>",
        '<p class="subhead"><em>Open the site before a session and start here: where the crew stands, and what to do next.</em></p>',
    ]

    # 1. Where we are
    if loc:
        where = f'The crew is at <a class="prep-loc" href="{loc.href}">{html.escape(loc.name)}</a>'
    else:
        where = "The crew is between ports"
    if as_of:
        where += f' — as of <a href="session-{as_of}.html">session {as_of}</a>.'
    else:
        where += "."
    sec = ['<section class="prep-block"><h2>Where we are</h2>', f'<p class="prep-where">{where}</p>']
    if latest and latest.summary:
        sec.append(f'<p class="prep-inbrief">“{md_inline(latest.summary)}”</p>')
    if latest and latest.meta.get("has_audio"):
        sec.append(f'<p class="prep-audio"><a href="session-{as_of}.html">▸ Listen to the recap of session {as_of}</a></p>')
    sec.append("</section>")
    parts.append("".join(sec))

    # 2. Do this next
    sec = ['<section class="prep-block"><h2>Do this next</h2>']
    if state.get("objective"):
        sec.append(f'<p class="prep-objective">{md_inline(state["objective"])}</p>')
    top = _top_active_quests(quests, limit=5)
    if top:
        sec.append('<ul class="home-quest-list">')
        for _i, _r, q in top:
            sec.append(_render_quest_li(q))
        sec.append('</ul><p class="home-more"><a href="quests.html">See the full quest log &rsaquo;</a></p>')
    sec.append("</section>")
    parts.append("".join(sec))

    # 3. Loose threads from the latest session
    fwd = extract_forward_sections(latest.meta.get("summary_md", "")) if latest else []
    if fwd:
        sec = ['<section class="prep-block"><h2>Loose threads</h2>',
               f'<p class="muted small">Left dangling as of <a href="session-{as_of}.html">session {as_of}</a>.</p>']
        for _head, bullets in fwd:
            sec.append('<ul class="prep-threads">')
            sec += [f'<li>{md_inline(b)}</li>' for b in bullets]
            sec.append('</ul>')
        sec.append('<p class="home-more"><a href="threads.html">See all open threads across the campaign &rsaquo;</a></p></section>')
        parts.append("".join(sec))

    # 4. People & leads where you are
    if loc:
        here = [n for n in npcs
                if _npc_at_location(n, loc)
                and (chip_for(_meta_first(n.meta.get("type"))) or ("", ""))[1]
                in ("standing-ally", "standing-lead", "standing-crew")]
        if here:
            sec = [f'<section class="prep-block"><h2>People &amp; leads at {html.escape(loc.name)}</h2>',
                   '<ul class="prep-leads">']
            for npc in sorted(here, key=lambda n: n.name.lower()):
                typ = _meta_first(npc.meta.get("type"))
                role = _meta_first(npc.meta.get("role"))
                meta = html.escape(typ) + (f' · {html.escape(role)}' if role else "")
                sec.append(f'<li><a href="{npc.href}">{html.escape(npc.name)}</a> '
                           f'<span class="muted small">{meta}</span></li>')
            sec.append('</ul></section>')
            parts.append("".join(sec))

    # 5. Unresolved items & who can crack them
    unresolved = [it for it in items
                  if _meta_first(it.meta.get("status")) == "Unresolved" and it.meta.get("helpers")]
    if unresolved:
        sec = ['<section class="prep-block"><h2>Unresolved items &amp; who can crack them</h2>',
               '<ul class="prep-leads">']
        for it in sorted(unresolved, key=lambda x: x.name.lower()):
            hlabels = []
            for hp in it.meta["helpers"]:
                where_h = _meta_first(hp.meta.get("location"))
                lbl = f'<a href="{hp.href}">{html.escape(hp.name)}</a>'
                if where_h:
                    lbl += f' <span class="muted small">· {html.escape(where_h)}</span>'
                hlabels.append(lbl)
            sec.append(f'<li><a href="{it.href}">{html.escape(it.name)}</a> '
                       f'<span class="dep-arrow">&rarr;</span> {" · ".join(hlabels)}</li>')
        sec.append('</ul></section>')
        parts.append("".join(sec))

    # 6. Open questions
    oq = state.get("open_questions") or []
    if oq:
        sec = ['<section class="prep-block"><h2>Open questions</h2>', '<ul class="prep-questions">']
        sec += [f'<li>{md_inline(q)}</li>' for q in oq]
        sec.append('</ul></section>')
        parts.append("".join(sec))

    # 7. The crew at a glance
    sec = ['<section class="prep-block"><h2>The crew at a glance</h2>', '<div class="grid grid-2">']
    for pc in sorted(pcs, key=lambda p: p.meta.get("full_name", p.name).lower()):
        holdings = [it for it in items
                    if _meta_first(it.meta.get("holder")) == pc.name
                    and _meta_first(it.meta.get("status")) in ("Active", "Unresolved")]
        hold_html = ""
        if holdings:
            links = " · ".join(f'<a href="{it.href}">{html.escape(it.name)}</a>'
                               for it in sorted(holdings, key=lambda x: x.name.lower()))
            hold_html = f'<p class="prep-holdings"><span class="muted small">Carrying:</span> {links}</p>'
        img = (f'<img class="portrait" src="{pc.image}" alt="{html.escape(pc.name)}">' if pc.image else "")
        sec.append(f'''<div class="card pc-card prep-crew-card">
  <a href="{pc.href}">{img}<h3>{html.escape(pc.meta.get("full_name", pc.name))}</h3></a>
  <p class="muted small">{html.escape(pc.summary)}</p>
  {hold_html}
</div>''')
    sec.append('</div></section>')
    parts.append("".join(sec))

    body = "\n".join(parts)
    return page("Prep — Where We Left Off",
                linkify_html(body, "next.html", link_map), current_nav="next.html",
                description=(
                    "Where the crew stands right now: the current objective, the open "
                    "questions, the top quests, and who's nearby — everything you need "
                    "to pick the story back up."),
                canonical="next.html")


def threads_page(sessions, session_lookup, link_map):
    """Cross-session board of every What's-next / Loose-ends bullet, newest
    first — the soft dangling threats the quest log doesn't track."""
    parts = [
        "<h1>Open Threads</h1>",
        '<p class="subhead"><em>Every loose end and stated next step the crew has left in its wake — newest first.</em></p>',
    ]
    any_threads = False
    for s in sorted(sessions, key=lambda x: x.meta.get("date", x.slug), reverse=True):
        fwd = extract_forward_sections(s.meta.get("summary_md", ""))
        if not fwd:
            continue
        any_threads = True
        date = s.meta.get("date", s.slug)
        parts.append(f'<section class="prep-block"><h2><a href="session-{date}.html">Session {date}</a></h2>')
        for head, bullets in fwd:
            parts.append(f'<h3 class="threads-head">{html.escape(head)}</h3><ul class="prep-threads">')
            parts += [f'<li>{md_inline(b)}</li>' for b in bullets]
            parts.append('</ul>')
        parts.append('</section>')
    if not any_threads:
        parts.append('<p class="muted">No open threads recorded yet.</p>')
    body = "\n".join(parts)
    return page("Open Threads", linkify_html(body, "threads.html", link_map),
                current_nav="next.html",
                description="Every loose end the archive knows about, harvested from each session's what's-next and loose-ends notes.",
                canonical="threads.html")
