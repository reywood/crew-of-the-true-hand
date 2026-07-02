# Battle Cards

Printable single-page combat reference cards for each PC. One self-contained HTML file per character (`fiz.html`, eventually `hal.html`, `toz.html`, `woz.html`). The player prints their card and brings it to sessions.

**Fiz's card is the working template.** Read `fiz.html` end-to-end before building another one — copy its structure verbatim, then swap in the new character's content and voice.

## Hard requirements

- **One self-contained `.html` file per character.** Inline CSS, inline SVG dice sprite. Zero external assets (no web fonts, no image files, no JS). The card must work when printed, emailed, or moved to a different folder.
- **Letter-size print, 0.4" margins.** `@page { size: letter; margin: 0.4in }` is the standing rule. If anyone has A4 needs, add a sibling `@page` rule, don't change the default.
- **System fonts only.** Cambria → Georgia → Times New Roman → serif. The card must render the same on a player's machine without an internet connection.

## Layout model (the part that took the longest to get right)

The card is a single column of full-width `<section>` blocks. Each section has:
1. A full-width `<h2>` banner with the section title (e.g. "Eldritch Cannon", "Cantrips", "1st-Level Spells").
2. A `<div class="section-grid">` immediately under the h2 that holds the action cards in a 2-column CSS multi-column flow.

```html
<section>
  <h2>1st-Level Spells <span class="meta">DC 15 …</span></h2>
  <div class="section-grid">
    <div class="action"> … </div>
    <div class="action"> … </div>
    …
  </div>
</section>
```

**Why this shape:** CSS multi-column is unreliable across page breaks (browsers will often leave one column empty on page 1). Confining the 2-column flow *inside* each section means the columns only need to balance within a single page, which all engines handle correctly. Sections themselves are simple block elements that the paginator handles well.

**Page-break rules** — already in the print stylesheet, don't remove:
- `section { break-inside: avoid; page-break-inside: avoid }` — sections stay together; if one can't fit on the current page, the whole section moves to the next.
- `.action { break-inside: avoid; page-break-inside: avoid }` — individual cards never split across pages or columns.
- `section h2 { break-after: avoid; page-break-after: avoid }` — a section heading can't be the last thing on a page.

