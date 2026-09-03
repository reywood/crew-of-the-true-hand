"""NPC roster pages."""

import html

from ...core.loaders import chip_for, port_for
from ..layout import page
from ..linkify import linkify_html
from .locations import _affiliations, _location_strip_qualifier


def npc_table_page(npcs, link_map):
    blocks = []
    for npc in sorted(npcs, key=lambda n: n.name.lower()):
        chip = chip_for(npc.meta.get("type", ""))
        chip_html = '<span class="muted">—</span>'
        if chip:
            label, cls = chip
            chip_html = (
                f'<span class="standing-chip {cls}">{html.escape(label)}</span>'
            )
        loc = npc.meta.get("location", "")
        if isinstance(loc, list):
            loc = ", ".join(loc)
        loc = (loc or "").strip()
        met = _location_strip_qualifier(loc)
        affiliations = _affiliations(npc.meta)
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
    chip = chip_for(npc.meta.get("type", ""))
    chip_html = ""
    if chip:
        label, cls = chip
        chip_html = f'<span class="standing-chip {cls}">{html.escape(label)}</span>'
    last_seen_html = ""
    if show_last_seen:
        loc = npc.meta.get("location", "")
        if isinstance(loc, list):
            loc = ", ".join(loc)
        loc = loc.strip() if loc else "—"
        last_seen_html = f'<p class="last-seen">Last seen: {html.escape(loc)}</p>'
    summary = html.escape(npc.summary or "")
    return (
        f'<a class="card npc-card" href="{npc.href}">'
        f'<div class="npc-card-head"><h3>{html.escape(npc.name)}</h3>{chip_html}</div>'
        f'{last_seen_html}'
        f'<p>{summary}</p>'
        f'</a>'
    )


def npc_chart_page(npcs, locations, link_map):
    loc_by_name = {l.name: l for l in locations}
    location_names = list(loc_by_name.keys())

    grouped = {}
    adrift = []
    for npc in npcs:
        port = port_for(npc, location_names)
        if port is None:
            adrift.append(npc)
        else:
            grouped.setdefault(port, []).append(npc)

    ordered = sorted(grouped.items(), key=lambda kv: (-len(kv[1]), kv[0].lower()))

    chunks = [
        '<h1>The Roster</h1>',
        '<p class="subhead"><em>By port, as the chart was last drawn.</em></p>',
    ]
    for port_name, entries in ordered:
        port = loc_by_name[port_name]
        port_type = port.meta.get("type", "")
        if isinstance(port_type, list):
            port_type = port_type[0] if port_type else ""
        port_type = (port_type or "").strip().lower()
        count = len(entries)
        souls = "soul" if count == 1 else "souls"
        gloss = " · ".join(p for p in [port_type, f"{count} {souls}"] if p)
        chunks.append('<section class="chart-port">')
        chunks.append('<header class="chart-port-header">')
        chunks.append(
            f'<a class="chart-port-name" href="{port.href}">{html.escape(port_name)}</a>'
        )
        chunks.append(f'<span class="chart-port-gloss">{html.escape(gloss)}</span>')
        chunks.append('</header>')
        chunks.append('<div class="chart-port-grid">')
        for npc in sorted(entries, key=lambda n: n.name.lower()):
            chunks.append(_npc_card(npc, show_last_seen=False))
        chunks.append('</div>')
        chunks.append('</section>')

    if adrift:
        count = len(adrift)
        souls = "soul" if count == 1 else "souls"
        chunks.append('<section class="chart-adrift">')
        chunks.append('<header class="chart-port-header chart-adrift-header">')
        chunks.append('<span class="chart-port-name">Adrift</span>')
        chunks.append(
            f'<span class="chart-port-gloss">{count} {souls}, no fixed port</span>'
        )
        chunks.append('</header>')
        chunks.append('<div class="chart-port-grid">')
        for npc in sorted(adrift, key=lambda n: n.name.lower()):
            chunks.append(_npc_card(npc, show_last_seen=True))
        chunks.append('</div>')
        chunks.append('</section>')

    body = "\n".join(chunks)
    return page("NPCs", linkify_html(body, "npcs.html", link_map),
                current_nav="npcs.html")
