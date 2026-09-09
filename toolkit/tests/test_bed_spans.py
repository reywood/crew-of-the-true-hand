"""Bed-span resolution, which used to be untestable.

The state machine that turns bed markers into concrete under-bed spans sat at
the bottom of build_episode, so it could only run after ElevenLabs had been
called and ffmpeg had stitched. It is pure logic over an ordered marker list;
now it is a function.
"""

from truehand.pipelines.session_audio import BedSpan, resolve_bed_spans


def marker(kind, at_ms, label=""):
    return {"kind": kind, "at_ms": at_ms, "label": label}


class TestResolveBedSpans:
    def test_no_markers_means_no_beds(self):
        assert resolve_bed_spans([], 10_000) == []

    def test_an_end_marker_closes_the_open_span(self):
        spans = resolve_bed_spans(
            [marker("start_hearth", 0, "fire"), marker("end", 4_000)], 10_000)
        assert spans == [BedSpan("hearth", "fire", 0, 4_000)]

    def test_a_span_left_open_closes_at_the_end_of_the_show(self):
        spans = resolve_bed_spans([marker("start_hearth", 2_000, "fire")], 9_000)
        assert spans == [BedSpan("hearth", "fire", 2_000, 9_000)]

    def test_an_opener_replaces_whatever_was_playing(self):
        spans = resolve_bed_spans(
            [marker("start_cold_open", 0, "ember"),
             marker("start_hearth", 3_000, "fire")], 8_000)
        assert spans == [BedSpan("cold_open", "ember", 0, 3_000),
                         BedSpan("hearth", "fire", 3_000, 8_000)]

    def test_zero_length_spans_are_dropped(self):
        """Two markers at the same cursor position render nothing."""
        spans = resolve_bed_spans(
            [marker("start_hearth", 5_000, "fire"), marker("end", 5_000)], 9_000)
        assert spans == []

    def test_an_end_with_nothing_open_is_harmless(self):
        assert resolve_bed_spans([marker("end", 3_000)], 9_000) == []

    def test_every_span_kind_is_recognised(self):
        for kind, expected in [("start_cold_open", "cold_open"),
                               ("start_hearth", "hearth"),
                               ("start_signature", "signature")]:
            spans = resolve_bed_spans([marker(kind, 0, "x")], 1_000)
            assert spans[0].kind == expected

    def test_duration_is_derived_not_stored(self):
        assert BedSpan("hearth", "x", 1_500, 4_000).duration_sec == 2.5


class TestEpisodeResult:
    def test_runtime_estimate_uses_the_measured_calibration(self):
        import pathlib

        from truehand.pipelines.session_audio import EpisodeResult
        result = EpisodeResult("dry-run", pathlib.Path("x.mp3"), characters=8880)
        assert round(result.estimated_minutes) == 10

    def test_the_pipeline_no_longer_prints(self, capsys):
        """Every other pipeline returns its outcome; this one used to print."""
        import inspect

        from truehand.pipelines import session_audio
        assert "print(" not in inspect.getsource(session_audio)
