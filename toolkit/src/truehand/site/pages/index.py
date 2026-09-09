"""The home page, and the quest scoring that drives it."""

import html
import re

from ...core.markdown import md_inline
from ..layout import SITE_NAME, page


def _quest_recency(quest) -> str:
    """Latest YYYY-MM-DD referenced in a quest's body — the parenthetical
    session dates at the end of each quest bullet in quests.md. Returns
    empty string if the quest carries no date."""
    dates = re.findall(r"\b(\d{4}-\d{2}-\d{2})\b", quest.body or "")
    return max(dates) if dates else ""


def _top_active_quests(quests, limit=6):
    """Rank active quests by (impact × recency). Completed quests drop out;
    impact wins ties, most-recent-session wins within an impact tier."""
    ranked = []
    for q in quests:
        impact = q.status.impact if q.status else 0
        if impact == 0:
            continue
        recency = _quest_recency(q) or "0000-00-00"
        ranked.append((impact, recency, q))
    ranked.sort(key=lambda t: (t[0], t[1]), reverse=True)
    return ranked[:limit]


def _render_quest_li(q, relations):
    """One <li class="home-quest"> for a quest — name + status chip, summary,
    dependency lines (helps / steps-toward), and a last-touched session link.
    Shared by the home 'What's on your plate' list and the prep hub."""
    recency = _quest_recency(q)
    last_touched = ""
    if recency:
        last_touched = (
            f'<a class="home-quest-touch" href="session-{recency}.html">'
            f"last touched · session {recency}</a>"
        )
    summary = md_inline(q.summary or "")

    dep_lines = []
    helps = relations.helps_for(q)
    supported_by = relations.supported_by_for(q)
    if helps:
        links = " · ".join(f'<a href="{d.href}">{html.escape(d.name)}</a>' for d in helps)
        dep_lines.append(
            f'<span class="home-quest-dep"><span class="dep-arrow">&rarr;</span> '
            f"helps: {links}</span>"
        )
    if supported_by:
        links = " · ".join(f'<a href="{d.href}">{html.escape(d.name)}</a>' for d in supported_by)
        dep_lines.append(
            f'<span class="home-quest-dep"><span class="dep-arrow">&larr;</span> '
            f"steps toward this: {links}</span>"
        )
    deps_html = f'<p class="home-quest-deps">{" ".join(dep_lines)}</p>' if dep_lines else ""

    return f"""
    <li class="home-quest">
      <div class="home-quest-head">
        <a class="home-quest-name" href="{q.href}">{html.escape(q.name)}</a>
        <span class="status-chip status-{q.status.css_class}">{html.escape(q.status.label)}</span>
      </div>
      <p class="home-quest-line">{summary}</p>
      {deps_html}
      {last_touched}
    </li>"""


def index_page(pcs, npcs, locations, quests, sessions, relations):
    top_quests = _top_active_quests(quests, limit=6)
    recent = sessions[::-1][:3] if sessions else []

    cards = """
<section class="hero">
  <h1>The Crew of the <em>True Hand</em></h1>
  <p class="tagline">A four-soul company aboard borrowed sails, chasing the cause of giants run wild across the North.</p>
  <p class="hero-cta">Prepping for the next session? <a href="next.html">Start here &rsaquo;</a></p>
</section>
"""

    if top_quests:
        cards += """
<section class="home-quests">
  <h2>What's on your plate</h2>
  <p class="muted small home-quests-note">Ranked by story impact, then by the last session that touched it.</p>
  <ul class="home-quest-list">"""
        for _impact, _recency, q in top_quests:
            cards += _render_quest_li(q, relations)
        cards += """
  </ul>
  <p class="home-more"><a href="quests.html">See the full quest log &rsaquo;</a></p>
</section>
"""

    if recent:
        cards += "<section class='recent'><h2>Most recent sessions</h2><ul class='session-list'>"
        for s in recent:
            cards += (
                f'<li><a href="{s.href}">{html.escape(s.name)}</a> — {html.escape(s.blurb)}</li>'
            )
        cards += "</ul></section>"

    # Directory / navigation grid — moved beneath the actionable content so
    # active players see quests and sessions first. Still useful as a
    # browsing directory for casual visitors.
    active_quests = [q for q in quests if q.status and q.status.is_active]
    cards += f"""
<section class="home-directory">
<h2>Browse the archive</h2>
<div class="grid grid-2">
  <a class="card" href="characters.html">
    <h2><span class="icon">⚓</span> The Crew</h2>
    <p>{len(pcs)} player characters, each with their own port of call.</p>
  </a>
  <a class="card" href="quests.html">
    <h2><span class="icon">🧭</span> Quests</h2>
    <p>{len(active_quests)} active threads, side leads, and completed jobs.</p>
  </a>
  <a class="card" href="sessions.html">
    <h2><span class="icon">📜</span> Sessions</h2>
    <p>{len(sessions)} logged sessions, from the wreck off Nightstone to the streets of Waterdeep.</p>
  </a>
  <a class="card" href="npcs.html">
    <h2><span class="icon">🪶</span> NPCs</h2>
    <p>{len(npcs)} catalogued friends, foes, and folk worth remembering.</p>
  </a>
  <a class="card" href="locations.html">
    <h2><span class="icon">🗺</span> Locations</h2>
    <p>{len(locations)} ports and waypoints across Faerûn.</p>
  </a>
</div>
</section>
"""
    return page(
        "Home",
        cards,
        current_nav="index.html",
        share_title=SITE_NAME,
        description=(
            "The player-side archive of a Storm King's Thunder campaign — "
            "session recaps and a narrated audio retelling, the crew, the folk "
            "they've met, and every thread still hanging."
        ),
        canonical="index.html",
    )
