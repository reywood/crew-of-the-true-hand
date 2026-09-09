"""Writing pages out and staging static/media assets into the site tree."""

import shutil


def write_page(out_dir, filename, content):
    (out_dir / filename).write_text(content, encoding="utf-8")


def setup_output(paths, out_dir, sessions):
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
    _stage_session_media(sessions, out_dir)


def _stage_session_media(sessions, out_dir):
    """Publish each session's media into the stable site URL layout.

    Which files exist and what they are called on the site is the Session
    aggregate's business — this only copies what it reports. It used to walk
    sessions/ a second time and re-apply the same four discovery rules that
    load_sessions had just applied ("skip library", "hero is the banner",
    "everything else is a beat", the extension whitelist), so adding an image
    format meant finding both copies.
    """
    audio_dst = out_dir / "audio" / "sessions"
    audio_dst.mkdir(parents=True, exist_ok=True)
    image_dst = out_dir / "images" / "sessions"
    image_dst.mkdir(parents=True, exist_ok=True)

    for session in sessions:
        art = session.artifacts
        if art.audio:
            shutil.copy2(art.audio, audio_dst / session.audio_name)
        if art.hero:
            shutil.copy2(art.hero, image_dst / session.hero_name)
        if art.beats:
            beats_dst = image_dst / session.date
            beats_dst.mkdir(parents=True, exist_ok=True)
            for path in art.beats.values():
                shutil.copy2(path, beats_dst / path.name)
