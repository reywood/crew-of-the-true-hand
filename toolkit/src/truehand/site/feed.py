"""The podcast RSS feed."""

import datetime as _dt
import html
import re
from email.utils import format_datetime

from ..core.text import _extract_in_brief, _hms
from .layout import base_url

# Cache for the parsed audio-library credits so we only read CREDITS.md once.
_AUDIO_CREDITS_CACHE = None


def _parse_audio_credits(paths):
    """Parse sessions/library/audio/CREDITS.md into a list of asset dicts.

    Each asset is a ``## <name>`` section carrying a ``**License**:`` line.
    We split the required-attribution assets (CC-BY and friends, whose license
    is a license condition) from the voluntary ones (Pixabay Content License,
    where attribution is a courtesy, not a requirement).

    Returns a dict with two lists of plain-text credit strings:
      {"required": [...], "voluntary": [...]}
    Both are ordered as they appear in CREDITS.md.
    """
    global _AUDIO_CREDITS_CACHE
    if _AUDIO_CREDITS_CACHE is not None:
        return _AUDIO_CREDITS_CACHE

    result = {"required": [], "voluntary": []}
    try:
        text = paths.audio_credits.read_text(encoding="utf-8")
    except OSError:
        _AUDIO_CREDITS_CACHE = result
        return result

    # Split into ``## <name>`` sections (skip the file's own preamble).
    sections = re.split(r"^##\s+(.+?)\s*$", text, flags=re.MULTILINE)
    # re.split with one capture group yields: [preamble, name1, body1, name2, body2, ...]
    for i in range(1, len(sections), 2):
        name = sections[i].strip()
        body = sections[i + 1] if i + 1 < len(sections) else ""

        lic_m = re.search(r"^\s*[-*]\s*\*\*License\*\*:\s*(.+?)\s*$",
                          body, flags=re.MULTILINE)
        license_line = lic_m.group(1).strip() if lic_m else ""
        # Strip markdown link syntax <...> from the trailing license URL.
        license_line = re.sub(r"\s*—\s*<[^>]+>\s*$", "", license_line).strip()

        # Attribution is required when the license itself demands it. Pixabay's
        # Content License does not; Creative Commons "Attribution" (CC BY) does.
        requires = bool(re.search(r"attribution", license_line, re.IGNORECASE)) \
            and "pixabay" not in license_line.lower()

        if requires:
            # Pull the required-attribution blockquote (the ``> ...`` lines that
            # follow the "Required attribution wording" note).
            quote_lines = []
            capture = False
            for ln in body.split("\n"):
                if re.search(r"required attribution wording", ln, re.IGNORECASE):
                    capture = True
                    continue
                if capture:
                    m = re.match(r"^\s*>\s?(.*)$", ln)
                    if m:
                        if m.group(1).strip():
                            quote_lines.append(m.group(1).strip())
                    elif quote_lines:
                        break
            wording = " — ".join(quote_lines) if quote_lines else name
            result["required"].append(f"{wording}  (used in {name})")
        else:
            # Voluntary credit: use the plain-text fallback line if present.
            fb_m = re.search(r"Plain-text fallback:\s*\*?(.+?)\*?\s*$",
                             body, flags=re.MULTILINE)
            if fb_m:
                result["voluntary"].append(fb_m.group(1).strip().rstrip("."))

    _AUDIO_CREDITS_CACHE = result
    return result


def _audio_credits_text(paths):
    """Human-readable attribution block appended to every podcast episode.

    CC-BY (and similar) assets carry their license-mandated attribution wording;
    Pixabay assets get a single courtesy roll-up line (attribution not required).
    Returns a plain-text string (no trailing newline) or "" if nothing to credit.
    """
    credits = _parse_audio_credits(paths)
    lines = []
    if credits["required"] or credits["voluntary"]:
        lines.append("Music & SFX credits:")
    for c in credits["required"]:
        lines.append(f"• {c}")
    if credits["voluntary"]:
        lines.append("Additional sound effects & ambience (Pixabay Content "
                     "License, attribution not required): "
                     + "; ".join(credits["voluntary"]) + ".")
    return "\n".join(lines)


