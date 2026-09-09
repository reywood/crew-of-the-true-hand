"""NPC roster pages."""

import html

from ...core.standing import for_type
from ..layout import page
from ..linkify import linkify_html
from .locations import _location_strip_qualifier


def npc_table_page(npcs, link_map):
    blocks = []
    for npc in sorted(npcs, key=lambda n: n.name.lower()):
        standing = for_type(npc.meta["type"].one())
        chip_html = '<span class="muted">—</span>'
        if standing:
            chip_html = (
                f'<span class="standing-chip {standing.css_class}">'
                f'{html.escape(standing.label)}</span>'
            )
        loc = npc.meta["location"].prose()
        met = _location_strip_qualifier(loc)
        affiliations = npc.meta["affiliation"].many()
        aff_html = (
            html.escape(", ".join(affiliations))
            if affiliations
            else '<span class="muted">—</span>'
        )
        met_html = html.escape(met) if met else '<span class="muted">—</span>'
        summary = html.escape(npc.summary or "")
        desc_html = (
            summary if summary else '<span class="muted">No notes yet.</span>'
        )

        blocks.append(
            '<tbody class="npc-block">'
            '<tr class="npc-main">'
            f'<td class="col-name"><a href="{npc.href}">{html.escape(npc.name)}</a></td>'
            f'<td class="col-affil">{aff_html}</td>'
            f'<td class="col-met">{met_html}</td>'
            f'<td class="col-status">{chip_html}</td>'
            '</tr>'
            '<tr class="npc-desc">'
            f'<td colspan="4">{desc_html}</td>'
            '</tr>'
            '</tbody>'
        )

    body = (
        '<h1>The Roster</h1>\n'
        '<p class="subhead"><em>Everyone the crew has met, heard tell of, or owes a debt to.</em></p>\n'
        '<div class="roster-wrap">\n'
        '<table class="roster-table">\n'
        '<thead><tr>'
        '<th class="col-name">Name</th>'
        '<th class="col-affil">Affiliations</th>'
        '<th class="col-met">First Encountered</th>'
        '<th class="col-status">Status</th>'
        '</tr></thead>\n'
        + "\n".join(blocks) + '\n'
        '</table>\n'
        '</div>'
    )
    return page("NPCs", linkify_html(body, "npcs.html", link_map),
                current_nav="npcs.html",
                description="Everyone the crew has met, been threatened by, or been sent to find — allies, antagonists, dragons and gods.",
                canonical="npcs.html")


def _npc_card(npc, show_last_seen):
    standing = for_type(npc.meta["type"].one())
    chip_html = ""
    if standing:
        chip_html = (f'<span class="standing-chip {standing.css_class}">'
                     f'{html.escape(standing.label)}</span>')
    last_seen_html = ""
    if show_last_seen:
        loc = npc.meta["location"].prose() or "—"
        last_seen_html = f'<p class="last-seen">Last seen: {html.escape(loc)}</p>'
    summary = html.escape(npc.summary or "")
    return (
        f'<a class="card npc-card" href="{npc.href}">'
        f'<div class="npc-card-head"><h3>{html.escape(npc.name)}</h3>{chip_html}</div>'
        f'{last_seen_html}'
        f'<p>{summary}</p>'
        f'</a>'
    )

