# Session 2026-08-12 — Distilled Fact-by-Fact Account

## Source & method

Reconstructed from two raw sources only: `sessions/2026-08-12/transcript.txt` (whisply diarized output, 1,501 lines, `[00:00:04]`–`[02:27:14]`) and `sessions/2026-08-12/player notes/fiz.md` (the player's own bullet notes, Fiz's POV — an independent record, not transcript-derived). No `summary.md`, no prior distillation, and no website artifact was consulted. `npcs/`, `locations/`, and `items/` were read for canonical proper-noun spellings only.

**Two structural caveats that shape everything below.**

1. **The recording ends before the session does.** `transcript.txt` stops mid-sentence at `[02:27:14]` during a joke about the immovable rod. Everything from the night visit to Kuyrl Stonepalm's shack onward — including the entire fog ambush combat — is **absent from the audio** and survives only in Fiz's player notes. Those beats are marked **[NOTES-ONLY]** below. Attribution there rests on Fiz's own written account cross-checked against class mechanics, which agree cleanly; it is *more* reliable than the transcript-derived combat attributions in a normal session, not less, but it carries no timestamps.

2. **The diarization on this recording is unusually degraded, worse than the K=8 over-split alone would predict.** The table is five people (4 PCs + DM) on one shared mic, and whisply's segmentation repeatedly runs a single tagged line *through* two, three, or four speaker changes — e.g. line 724 is tagged `SPEAKER_05` but contains the DM's narration, Hal's reply, the DM again, and table cross-talk in one unbroken string. The speaker tag is therefore only reliable for the **first few words** of a line, and often not even then. Consequently attribution in this file is driven by **content and class mechanics first, tags a distant second**: Flash of Genius / tinker's tools / *identify* / *scorching ray* → Fiz; *guidance* / *locate object* / *zone of truth* / insight +7 → Eno; Halfling-language dialogue / the Valkur book / the ocean dream → Toz; the cursed crypt sword and its elf-prejudice → Hal. Where a claim rests on a tag rather than a mechanic, it is flagged in `transcript-distilled.factcheck.md`.

## Session overview

A talking session, bookended by violence. It opens in the immediate aftermath of the Deep Water Inn brawl: the crew examines the man who was the source of the mind-control, finds an eye-stamped, permanently corroded coin on his body, and spends the morning chasing what it means. A possessed guard tries to detain them and is talked down. At the Plinth in the Sea Ward, a gray-tent priestess of Kelemvor names Hal's curse — *grave goods* — and gives two exact ways to break it, while a priestess of Umberlee identifies the coin's eye as her goddess's old symbol and blames the tavern incident on a warlock. Fiz casts *identify* on the coin, learns it carries the spell **Eternal Corrosion**, and walks away knowing the spell himself. In parallel the crew works the Kuyrl Stonepalm thread: Brindle Stormtide laughs off any notion of the goliath repaying his debt, Fiz audits Kuyrl's ledger and proves the debt grows by 80 gold a year, and Kuyrl smashes a barrel in rage before being talked into playing along until nightfall. A late visit to Chazlauth cracks the Draconic notes — a full mission brief to the half-dragon from a Cult of the Dragon master — and trades the blue-steel thieves' tools for an immovable rod. Then, off-recording: a night fog rolls over the docks and something barnacled and robed tries to kill them.

## Speaker → character key (many-to-one; K=8 over-split)

| Cluster | Character | Lines | Confidence | Key evidence |
|---|---|---|---|---|
| `SPEAKER_05` | **DM (primary) + Fiz (merged)** | 577 | Medium | Dominant narration cluster: `[00:02:07]` "so this guy has a clothes of just an ordinary dockhand… he's a human man"; `[01:03:42]` "alright we'll go to the plinth"; `[02:17:29]` the whole Cult of the Dragon exposition. But Fiz's first-person lines land here too — `[00:20:30]` "i have tinker's tools i mean i my guild artisan"; `[01:56:38]` "I'm good with jeweler's tools, thieves' tools, tinker's tools, and woodcarver's tools"; `[02:16:53]` "We got these tools with these draconic numerals on them… we took off this fool that we smoked." Fiz has **no clean home cluster**; he is absorbed here and into `02`/`04`/`01`. |
| `SPEAKER_07` | **DM, NPC voice register** | 87 | High | `[00:41:23]` Kuyrl: "hello friends good to see you again" / "kurl stone palm"; `[00:44:02]` Brindle: "get the thing and carry it on… what am I paying you for?"; `[01:07:57]` the gray priestess: "There is a woman in the center, kneeling in prayer… It's a place of gray"; `[01:11:27]` the curse terms; `[01:19:00]` the Umberlee priestess. The DM shifts voice for NPCs and diarization splits it off. |
| `SPEAKER_03` | **DM, NPC voice register (second bucket)** | 22 | Medium | `[00:23:06]` barkeep: "oh yeah I'll see to his wife Thora"; `[00:31:08]` grumpy patron: "why are you bothering me again… scam me with your dirty old coins"; `[00:44:36]` Kuyrl on his pilgrimage; `[02:00:08]` "The place of the oracle is a place only for giants"; `[02:10:39]` the ledger verdict. |
| `SPEAKER_06` | **Toz (Tozlo Greenbottle)** | 228 | **High** | `[00:28:30]` "they could have accepted the offer, I didn't, I resisted at the last minute… I choose not to tell any of my fellow party members this information" — the ocean dream, Toz's secret; `[00:46:09]` "I say how's the sea looking captain — and Halfling — to Brindle"; `[01:44:14]` the halfling-to-halfling approach; `[00:29:30]` "I read my book about Balcor [Valkur]"; `[01:33:50]` "I'll ask her one more question — the coin on the corroded side, what does it say?" |
| `SPEAKER_01` | **Eno (Enoril Wazek) + heavy Fiz bleed** | 249 | Medium-High for Eno | Eno: `[00:26:45]` "I got perception, I got medicine, insight… " → DM "your medicine is plus seven"; `[00:32:58]` "when I asked about if I should cast zone of truth"; `[01:33:15]` DM "you as a cleric can choose your spells every long rest"; `[01:34:16]` "I have locate object"; `[02:04:32]` the *guidance* readout. **Bleed:** `[02:05:08]` "I also have Flash of Genius" and `[01:41:39]` "I can only cast the spell once…" are **Fiz**, not Eno. |
| `SPEAKER_02` | **Overflow: Hal + Fiz + DM asides** | 171 | Low | Hal: `[00:14:38]` "this sword is called Fey Killer, so that's why I'm being a little bit…" Fiz: `[01:38:23]` "Yeah, so I'll identify this." DM: `[01:10:46]` "But kneel down, son"; `[01:12:15]` "How about you roll an intelligence check." Not usable as an identity signal on its own. |
| `SPEAKER_04` | **Bleed cluster (DM adjudication + table cross-talk)** | 98 | Low | `[00:14:53]` "you can do [it] with disadvantage though, because of your welling anger"; `[00:27:32]` "basically describing the same dream that you've been having"; `[00:32:13]` "you're going to make either a deception or a performance check". Mostly DM fragments caught mid-turn. |
| `SPEAKER_00` | **Hal-leaning bleed** | 69 | Low-Medium | `[00:13:47]` "I'm forced to carry this cursed sword"; `[00:24:41]` "can't get rid of it"; `[01:50:19]` "I wanted to tell him that the Goliath knows that he's being… swindled." Also catches DM fragments (`[00:24:53]`, `[01:38:04]`). |

