"""The podcast RSS feed."""

import datetime as _dt
import html
from email.utils import format_datetime

from ..core.audio_credits import AudioCredits
from ..core.text import _hms
from .layout import base_url


def podcast_feed(paths, sessions, probe):
    channel_title = "Tales of the True Hand"
    channel_desc = ("Weekly recaps of the Crew of the True Hand — a D&D 5e "
                    "campaign following Storm King's Thunder — told by "
                    "Vandal Lovelace, bard and hearth-storyteller.")
    channel_link = f"{base_url()}/sessions.html"
    feed_url = f"{base_url()}/feed.xml"
    cover_url = f"{base_url()}/static/podcast-cover.jpg"

    with_audio = [s for s in sessions if s.has_audio]
    with_audio.sort(key=lambda x: x.date, reverse=True)

    # License-mandated + courtesy attribution for the shared audio library.
    # The music/SFX library is common to every episode, so the same credit
    # block is carried on every item's <description>/<content:encoded>.
    credits = AudioCredits.load(paths)
    credits_text = credits.as_text()

    items_xml = []
    latest_pub = None
    for s in with_audio:
        date = s.date
        audio_name = s.audio_name
        audio_path = s.artifacts.audio
        try:
            size = audio_path.stat().st_size if audio_path else 0
        except OSError:
            size = 0
        duration = int(probe(audio_path)) if audio_path else 0

        subtitle = s.artifacts.episode_title
        ep_title = f"{date} — {subtitle}" if subtitle else f"{date}"
        in_brief = s.summary.in_brief
        ep_blurb = in_brief or s.blurb
        # Plain-text description carries the blurb + the credits block.
        ep_desc = ep_blurb
        if credits_text:
            ep_desc = f"{ep_blurb}\n\n{credits_text}" if ep_blurb else credits_text

        # Richer HTML variant for readers that honour <content:encoded>.
        content_html_parts = []
        if ep_blurb:
            content_html_parts.append(f"<p>{html.escape(ep_blurb)}</p>")
        if credits:
            content_html_parts.append("<p><strong>Music &amp; SFX credits:</strong></p>")
            if credits.required:
                lis = "".join(
                    f"<li>{html.escape(c)}</li>" for c in credits.required
                )
                content_html_parts.append(f"<ul>{lis}</ul>")
            if credits.voluntary:
                vol = "; ".join(html.escape(v) for v in credits.voluntary)
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
        if s.has_hero:
            item_image = (
                f'    <itunes:image href="{base_url()}/images/sessions/'
                f'{html.escape(s.hero_name)}"/>\n'
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
