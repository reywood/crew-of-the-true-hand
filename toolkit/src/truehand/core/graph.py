"""The materialized entity graph behind graph.json and the Connections block."""

from .loaders import SESSION_LOCATIONS, port_for
from .text import _clean_blurb, _extract_session_dates, slugify


def _meta_first(val):
    """First scalar of a frontmatter field that may be a str, list, or None."""
    if isinstance(val, list):
        return val[0] if val else ""
    if isinstance(val, str):
        return val.strip()
    return val or ""


def _first_scalar(v):
    if isinstance(v, list):
        return v[0] if v else ""
    return v or ""


def _as_list(v):
    if not v:
        return []
    if isinstance(v, list):
        return [str(x).strip() for x in v if str(x).strip()]
    return [x.strip() for x in str(v).split(",") if x.strip()]


class Graph:
    """Materialized entity graph. Nodes/edges are JSON-serializable; the
    adjacency dicts and faction index drive the Connections block."""
    def __init__(self):
        self.nodes = []                 # list of node dicts
        self.edges = []                 # list of {source, target, rel}
        self.node_by_id = {}            # id -> node dict
        self.out_adj = {}               # id -> [(rel, target_id)]
        self.in_adj = {}                # id -> [(rel, source_id)]
        self.faction_members = {}       # faction_id -> [npc id, ...]

    def _edge(self, src, tgt, rel):
        if not src or not tgt or src == tgt:
            return
        self.edges.append({"source": src, "target": tgt, "rel": rel})
        self.out_adj.setdefault(src, []).append((rel, tgt))
        self.in_adj.setdefault(tgt, []).append((rel, src))

    def as_dict(self):
        return {"nodes": self.nodes, "edges": self.edges}


def build_graph(pcs, npcs, locations, items, quests, sessions, session_lookup):
    entities = pcs + npcs + locations + items + quests + sessions
    g = Graph()

    # id resolution: alias -> entity, first-wins (PCs first, matching the
    # prose linker's precedence). Used to turn frontmatter name strings into
    # node ids.
    alias_lookup = {}
    for e in entities:
        for n in [e.name] + list(e.aliases or []):
            key = n.strip().lower()
            if key and key not in alias_lookup:
                alias_lookup[key] = e

    def resolve(name):
        if not name:
            return None
        return alias_lookup.get(str(name).strip().lower())

    loc_by_slug = {l.slug: l for l in locations}
    location_names = [l.name for l in locations]

    # --- nodes (one per real entity) ---
    for e in entities:
        node = {
            "id": e.href,
            "kind": e.kind,
            "name": e.name,
            "aliases": list(e.aliases or []),
            "url": e.href,
            "blurb": _clean_blurb(e.summary or e.body),
        }
        g.nodes.append(node)
        g.node_by_id[e.href] = node

    def faction_node(name):
        """Get-or-create a synthetic faction node (no page). Returns its id."""
        fid = "faction-" + slugify(name)
        if fid not in g.node_by_id:
            node = {"id": fid, "kind": "faction", "name": name,
                    "aliases": [name], "url": "", "blurb": ""}
            g.nodes.append(node)
            g.node_by_id[fid] = node
            g.faction_members[fid] = []
        return fid

    # --- edges ---
    for e in entities:
        # appears_in: entity -> session (materialized 'sessions:' field)
        for d in _extract_session_dates(e.meta.get("sessions")):
            s = session_lookup.get(d)
            if s:
                g._edge(e.href, s.href, "appears_in")

    for npc in npcs:
        # located_in: npc -> location (port_for normalizes the free-text field)
        port = port_for(npc, location_names)
        if port:
            tgt = resolve(port)
            if tgt and tgt.kind == "location":
                g._edge(npc.href, tgt.href, "located_in")
        # affiliated_with: npc -> faction (synthetic node)
        for aff in _as_list(npc.meta.get("affiliation")):
            fid = faction_node(aff)
            g._edge(npc.href, fid, "affiliated_with")
            g.faction_members[fid].append(npc.href)
        # can_help: npc -> item (expertise join, already attached)
        for item in npc.meta.get("can_help_with") or []:
            g._edge(npc.href, item.href, "can_help")

    for loc in locations:
        # within: loc -> loc, only when the referenced place is a known location
        for field in ("region", "location", "near"):
            for ref in _as_list(loc.meta.get(field)):
                tgt = resolve(ref)
                if tgt and tgt.kind == "location":
                    g._edge(loc.href, tgt.href, "within")
        # governs: loc's ruler/patron/captain -> this location
        for field in ("ruler", "patron", "captain"):
            for ref in _as_list(loc.meta.get(field)):
                who = resolve(ref)
                if who and who.kind in ("npc", "pc"):
                    g._edge(who.href, loc.href, "governs")

    for item in items:
        # held_by: item -> pc (skip "Party")
        holder = _first_scalar(item.meta.get("holder"))
        if holder and holder.strip().lower() != "party":
            who = resolve(holder)
            if who and who.kind == "pc":
                g._edge(item.href, who.href, "held_by")
        # acquired_in: item -> session (origin date)
        origin = _first_scalar(item.meta.get("origin"))
        s = session_lookup.get(str(origin).strip())
        if s:
            g._edge(item.href, s.href, "acquired_in")
        # gave: giver npc -> item
        giver = _first_scalar(item.meta.get("giver"))
        who = resolve(giver)
        if who and who.kind in ("npc", "pc"):
            g._edge(who.href, item.href, "gave")

    for q in quests:
        # depends_on: quest -> quest (QUEST_DEPENDENCIES, already attached)
        for tgt in q.meta.get("helps") or []:
            g._edge(q.href, tgt.href, "depends_on")

    for date, slugs in SESSION_LOCATIONS.items():
        s = session_lookup.get(date)
        if not s:
            continue
        for slug in slugs:
            loc = loc_by_slug.get(slug)
            if loc:
                g._edge(s.href, loc.href, "session_at")

    return g