**Player-cluster totals (best estimate):**

- **DM** — `05` (majority of), `07`, `03`, plus fragments in `04` and `02`. Roughly 55–60% of all lines; this was a heavily narrated, NPC-dense session.
- **Toz** — `06` (~228 lines). The one clean PC cluster.
- **Eno** — `01` (majority of, ~200 of 249).
- **Hal** — `00` + part of `02` (~120–150 lines). Hal's player is the least talkative at the table this session and has no dedicated cluster.
- **Fiz** — **no dedicated cluster.** Distributed through `05`, `02`, `01`, and `04`. Fiz is highly active in-fiction (he audits the ledger, casts *identify*, argues down the guard, does the talking at Chazlauth's) but diarization never isolated him. **This is the single biggest attribution risk in the file** and the reason so much of it leans on Fiz's own player notes.

## Name reconciliation key (garbled audio → canonical)

- "emmett doro", "Emmert Doro" → **Emmert Dorrow** (Fiz's notes spelling; the dead dock worker)
- "his wife Thora" → **Thora Dorrow** (Emmert's widow; surname inferred)
- "kurl", "curl", "Carl", "K-U-Y-R-L… kurl kurl", "cor the goliath of Cormyr" → **Kuyrl Stonepalm**, goliath of **Cormeer**
- "Brindle", "Brendol", "Brendel", "Brendan", "grendel" → **Brindle Stormtide**
- "Larry", "Doug", "Larry Doug" → **Larry**, Brindle's human translator/minder (silver ponytail, eye patch). The name is table-improvised but the DM adopted it in play (`[01:47:59]` "Isn't that right, Larry?" / "Yes, sir.")
- "Chaz", "Chad", "Chaz Osloff", "Chaslauth" → **Chazlauth**
- "Umberley", "Underly", "Unbelie", "Umber Bible", "the sea bitch" → **Umberlee** (a.k.a. the Bitch Queen, Queen of the Depths)
- "Kalimbor" → **Kelemvor** (god of the dead; the gray tent)
- "Balcor", "Valkyr", "book of Verun", "the alcar" → **Valkur** (god of sailors; Toz's holy book)
- "Clough", "Klough", spelled out on air as "K-L-A-U-T-H" → **Klauth**, ancient red dragon, the "Old Wyrm of the North"
- "Zulkin" → **Xolkin**; "Morath" → **Morak/Morath**, the Nightstone merchant (low confidence on the latter)
- "Yacurdy", "Yackerty" → **Yackerty** (dwarf Harper, Trades Ward)
- "Silvery Moon", "Silver Moon", "Silvermoon" → **Silverymoon**
- "Harshnag", "Harshnag's" → **Harshnag** (frost giant)
- "Zephan…", "Zephyros" → **Zephyros** (cloud giant)
- "the c ward" / "sea ward" → **Sea Ward** (per Fiz's notes; the Plinth's location)
- "Nandar", "N-A-A-N-D-A-R", "Lady Nandar" → **Lady Nandar** / the **Nandar** family
- "grave goods" → the curse type, verbatim from the priestess
- "Eternally Dirty Corrosion" → **Eternal Corrosion** (the spell on the coin)
- "Fey Killer" → Hal's name for the **cursed crypt sword** (see Loose ends — this may be a new in-fiction name or a mis-hearing)

---

## Scene 1 — Aftermath in the Deep Water Inn `[00:00:04]`–`[00:12:00]`

- The session resumes **immediately** where the last one ended, still inside the tavern, bodies not yet cold.
- The party confirmed the kill: the man who was the source of the mind-control took **a crossbow bolt** as the last shot of the fight. `[00:00:12]` "the last shot was a crossbow bolt to the leader"; `[00:01:07]` "we used a crossbow to kill them." The DM ruled it lethal because it was a ranged attack and no one had declared non-lethal intent. **Light crossbow → Toz** (class fingerprint; the transcript does not name the shooter).
- The moment he died, every white-eyed townsperson's eyes cleared. He is the **only** casualty; everyone else is on their feet, shaken.
- **DM description of the body:** a human man, a bit gray, some stubble, worn dockhand clothes — "he doesn't look like a criminal mastermind."
- A patron identifies him: **Emmert Dorrow**, a dockhand.
- **The seawater.** A large pool of water has spread out from beneath the body. Asked whether it came from his mouth or a wound, the DM: `[00:04:47]` "no, it doesn't… it just sort of washed out and then settled." Distinct from the blood. Nobody touches it; one PC gives it a sniff (no result stated).
- Two of the **guards** who had been possessed are also waking up and shaking their heads.
- The formerly-possessed describe it identically: they remember nothing, only the sound of ocean waves, a deep rumbling, and then everything going **dark** (`[00:24:41]` explicitly corrected from "white" to "dark").
- The waitress **Eno healed** last session is clutching his shirt: "I don't know what happened there. I watched myself pick up the knife and then everything just went white." She pleads with him to promise it won't happen again; he tells her the vile feeling is gone, it died with that man.
- **Fiz re-runs *detect magic*** as a 10-minute ritual (the same spell that fingered Emmert as the source during the fight). Result: **no trace of magic** anywhere. `[00:09:04]` "no trace of magic." *(Ritual detect magic + "like I did before" → Fiz; Eno also has the spell, so this is flagged in the factcheck.)*
- **Eno** is prompted for a religion check, protests he has no religion bonus, rolls **2 − 1 = 1**. Nothing.
- **Toz** pulls out his **holy book of Valkur** (given to him by the priest at the Wave Hall) and searches it for stories of possession. Intelligence check with religion proficiency: **14**. He finds a section on **sea beasts and demigods** — the things Valkur contends with in other realms — including **Umberlee, "the sea bitch."** Several named monsters, none identified without further study. The DM explicitly leaves the door open to learn more with more study time.
- Outside, the morning is ordinary: a man with a barrow of fish, a wealthy-looking child with a red balloon, the sea calm. It is **just after morning**.
- **Toz retries the book for another hour** later in the scene: religion **10**, nothing further.

## Scene 2 — The elf guard, and being talked out of custody `[00:12:00]`–`[00:18:30]`

- A guard puts a hand on **Hal's** shoulder: "excuse me sir, you have a kind and honest face, can you tell me what just went down in your own words?"
- The DM plays the curse: as Hal looks at him he feels a shiver and anger welling — long pointed ears, symmetrical features. **The guard is an elf.** Hal cannot roll to resist; the curse simply applies.
- Hal is openly rude, then tries to explain: `[00:13:47]` "I'm forced to carry this cursed sword and it makes me prejudiced." Confirmed with the DM that nothing in the curse prevents him from *talking about* the curse. `[00:14:38]` "this sword is called **Fey Killer**, so that's why I'm being a little bit…" — **fact-checked: *Fey Killer* is genuinely the sword's name**, not an in-the-moment invention.
- **Curse mechanics restated by the DM** (`[01:09:20]`, referenced here): the sword is not physically glued to Hal — at the moment he would choose to be rid of it, he chooses not to. "It's like Frodo." **Alex the player cannot override Hal the character's decision.** Hal consciously does not want the sword.
- **Hal rolls Persuasion at disadvantage** (the welling anger): **4 + 5 = 9**. Failure. The DM: "it feels like you're just looking for excuses to be rude to people." Hal offers to switch to Intimidation — same +5 bonus — no improvement.
- Table clarification, in-fiction relevant: **elves are a subgroup of fey**, which is why the "fey killer" curse fires on this guard.
- The guard hardens: `[00:15:55]` "I'm gonna need you all to stay here for a little while. Don't any of you go anywhere." Pressed on where *he* is going: **"I'm getting my captain and more guards."**
- **Fiz turns it around.** He establishes that this guard is one of the ones whose eyes went white, then says to him in front of the room: "sir, **you** did attack us. Can anyone here corroborate that story?" — and asks the patrons who were *not* taken over, and who therefore have clear memories, to speak up.
- **Persuasion vs a DM-set DC.** *(**Fact-checked:** the **13 was a DC the DM set** for convincing the patrons to corroborate — *not* a contested roll by the guard.)* **Fiz rolled 21** and cleared it.
- **Three patrons step forward.** One says directly: "I saw you trying to attack those folks."
- The guard and his partner **hurry out of the tavern** — "we've got guard business" — rather than pressing the matter. (**Fact-checked: the transcript is right** — the two guards hurried out of the tavern after several patrons vouched that the guards had attacked the party. The party was not ordered to leave.)

## Scene 3 — Searching the body; the eye-coin `[00:18:30]`–`[00:24:30]`

- With the barkeep's blessing ("go ahead… get the hell out of here" — he wants the body gone), the crew searches Emmert Dorrow.
- **Found:** his ordinary effects, a **purse with a little money**, and — in a **separate pocket, wrapped in a folded piece of leather / a small leather pouch** — **a coin**.
- **The coin.** One face bears an **eye** — "like an eyeball." The other face is **so corroded as to be indecipherable**: there is writing or a marking there, but it is unreadable, buried under white-and-green **calcification**.
- **Fiz tries to clean it.** Intelligence check with **tinker's tools proficiency, +7 total**. The DM rules this narrowly outside his fields ("a weird gap") — he even pulls out his kit and tries a few things, and only risks **damaging it further**. It does not clean at all. The DM allows that *somebody* might be able to clean it, just not Fiz with what he has.
- **Group Religion check on the eye symbol** — everyone who studies it. Rolls: **11, 6, 9, 4, 10.** No one recognizes it. Not a religious symbol any of them knows.
- **The purse goes to the barkeep** to be returned to Emmert's family. The barkeep: "oh yeah, I'll see to his wife **Thora**."
- **Who the coin affects — the key experiment sequence:**
  1. **Fiz shows the coin to the barkeep** and asks if he's seen anything like it. The barkeep **takes it and zones out**, going blank for a moment. **Fiz snatches it back out of his hand.** The barkeep: "sorry — what?" No memory of it. *The barkeep had been one of the white-eyed.*
  2. **Fiz is holding the coin the entire time and is unaffected.** `[00:24:13]` "you feel alright?" / "I feel fine."
  3. **Fiz then shows it to a patron who was NOT taken over.** No effect at all — the man is merely annoyed: "why are you bothering me… don't scam me with your dirty old coins."
  4. **Conclusion the party reaches (and Fiz records):** the coin only affects people who went white-eyed.
- Fiz puts the coin back in its leather pouch, declares nobody should be touching it, and stows it in the party **Bag of Holding**.

## Scene 4 — Toz takes the coin; Eno catches him `[00:24:30]`–`[00:33:30]`

- The party canvasses the formerly-possessed. All tell the same story: a compulsion came over them, then darkness.
- **Ol' Rourke** was in the tavern and was **not** affected. The party takes him aside; he offers only generalities ("I've seen many a thing").
- **The DM runs a group skill challenge**: each PC contributes a *different* skill to investigating the tavern; the number of successes (DC 15) determines how much they learn. Skills chosen: **Persuasion** (Toz), **Arcana**, **Persuasion**, **Intimidation**, **Insight**. Rolls: **19, 6/7, 14, 6, 10.** → **one success**, the Persuasion.
- **What that one success bought (Toz's information, and Toz's alone):** every single person who was taken over has recently had **the same dream** — being **called to the ocean** by some kind of creature, a "pied piper from the sea."
- The DM confirms out loud: this is **the same dream Toz has been having**. And: *only* the people who were taken over have had it — Toz has had it and was *not* taken over.
- **Toz explicitly and deliberately withholds this from the party.** `[00:28:30]` "they could have accepted the offer, I didn't, I resisted at the last minute, thinking to myself, I'm not telling these guys any of this stuff… I'm the one who did the persuading and found this out from the townfolk, and so I have not told… I choose not to tell any of my fellow party members this information." The DM ratifies it: "so you guys don't know that they've all had this dream."
- Separately, the room recalls what the ringleader's woman said before the attack: **"you should have taken their offer."** Toz *does* relay that fragment to the party. A second remembered line — "we're going to take back what's ours" / "we will get back what's ours" — is disputed at the table `[01:28:03]` and left unresolved.
- **The coin is handed around.** When it reaches **Toz**, the DM has him roll **Deception (or Performance): 16**, i.e. a poker-face check to hide his reaction.
- **Insight bonuses compared: +7, +4, −1.** **Eno's +7 beats the 16.** The DM: "you notice he is affected by the coin" — a very subtle twitch, the kind of thing only Eno's hunter's stillness would catch.
- **Net result:** Toz *is* affected by the coin (like the white-eyed). **Eno alone knows Toz is hiding something.** Nobody else does. Eno chooses to sit on it — `[00:33:28]` "I'm enjoying the metagamer crew and I'm just going to sit on that for a while."
- **The barkeep's lead:** asked who in town could identify the coin, he says **Brindle** — "well-connected fellow, might be able to point you in the right direction."

## Scene 5 — The tip about the Plinth `[00:35:50]`–`[00:39:20]`

- A **human** patron — one of the three who stood up to the guards — tugs Hal's sleeve. He **overheard** the curse talk.
- His story: **his sister** had a ring like that, which "made her real mean" and which she couldn't take off. She took it to **the Plinth**.
- Details he gives: the Plinth is a **temple in Waterdeep**, in the **Sea Ward, near the marketplace**. It's "the one with all the shrines." **Look for the gray shrine / gray tent in the back** — there's a **death priest** there. He helped her.
- On price: "he asked her a lot of questions about where she got it," and it took a while. No fixed fee quoted.
- The party locates the Sea Ward on the map — just south of where they are.
- **Planning.** Three open errands: (a) the sword curse at the Plinth, (b) Brindle about the coin and a ship, (c) revisit **Chazlauth** about the dragon loot they forgot to show him last time. Fiz names the forgotten items explicitly: `[00:34:32]` "we have a **blue dragon sigil ring** we took off of them, we have some **blue steel thieves' tools** etched with **draconic numerals**, and we have some **draconic notes** that are all in Draconic."
- The party debates splitting up and **decides to stay together**.

## Scene 6 — The docks: Kuyrl Stonepalm, and Brindle brushes them off `[00:41:23]`–`[00:56:00]`

- On the docks they find **Kuyrl Stonepalm**, the goliath from the city gate — hauling **two hulking barrels** at once with ease, setting them down heavily. He greets them **in Giant**: "hello friends, good to see you again." (He speaks **no Common**; one PC understands and translates for the rest.)
- Name confirmed on air: **Kuyrl Stonepalm**, spelled out K-U-Y-R-L.
- He is happy in his work: "yes, have job, going to save money for my **pilgrimage**."
- **Fiz shows him the coin** — offering it to be touched — no reaction. Kuyrl reads it as money. `[00:44:29]` "that's my coin?" / "not that coin, but a coin" / "this is gonna help me on my journey."
- Kuyrl **points them to Brindle**: a halfling standing on a stack of boxes, barking orders at dock workers loading a ship. `[00:44:02]` "you over there, get the thing and carry it on, we gotta get this shipment out, we're running behind — what am I paying you for?"
- **Toz hails Brindle in Halfling.** Brindle answers in Halfling: "halfling friend, can't you see I'm busy? I'm doing a lot of work here." The crew offers to help move barrels for information; Brindle refuses — explaining anything to them would cost him more time than it saves — and tells them to **come back in an hour, at the tavern they just came from**. A Persuasion attempt (**9**) fails to speed him up. "Faster, please, get out of the way."
- **The ledger drops.** Walking away, the crew sees a **small booklet** fall out of a **rip in Kuyrl's back pocket** onto the dock. He doesn't notice.
- **A PC tries to pocket it secretly: Sleight of Hand, 3 + 3 = 6.** Failure. Kuyrl turns around: "oh, thank you friend, I appear to have dropped this." The PC hands it back openly. *(Fiz's notes compress this to "He picks it up," i.e. Kuyrl recovers it — consistent outcome.)*
- **What the booklet is:** "it's my **ledger** — I write my earnings, my wages, my costs." It **also contains a map**.
- **Kuyrl's story, drawn out over the conversation:**
  - He is going **north, to the Spine of the World, to see the great Oracle.**
  - "The Oracle can grant any wisdom one desires. Can answer any question."
  - His own question is **"deeply personal"** — he will not share it, friend or not.
  - He is **in debt to Brindle**, though he doesn't frame it that way — he thinks of it as working and "I'll get it back eventually."
  - He is **not** sailing with Brindle's ship; Brindle is a **merchant, not a captain**, and stays put. Kuyrl stays and works the docks.
  - He has a **wife and a son** in the city and will not leave them exposed to his debt.
  - **He has a map to the Oracle.** He tells the crew **where he lives** and invites them to come talk after work.
  - Later, when pressed, he adds the critical condition: **"The place of the Oracle is a place only for giants. A giant is needed to open the way."** Told a goliath is not a giant, he insists: **"I am giant kin. I am a giant. I can open the way."**
- **The debt is 80 gold.** The party argues at length about simply paying it (they estimate they have thousands; the table converts 1 gp ≈ $100, so 80 gp ≈ "$8,000" — a fortune to Kuyrl, pocket change to them). Options floated: pay it, offer Brindle 50 gp to settle it, **buy the debt** and hold Kuyrl to it themselves, steal the map, copy the map, or smuggle Kuyrl and his family out. No decision yet.
- **The competing route to the Oracle is restated:** **Vandal Lovelace** pointed them at **Yackerty**, a dwarf Harper in the **Trades Ward**, who may get them into the **Harpers' portal network** to **Silverymoon**, where they hope to find **Harshnag** the frost giant, who knows where the Oracle is. Silverymoon is not itself near the Spine of the World — hence the value of Kuyrl's map either way.

## Scene 7 — The Plinth: the gray tent and the *grave goods* curse `[01:03:42]`–`[01:15:45]`

- **The Plinth** is described as an offshoot of the market: **rows and rows of tents**, each devoted to a particular religion — the gods who have no permanent stone temple in Waterdeep. Ceremonies and rituals in progress everywhere; each tent holds an idol of a different god. (Colour: a man floating upside down with small cuts over his eyebrows dripping blood.)
- **The gray tent, at the back.** Everything in it is gray: gray tent, gray rug, gray robes, gray hair. A woman kneels in prayer at the center and, without looking up, says **"someone approaches."**
- She asks: **"You have come to worship Kelemvor, have you?"** Hal says no — he was told his cursed sword could be removed here. Her answer: **"Sometimes. Maybe. Depending on the curse."**
- **The offering.** Before doing anything she **holds out a cup and rattles it**. **Hal drops in a gold coin** *(**fact-checked and confirmed**; the DM later confirms `[01:15:46]` "that was a donation, that was not an exchange of services")*. She plucks it out and pockets it.
- She has Hal **kneel**, takes out her rocks and implements, and casts a small spell — **gray smoke shifting over her hands**.
- **Her reading, verbatim in substance:** "This is no ordinary curse. This is what we call **grave goods**. You stole this from a tomb. **This does not belong to you.**"
- **The two ways to undo it — the exact stated terms:**
  1. **Return the sword to where you found it.**
  2. **Find a proper owner** — "someone in the **lineage** of the one who owned the sword" — and **get their permission to own the sword.** Then the curse is undone.
- Asked who the owner was: **Hal rolls an Intelligence check and gets a natural 1, −1 = 0.** He cannot remember. **Fiz supplies it instead** (**fact-checked and confirmed**)**:** they took the sword from a **crypt / sarcophagus beneath Nightstone**.
- **The DM then fills in what they know:** the sword belonged to the **Nandar** family — **Lady Nandar**, the last of them, was **killed by the giants** in the Nightstone raid ("smooshed"). As far as the party knows, **there were no Nandar descendants living in Nightstone.**
- **The precise requirement, restated by the priestess:** it must be **whoever rightfully owns the sword** — whoever would have **inherited the Nandar estate**, or a **blood relative / descendant**.
- **Nightstone status check** (asked at the table, answered by the DM as established fact): Nightstone is **no longer occupied**. The illusionist — the noble from Waterdeep — was **killed by the party**. **Xolkin** took over the remaining gang and **left**. The merchant (Morak/Morath) is the one who gave them an item.
- The party decides a three-day round trip back to Nightstone isn't happening now. **The curse stands.** Hal is stuck with the sword.

## Scene 8 — The Plinth: Umberlee, the bracelet, and *identify* `[01:15:45]`–`[01:42:35]`

- **The search.** The party spends about an hour walking the Plinth looking for the eye symbol. **Investigation check: 20** (other rolls 17 and 2).
- **What they find is deliberately not what they expected.** The DM: it was hard to find *because it is not one of the gods' displayed symbols*. Instead they spot a **priestess at one of the shrines wearing it by chance as a bracelet** — **the same coin, eye on one face, and it has begun to corrode.** *(Fiz's notes describe this as finding "a tent with a banner similar to the eye"; the transcript is explicit that it was a bracelet on a person, not a banner. **Fact-checked: the transcript is right** — the crew spotted a priestess wearing the coin as a bracelet purely by chance.)*
- **The shrine is Umberlee's.** The priestess: a **short human woman, long gray wavy hair, robes covering her feet.**
- The party approaches without revealing their coin at first. Her opening: "Have you come to get protection from the dangers of the ocean from the powerful god Umberlee?"
- **Toz challenges her theology:** "You don't worship Umberlee yourself?" — "I do. I am one of her priestesses." — "Why would you need protection from your own god?"
  - Her answer: "There are many dangers out there in the ocean. Even the wind and sea itself are treacherous… Umberlee is ferocious. Umberlee is fierce. Umberlee brings terror into the hearts of her enemies. But Umberlee **does** protect. Umberlee does love and watch over all of her children on the vast ocean and beyond." And a sales point: you can be an **inland landlubber** and still worship Umberlee and get all the protection.
- **The offering cup** comes out again. The party puts in **a few copper**, then **one gold** (grumbling about flashing money around town and making themselves targets).
- **The bracelet, explained — the coin's meaning:**
  - "This is an **old symbol**. This is a way that **Umberlee manifests herself for protection**."
  - **The duality:** "You see the coin — it's clean, it shines, but it also is a bit corroded, and **these two things are at war with each other**. It's a cycle. It's **life and death**."
  - **Its life-cycle:** a coin starts **shiny and new and corrodes over time**. "If you find one like this and you give your heart to Umberlee, you will see the same thing in your life. You will find life often corrodes you, it brings you misfortune — but there's the other side of things: it **washes them away, cleans them**."
  - **The corroded face bears a number. Each coin is unique.** She can read hers; the party's is illegible under the calcification.
- **The blessing.** She blesses the whole party ("you're all blessed") and urges them to say their own prayers. She offers an **Umberlee scripture, hand-transcribed, for 20 silver / 2 gold**. **No takers.**
- **Toz tells her bluntly he follows a different god** (Valkur). Her reply is antagonistic and quietly important: "**Valkur won't always be there** — especially when he is crushed by the sea. **Umberlee will eventually defeat him.**" Asked why she hasn't yet: "there are mitigating factors, of course, well beyond my knowledge. **Those beings are at war, and no war lasts forever.**"
- **Umberlee's standing in Waterdeep** (DM, via Toz's sailor knowledge): **not very popular** — even among the seedier folk, because she is essentially an **evil god**. Sailors will keep Umberlee symbols on their ships as **superstitious protection**. Valkur is more popular, though his temple here is a **wooden shack**, not stone.
- **The party tells her the whole tavern story** — the white eyes, the dead man's name, the coin found on him, and that when they handed the coin to one of the affected people afterward it **still had power over them**, even though those people plainly knew nothing about the coin and were not followers.
- **Her verdict:**
  - "It's **connected to Umberlee**, but this **isn't usual**. This is **strange**." Pressed: **the events are strange, not the coin.**
  - **"I think this is the work of a warlock. Somebody who has tapped into the power of Umberlee and is using it to their own means."**
  - Alternative she floats: "or it's some… I don't know, maybe an **imposter god**."
  - **"Is the coin cursed?" — "No. No. The coin is displaying the corruption** — the corruption of the sea, the ocean. Nothing man-made can withstand the waves."
  - On whether Umberlee would sanction such use: **"that all depends on the nature of the contract."**
  - She knows **no warlocks personally** — "warlocks tend to operate in secret, they're not supposed to reveal their patrons unless that's part of their contract."
  - **To track the caster: find a divination wizard or cleric.**
- **Eno tries to recall relevant divination lore: 7 − 1 = 6.** Failure. The DM then explicitly permits player meta-knowledge: as a cleric Eno **re-picks spells every long rest**, so he can look for a spell that fits. **Eno has *locate object* prepared** (2nd level) and considers using it to find *another* such coin nearby (1,000 ft range).
- **Fiz casts *identify* on the coin** — 1st level, cast as a **10-minute ritual**, touching the coin throughout.
- **The identify readout, in full:**
  - It **is** a magic-imbued object. Therefore it counts as a magic item.
  - **Properties:** it is **continually corroded**, and **cleaning the corrosion will result in the corrosion returning magically.**
  - **Does not require attunement. No charges.**
  - **It was not created by a spell** (i.e. no *fabricate*-style origin).
  - **Spells currently affecting it: one — "Eternal Corrosion."**
- **The bonus.** Because *identify* tells you a magic item's properties **and how to use them**, the DM rules that Fiz **learns the spell Eternal Corrosion**, as **a cantrip**. Terms as stated:
  - Target: **an object you touch that can fit in the palm of your hand.**
  - Effect: **it corrodes, eternally** — cleaning it is futile, the corrosion returns.
  - **Objects only — not creatures.** Explicitly not usable on something ship-sized.
  - The DM's own commentary, worth preserving: `[01:41:03]` "I should have made you roll for that. I'm just throwing you a bonus, because it sounded cool at the moment — but now I'm regretting [it]." Table floated homebrew guardrails (one use ever; forgetting on cast; needing successful practice runs) — **none were adopted.**
  - **Fact-checked:** the DM stated this is a **homebrewed spell whose full details are yet to be determined.** As it stands it is a **cantrip, castable on any object Fiz can touch that fits in the palm of his hand.** Expect the terms to be firmed up later.
- Party joke that lands as a real capability: this can be used to **destroy locks** ("and there goes your thieves' guild entrance").

## Scene 9 — Brindle Stormtide at the tavern `[01:42:35]`–`[01:56:00]`

- Back at the Deep Water Inn. **Brindle is holding court**: a crowd around his table hanging on his every word and laughing at his jokes, a local bard (explicitly **not** Vandal Lovelace, "just some schmo") plucking a tune aimed at his table, Brindle **sitting on a box on top of a chair** so he looks down on everyone.
- **Toz walks up** — halfling to halfling. Brindle warms instantly: **"Oh, the halfling guy! Good to see another halfling here. What can Brindle do for you? Sorry for being so dismissive earlier."**
- **On Kuyrl:** Brindle knows exactly who they mean. **"Oh yeah, Kuyrl. Guy doesn't speak a lick of Common, but boy, he can lift a barrel of fish."**
- Toz raises the debt. Brindle's response, laughing:
  - **"I don't see that happening. So if that's the avenue you're after here, I think probably go find your own goliath."**
  - **"I'm gonna make a lot of money off that dude, that's all I'm gonna say."**
  - **"I mean, the amount that he makes… but I get him a nice place, I put him up, and his family and his kid. You know, they're pretty big, so it's a tall room. I think it'll be years."**
  - Asked if Kuyrl knows that: **"Maybe. I don't know what he knows."**
- **Larry.** Brindle's translator stands at his side: lanky, **silver ponytail, eye patch**, quiet and unassuming. "Thankfully I have him here to translate. Isn't that right, Larry?" — "Yes, sir."
- **On ships.** Asked whether he knows of vessels leaving port and where they're bound, Brindle says **"I know the comings and goings of all the ships around here"** — then takes offense at being asked for the schedule: **"Do you realize who you're talking to here? Am I your secretary now? Am I just giving you my ship ledgers? What is this?"** He **gestures**, and **a few big dudes drift closer.**
- The party backs off fast. Toz tries status — "the heroes who saved Goldenfields" — and rolls **Persuasion: 1 + 7 = 8.** Nothing. The DM notes Brindle is **agitated**, wants to get back to his night of adulation, and is not entertained by them.
- **The Larry gambit.** One PC (`SPEAKER_01`/`SPEAKER_00`, most consistent with **Eno**; see factcheck) addresses **Larry in Giant** — first to test whether Larry actually speaks it, then to bluff that **Kuyrl already knows he's being swindled and is not happy about it.**
- Larry answers **in Giant** — "how does he know that?" — then, when told, replies **in Common**, flatly: **"What's he going to do about it?"**
- **Fact-checked:** **Eno** did address Larry in Giant and attempt the intimidation — but **the 8 total was Toz rolling Persuasion**, not the Larry intimidation, and the two were merged by the diarization. The Larry attempt failed; its roll is not separately recoverable. The player's own read of the failure: "he threw me off with his response, so I feel like that played accurate."
- **Net result of the Brindle meeting:** no ship information, no debt negotiation, no coin information (they'd already gotten that from the Umberlee priestess). Confirmation that **Brindle never intends to let Kuyrl out.**
- **Plan formed:** get a **copy of Kuyrl's map** first, before picking any fight; then extract Kuyrl **and his family**; then Yackerty → Harpers' portal → Silverymoon → Harshnag → the Oracle. Copying the map is debated as a skill: **cartographer's tools** is ruled the right one; **navigator's tools** allowed as applicable; Fiz's **wind chalk** is clarified to be for **weather/favorable-wind navigation**, not mapmaking. Fiz's own tool proficiencies stated on air: **jeweler's, thieves', tinker's, and woodcarver's tools.**

## Scene 10 — Kuyrl's ledger, and the rage `[01:59:00]`–`[02:14:30]`

- **Afternoon.** They find Kuyrl still on the docks, coiling heavy ropes.
- Asked about the map, he first refuses on principle: **"only for giants. The place of the Oracle is a place only for giants."**
- **The book of giant runes.** A PC shows him **Zephyros's book of giant runes**. He asks to see it ("as long as you give it back") and is **visibly awed** — the DM notes the book's quality, but more than that, this is **material he has only ever received through oral tradition and scratches on stones, never seen printed**. The party offers a **trade: he may copy anything out of the rune book, and they copy his map.**
- The party names **Zephyros** as the **cloud giant** who told them they were destined to find the Oracle, and **Harshnag** as the frost giant they're seeking. Kuyrl: **"I have heard tale of this Harshnag. A frost giant of great renown."**
- **Kuyrl affirms he can open the way** — he is giant-kin, he counts.
- **The crew tells him the truth about Brindle:** that they've spoken to his boss and to Larry; that Brindle is "pretty attached to using you"; that he will never be allowed to pay off the debt; that he is effectively a **slave** / indentured. Kuyrl resists: **"What do you mean? They pay me and they give me a home."** Toz: **"He told us quite plainly that he doesn't see you leaving for many years."** The DM: he's **struggling to believe it**, being pulled both ways, and it will take convincing.
- **The persuasion, with the whole party stacking:**
  - **Toz rolls Persuasion with advantage** (the others are helping) — **natural 20.**
  - **Eno's *guidance*** adds a **d4: 2** → 22.
  - **Toz's +7** → **29.**
  - **Fiz's Flash of Genius** (+4 to any ability check by himself or a creature within 30 ft, 4 uses) → **33.**
- **Kuyrl breaks.** He **throws a barrel to the ground and smashes it.** His face boils over with rage; he paces back and forth: **"What are we going to do about this?"**
- **Then the audit.** Fiz asks to see the ledger and actually do the books — **"let the money guy do it."** The DM notes Kuyrl's disposition has swung all the way to loyal follower; he hands it over.
- **Intelligence check** (straight INT, no applicable skill). *(**Fact-checked** — the transcript's assembly of this roll was wrong.)* **Fiz rolled d20 6, + 4 INT, + 4 Flash of Genius, + 2 Eno's *guidance* = 16.** Success. **Flash of Genius *was* spent here** (a second use, after the one on Toz's persuasion).
- **The arithmetic Fiz works out:**
  - **Kuyrl owes 80 gold now.**
  - **He is projected to add another 80 gold of debt for every year he keeps working for Brindle.** *(Fact-checked and confirmed as the finding.)*
  - **Because Brindle charges him for room and board** — lodging, food — against his wages.
  - **He is going deeper into debt the longer he works. He can never pay it off.** The table names it exactly: **"He's literally indentured. It's a company-store thing."**
  - The party's conclusion: **don't pay Brindle anything.** Take Kuyrl and his family out instead.
- **The commotion.** The smashed barrel has drawn attention — other dock workers are gawking, and **an authority figure comes walking down the dock.**
- **The cover story.** The crew coaches Kuyrl: he must **loudly tell them off** so no one suspects him, they'll leave, and they'll come back for him. One PC offers to kick dirt and be shoved for realism.
- **Group Deception check** — DM needs **at least 2 successes** (DC 10). Rolls: **16, 2, 17, 12, 2, 23** (six values called out across the table). **Three successes.** It works.
- **Kuyrl plays his part:** the overseer arrives — **"Why you knock fish down?"** — and Kuyrl **shoves/slaps a PC down** hard enough that they just crumble (no resistance roll taken). The crew scatters. The DM confirms the deception held: the overseer points Kuyrl back to work.
- **They already have his address** — he told them where he lives. **The plan: come to his house tonight**, get the family, get out.

## Scene 11 — Chazlauth and the Draconic notes `[02:14:30]`–`[02:27:14]` (recording ends here)

- **Early-to-mid evening.** The crew crosses town to the nice part of Waterdeep and knocks at **Chazlauth's**. He lets them in: "Hey guys, you're back already. What's up?" — "We forgot some things."
- They lay out the three items taken from the Goldenfields fight: the **blue dragon sigil ring**, the **blue-steel thieves' tools** etched with Draconic numerals, and the **Draconic notes**.
- **The ring.** It is **a symbol of the Cult of the Dragon — a badge of membership.**
- **The Cult of the Dragon** (Chazlauth's explanation): essentially a **religion** — they don't call themselves that — which **worships the god Tiamat** and works to promote the goals of **chromatic dragons.**
- **The Draconic notes.** Chazlauth reads them: they are **instructions issued to the half-dragon the crew killed, from his master.** The full list as read out:
  1. **Acquire the navigation orb** — i.e. **Zephyros's navigation orb.**
  2. **Avoid storm giants unless discovery is unavoidable.**
  3. **Observe giant envoys on the coast — record, but do not interfere.**
  4. **Spread rumour and gold among the lesser giants** — *"confusion is sufficient"* (in quotes in the notes).
  5. **"Ensure the old sites remain quiet."**
  6. **"If signs of the Old Wyrm of the North appear, withdraw."**
  7. **"Do not impede the designs of the deep speaker."**
  8. **Report any cultist who speaks of alliances as if they were equals.**
- **Chazlauth's reading of the whole:** the mission is to get the **navigation orb**; they are **deliberately interfering with the giants**; and there is **some larger alliance in play involving the dragons** — with a hierarchy the notes are careful to police ("as if they were equals").
- **"The Old Wyrm of the North."** The party asks whether this is the ancient green dragon Chazlauth mentioned before (Old Gnawbone) or the copper dragon. **Chazlauth doesn't think so.** His candidate: **Klauth** (spelled out **K-L-A-U-T-H**), an **ancient red dragon**, one of the oldest dragons alive, famous, known to **have dealings with small folk**, living **somewhere in the north** — Chazlauth doesn't know precisely where. The dragons' own instruction is to **withdraw** from any sign of him.
- **"The deep speaker."** Read aloud without comment from Chazlauth. At the table, someone asks whether **Toz** reacts to the phrase — his possession/dream thread. The DM: **"I don't know if Toz reacts to that… I guess they could roll for it."** **No roll was taken and no answer was given** (**fact-checked and confirmed** — Toz did not roll to see whether he reacts to the phrase). This is left dangling. *(Given Toz's ocean dream, the white-eyed callers, and Umberlee's "warlock," this is the most consequential loose thread of the session.)*
- **The blue-steel thieves' tools.** Chazlauth reveals **no** hidden information about them and confirms **they are not magical** — the Draconic numerals are decorative. He simply **wants them because they look incredible** ("like some rich kid"). He offers to **buy them for a hundred-and-something gold** — the party is told it's roughly **ten times the price of a normal set.**
- The party debates keeping them (Fiz notes he can **conjure a set of artisan's tools himself** — Artificer's *Right Tool for the Job* — which triggers a rules tangent about needing tools to make tools; thieves' tools are confirmed to be a **type** of artisan's tools).
- **The trade.** Asked whether he has any **item** better than gold, Chazlauth looks around, says "you know what, I don't think I really need this," and **grabs a cloak off a hook** — revealing the cloak is hanging on **a bar of metal suspended in mid-air.** He **presses a button**, it drops into his hand, and he demonstrates by trying (and failing) to do a pull-up on it once re-fixed.
- **Deal: the blue-steel thieves' tools → Chazlauth, in exchange for an immovable rod.** The crew takes the rod. Reasoning stated: keeping Chazlauth happy means better prices and favours later.
- **The recording cuts out here**, mid-joke about whether an immovable rod fixed on a moving ship is fixed relative to the ship or the world.

---

## Scene 12 — [NOTES-ONLY] Night at the docks: Kuyrl's shack

> **Source: `player notes/fiz.md` only. Not on the recording.** Attributions here are Fiz's own, and every one of them matches the caster's class mechanics exactly.

- **As night falls**, the crew goes to **Kuyrl's residence: a small one-room shack among many others, under the docks.**
- They tell him **the plan has changed**: they need to find a man named **Yackerty**, who can maybe get them all to **Silverymoon**, which gets them to the Oracle.
- **Kuyrl agrees to work one more day.** The crew tells him **they'll come back the following night.**

## Scene 13 — [NOTES-ONLY] The fog ambush on the docks

> **Source: `player notes/fiz.md` only.** No timestamps, no rolls recorded. The sequence below is Fiz's written order of events, preserved exactly.

- **As they leave the docks, a dense fog rises from the ground and envelops them.** (Fog imposes disadvantage on attacks.)

**Round 1 — the ambush**

1. **A figure attacks Eno from behind with a sword — and misses.**
2. **A second figure casts a spell at Fiz. Fiz uses *shield* to block it.** *(**Fact-checked:** the spell was **not *shatter*** — Fiz's notes were wrong on that point, and the player does not recall which spell it was. *Shield* did turn it, which means it was a spell attack or *magic missile* rather than a saving-throw spell. Recorded as an unidentified spell.)*
3. **Fiz whips around and casts *faerie fire*.** Flakes of metal blast out of his **spellcasting rod** and blanket **five targets**: the two shadowy figures, **another figure standing next to Hal**, **a figure in front of Eno**, and **Eno himself**. All are outlined in blue light. **This negates the fog's disadvantage on attacks.**
4. **Eno casts *wind wall*, shaping it to catch all of the attackers. The wind also dissipates the fog.** *(**Fact-checked and confirmed.** *Wind wall* need not be a straight line — "you can shape the wall in any way you choose so long as it makes one continuous path along the ground" — so catching every attacker with one placement is legal. The fog clearing was an explicit DM ruling.)*

**What the light and the cleared air reveal**

- **The figure behind Fiz** — a **robed figure in gray, encrusted with barnacles.**
- **The figure behind Eno** and **the figure next to Hal** — **entranced dock workers.**
- **The figure in front of Eno** — **an octopus.**
- **A second octopus** in the water just off the dock.
- *(Fiz's notes carry an internal tension here: the "figure behind Eno" is first described as a sword-wielder and then grouped with the dock workers, while "the figure in front of Eno" is the octopus. Preserved as written; see factcheck.)*

**Round 2 — the counterattack**

5. **Toz casts *thunderwave***, catching **the gray-robed figure next to Fiz** and **the dock worker next to Hal**. **The dock worker is obliterated — killed outright.**
6. **Hal attacks the robed figure with his sword and hits twice** (Extra Attack). **The robed figure appears shocked that Hal's sword was able to hurt him at all** — implying resistance or immunity to ordinary weapons, which Hal's **+1 cursed crypt sword** bypasses.
7. **The octopuses attack Eno and Fiz. Both miss.**
8. **The robed figure flees and jumps off the dock into the water.**
9. **Fiz hits the fleeing figure with *scorching ray* — all three beams connect.**
10. **Hal hits him once more with the sword and kills him.** The body **sinks below the water.**

**Aftermath**

- **The surviving dock worker snaps out of his trance.**
- **The octopuses lose all interest in attacking.**
- **Toz pushes the octopuses away with a wave.** *(**Fact-checked:** Toz confirmed, but the **exact spell is not recorded** and the player does not recall it. Earlier guess of Shape Water withdrawn.)*
- **The session ends here.** The robed body was not recovered.

---

## Items, gains, and losses

**Gained**

- **The eye-coin** — taken from **Emmert Dorrow's** body in a folded leather pouch. One face bears an **eye**; the other bears **a number**, unreadable under permanent white-and-green calcification. Under the spell **Eternal Corrosion**. A magic-imbued object; **no attunement, no charges, no useful properties**. **It affects anyone who was white-eyed at the tavern** (and **Toz**, secretly). It did **not** affect Fiz or an unaffected patron. Per the Umberlee priestess, it is **an old symbol of Umberlee**, expressing the war between clean and corroded, life and death — and it is **not itself cursed**. **Stowed in the party's Bag of Holding.**
- **Eternal Corrosion (cantrip)** — **learned by Fiz** from the *identify* reading. Corrodes, permanently and irreversibly, **one object you touch that fits in the palm of your hand.** Objects only. DM-granted with no roll; DM voiced regret but did not retract it.
- **Immovable rod** — from **Chazlauth**, in trade. Fixes rigidly in mid-air at the press of a button.
- **Umberlee's blessing** — the priestess blessed the whole party. No mechanical effect stated.
- **Kuyrl Stonepalm's cooperation** — after the 33-total persuasion, he is described as swung all the way to loyal follower. **Not yet extracted.**

**Given up / spent**

- **The blue-steel thieves' tools** — traded to **Chazlauth** for the immovable rod. (He'd offered ~100+ gold, roughly ten times a normal set's price. Confirmed **non-magical**; the Draconic numerals are decorative.)
- **1 gold** into the Kelemvor priestess's cup at the gray tent (a **donation**, not payment for services).
- **A few copper plus 1 gold** into the Umberlee shrine's cup.
- **Emmert Dorrow's purse** — handed to the barkeep to pass to his widow, **Thora**. (Never the crew's; recorded for the ledger.)
- **Declined:** the hand-transcribed Umberlee scripture at 20 silver / 2 gold.

**Loaned / shown, not given**

- **Zephyros's book of giant runes** — shown to Kuyrl, who was awed by it; returned. Basis of the proposed copy-for-copy trade with his map.

## Leads standing at session end

- **The map.** Kuyrl has a **map to the Oracle** in his ledger booklet. **The crew has not yet copied it.** Agreed method: cartographer's tools (or navigator's tools) rather than forgery kit or calligraphy.
- **Giants only.** **"A giant is needed to open the way"** at the Oracle. Kuyrl claims goliath giant-kin counts. This makes him — or Harshnag — structurally necessary, not merely useful.
- **The extraction.** Return to Kuyrl's shack under the docks; take **Kuyrl, his wife, and his son**; relocate the family somewhere safe (Silverymoon or Goldenfields floated). **Explicitly do NOT pay Brindle** — the debt is designed never to clear.
- **Yackerty**, dwarf Harper in the **Trades Ward** → **Harpers' portal network** → **Silverymoon** → **Harshnag** → the Oracle. Named by **Vandal Lovelace**. Still the primary route.
- **The warlock.** Someone has tapped Umberlee's power and is using it to their own ends. **To find them: a divination wizard or cleric.** Warlocks operate in secret and are contract-bound not to name their patrons.
- **Another coin.** Eno has ***locate object*** prepared and floated using it to find a second eye-coin within 1,000 ft. **Never cast.**
- **The Nandar heir.** To break Hal's curse without a three-day trip back to Nightstone: find whoever would have **inherited the Nandar estate**, or a **blood descendant**, and get their **permission** to wield the sword. Lady Nandar died in the giant raid; no known Nightstone descendants.
- **Klauth**, ancient red dragon, "Old Wyrm of the North," somewhere in the north, known to deal with small folk — and the Cult's own agents are ordered to **withdraw** from him. A potential lever.
- **Chazlauth** remains a friendly, well-disposed dragon expert and now owes the crew goodwill.

## Unresolved threads and open questions

1. **"Do not impede the designs of the deep speaker."** Who or what is the deep speaker? A DM prompt to roll for Toz's reaction was raised and then dropped without a roll. Standing alongside Toz's ocean dreams, the "pied piper from the sea," and Umberlee's warlock, this reads as the same thread from three directions.
2. **Toz is hiding two things.** (a) That every white-eyed victim had **his** dream of being called to the ocean. (b) That the coin visibly affects him — which **only Eno** noticed, and Eno has said nothing. Neither secret has surfaced to the party.
3. **The seawater.** A pool of seawater "washed out" of Emmert Dorrow's body at the moment of death, not from any wound or orifice. Never explained, never sampled.
4. **"You should have taken their offer."** What offer? To whom? The room's other remembered line — "we're going to take back what's ours" — was disputed at the table and never settled.
5. **The number on the coin.** Each Umberlee coin bears a unique number on its corroded face. This one's is unreadable — and **Eternal Corrosion** guarantees it stays that way. Whatever the number identifies is deliberately locked away.
6. **Why the coin only touches the already-touched.** It works on people who went white-eyed and on Toz; it does nothing to Fiz or to an unaffected patron. The mechanism is unexplained.
7. **The robed, barnacle-encrusted figure** (notes-only) died and **sank into the harbour**. Not searched, not identified. Given it was shocked that a magical blade could hurt it, it was likely resistant to nonmagical weapons. **The best candidate yet for the warlock — or the warlock's servant — and the body is gone.**
8. **Two octopuses** broke off and swam away unharmed once the robed figure died — the same pattern as the tavern, where the puppets fell still the instant the source died.
9. **A second entranced dock worker was killed by *thunderwave***. That is a dead innocent civilian on the docks at night, with a city watch that already tried to detain the crew once today.
10. **No ship.** Brindle will not sell, will not share schedules, and now has the crew on his radar. Sea passage north is closed for the moment; the portal is the live route.
11. **Eternal Corrosion is homebrew, with details yet to be determined.** DM-granted mid-session with explicit second thoughts, and confirmed afterwards as a homebrewed spell still being worked out. Currently: a cantrip, any object Fiz can touch that fits in his palm.