If any single section is too tall to fit on one page (Fiz's 1st-Level Spells with 9 cards comes close), split it into two sections (e.g. "1st-Level Spells (A–F)" / "(G–Z)"). Don't try to allow mid-section breaks — that defeats the whole layout.

## Per-card components

### Header strip
```
HISFIZ "FIZ" SPINFIZZLER
Rock Gnome · Artillerist Artificer · Lv 7        [italic tagline, right-aligned]
```

### Stats strip (`<div class="stats">`)
Six cells: Init, AC, HP, Spell DC, Spell Atk, Prof. Use `<span class="value">+8</span>` for known numbers and `<span class="fillbox">&nbsp;&nbsp;</span>` for things that drift between sessions (AC, HP). Pen-in is fine.

If a character isn't a caster, swap Spell DC / Spell Atk for something more relevant (e.g. Channel Divinity uses for Hal; Sorcery Points for Toz; Wild Shape uses for druids if applicable).

### Action cards (`<div class="action">`)
Every action card has the same shape:
```html
<div class="action">
  <div class="action-head">
    <span class="action-name">Spell or Move Name</span>
    <span class="chip">Action</span>
    <!-- optional extra chips here -->
  </div>
  <div class="effect"><span class="label">Range / target / save</span></div>
  <div class="effect">Damage + dice + brief effect text.</div>
  <div class="flavor">One italic sentence: what observers see.</div>
</div>
```

### Chip types (action cost / qualifier)
| Class | Use | Color |
| --- | --- | --- |
| `chip` | Action | brass-brown |
| `chip-bonus` | Bonus Action | amber |
| `chip-reaction` | Reaction | red |
| `chip-none` | Passive, Free, No Action | slate |
| `chip-slow` | Long Rest, Ritual, charge cost, "1/LR", "2nd-level slot" | dark wood |

Stack chips when an ability has multiple modes (e.g. a Repulsion Shield is `[Passive +AC] [Reaction]`).

### Dice notation
Always wrap dice in this triple — count + bold dN label + icon — so the player can grab the right die at a glance:
```html
<span class="dice">
  <span class="count">2</span>
  <span class="die-label">d8</span>
  <svg class="die"><use href="#d8"/></svg>
</span>
```
The SVG sprite at the top of the file defines `#d4`, `#d6`, `#d8`, `#d10`, `#d12`, `#d20`. Don't re-render the sprite per file — copy it from Fiz's card.

Count can be plain ("2"), with a sign ("+1"), or omitted for solo dice (but cleaner to always include the count, even if it's "1").

### Flavor lines
Every action gets one italic sentence describing what other characters at the table see. Past tense or present tense both fine — pick one and stick with it on a card. Match the **character's voice** (see below).

## Section ordering

Lead with the character's **signature combat resource**, then group from most-used to least-used. Use Fiz as a model:

1. **Signature class feature** (Fiz: Eldritch Cannon) — biggest thing, lead with it.
2. **Cantrips** if caster.
3. **Spells by level** if caster.
4. **Weapons**.
5. **Class features** (passive / utility / non-combat).
6. **Magic items / infusions** (anything attuned that affects combat).
7. **Reactions** — pull all reactions into one section even if they appeared above. This is the "what can I do on someone else's turn" lookup.

If a character doesn't have one of these (no spells, no magic items, etc.), skip that section. If they have something Fiz doesn't (Hal's Channel Divinity, Toz's Metamagic, Woz's Wild Shape if multiclassed), add a section in the appropriate position.

## Character voices (for flavor lines)

- **Fiz** — Clockwork brass tinker from Halruaa. Imagery: hand-pumped reservoirs, brass shavings, gauges, copper wire, mortar-round whistles, mechanical *clicks*, *fwip* and *fzzt* sounds, hand-built apparatus that turns spell components into mechanical action.
- **Hal** — Variant Human Paladin, Oath of Vengeance, ex-Silver Marches militia. Imagery: shield-and-sword soldier discipline, weight of plate, a battered playing-card deck, an old officer's voice in his head, oaths spoken aloud, light from a holy symbol, the heft of a maul.
- **Toz** — Lightfoot Halfling Storm Sorcerer, captain of the wrecked *True Hand*. Imagery: salt spray, sea-wind, cracks of static, distant thunder, lightning at the fingertips, the smell of ozone, a rope-coiled grip, half-sung sailor's chants. Toz has been having dreams of a malevolent ocean presence — that thread can color any spell about water.
- **Woz** — Half-Elf Nature Cleric of Eldath, raised in the wild, adopted Greenbottle. Imagery: stillness, water that's never disturbed, leaf shadows, animal scents, bark and moss, the way old druids speak slowly, prayers murmured in elven, a quiet presence that animals trust.

For ranged-attack spells (Fire Bolt, Eldritch Blast, etc.), the flavor should describe the *delivery* — what the projectile looks like, how it leaves the caster. For area saves (Thunderwave, Shatter), describe the wave or pulse. For buffs (Bless, Bardic Inspiration), describe the small physical sign that something has happened.

## Recipe for a new character card

1. **Get the character data.** Read `characters/<name>.md` — race, class, level, feats, features, infusions, prepared spell list. Cross-reference the DnD Beyond link if present for things the markdown doesn't capture.
2. **Copy `fiz.html` to `<name>.html`.** Don't start from scratch.
3. **Update the `<head>` title and the header strip.** Name, race/class/level, tagline.
4. **Recompute the stats strip.** Values you know from the sheet go in `<span class="value">`; values that drift go in `<span class="fillbox">`. For non-casters, swap Spell DC / Spell Atk for something more relevant.
5. **Replace the sections.** Keep the same section structure, but:
   - Drop sections that don't apply (a non-caster has no Spells; a character with no infusions has no Infusions section).
   - Add sections the character needs that Fiz didn't have (Channel Divinity, Metamagic, Wild Shape, etc.).
   - For each section, write one `<div class="action">` per ability the character can take.
6. **Match dice notation exactly** (count + icon + dN label, inside `<span class="dice">`). Use the existing SVG sprite — don't redefine it.
7. **Write flavor lines in the character's voice.** One italic sentence per action, describing what observers see. See voices above.
8. **Pull all reactions into the final Reactions section.** Even if they appeared earlier, repeat them in Reactions so the player can scan a single place during another player's turn.
9. **Open in a browser and hit Cmd-P to preview the print output.** Verify:
   - Both columns of action cards appear under each section's h2.
   - No section is split across pages.
   - All dice icons + dN labels render.
   - Color chips become black-outlined pills on print (not solid color blocks).

## Adding more dice or chip types

The dice sprite at the top of the file has d4 / d6 / d8 / d10 / d12 / d20 only. If a character ever needs d100 (e.g. wild magic surge), add a new `<symbol>` to the sprite using the same shape grammar. The shapes are intentionally simple geometric silhouettes with the number inside.

For new chip types (e.g. a "Ki Point" cost for a monk multiclass), add a new `--chip-...` CSS variable and a `.chip-...` rule alongside the existing ones. Keep the print stylesheet generic — `.chip` defaults already collapse all chips to black-outline pills on print.
