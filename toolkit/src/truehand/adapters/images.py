"""Image generation.

Replaces three copies of the same Gemini bootstrap (import guard, API-key
check, client construction, generate_content call, response unpacking) that
had drifted apart — different default models and different exit codes on a
missing dependency.

The ImageBackend protocol is the one dependency inversion here that earns its
keep: three pipelines generate images, and a fake backend lets prompt assembly
be tested without spending Gemini quota.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from ..core.env import require_env
from ..errors import OperationFailed
from ._optional import require

#: One default for every image command. The podcast-cover script was still
#: pinned to gemini-2.5-flash-image after the session-image and character-
#: reference pipelines moved to 3.1; this reconciles them.
DEFAULT_IMAGE_MODEL = "gemini-3.1-flash-image"

GEMINI_API_KEY = "GEMINI_API_KEY"


@runtime_checkable
class ImageBackend(Protocol):
    """Anything that can turn a prompt into image bytes."""

    def generate(self, contents: list[Any], *, model: str, aspect: str) -> bytes:
        """Return the bytes of a single generated image."""
        ...

    def part_from_bytes(self, data: bytes, mime_type: str) -> Any:
        """Wrap raw image bytes as a prompt part this backend understands."""
        ...


def extract_image(response) -> bytes:
    """Pull the first inline image out of a Gemini response.

    If the model returned text instead of an image, that text goes into the
    exception message — the three original copies variously raised a bare
    error and printed the text separately at the call site.
    """
    for candidate in getattr(response, "candidates", []) or []:
        content = getattr(candidate, "content", None)
        if not content:
            continue
        for part in getattr(content, "parts", []) or []:
            inline = getattr(part, "inline_data", None)
            if inline and getattr(inline, "data", None):
                return inline.data

    bits = []
    for candidate in getattr(response, "candidates", []) or []:
        for part in getattr(getattr(candidate, "content", None), "parts", []) or []:
            if getattr(part, "text", None):
                bits.append(part.text)
    raise OperationFailed(
        "no image in the Gemini response" + (":\n" + "\n".join(bits) if bits else "")
    )


class GeminiImageBackend:
    """ImageBackend backed by Google's Gemini image models."""

    def __init__(self, api_key: str | None = None, *, why: str = "Image generation"):
        genai = require("google.genai", extra="image", why=why)
        self._types = require("google.genai.types", extra="image", why=why)
        self._client = genai.Client(api_key=api_key or require_env(GEMINI_API_KEY, why=why))

    def part_from_bytes(self, data: bytes, mime_type: str = "image/jpeg"):
        return self._types.Part.from_bytes(data=data, mime_type=mime_type)

    def generate(self, contents: list[Any], *, model: str = DEFAULT_IMAGE_MODEL,
                 aspect: str = "16:9") -> bytes:
        response = self._client.models.generate_content(
            model=model,
            contents=contents,
            config=self._types.GenerateContentConfig(
                image_config=self._types.ImageConfig(aspect_ratio=aspect),
            ),
        )
        return extract_image(response)
