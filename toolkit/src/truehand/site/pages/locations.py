"""The locations sea-chart and its pins."""

import html
import re

from ..layout import page
from ..linkify import linkify_html

LOCATION_MAP_DATA = {
    # On-chart pins: x%, y% of the map image (faerun.png, 1573×1000).
    # Coords are the brass dot position. Region labels (no dot) are centered on
    # the coord. Most positions come from faerun.csv (pixel coords ÷ map size).
    #
    "waterdeep":           {"x": 34.9, "y": 78.3, "dir": "w"},
    "nightstone":          {"x": 43.3, "y": 79.3, "dir": "se"},
    "ardeep-forest":       {"x": 42.8, "y": 76.6, "dir": "nw"},  # west of dot to clear Nightstone
    "golden-fields":       {"x": 44.3, "y": 71.8, "dir": "ne"},  # north of dot to clear Ardeep
    "triboar":             {"x": 42.2, "y": 43.8},
    "kryptgarden-forest":  {"x": 36.7, "y": 58.1},
    "silverymoon":         {"x": 58.4, "y": 27.0},
    "silver-marches":      {"x": 71.8, "y": 15.9},  # region label
    "spine-of-the-world":  {"x": 38.8, "y": 9.3},   # region label across top
    "bryn-shandar":        {"x": 19.5, "y": 11.1, "dir": "se"},  # "Bryn Shander" in CSV
    # Not on the canon map — campaign-specific wreck site, placed offshore in
    # the Sea of Swords, west of Nightstone. Label hangs further west into
    # the open sea.
    "the-true-hand":       {"x": 38.0, "y": 83.0, "dir": "w"},
    #
    # Off-chart cartouches (south of frame, mythic, or fictional):
    "athkatla":            {"cartouche": "Far South"},
    "halruaa":             {"cartouche": "Far South"},
    "eye-of-annam":        {"cartouche": "Beyond the Charts"},
    "pearl-isles":         {"cartouche": "Beyond the Charts"},
    "darkar":              {"cartouche": "Whereabouts Unknown"},
    "darkhope":            {"cartouche": "Whereabouts Unknown"},
}


CARTOUCHE_ORDER = ["Far South", "Beyond the Charts", "Whereabouts Unknown"]


MAP_IMAGE = '<img class="map-image" src="static/faerun.png" alt="A map of the Sword Coast" loading="lazy">'


def locations_chart_page(locations, link_map):
    pins = []
    cartouches = {n: [] for n in CARTOUCHE_ORDER}
    for loc in locations:
        data = LOCATION_MAP_DATA.get(loc.slug, {})
        if "x" in data:
            pins.append((loc, data["x"], data["y"], data.get("dir", "e")))
        elif "cartouche" in data:
            cartouches[data["cartouche"]].append(loc)

    chunks = [
        '<h1>The Chart</h1>',
        '<p class="subhead"><em>A working chart of the Sword Coast. Mark not for scale.</em></p>',
        '<div class="map-plate">',
        MAP_IMAGE,
    ]
    for loc, x, y, label_dir in pins:
        is_region = loc.slug in ("spine-of-the-world", "silver-marches")
        classes = ["map-pin"]
        if is_region:
            classes.append("map-pin-region")
        elif label_dir != "e":
            classes.append(f"map-pin-dir-{label_dir}")
        cls = " ".join(classes)
        chunks.append(
            f'<a class="{cls}" href="{loc.href}" style="left:{x}%;top:{y}%">'
            f'<span class="map-pin-dot"></span>'
            f'<span class="map-pin-label">{html.escape(loc.name)}</span>'
            f'</a>'
        )
    chunks.append('</div>')

    chunks.append('<aside class="map-cartouches">')
    for cname in CARTOUCHE_ORDER:
        members = cartouches[cname]
        if not members:
            continue
        chunks.append('<div class="cartouche">')
        chunks.append(f'<h4>{html.escape(cname)}</h4>')
        chunks.append('<ul>')
        for loc in sorted(members, key=lambda l: l.name.lower()):
            chunks.append(f'<li><a href="{loc.href}">{html.escape(loc.name)}</a></li>')
        chunks.append('</ul>')
        chunks.append('</div>')
    chunks.append('</aside>')

    chunks.append('<section class="location-roster">')
    chunks.append('<h2>All Locations</h2>')
    chunks.append('<ul class="location-list">')
    for loc in sorted(locations, key=lambda l: l.name.lower()):
        loc_type = loc.meta.get("type", "")
        if isinstance(loc_type, list):
            loc_type = loc_type[0] if loc_type else ""
        type_html = (f'<span class="loc-type">{html.escape(loc_type)}</span>'
                     if loc_type else "")
        chunks.append(
            f'<li><a href="{loc.href}">{html.escape(loc.name)}</a>{type_html}</li>'
        )
    chunks.append('</ul>')
    chunks.append('</section>')

    body = "\n".join(chunks)
    return page("Locations", linkify_html(body, "locations.html", link_map),
                current_nav="locations.html",
                description='Everywhere the crew has been or heard of, from Nightstone to Waterdeep to the Spine of the World.',
                canonical="locations.html")


def _location_strip_qualifier(loc):
    """'Silverymoon (last known)' -> 'Silverymoon'; 'Waterdeep, Trades Ward' kept."""
    if not loc:
        return ""
    return re.sub(r"\s*\([^)]*\)\s*", "", loc).strip()


def _affiliations(meta):
    aff = meta.get("affiliation", "")
    if isinstance(aff, list):
        return [a for a in aff if a]
    if isinstance(aff, str) and aff.strip():
        return [a.strip() for a in aff.split(",") if a.strip()]
    return []
