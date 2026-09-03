"""Orchestration: load the archive, render every page, write the tree."""

import json

from ..core.entity import build_link_map
from ..core.graph import build_graph
from ..core.loaders import (
    load_campaign_state,
    load_dir_entities,
    load_pcs,
    load_quests,
    load_sessions,
)
from .assets import setup_output, write_page
from .feed import _mp3_duration_seconds, podcast_feed
from .layout import DEFAULT_BASE_URL, configure
from .pages.detail import detail_page_generic
from .pages.index import _attach_item_expertise, _attach_quest_deps, index_page
from .pages.items import item_list_page
from .pages.locations import locations_chart_page
from .pages.npcs import npc_table_page
from .pages.pcs import detail_page_pc, pc_list_page
from .pages.prep import prep_page, threads_page
from .pages.quests import detail_page_quest, quest_list_page
from .pages.sessions import detail_page_session, session_list_page


def build_site(paths, *, base_url=None, out_dir=None, probe=None):
    """Render the whole site into *out_dir*.

    ``probe`` is the MP3 duration function used for the podcast feed's
    <itunes:duration>. It is injected because it is the only nondeterminism in
    the build (it shells out to ffprobe), which lets the golden test run
    hermetically with frozen durations.
    """
    base_url = (base_url or DEFAULT_BASE_URL).rstrip("/")
    out_dir = out_dir or paths.site
    probe = probe or _mp3_duration_seconds
    configure(paths.static, base_url)

    pcs = load_pcs(paths)
    npcs = load_dir_entities("npc", paths.npcs)
    locations = load_dir_entities("location", paths.locations)
    items = load_dir_entities("item", paths.items)
    quests = load_quests(paths)
    _attach_quest_deps(quests)
    _attach_item_expertise(items, npcs)
    sessions = load_sessions(paths)
    session_lookup = {s.slug: s for s in sessions}

    all_entities = pcs + npcs + locations + items + quests + sessions
    link_map = build_link_map(all_entities)

    graph = build_graph(pcs, npcs, locations, items, quests, sessions,
                        session_lookup)

    setup_output(paths, out_dir)

    def write(filename, content):
        write_page(out_dir, filename, content)

    # Materialize the graph + a slim search index. graph.json is for tooling
    # and reasoning; search-index.json powers the client-side site search.
    write("graph.json", json.dumps(graph.as_dict(), indent=1,
                                   ensure_ascii=False, sort_keys=True))
    search_index = [
        {"name": n["name"], "aliases": n["aliases"], "kind": n["kind"],
         "url": n["url"], "blurb": n["blurb"]}
        for n in graph.nodes if n["url"]
    ]
    write("search-index.json", json.dumps(search_index,
                                          ensure_ascii=False, sort_keys=True))

    write("index.html", index_page(pcs, npcs, locations, quests, sessions))

    state = load_campaign_state(paths)
    write("next.html", prep_page(pcs, npcs, locations, items, quests,
                                  sessions, state, session_lookup, link_map))
    write("threads.html", threads_page(sessions, session_lookup, link_map))

    write("characters.html", pc_list_page(pcs, link_map))
    for pc in pcs:
        write(pc.href, detail_page_pc(pc, link_map, graph))

    write("npcs.html", npc_table_page(npcs, link_map))
    for e in npcs:
        write(e.href, detail_page_generic(
            e, "npcs.html", "NPCs", link_map, session_lookup, graph))

    write("locations.html", locations_chart_page(locations, link_map))
    for e in locations:
        write(e.href, detail_page_generic(
            e, "locations.html", "Locations", link_map, session_lookup, graph))

    write("items.html", item_list_page(items, link_map))
    for e in items:
        write(e.href, detail_page_generic(
            e, "items.html", "Items", link_map, session_lookup, graph))

    write("quests.html", quest_list_page(quests, link_map))
    for q in quests:
        write(q.href, detail_page_quest(q, link_map, session_lookup))

    write("sessions.html", session_list_page(sessions, locations, link_map))
    # `sessions` is ordered oldest→newest; give each detail page its
    # chronological neighbours for the prev/next pager.
    for i, s in enumerate(sessions):
        prev = sessions[i - 1] if i > 0 else None
        nxt = sessions[i + 1] if i < len(sessions) - 1 else None
        write(s.href, detail_page_session(s, link_map, prev, nxt))

    write("feed.xml", podcast_feed(paths, sessions, probe))
    n_episodes = sum(1 for s in sessions if s.meta.get("has_audio"))

    total = 9 + len(pcs) + len(npcs) + len(locations) + len(items) + len(quests) + len(sessions)
    return {
        "out_dir": out_dir,
        "total": total,
        "episodes": n_episodes,
        "counts": {
            "pcs": len(pcs), "npcs": len(npcs), "locations": len(locations),
            "items": len(items), "quests": len(quests), "sessions": len(sessions),
        },
    }
