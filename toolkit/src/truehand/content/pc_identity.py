"""The party's visual identity, as prompt text.

Single source of truth for how the four PCs are described to an image model.
This existed in four copies — PC_PORTRAITS in the session-image and podcast-
cover scripts, PC_ANCHORS in the character-reference script, and LEAN_CAST —
under a comment claiming they were "kept verbatim in sync". They were not:
MUSTACHE vs MOUSTACHE, and Fiz's beardless-face sentence and Eno's "rugged,
broad-shouldered" line existed in only one copy. The superset wins here.

PC_ANCHORS is the full description. LEAN_CAST is a deliberately shorter
gear-only variant for crowded scenes, not a drifted copy — keep both.
"""

#: Slugs in party order; also the order portraits are fed to the model.
PC_SLUGS = ("fiz", "hal", "toz", "eno")

PC_ANCHORS = {
    "fiz": (
        "Fiz — a ROCK GNOME (small, about 3.5 feet tall — definitely NOT a "
        "dwarf and NOT a halfling). Male, young-looking (young for a gnome). "
        "HAIR: WHITE / SILVER-GRAY, spiky and messy, standing up wildly. "
        "FACE: CLEAN-SHAVEN — a smooth, bare, beardless face; NO BEARD, NO "
        "STUBBLE, NO MOUSTACHE, NO sideburns, EVER. His cheeks, chin and jaw "
        "are smooth bare skin. Bright BLUE eyes, pale skin, a small "
        "mischievous grin. Large pointed gnomish ears. GEAR: brass steampunk "
        "tinker's goggles with dark lenses pushed up on his forehead; brass-"
        "fitted wand-arquebus (a stubby wand-sized cannon) in hand with a "
        "faint blue glow; a small floating drone-cannon accompanies him. "
        "Wears dark brown leather armor with brass plating, fingerless brass-"
        "studded gloves, and a utility belt with pouches and small colored "
        "potion vials. Overall look: an inventor, not a warrior. Steampunk "
        "brass-and-leather aesthetic."
    ),
    "hal": (
        "Hal — a Variant Human paladin (Oath of Vengeance). Male, mid-40s, "
        "tall and broad-shouldered. HAIR: COMPLETELY BALD on top, no hair. "
        "BEARD: a full, thick DARK BROWN beard, chin-length. Serious, grim "
        "expression, brown eyes. Weathered pale skin. GEAR: dull silver-grey "
        "plate armor with a visible breastplate; a deep crimson RED CLOAK "
        "fastened at the neck with a round metal clasp. Carries a sword and "
        "shield or a maul. Ex-Silver Marches militia bearing — steady and "
        "disciplined. He is the ONLY human in the party, the tallest of the "
        "four."
    ),
    "toz": (
        "Toz — a LIGHTFOOT HALFLING (small, about 3 feet tall, halfling "
        "proportions). Male, warm ruddy-tan skin, mid-60s (middle-aged for a "
        "halfling but doesn't look old). HAIR: TOUSLED CURLY DARK BROWN hair "
        "peeking out from under his hat. FACE: clean-shaven, wide cheerful "
        "GRIN, a slightly upturned nose. GEAR: wears a DARK BLUE NAVAL "
        "TRICORN HAT and a matching dark blue naval captain's coat with brass "
        "buttons; a RED NECKERCHIEF or bandana tied at his neck. Ship's "
        "captain of the wrecked True Hand. Casts wind and water magic — a "
        "swirling grey whirlwind and streams of blue water at his fingertips. "
        "Pirate-captain aesthetic."
    ),
    "eno": (
        "Eno — a HALF-ELF nature cleric of Eldath (goddess of still waters). "
        "MALE, mid-50s, wild-raised. Pointed elven ear-tips clearly visible. "
        "HAIR: medium-length wavy MEDIUM BROWN hair. FACE: LIGHT SHORT "
        "STUBBLE (not a full beard, not clean-shaven — just several days' "
        "growth). Blue-gray eyes, weathered tanned skin, quiet serious "
        "expression. NEVER draw him as feminine, delicate, or a woman — he is "
        "a rugged, broad-shouldered man. GEAR: dark green wool cloak with a "
        "small round metal clasp at the throat; simple green-and-brown "
        "druidic robes over leather beneath; wooden holy symbol shaped like a "
        "calm pond; wooden staff. Looks like someone who has spent decades "
        "outdoors — a broad-shouldered woodsman in monk's robes."
    ),
}


LEAN_CAST = {
    "fiz": (
        "Fiz — a small rock gnome artificer/artillerist (an inventor, not a "
        "warrior). Signature gear: brass tinker's goggles pushed up on his "
        "forehead; a brass wand-arquebus (a stubby wand-sized cannon) that "
        "glows faint blue; a small floating brass drone-cannon hovering near "
        "him; dark leather-and-brass armour and a potion-vial belt."
    ),
    "hal": (
        "Hal — a human paladin, the tallest of the four and the only human. "
        "Signature gear: dull silver-grey plate armour and a deep crimson RED "
        "CLOAK; fights with a sword and shield or a maul."
    ),
    "toz": (
        "Toz — a small halfling storm-sorcerer and ship's captain. Signature "
        "gear: a dark blue naval TRICORN HAT and matching blue captain's coat "
        "with a red neckerchief; conjures a swirling grey whirlwind and "
        "streams of blue water at his fingertips."
    ),
    "eno": (
        "Eno — a half-elf nature cleric. Signature gear: a dark green hooded "
        "cloak, a wooden staff, and a wooden holy symbol shaped like a calm "
        "pond."
    ),
}


CAST_ROLLCALL = (
    "CAST ROLL-CALL: the four player characters are Fiz, Hal, Toz, and Eno. "
    "This party travels together — assume ALL FOUR are present in the scene "
    "and MUST be depicted, each with their signature gear listed above, "
    "UNLESS the summary below clearly says one of them is absent. Never omit "
    "a party member; never invent an extra player character."
)


REFERENCE_USAGE = (
    "HOW TO USE THE CHARACTER REFERENCE IMAGES BELOW — read carefully. They "
    "exist ONLY to keep each character's IDENTITY consistent between "
    "illustrations: their face, hair, skin and colouring, costume, and gear, "
    "and their body proportions. They are NOT poses to reproduce. Do NOT copy "
    "any reference's pose, gesture, hand position, camera angle, cropping, or "
    "its plain empty background. RE-DRAW every character from scratch in a "
    "NEW pose and action that fits THIS scene and the specific moment "
    "described below — turned, leaning, crouching, fighting, reacting as the "
    "moment demands — fully sharing space and interacting with the other "
    "characters, the terrain, the props, and the lighting. Treat each "
    "reference like a turnaround sheet an illustrator glances at for likeness "
    "and then sets aside to draw a brand-new picture. A character whose pose "
    "matches its reference plate is WRONG."
)


MAX_REFS_PER_PC = 2
