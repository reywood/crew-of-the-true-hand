"""The TTS cache key.

The only test here that protects money. chunk_hash() decides whether a speech
line is reused from sessions/<date>/audio/chunks/ or re-synthesized. Perturb it
and every cached chunk in every episode invalidates at once, re-billing a paid
ElevenLabs voice for ~366 lines.
"""

import json

import pytest

from truehand.pipelines.session_audio import (
    DELIVERY_PRESETS,
    chunk_hash,
    parse_script,
    resolve_delivery,
)

VOICE = "tEo3d4j7gzVojBL5Z4Pt"
MODEL = "eleven_multilingual_v2"


def test_frozen_hash_for_a_known_line():
    """Captured from the pre-migration script, so this pins equivalence
    with the code that produced every committed manifest — not merely with
    whatever the current implementation happens to do."""
    assert chunk_hash(
        "Well met, friend. Draw close to the fire.", VOICE, MODEL, "storyteller"
    ) == "88c000309ecec24d4df054b87ecfb8f8c05783f6cf34d84bde398b3c869b82d6"


def test_hash_is_stable_across_calls():
    a = chunk_hash("x", VOICE, MODEL, "storyteller")
    b = chunk_hash("x", VOICE, MODEL, "storyteller")
    assert a == b


@pytest.mark.parametrize("field", ["text", "voice", "model", "delivery"])
def test_every_input_participates(field):
    base = {"text": "x", "voice_id": VOICE, "model_id": MODEL,
            "delivery_key": "storyteller"}
    other = dict(base)
    other[{"text": "text", "voice": "voice_id", "model": "model_id",
           "delivery": "delivery_key"}[field]] = {
        "text": "y", "voice": "OTHERVOICE", "model": "other_model",
        "delivery": "hushed"}[field]
    assert chunk_hash(**base) != chunk_hash(**other)


def test_preset_values_are_baked_in(monkeypatch):
    """Tweaking a preset must invalidate its cached chunks."""
    before = chunk_hash("x", VOICE, MODEL, "storyteller")
    tweaked = dict(DELIVERY_PRESETS)
    tweaked["storyteller"] = dict(tweaked["storyteller"])
    tweaked["storyteller"]["stability"] = 0.999
    monkeypatch.setattr("truehand.pipelines.session_audio.DELIVERY_PRESETS", tweaked)
    assert chunk_hash("x", VOICE, MODEL, "storyteller") != before


def test_every_committed_manifest_still_resolves(paths):
    """The real guarantee: no episode re-bills on its next rebuild."""
    checked = 0
    for manifest_path in sorted(paths.sessions.glob("*/audio/manifest.json")):
        script = manifest_path.parent / "script.md"
        if not script.exists():
            continue
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        live = {
            chunk_hash(text, data["voice_id"], data["model_id"],
                       resolve_delivery(delivery)[0])
            for kind, text, delivery in
            (e for e in parse_script(script.read_text(encoding="utf-8")) if e[0] == "speak")
        }
        orphaned = set(data["chunks"]) - live
        assert not orphaned, (
            f"{manifest_path.parent.parent.name}: {len(orphaned)} cached chunks "
            f"would be re-synthesized"
        )
        checked += 1
    assert checked >= 10, f"only checked {checked} episodes"
