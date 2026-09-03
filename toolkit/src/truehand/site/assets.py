"""Writing pages out and staging static/media assets into the site tree."""

import shutil


def write_page(out_dir, filename, content):
    (out_dir / filename).write_text(content, encoding="utf-8")


def setup_output(paths, out_dir):
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)
    (out_dir / "static").mkdir()
    if paths.static.exists():
        for f in paths.static.glob("*"):
            shutil.copy2(f, out_dir / "static" / f.name)
    img_dir = out_dir / "images" / "characters"
    img_dir.mkdir(parents=True, exist_ok=True)
    if paths.characters.exists():
        for img in paths.characters.glob("*.jpeg"):
            shutil.copy2(img, img_dir / img.name)
    # Battle cards (battle-cards/<slug>.html) are self-contained printable pages;
    # copy them verbatim to site/battle-cards/ and link them from each PC page.
    if paths.battle_cards.exists():
        card_dst = out_dir / "battle-cards"
        card_dst.mkdir(parents=True, exist_ok=True)
        for card in paths.battle_cards.glob("*.html"):
            shutil.copy2(card, card_dst / card.name)
    # Podcast cover (website/static/podcast-cover.jpg) is copied to site/static/
    # by the static-asset glob above, alongside style.css / podcast-subscribe.js.
    # Per-session audio + images live under sessions/YYYY-MM-DD/. Copy them into
    # the stable site URL layout: final.mp3 → site/audio/sessions/DATE.mp3,
    # hero.<ext> → site/images/sessions/DATE.<ext>, and each beat image →
    # site/images/sessions/DATE/<beat-slug>.<ext>.
    audio_dst = out_dir / "audio" / "sessions"
    audio_dst.mkdir(parents=True, exist_ok=True)
    session_img_dir = out_dir / "images" / "sessions"
    session_img_dir.mkdir(parents=True, exist_ok=True)
    if paths.sessions.exists():
        for sdir in paths.sessions.iterdir():
            if not sdir.is_dir() or sdir.name == "library":
                continue
            date = sdir.name
            final = sdir / "audio" / "final.mp3"
            if final.exists():
                shutil.copy2(final, audio_dst / f"{date}.mp3")
            img_src = sdir / "images"
            if img_src.exists():
                for ext in ("*.jpg", "*.jpeg", "*.png", "*.webp"):
                    for img in img_src.glob(ext):
                        if img.stem == "hero":
                            shutil.copy2(img, session_img_dir / f"{date}{img.suffix}")
                        else:
                            beats_dst = session_img_dir / date
                            beats_dst.mkdir(parents=True, exist_ok=True)
                            shutil.copy2(img, beats_dst / img.name)
