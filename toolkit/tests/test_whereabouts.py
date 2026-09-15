"""An NPC's `location:` has one reading, and its three answers differ on purpose.

The regression this guards: three modules each extracted a different meaning
from the same free-text field, disagreeing even on its shape — `one()` (the
first comma-fragment) in the loader, `prose()` (the whole line) in the prep
hub. "Is she at Silverymoon?" answered differently on the chart, the prep hub
and the roster, and nothing said which was intended.

The port-versus-whole-line distinction is the load-bearing one: Trades Ward is
itself a location, so reading the whole of "Waterdeep, Trades Ward" would move
the chart edge off Waterdeep onto the ward.
"""

import pytest

from truehand.core.entity import Entity
from truehand.core.frontmatter import Frontmatter
from truehand.core.loaders import load_dir_entities
from truehand.core.whereabouts import Whereabouts


def _npc(location=None):
    meta = {"location": location} if location is not None else {}
    return Entity(kind="npc", slug="n", name="N", meta=Frontmatter(meta))


def _loc(name, slug=None):
    return Entity(kind="location", slug=slug or name.lower().replace(" ", "-"), name=name)


WATERDEEP = _loc("Waterdeep")
TRADES_WARD = _loc("Trades Ward")
SILVERYMOON = _loc("Silverymoon")
EVERYWHERE = [WATERDEEP, TRADES_WARD, SILVERYMOON, _loc("Silver Marches")]


class TestReadingTheLine:
    def test_unset_is_falsey_and_nowhere(self):
        w = Whereabouts.of(_npc())
        assert not w
        assert w.port == "" and w.place == "" and str(w) == ""
        assert w.resolve(EVERYWHERE) is None

    def test_str_is_the_source_line_rejoined(self):
        assert str(Whereabouts.of(_npc(["Waterdeep", "Dock Ward"]))) == "Waterdeep, Dock Ward"

    def test_port_is_the_broad_place_the_line_leads_with(self):
        assert Whereabouts.of(_npc(["Waterdeep", "Dock Ward"])).port == "Waterdeep"

    def test_place_drops_a_parenthetical_but_keeps_a_comma_list(self):
        assert Whereabouts.of(_npc("Silverymoon (last known)")).place == "Silverymoon"
        assert Whereabouts.of(_npc(["Waterdeep", "Trades Ward"])).place == "Waterdeep, Trades Ward"


class TestProvisional:
    @pytest.mark.parametrize("raw", ["Silverymoon (last known)", "Pearl Isles (origin)"])
    def test_hedged_wording_is_provisional(self, raw):
        assert Whereabouts.of(_npc(raw)).is_provisional

    def test_a_plain_place_is_not(self):
        assert not Whereabouts.of(_npc("Nightstone")).is_provisional

    def test_only_the_port_fragment_is_tested(self):
        """A line naming a solid place first is not made provisional by a hedge
        further down it."""
        assert not Whereabouts.of(_npc(["Waterdeep", "Silverymoon (last known)"])).is_provisional

    def test_provisional_draws_no_chart_edge(self):
        assert Whereabouts.of(_npc("Silverymoon (last known)")).resolve(EVERYWHERE) is None


class TestResolveReadsThePort:
    def test_a_ward_does_not_steal_the_edge_from_its_city(self):
        """The load-bearing case: Trades Ward is a location, and longest-match
        over the whole line would pick it over Waterdeep."""
        w = Whereabouts.of(_npc(["Waterdeep", "Trades Ward"]))
        assert w.resolve(EVERYWHERE) is WATERDEEP

    def test_longest_name_wins_within_the_port(self):
        assert Whereabouts.of(_npc("The Silver Marches")).resolve(EVERYWHERE).name == (
            "Silver Marches"
        )

    def test_an_unknown_place_is_adrift(self):
        assert Whereabouts.of(_npc("With the crew")).resolve(EVERYWHERE) is None


class TestIsAtReadsTheWholeLine:
    def test_a_ward_dweller_is_found_from_the_city(self):
        assert Whereabouts.of(_npc(["Waterdeep", "Trades Ward"])).is_at(WATERDEEP)

    def test_and_from_the_ward(self):
        assert Whereabouts.of(_npc(["Waterdeep", "Trades Ward"])).is_at(TRADES_WARD)

    def test_a_provisional_lead_still_counts(self):
        """Who you would ask after there, even if we are not sure she is there."""
        assert Whereabouts.of(_npc("Silverymoon (last known)")).is_at(SILVERYMOON)

    def test_the_slug_spelling_matches_too(self):
        assert Whereabouts.of(_npc("golden fields")).is_at(_loc("Golden Fields", "golden-fields"))

    def test_elsewhere_is_not_here(self):
        assert not Whereabouts.of(_npc("Nightstone")).is_at(WATERDEEP)

    def test_unset_is_not_anywhere(self):
        assert not Whereabouts.of(_npc()).is_at(WATERDEEP)


class TestAgainstTheRealRoster:
    def test_every_npc_line_reads_without_raising(self, paths):
        npcs = load_dir_entities("npc", paths.npcs)
        locations = load_dir_entities("location", paths.locations)
        assert npcs and locations
        for npc in npcs:
            w = Whereabouts.of(npc)
            assert isinstance(w.place, str)
            port = w.resolve(locations)
            assert port is None or port.kind == "location"

    def test_ward_dwellers_moor_at_their_city(self, paths):
        """The real corpus has `location: Waterdeep, Trades Ward` and a
        Trades Ward location file; the edge belongs to Waterdeep."""
        npcs = load_dir_entities("npc", paths.npcs)
        locations = load_dir_entities("location", paths.locations)
        warded = [n for n in npcs if len(Whereabouts.of(n).parts) > 1]
        assert warded, "expected some comma-listed locations in npcs/"
        for npc in warded:
            port = Whereabouts.of(npc).resolve(locations)
            assert port is None or port.name == Whereabouts.of(npc).parts[0]
