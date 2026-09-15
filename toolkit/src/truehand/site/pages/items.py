"""Item list pages."""

import html

from ...core.markdown import md_inline
from ..layout import page
from ..linkify import linkify_html


def item_list_page(items, link_map):
    """Group items by status, unresolved first so mysteries lead.

    The vocabulary and its order live on ItemStatus (see core/item_status.py),
    not here — this page only renders what a status says about itself.
    """
    grouped = {}
    for it in items:
        grouped.setdefault(it.status, []).append(it)

    chunks = [
        "<h1>The Ledger</h1>",
        (
            '<p class="subhead"><em>Everything the crew has hauled ashore. Unresolved mysteries '
            "lead.</em></p>"
        ),
    ]
    for status in sorted(grouped, key=lambda s: (s.display_order, s.label)):
        bucket = grouped[status]
        chunks.append(
            f'<h2 class="status-heading"><span class="status-chip '
            f'status-{status.css_class}">{html.escape(status.label)}</span></h2>'
        )
        chunks.append('<ul class="item-list">')
        for it in sorted(bucket, key=lambda x: x.name.lower()):
            # As written, "Party" included — the ledger names who holds it,
            # which is a different question from who is carrying it.
            holder = it.meta["holder"].one()
            typ = it.meta["type"].one()
            meta_bits = []
            if typ:
                meta_bits.append(f'<span class="item-type">{html.escape(typ)}</span>')
            if holder:
                meta_bits.append(f'<span class="item-holder">held by {html.escape(holder)}</span>')
            meta_line = (
                f'<span class="item-meta">{" · ".join(meta_bits)}</span>' if meta_bits else ""
            )
            summary = md_inline(it.summary or "")
            chunks.append(
                f'<li><a class="item-name" href="{it.href}">{html.escape(it.name)}</a>'
                f"{meta_line}"
                f'<p class="item-blurb">{summary}</p></li>'
            )
        chunks.append("</ul>")

    body = "\n".join(chunks)
    return page(
        "Items",
        linkify_html(body, "items.html", link_map),
        current_nav="items.html",
        description="The magical, mysterious and merely sentimental things the crew is carrying — "
        "and who might be able to explain them.",
        canonical="items.html",
    )
