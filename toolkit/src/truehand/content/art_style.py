"""Art-direction prose for the image pipelines.

These three prompts lived in three scripts and had drifted in wording. They
are co-located here so there is one place to edit them, but deliberately NOT
merged into a single string: they serve different jobs (a full scene, a
character reference plate, the podcast cover) and rewriting the prose would
change the art the model produces. Unifying the wording is a content decision,
not a refactor — do it separately, with the images reviewed.

What must stay consistent between them is the palette and the reference,
named below so a change to one is an obvious prompt to update the others.
"""

#: The shared visual vocabulary. Every prompt below expresses this; keep them
#: in agreement when editing.
ART_PALETTE = (
    "pen-and-ink with a light watercolor wash; loose crosshatch linework; "
    "umber, sepia, burnished gold, muted teal, dusty rose; thin tints letting "
    "paper texture show; mid-20th-century illustrated storybook or Victorian "
    "traveler's sketchbook; NOT a polished full-color fantasy painting, NOT a "
    "video-game render, NOT thick opaque paint"
)

# -- full scene illustrations (hero + beat images) --------------------------

STYLE_INSTRUCTIONS = """You are illustrating a scene from a Dungeons & Dragons \
campaign recap that will sit on a parchment-toned website page.

STYLE (critical — this is the number-one thing to get right):
Pen-and-ink drawing with a LIGHT WATERCOLOR WASH over it. Loose crosshatch \
linework doing most of the work; watercolor tints (umber, sepia, burnished \
gold, muted teal, dusty rose) applied thinly, letting paper texture show \
through. NOT a polished full-color fantasy painting. NOT a video-game cover. \
NOT thick opaque paint. Think mid-20th-century illustrated storybook or a \
Victorian traveler's sketchbook — an evocative moment captured with restraint. \
Leave real negative space: parts of the image should be sparser, not \
crammed with detail from edge to edge.

COMPOSITION:
The image MUST be LANDSCAPE ORIENTATION, roughly 2:1 aspect ratio (much wider \
than it is tall — think of a book spread, not a square panel). Frame ONE \
evocative moment — the pivotal beat of the scene, not an action-pose lineup \
of every character present.

CHARACTERS:
The four portrait references (Fiz, Hal, Toz, Eno) are provided so you can \
tell the PCs apart. Include ONLY the PCs actually named in the pivotal moment \
below. Read each identity anchor carefully — the model has a habit of drifting \
Fiz into a dwarf or bald tinker and drifting Eno feminine. Both are wrong. \
Preserve race, size, sex, and costume from the identity anchors. Do NOT \
label them, do NOT add speech bubbles, do NOT add any text, letters, numbers, \
or captions anywhere in the image."""


# -- character reference plates -------------------------------------------

REFERENCE_PLATE_STYLE = """STYLE (critical — match this exactly): pen-and-ink drawing with a \
LIGHT WATERCOLOR WASH over it. Loose crosshatch linework doing most of the \
work; watercolor tints (umber, sepia, burnished gold, muted teal, dusty rose) \
applied thinly, letting paper texture show through. NOT a polished full-color \
fantasy painting, NOT a video-game render, NOT thick opaque paint. Think a \
mid-20th-century illustrated storybook or a Victorian traveler's sketchbook."""


PLATES = {
    1: (
        "2:3",
        "A full-length CHARACTER REFERENCE PLATE of ONE single figure, "
        "standing in a relaxed, neutral three-quarter pose facing the viewer, "
        "the whole body visible from head to boots. Plain, empty parchment-"
        "toned background — NO scenery, NO landscape, NO other characters. "
        "Render every signature feature and piece of gear from the identity "
        "anchor clearly and correctly.",
    ),
    2: (
        "1:1",
        "A HEAD-AND-SHOULDERS PORTRAIT REFERENCE PLATE of the SAME single "
        "character, facing the viewer against a plain parchment-toned "
        "background — NO scenery, NO other characters. Emphasize the face and "
        "head with total clarity: hair shape and color, ear shape, eyes, "
        "expression, and — critically — the exact state of the facial hair "
        "described in the anchor (a clean-shaven man must have a visibly "
        "smooth bare face; a bearded man a full beard).",
    ),
}


# -- podcast cover ---------------------------------------------------------

COVER_PROMPT = """You are illustrating the podcast cover art for a Dungeons & \
Dragons audio recap series called "TALES OF THE TRUE HAND". The cover will be \
displayed at small sizes (as tiny as 55x55 pixels in a podcast grid) as well \
as large (1400x1400+). Design accordingly: bold silhouettes, strong central \
subject, minimal small detail near the edges.

FORMAT: SQUARE — 1:1 aspect ratio. This is podcast cover art, not a landscape \
scene. Fill the whole square.

STYLE: Pen-and-ink drawing with a warm watercolor wash. Loose crosshatch \
linework; watercolor tints in umber, sepia, burnished gold, and muted teal, \
applied thinly with paper texture showing through. Mid-20th-century \
illustrated storybook / Victorian traveler's sketchbook — NOT a polished 3D \
fantasy render, NOT a video-game cover, NOT thick opaque paint. Warm, \
inviting, hearth-lit.

COMPOSITION: A hearth-side storyteller vignette. In the FOREGROUND, silhouetted \
against a warm firelit hearth, the four heroes of the party sit or stand \
gathered close, seen from behind or in three-quarter view — they are the \
listeners around the fire, and their four silhouettes are the primary shape. \
Above and behind them, the composition opens into a stormy sky of a fantasy \
North: distant flying tower, a hint of giant silhouettes at the horizon, \
lightning webbing through cloud. A weathered wooden ship's wheel or the \
splintered ribs of a shipwreck may appear as a background/framing element on \
one side.

CHARACTERS: The four portrait references (Fiz, Hal, Toz, Eno) are provided so \
you can tell them apart. All four should appear in the foreground silhouettes, \
readable by outline: Hal tallest (bald, bearded, cloaked human); Fiz smallest \
and gnomish with spiky pale hair and goggles; Toz halfling with tricorn hat; \
Eno half-elf with hooded green cloak and staff. Read the identity anchors — \
Fiz is NOT a dwarf, Eno is NOT feminine.

TEXT: Include the title 'TALES OF THE TRUE HAND' rendered as prominent \
illuminated-manuscript display lettering across the top or the upper third of \
the square, in a gilt / burnished-gold Cinzel-like serif. It should be legible \
at thumbnail sizes. Do NOT include any other text, subtitle, byline, or \
tagline. NO episode numbers, NO dates. Only the show title."""
