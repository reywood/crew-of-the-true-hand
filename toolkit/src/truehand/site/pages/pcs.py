"""Player-character list and detail pages."""

import html

from ...core.markdown import md_to_html
from ..layout import page
from ..linkify import linkify_html
from .detail import _render_connections


def pc_list_page(pcs, link_map):
    cards = []
    for pc in sorted(pcs, key=lambda p: p.meta["full_name"].one(p.name).lower()):
        img = (
            f'<img class="portrait" src="{pc.image}" alt="{html.escape(pc.name)}">'
            if pc.image
            else ""
        )
        cards.append(f"""
<a class="card pc-card" href="{pc.href}">
  {img}
  <h3>{html.escape(pc.meta["full_name"].one(pc.name))}</h3>
  <p>{html.escape(pc.summary)}</p>
</a>""")
    body = "<h1>The Crew</h1>\n<section class='grid grid-2'>" + "".join(cards) + "</section>"
    return page(
        "The Crew",
        linkify_html(body, "characters.html", link_map),
        current_nav="characters.html",
        description="Four adventurers out of a wrecked ship: Fiz the artificer, Hal the paladin, "
        "Toz the storm sorcerer, and Eno the nature cleric.",
        canonical="characters.html",
    )


def detail_page_pc(pc, link_map, graph=None):
    rendered = md_to_html(pc.body)
    linked = linkify_html(rendered, pc.href, link_map)
    img = (
        f'<img class="portrait portrait-large" src="{pc.image}" alt="{html.escape(pc.name)}">'
        if pc.image
        else ""
    )
    connections_block = _render_connections(pc.href, graph)
    battle_card = pc.meta["battle_card"].one()
    card_link = (
        f'<p class="battle-card-link"><a href="{battle_card}">'
        f"&#9876;&#65039; {html.escape(pc.name)}&rsquo;s battle card</a></p>"
        if battle_card
        else ""
    )
    body = f"""<article class="detail">
  {img}
  <p class="muted">{html.escape(pc.summary)}</p>
  {card_link}
  {connections_block}
  <div class="detail-body">
  {linked}
  </div>
</article>"""
    bc = f'<a href="characters.html">Characters</a> &rsaquo; {html.escape(pc.name)}'
    return page(
        pc.name,
        body,
        current_nav="characters.html",
        breadcrumb=bc,
        description=pc.summary,
        image=pc.image,
        canonical=pc.href,
        og_type="profile",
    )
