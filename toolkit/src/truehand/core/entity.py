"""The one entity model every kind of page is built from."""



class Entity:
    def __init__(self, kind, slug, name, aliases=None, body="",
                 meta=None, image=None, status=None, summary=None):
        self.kind = kind  # 'pc', 'npc', 'location', 'quest', 'session'
        self.slug = slug
        self.name = name
        self.aliases = aliases or []
        self.body = body
        self.meta = meta or {}
        self.image = image
        self.status = status
        self.summary = summary

    @property
    def href(self):
        prefix = {"pc": "pc", "npc": "npc", "location": "loc", "item": "item",
                  "quest": "quest", "session": "session"}[self.kind]
        return f"{prefix}-{self.slug}.html"


def build_link_map(entities):
    """alias -> href. First registration wins (PCs are added first)."""
    table = {}
    for e in entities:
        for n in [e.name] + list(e.aliases or []):
            n = n.strip()
            if not n or n in table:
                continue
            table[n] = e.href
    return table