def podcast_feed(paths, sessions, probe):
    channel_title = "Tales of the True Hand"
    channel_desc = ("Weekly recaps of the Crew of the True Hand — a D&D 5e "
                    "campaign following Storm King's Thunder — told by "
                    "Vandal Lovelace, bard and hearth-storyteller.")
    channel_link = f"{base_url()}/sessions.html"
    feed_url = f"{base_url()}/feed.xml"
    cover_url = f"{base_url()}/static/podcast-cover.jpg"

    with_audio = [s for s in sessions if s.meta.get("has_audio")]
    with_audio.sort(key=lambda x: x.meta.get("date", x.slug), reverse=True)

    # License-mandated + courtesy attribution for the shared audio library.
    # The music/SFX library is common to every episode, so the same credit
    # block is carried on every item's <description>/<content:encoded>.
    credits_text = _audio_credits_text(paths)
    credits = _parse_audio_credits(paths)

    items_xml = []
    latest_pub = None
    for s in with_audio:
        date = s.meta.get("date", s.slug)
        audio_name = s.meta.get("audio_name") or f"{date}.mp3"
        audio_path = s.meta.get("audio_src")
        try:
            size = audio_path.stat().st_size if audio_path else 0
        except OSError:
            size = 0
        duration = int(probe(audio_path)) if audio_path else 0

        subtitle = s.meta.get("audio_subtitle") or ""
        ep_title = f"{date} — {subtitle}" if subtitle else f"{date}"
        in_brief = _extract_in_brief(s.meta.get("summary_md", ""))
        ep_blurb = in_brief or (s.summary or "")
        # Plain-text description carries the blurb + the credits block.
        ep_desc = ep_blurb
        if credits_text:
            ep_desc = f"{ep_blurb}\n\n{credits_text}" if ep_blurb else credits_text

        # Richer HTML variant for readers that honour <content:encoded>.
        content_html_parts = []
        if ep_blurb:
            content_html_parts.append(f"<p>{html.escape(ep_blurb)}</p>")
        if credits["required"] or credits["voluntary"]:
            content_html_parts.append("<p><strong>Music &amp; SFX credits:</strong></p>")
            if credits["required"]:
                lis = "".join(
                    f"<li>{html.escape(c)}</li>" for c in credits["required"]
                )
                content_html_parts.append(f"<ul>{lis}</ul>")
            if credits["voluntary"]:
                vol = "; ".join(html.escape(v) for v in credits["voluntary"])
                content_html_parts.append(
                    "<p>Additional sound effects &amp; ambience (Pixabay Content "
                    f"License, attribution not required): {vol}.</p>"
                )
        content_html = "".join(content_html_parts)

        try:
            y, m, d = [int(x) for x in date.split("-")]
            pub_dt = _dt.datetime(y, m, d, 12, 0, 0, tzinfo=_dt.UTC)
        except (ValueError, TypeError):
            pub_dt = _dt.datetime.now(_dt.UTC)
        pub_str = format_datetime(pub_dt)
        if latest_pub is None or pub_dt > latest_pub:
            latest_pub = pub_dt

        episode_page = f"{base_url()}/{s.href}"
        enclosure_url = f"{base_url()}/audio/sessions/{audio_name}"
        guid = enclosure_url

        item_image = ""
        if s.meta.get("has_image"):
            img_name = s.meta.get("image_name") or f"{date}.jpg"
            item_image = (
                f'    <itunes:image href="{base_url()}/images/sessions/{html.escape(img_name)}"/>\n'
            )

        items_xml.append(f"""  <item>
    <title>{html.escape(ep_title)}</title>
    <link>{html.escape(episode_page)}</link>
    <guid isPermaLink="false">{html.escape(guid)}</guid>
    <pubDate>{pub_str}</pubDate>
    <description>{html.escape(ep_desc)}</description>
    <itunes:summary>{html.escape(ep_desc)}</itunes:summary>
    <content:encoded><![CDATA[{content_html}]]></content:encoded>
    <itunes:duration>{_hms(duration)}</itunes:duration>
    <itunes:explicit>false</itunes:explicit>
    <itunes:episodeType>full</itunes:episodeType>
{item_image}    <enclosure url="{html.escape(enclosure_url)}" length="{size}" type="audio/mpeg"/>
  </item>""")

    last_build = format_datetime(latest_pub or _dt.datetime.now(_dt.UTC))

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"
     xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd"
     xmlns:atom="http://www.w3.org/2005/Atom"
     xmlns:content="http://purl.org/rss/1.0/modules/content/">
<channel>
  <title>{html.escape(channel_title)}</title>
  <link>{html.escape(channel_link)}</link>
  <atom:link href="{html.escape(feed_url)}" rel="self" type="application/rss+xml"/>
  <language>en-us</language>
  <description>{html.escape(channel_desc)}</description>
  <itunes:summary>{html.escape(channel_desc)}</itunes:summary>
  <itunes:author>Vandal Lovelace</itunes:author>
  <itunes:owner>
    <itunes:name>Crew of the True Hand</itunes:name>
    <itunes:email>noreply@crew-of-the-true-hand.local</itunes:email>
  </itunes:owner>
  <itunes:image href="{html.escape(cover_url)}"/>
  <itunes:category text="Leisure">
    <itunes:category text="Games"/>
  </itunes:category>
  <itunes:explicit>false</itunes:explicit>
  <itunes:type>episodic</itunes:type>
  <lastBuildDate>{last_build}</lastBuildDate>
{chr(10).join(items_xml)}
</channel>
</rss>
"""
