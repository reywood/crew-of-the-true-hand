"""Item list pages."""

import html

from ...core.markdown import md_inline
from ..layout import page
from ..linkify import linkify_html

ITEM_STATUS_ORDER = ["Unresolved", "Active", "Consumed", "Lost", "Sold"]


ITEM_STATUS_CLASS = {
    "Unresolved": "unresolved",
    "Active":     "active",
    "Consumed":   "completed",
    "Lost":       "completed",
    "Sold":       "completed",
}


def item_list_page(items, link_map):
    """Group items by status, unresolved first so mysteries lead."""
    grouped = {}
    for it in items:
        status = it.meta.get("status", "Active")
        if isinstance(status, list):
            status = status[0] if status else "Active"
        grouped.setdefault(status, []).append(it)

    chunks = [
        '<h1>The Ledger</h1>',
        '<p class="subhead"><em>Everything the crew has hauled ashore. Unresolved mysteries lead.</em></p>',
    ]
    order = ITEM_STATUS_ORDER + [s for s in grouped if s not in ITEM_STATUS_ORDER]
    for status in order:
        bucket = grouped.get(status, [])
        if not bucket:
            continue
        cls = ITEM_STATUS_CLASS.get(status, "active")
        chunks.append(
            f'<h2 class="status-heading"><span class="status-chip status-{cls}">{html.escape(status)}</span></h2>'
        )
        chunks.append('<ul class="item-list">')
        for it in sorted(bucket, key=lambda x: x.name.lower()):
            holder = it.meta.get("holder", "")
            if isinstance(holder, list):
                holder = ", ".join(holder)
            typ = it.meta.get("type", "")
            if isinstance(typ, list):
                typ = typ[0] if typ else ""
            meta_bits = []
            if typ:
                meta_bits.append(f'<span class="item-type">{html.escape(typ)}</span>')
            if holder:
                meta_bits.append(f'<span class="item-holder">held by {html.escape(holder)}</span>')
            meta_line = f'<span class="item-meta">{" · ".join(meta_bits)}</span>' if meta_bits else ""
            summary = md_inline(it.summary or "")
            chunks.append(
                f'<li><a class="item-name" href="{it.href}">{html.escape(it.name)}</a>'
                f'{meta_line}'
                f'<p class="item-blurb">{summary}</p></li>'
            )
        chunks.append('</ul>')

    body = "\n".join(chunks)
    return page("Items", linkify_html(body, "items.html", link_map),
                current_nav="items.html",
                description='The magical, mysterious and merely sentimental things the crew is carrying — and who might be able to explain them.',
                canonical="items.html")
