"""The minimal markdown subset the archive uses."""

import html
import re


def md_inline(s):
    s = html.escape(s)
    parts = re.split(r"(`[^`]+`)", s)
    for i, p in enumerate(parts):
        if p.startswith("`") and p.endswith("`"):
            parts[i] = f"<code>{p[1:-1]}</code>"
        else:
            p = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", p)
            p = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", p)
            p = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', p)
            parts[i] = p
    return "".join(parts)


def md_to_html(text):
    if not text:
        return ""
    out, para, list_items = [], [], None

    def flush_para():
        nonlocal para
        if para:
            out.append("<p>" + " ".join(md_inline(line) for line in para) + "</p>")
            para = []

    def flush_list():
        nonlocal list_items
        if list_items is not None:
            out.append("<ul>" + "".join(
                f"<li>{md_inline(it)}</li>" for it in list_items) + "</ul>")
            list_items = None

    def flush():
        flush_para()
        flush_list()

    for raw in text.split("\n"):
        line = raw.rstrip()
        if not line.strip():
            flush()
            continue
        if re.match(r"^---+$", line):
            flush()
            out.append("<hr>")
            continue
        m = re.match(r"^(#{1,6})\s+(.*)$", line)
        if m:
            flush()
            n = len(m.group(1))
            out.append(f"<h{n}>{md_inline(m.group(2))}</h{n}>")
            continue
        m = re.match(r"^\s*[-*]\s+(.*)$", line)
        if m:
            flush_para()
            if list_items is None:
                list_items = []
            list_items.append(m.group(1))
            continue
        flush_list()
        para.append(line)
    flush()
    return "\n".join(out)
