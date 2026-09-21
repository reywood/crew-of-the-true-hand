"""The `sessions:` projection is computed through the model, not beside it.

The regression this guards: the sync carried its own copies of two rules core
already owned, and both had drifted. It folded an entity's `name` into its
alias list only when `aliases:` was absent entirely, where `load_dir_entities`
always prepends it — so `npcs/garret-ox-dorn.md`, whose name is the quoted
`Garret "Ox" Dorn` and whose aliases are the unquoted spellings, was linked on
its name across the site but never counted as mentioned by the one summary that
uses it. And it grepped the raw `summary.md`, frontmatter delimiters included,
where the Session aggregate strips that into `carried`.
"""

import pytest

from truehand.core.frontmatter import Frontmatter, parse_frontmatter
from truehand.core.loaders import entity_names, load_dir_entities, load_sessions
from truehand.core.session import Session
from truehand.core.summary import SessionSummary
from truehand.pipelines.entity_sessions import find_sessions, sync


def _session(date, markdown="", carried=()):
    return Session(date, summary=SessionSummary.parse(markdown), carried=tuple(carried))


class TestOneNamingRule:
    def test_the_name_is_always_among_the_aliases(self, tmp_path):
        p = tmp_path / "x.md"
        meta = Frontmatter({"name": 'Garret "Ox" Dorn', "aliases": ["Garret Dorn", "Ox Dorn"]})
        name, aliases = entity_names(meta, p)
        assert name == 'Garret "Ox" Dorn'
        assert aliases[0] == 'Garret "Ox" Dorn'
        assert "Garret Dorn" in aliases

    def test_a_repeated_name_is_not_duplicated(self, tmp_path):
        meta = Frontmatter({"name": "Molak", "aliases": ["Molak", "the innkeeper"]})
        _name, aliases = entity_names(meta, tmp_path / "molak.md")
        assert aliases == ["Molak", "the innkeeper"]

    def test_no_name_falls_back_to_the_filename(self, tmp_path):
        name, aliases = entity_names(Frontmatter({}), tmp_path / "old-sea-dog.md")
        assert name == "Old Sea Dog"
        assert aliases == ["Old Sea Dog"]

    def test_the_loader_and_the_sync_agree_on_every_real_file(self, paths):
        """The two used to disagree; nothing may reintroduce a second rule."""
        for directory, kind in ((paths.npcs, "npc"), (paths.locations, "location")):
            for entity in load_dir_entities(kind, directory):
                path = directory / f"{entity.slug}.md"
                fm, _ = parse_frontmatter(path.read_text(encoding="utf-8"))
                assert entity_names(Frontmatter(fm), path) == (entity.name, entity.aliases)


class TestTheSessionOwnsTheMatch:
    def test_a_summary_mention_counts(self):
        s = _session("2026-01-01", "*In brief: Naxene explains the rift.*")
        assert s.mentions(["Naxene"])

    def test_matching_is_word_boundary_and_case_sensitive(self):
        s = _session("2026-01-01", "*In brief: they met Ox Dornish.*")
        assert not s.mentions(["Ox Dorn"])
        assert not s.mentions(["ox dornish"])

    def test_a_quoted_nickname_matches(self):
        s = _session("2026-01-01", '*In brief: Garret "Ox" Dorn hauls the line.*')
        assert s.mentions(['Garret "Ox" Dorn'])

    def test_the_carried_list_counts_too(self):
        s = _session("2026-01-01", "*In brief: loot.*", carried=["a brass bottle"])
        assert s.mentions(["brass bottle"])

    def test_frontmatter_delimiters_are_not_searchable_text(self):
        """The sync used to grep the raw file, so `carried` and `---` were in
        scope as prose. The aggregate strips them."""
        s = _session("2026-01-01", "*In brief: nothing.*", carried=["a rope"])
        assert not s.mentions(["carried"])

    def test_no_aliases_matches_nothing(self):
        assert not _session("2026-01-01", "*In brief: x.*").mentions([])

    def test_a_session_with_no_summary_mentions_nothing(self):
        assert not Session("2026-01-01", notes="Naxene").mentions(["Naxene"])


class TestFindSessions:
    def test_dates_come_back_oldest_first(self):
        sessions = [
            _session("2026-02-01", "*In brief: Naxene again.*"),
            _session("2025-09-23", "*In brief: Naxene first.*"),
            _session("2026-01-01", "*In brief: nobody.*"),
        ]
        assert find_sessions(["Naxene"], sessions) == ["2025-09-23", "2026-02-01"]

    def test_no_match_is_empty(self):
        assert find_sessions(["Nobody"], [_session("2026-01-01", "*In brief: x.*")]) == []


@pytest.fixture(scope="module")
def synced(paths):
    """The archive is already in sync, so a dry run must change nothing."""
    return sync(paths, dry_run=True)


class TestAgainstTheRealArchive:
    def test_the_archive_is_in_sync(self, synced):
        stale = [(r.directory.name, r.changes) for r in synced if r.changed]
        assert stale == [], "run `truehand entities sync`"

    def test_every_directory_was_scanned(self, synced, paths):
        expected = [len(list(d.glob("*.md"))) for d in (paths.npcs, paths.locations, paths.items)]
        assert [r.total for r in synced] == expected
        assert all(n for n in expected)

    def test_the_quoted_nickname_is_recorded(self, paths):
        """The bug this rule change fixed, pinned to the file that had it."""
        garret = next(n for n in load_dir_entities("npc", paths.npcs) if n.slug == "garret-ox-dorn")
        assert "2025-09-23" in garret.meta["sessions"].many()

    def test_recorded_mentions_match_what_the_sessions_say(self, paths):
        sessions = load_sessions(paths)
        for kind, directory in (("npc", paths.npcs), ("item", paths.items)):
            for entity in load_dir_entities(kind, directory):
                assert entity.meta["sessions"].many() == find_sessions(entity.aliases, sessions)
