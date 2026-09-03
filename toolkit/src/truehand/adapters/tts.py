"""Text-to-speech.

TTSBackend exists as a Protocol despite having one implementation: it is the
seam that lets the audio pipeline be exercised without calling ElevenLabs,
which costs real money on the paid Cormac voice.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from ..core.env import require_env
from ._optional import require

#: How much surrounding text is sent for prosody continuity. These caps are
#: part of the API call, so changing them changes the audio.
PREVIOUS_TEXT_CHARS = 600
NEXT_TEXT_CHARS = 200

#: Cormac, "Irish Fantasy Storyteller". A professional voice — needs a paid
#: ElevenLabs plan; the free tier cannot use it via the API.
DEFAULT_VOICE_ID = "tEo3d4j7gzVojBL5Z4Pt"
DEFAULT_MODEL_ID = "eleven_multilingual_v2"
DEFAULT_OUTPUT_FORMAT = "mp3_44100_128"

ELEVENLABS_API_KEY = "ELEVENLABS_API_KEY"


@runtime_checkable
class TTSBackend(Protocol):
    def synthesize(self, text: str, *, voice_id: str, model_id: str,
                   settings: dict[str, Any], previous_text: str | None,
                   next_text: str | None) -> bytes:
        """Return MP3 bytes for one spoken line."""
        ...


class ElevenLabsBackend:
    """TTSBackend backed by the ElevenLabs API.

    The client is built lazily on first use, so a fully cached rebuild needs
    neither the package nor an API key.
    """

    def __init__(self, api_key: str | None = None,
                 output_format: str = DEFAULT_OUTPUT_FORMAT):
        self._api_key = api_key
        self._output_format = output_format
        self._client = None

    def _ensure(self):
        if self._client is None:
            mod = require("elevenlabs.client", extra="audio",
                          why="Audio generation")
            key = self._api_key or require_env(ELEVENLABS_API_KEY,
                                               why="Audio generation")
            self._client = mod.ElevenLabs(api_key=key)
        return self._client

    def synthesize(self, text, *, voice_id=DEFAULT_VOICE_ID,
                   model_id=DEFAULT_MODEL_ID, settings=None,
                   previous_text=None, next_text=None) -> bytes:
        client = self._ensure()
        kwargs = {"text": text, "voice_id": voice_id, "model_id": model_id,
                  "output_format": self._output_format,
                  "voice_settings": settings or {}}
        # Omitted entirely when empty, and truncated — matching the original
        # call exactly, because either change would alter the rendered audio.
        if previous_text:
            kwargs["previous_text"] = previous_text[-PREVIOUS_TEXT_CHARS:]
        if next_text:
            kwargs["next_text"] = next_text[:NEXT_TEXT_CHARS]
        return b"".join(client.text_to_speech.convert(**kwargs))
