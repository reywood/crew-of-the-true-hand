"""The generic entity detail page, and the Connections block."""

import html

from ...core.markdown import md_to_html
from ...core.text import _extract_session_dates
from ..layout import page
from ..linkify import linkify_html


def _render_mentioned_in(dates, session_lookup):
    """Render a 'Mentioned in sessions' block below the h1 of a detail page.
    dates: iterable of YYYY-MM-DD strings; sorted+deduped internally.
    session_lookup: dict {date: session Entity} for hrefs."""
    seen = sorted({d for d in dates if d})
    if not seen:
        return ""
    chips = []
    for d in seen:
        s = session_lookup.get(d)
        if s:
            chips.append(f'<a class="session-chip" href="{s.href}">{html.escape(d)}</a>')
        else:
            chips.append(f'<span class="session-chip session-chip-missing">{html.escape(d)}</span>')
    return (
        '<aside class="mentioned-in">'
        '<span class="mentioned-in-label">Mentioned in sessions:</span> '
        + " ".join(chips)
        + '</aside>'
    )


def _render_expertise_link_block(label, entries):
    """Render a small cross-reference block used on item + NPC pages."""
    if not entries:
        return ""
    links = ", ".join(
        f'<a href="{ent.href}">{html.escape(ent.name)}</a>'
        for ent in entries
    )
    return (
        '<aside class="expertise-link">'
        f'<span class="expertise-label">{html.escape(label)}:</span> {links}'
        '</aside>'
    )


def detail_page_generic(e, list_href, list_label, link_map, session_lookup=None,
                        graph=None):
    rendered = md_to_html(e.body)
    linked = linkify_html(rendered, e.href, link_map)
    meta_rows = []
    # 'sessions' is rendered separately as the mentioned-in block, so skip it
    # here to avoid showing it twice. Same for the computed cross-reference
    # lists (helpers / can_help_with) — they get their own rendering below.
    skip = {"name", "aliases", "summary", "transcript", "has_notes",
            "has_transcript", "date", "status_class", "section", "sessions",
            "helpers", "can_help_with"}
    for k, v in e.meta.items():
        if k in skip:
            continue
        if isinstance(v, list):
            v = ", ".join(v)
        if not v:
            continue
        label = k.replace("_", " ").title()
        val_html = linkify_html(html.escape(v), e.href, link_map)
        meta_rows.append(
            f'<div class="meta-row"><span class="meta-label">{html.escape(label)}:</span> '
            f'<span class="meta-value">{val_html}</span></div>'
        )
    meta_block = (f'<aside class="meta-block">{"".join(meta_rows)}</aside>'
                  if meta_rows else "")

    sessions_block = _render_mentioned_in(
        _extract_session_dates(e.meta.get("sessions")),
        session_lookup or {},
    )

    # Cross-reference by expertise (populated by _attach_item_expertise):
    #   items get "Who could help" (NPCs with matching expertise)
    #   NPCs get "Could help with" (items whose expertise_needed matches)
    helpers_block = _render_expertise_link_block(
        "Who could help", e.meta.get("helpers") or [])
    can_help_block = _render_expertise_link_block(
        "Could help with", e.meta.get("can_help_with") or [])

    connections_block = _render_connections(e.href, graph)

    body = f"""<article class="detail">
  <h1>{html.escape(e.name)}</h1>
  {sessions_block}
  {helpers_block}
  {can_help_block}
  {connections_block}
  {meta_block}
  <div class="detail-body">
  {linked}
  </div>
</article>"""
    bc = f'<a href="{list_href}">{html.escape(list_label)}</a> &rsaquo; {html.escape(e.name)}'
    return page(e.name, body, current_nav=list_href, breadcrumb=bc,
                description=e.summary or e.body, image=e.image,
                canonical=e.href, og_type="article")


# What each relation is called on a page, and which side of the edge the
# current page sits on. Only relations listed per-kind are rendered; the ones
# rendered elsewhere (appears_in -> "Mentioned in sessions"; can_help -> the
# expertise blocks) are deliberately omitted here to avoid duplication.
CONNECTION_SPEC = {
    "npc": [
        ("out", "located_in", "Based at"),
        ("out", "governs", "Governs"),
        ("out", "gave", "Gifts given"),
        ("faction", "affiliated_with", None),
    ],
    "location": [
        ("out", "within", "Part of"),
        ("in", "within", "Contains"),
        ("in", "located_in", "Figures here"),
        ("in", "governs", "Governed by"),
    ],
    # Items are omitted: their held_by / acquired_in / giver relations already
    # show as frontmatter meta rows on the item page, so a Connections block
    # would only duplicate them. The reverse of `gave` shows up usefully on the
    # NPC side ("Gifts given") instead.
    "pc": [
        ("in", "held_by", "Carrying"),
    ],
}


def _render_connections(href, graph):
    """Render the 'Connections' backlink block for a detail page, if any."""
    if not graph:
        return ""
    node = graph.node_by_id.get(href)
    if not node:
        return ""
    spec = CONNECTION_SPEC.get(node["kind"])
    if not spec:
        return ""

    def links_for(adj, rel):
        seen, out = set(), []
        for r, other_id in adj:
            if r != rel or other_id in seen:
                continue
            seen.add(other_id)
            other = graph.node_by_id.get(other_id)
            if other and other["url"]:
                out.append(
                    f'<a href="{other["url"]}">{html.escape(other["name"])}</a>'
                )
        return out

    rows = []
    for direction, rel, label in spec:
        if direction == "faction":
            # For each faction this NPC serves, list fellow members.
            for r, fid in graph.out_adj.get(href, []):
                if r != rel:
                    continue
                fac = graph.node_by_id.get(fid)
                members = [
                    graph.node_by_id[m] for m in graph.faction_members.get(fid, [])
                    if m != href and m in graph.node_by_id
                ]
                if not fac or not members:
                    continue
                mlinks = ", ".join(
                    f'<a href="{m["url"]}">{html.escape(m["name"])}</a>'
                    for m in members if m["url"]
                )
                if mlinks:
                    rows.append((f'Also in {fac["name"]}', mlinks))
            continue
        adj = graph.out_adj.get(href, []) if direction == "out" else graph.in_adj.get(href, [])
        links = links_for(adj, rel)
        if links:
            rows.append((label, ", ".join(links)))

    if not rows:
        return ""
    row_html = "".join(
        f'<div class="conn-row"><span class="conn-label">{html.escape(lbl)}:</span> {val}</div>'
        for lbl, val in rows
    )
    return f'<aside class="connections">{row_html}</aside>'
