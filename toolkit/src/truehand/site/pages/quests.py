"""Quest list and detail pages."""

import html
import re

from ...core.markdown import md_inline, md_to_html
from ..layout import page
from ..linkify import linkify_html
from .detail import _render_mentioned_in


def quest_list_page(quests, link_map):
    order = ["Active — main arc", "Active — lead", "Active — region",
             "Unresolved", "Completed"]
    grouped = {}
    for q in quests:
        grouped.setdefault(q.status, []).append(q)
    chunks = ["<h1>Quest Log</h1>",
              '<p class="subhead"><em>See also <a href="next.html">Prep — Where We Left Off</a> '
              'and the <a href="threads.html">Open Threads</a> board.</em></p>']
    for status in order:
        items = grouped.get(status, [])
        if not items:
            continue
        status_class = items[0].meta.get("status_class", "active")
        chunks.append(
            f'<h2 class="status-heading"><span class="status-chip status-{status_class}">{html.escape(status)}</span></h2>')
        chunks.append("<ul class='quest-list'>")
        for q in items:
            helps = q.meta.get("helps") or []
            supported_by = q.meta.get("supported_by") or []
            dep_lines = []
            if helps:
                links = " · ".join(
                    f'<a href="{d.href}">{html.escape(d.name)}</a>'
                    for d in helps
                )
                dep_lines.append(
                    f'<span class="quest-dep quest-dep-helps">'
                    f'<span class="dep-arrow">&rarr;</span> helps: {links}'
                    f'</span>'
                )
            if supported_by:
                links = " · ".join(
                    f'<a href="{d.href}">{html.escape(d.name)}</a>'
                    for d in supported_by
                )
                dep_lines.append(
                    f'<span class="quest-dep quest-dep-supports">'
                    f'<span class="dep-arrow">&larr;</span> steps toward this: {links}'
                    f'</span>'
                )
            deps_html = (
                f'<div class="quest-list-deps">{"".join(dep_lines)}</div>'
                if dep_lines else ""
            )
            chunks.append(
                f'<li><a href="{q.href}"><strong>{html.escape(q.name)}</strong></a> — '
                f'{md_inline(q.summary or "")}{deps_html}</li>'
            )
        chunks.append("</ul>")
    body = "\n".join(chunks)
    return page("Quests", linkify_html(body, "quests.html", link_map),
                current_nav="quests.html",
                description='Every thread the crew is pulling: the main arc, allies to recruit, giant hotspots, and the leads still dangling.',
                canonical="quests.html")


def _render_dep_line(label, arrow_class, deps):
    """Render one directional dependency line, e.g.
       → Helps achieve: [Reach the Oracle]"""
    if not deps:
        return ""
    links = ", ".join(
        f'<a href="{d.href}">{html.escape(d.name)}</a>'
        for d in deps
    )
    return (
        f'<p class="dep-line">'
        f'<span class="dep-arrow {arrow_class}">&rarr;</span> '
        f'<span class="dep-label">{html.escape(label)}:</span> {links}'
        f'</p>'
    )


def detail_page_quest(q, link_map, session_lookup=None):
    rendered = md_to_html(q.body)
    linked = linkify_html(rendered, q.href, link_map)
    status_class = q.meta.get("status_class", "active")
    chip = f'<span class="status-chip status-{status_class}">{html.escape(q.status or "")}</span>'

    helps = q.meta.get("helps") or []
    supported_by = q.meta.get("supported_by") or []
    deps_html = ""
    if helps or supported_by:
        forward = _render_dep_line("Helps achieve", "dep-forward", helps)
        backward = _render_dep_line("Steps toward this", "dep-backward",
                                    supported_by)
        deps_html = f'<aside class="quest-deps">{forward}{backward}</aside>'

    # Quests carry their session dates inline in the body as (YYYY-MM-DD)
    # parentheticals, so extract from there rather than a frontmatter field.
    session_dates = re.findall(r"\b(\d{4}-\d{2}-\d{2})\b", q.body or "")
    sessions_block = _render_mentioned_in(session_dates, session_lookup or {})

    body = f"""<article class="detail">
  <h1>{html.escape(q.name)}</h1>
  <p class="meta-line">{chip} <span class="muted">{html.escape(q.meta.get("section", ""))}</span></p>
  {sessions_block}
  {deps_html}
  <div class="detail-body">
  {linked}
  </div>
</article>"""
    bc = f'<a href="quests.html">Quests</a> &rsaquo; {html.escape(q.name)}'
    return page(q.name, body, current_nav="quests.html", breadcrumb=bc,
                description=q.summary or q.body,
                canonical=q.href, og_type="article")
