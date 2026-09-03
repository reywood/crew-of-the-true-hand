"""Rendering the fact-check worksheet as a reviewable HTML page.

Was scripts/generate-factcheck-review.py — the only script with no argparse at
all; it hand-rolled sys.argv and is undocumented in CLAUDE.md. Reads
sessions/<date>/transcript-distilled.factcheck.md and writes the .html beside
it. Pure stdlib, no external calls.

The page template below is a self-contained one-off, deliberately left as-is:
it is not site output and shares nothing with the site's renderer.
"""

from __future__ import annotations

import html
import pathlib
import re

from ..errors import UserError

FACTCHECK_NAME = "transcript-distilled.factcheck.md"


# [HH:MM:SS] or [HH:MM:SS.mmm] — the diarized-transcript timestamp form.
TS_RE = re.compile(r"\[(\d{1,2}):([0-5]\d):([0-5]\d)(?:\.\d+)?\]")


def linkify_timestamps(s: str) -> str:
    """Wrap each [HH:MM:SS] in a play-from-here anchor. Runs on already-escaped,
    already-inline-formatted HTML; timestamps contain no HTML-special chars so
    ordering versus code/bold/italic is safe."""
    def repl(m: re.Match) -> str:
        h, mm, ss = int(m.group(1)), int(m.group(2)), int(m.group(3))
        secs = h * 3600 + mm * 60 + ss
        return (f'<a class="ts" data-t="{secs}" role="button" tabindex="0" '
                f'title="Play from {m.group(0)[1:-1]}">{m.group(0)}</a>')
    return TS_RE.sub(repl, s)


def inline(text: str) -> str:
    """Minimal inline markdown → HTML for the constructs the worksheet uses."""
    s = html.escape(text)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", s)
    s = linkify_timestamps(s)
    return s


def split_row(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def is_sep(line: str) -> bool:
    return bool(re.fullmatch(r"\|[\s:|-]+\|", line.strip()))


def render(md: str) -> str:
    lines = md.splitlines()
    out: list[str] = []
    i, n = 0, len(lines)
    while i < n:
        line = lines[i]
        stripped = line.strip()

        if not stripped:
            i += 1
            continue

        # Headings
        m = re.match(r"(#{1,6})\s+(.*)", stripped)
        if m:
            level = len(m.group(1))
            out.append(f"<h{level}>{inline(m.group(2))}</h{level}>")
            i += 1
            continue

        # Tables (a run of pipe lines)
        if stripped.startswith("|"):
            block = []
            while i < n and lines[i].strip().startswith("|"):
                block.append(lines[i])
                i += 1
            header = split_row(block[0])
            body = [split_row(r) for r in block[1:] if not is_sep(r)]
            # A worksheet table whose last column is the ✔/✘ verdict is reviewable.
            reviewable = bool(header) and ("✔" in header[-1] or "✘" in header[-1])
            ncols = len(header)
            out.append('<table>')
            out.append("<thead><tr>" + "".join(
                f"<th>{inline(c)}</th>" for c in header) + "</tr></thead>")
            out.append("<tbody>")
            for cells in body:
                row_id = re.sub(r"[^0-9A-Za-z]+", "", cells[0]) if cells else ""
                rid = html.escape(row_id)
                out.append(f'<tr data-row="{rid}">')
                for j, c in enumerate(cells):
                    last = j == len(cells) - 1
                    if reviewable and last:
                        seed = "✔" if "✔" in c else ("✘" if "✘" in c else "")
                        out.append(
                            f'<td class="verdict">'
                            f'<button class="mark" data-state="{seed}">'
                            f'{seed or "—"}</button>'
                            f'<button class="notebtn" title="Add correction / note"'
                            f' aria-label="Add correction or note">✎</button>'
                            f'</td>')
                    else:
                        out.append(f"<td>{inline(c)}</td>")
                out.append("</tr>")
                if reviewable:
                    out.append(
                        f'<tr class="note-row" data-row="{rid}">'
                        f'<td colspan="{ncols}">'
                        f'<textarea class="corr" '
                        f'placeholder="Correction for row {rid} — what is wrong '
                        f'and what it should say"></textarea></td></tr>')
            out.append("</tbody></table>")
            continue

        # Bullet list
        if re.match(r"[-*]\s+", stripped):
            out.append("<ul>")
            while i < n and re.match(r"[-*]\s+", lines[i].strip()):
                item = re.sub(r"^[-*]\s+", "", lines[i].strip())
                out.append(f"<li>{inline(item)}</li>")
                i += 1
            out.append("</ul>")
            continue

        # Paragraph (gather until blank)
        para = [stripped]
        i += 1
        while i < n and lines[i].strip() and not lines[i].strip().startswith(
                ("|", "#", "-", "*")):
            para.append(lines[i].strip())
            i += 1
        out.append(f"<p>{inline(' '.join(para))}</p>")

    return "\n".join(out)


PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Fact-check review — {date}</title>
<style>
  :root {{
    --bg:#faf8f4; --fg:#1e1b16; --muted:#6b6459; --line:#e0d8ca;
    --card:#fff; --accent:#8a5a2b; --accent-fg:#fff;
    --ok:#1f7a3f; --no:#b3261e; --ts:#8a5a2b; --ts-bg:#f0e7d8; --code:#514a3e;
  }}
  @media (prefers-color-scheme: dark) {{
    :root {{
      --bg:#17140f; --fg:#ece6da; --muted:#9c9384; --line:#332d24;
      --card:#211d16; --accent:#d59a5c; --accent-fg:#17140f;
      --ok:#5fce87; --no:#f2867d; --ts:#e0b07a; --ts-bg:#2a2318; --code:#c9c0af;
    }}
  }}
  * {{ box-sizing:border-box; }}
  body {{
    margin:0; background:var(--bg); color:var(--fg);
    font:15px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;
  }}
  .wrap {{ max-width:1040px; margin:0 auto; padding:0 20px 80px; }}
  header.player {{
    position:sticky; top:0; z-index:10; background:var(--bg);
    border-bottom:1px solid var(--line); padding:14px 0 12px; margin-bottom:8px;
  }}
  header.player .inner {{ max-width:1040px; margin:0 auto; padding:0 20px;
    display:flex; gap:14px; align-items:center; flex-wrap:wrap; }}
  audio {{ flex:1 1 320px; min-width:280px; height:38px; }}
  .now {{ font-variant-numeric:tabular-nums; color:var(--muted); font-size:13px;
    white-space:nowrap; }}
  .now b {{ color:var(--accent); }}
  .warn {{ display:none; width:100%; margin-top:8px; padding:8px 12px;
    background:var(--ts-bg); border:1px solid var(--line); border-radius:8px;
    color:var(--no); font-size:13px; }}
  h1 {{ font-size:22px; margin:18px 0 4px; }}
  h3 {{ font-size:16px; margin:26px 0 6px; }}
  p {{ color:var(--fg); }}
  table {{ width:100%; border-collapse:collapse; margin:14px 0; font-size:14px; }}
  th, td {{ text-align:left; vertical-align:top; padding:9px 10px;
    border-bottom:1px solid var(--line); }}
  th {{ font-size:12px; text-transform:uppercase; letter-spacing:.04em;
    color:var(--muted); }}
  tbody tr:not(.note-row):hover {{
    background:color-mix(in srgb, var(--card) 60%, transparent); }}
  tr.playing {{ background:var(--ts-bg) !important;
    outline:2px solid var(--accent); outline-offset:-2px; }}
  code {{ font:13px/1.5 ui-monospace,SFMono-Regular,Menlo,monospace;
    color:var(--code); word-break:break-word; }}
  a.ts {{ display:inline-block; cursor:pointer; color:var(--ts);
    background:var(--ts-bg); border:1px solid var(--line); border-radius:5px;
    padding:0 4px; margin:1px 0; font:12px/1.5 ui-monospace,Menlo,monospace;
    text-decoration:none; }}
  a.ts:hover {{ background:var(--accent); color:var(--accent-fg);
    border-color:var(--accent); }}
  a.ts::before {{ content:"\\25B6\\FE0E"; font-size:9px; margin-right:3px;
    opacity:.75; }}
  td.verdict {{ text-align:center; white-space:nowrap; }}
  button.mark {{ cursor:pointer; min-width:40px; font-size:16px; line-height:1;
    padding:6px 8px; border-radius:7px; border:1px solid var(--line);
    background:var(--card); color:var(--muted); }}
  button.mark[data-state="\\2714"] {{ color:var(--ok);
    border-color:var(--ok); font-weight:700; }}
  button.mark[data-state="\\2718"] {{ color:var(--no);
    border-color:var(--no); font-weight:700; }}
  button.notebtn {{ cursor:pointer; margin-left:5px; font-size:13px;
    padding:5px 7px; border-radius:6px; border:1px solid var(--line);
    background:var(--card); color:var(--muted); }}
  button.notebtn.has-note {{ color:var(--accent); border-color:var(--accent); }}
  tr.note-row {{ display:none; }}
  tr.note-row.open {{ display:table-row; }}
  tr.note-row td {{ padding-top:0; border-bottom:1px solid var(--line); }}
  textarea.corr {{ width:100%; min-height:54px; resize:vertical;
    font:13px/1.5 ui-monospace,SFMono-Regular,Menlo,monospace;
    background:var(--card); color:var(--fg); border:1px solid var(--accent);
    border-radius:8px; padding:8px; }}
  .tools {{ display:flex; gap:10px; align-items:center; flex-wrap:wrap;
    margin:6px 0 2px; position:sticky; top:64px; }}
  .tools button {{ cursor:pointer; padding:7px 12px; border-radius:8px;
    border:1px solid var(--line); background:var(--card); color:var(--fg);
    font-size:13px; }}
  .tools button.primary {{ background:var(--accent); color:var(--accent-fg);
    border-color:var(--accent); }}
  .tally {{ color:var(--muted); font-size:13px; }}
  .tally b.ok {{ color:var(--ok); }} .tally b.no {{ color:var(--no); }}
  #copyOut {{ width:100%; margin-top:10px; height:150px; display:none;
    font:13px/1.5 ui-monospace,Menlo,monospace; background:var(--card);
    color:var(--fg); border:1px solid var(--line); border-radius:8px;
    padding:8px; }}
  .hint {{ color:var(--muted); font-size:12.5px; margin:2px 0 0; }}
</style>
</head>
<body>
<header class="player">
  <div class="inner">
    <audio id="player" controls preload="metadata" src="recording.m4a"></audio>
    <span class="now">Playing from <b id="nowAt">—</b></span>
    <div class="warn" id="warn">Couldn't load <code>recording.m4a</code>.
      Open this page from inside the session folder
      (<code>sessions/{date}/</code>) so the recording sits beside it.</div>
  </div>
</header>
<div class="wrap">
  <h1>Fact-check review — {date}</h1>
  <p class="hint">Click any <a class="ts" data-t="0" role="button"
    tabindex="0">[timestamp]</a> to hear that line. Click the ✔/✘ cell to cycle
    unset → ✔ → ✘— marking ✘ opens a correction box (or hit ✎ on any row). Then
    <b>Copy results</b> to paste your verdicts + corrections back. Everything is
    saved in this browser.</p>
  <div class="tools">
    <button class="primary" id="copyBtn">Copy results</button>
    <button id="clearBtn">Clear all</button>
    <span class="tally" id="tally"></span>
  </div>
  <textarea id="copyOut" readonly></textarea>
{body}
</div>
<script>
  const DATE = "{date}";
  const player = document.getElementById('player');
  const nowAt = document.getElementById('nowAt');
  const KEY = r => `fc:${{DATE}}:${{r}}`;
  const NKEY = r => `fcnote:${{DATE}}:${{r}}`;

  function fmt(t) {{
    t = Math.max(0, Math.floor(t));
    const h = Math.floor(t/3600), m = Math.floor((t%3600)/60), s = t%60;
    const p = n => String(n).padStart(2,'0');
    return `${{p(h)}}:${{p(m)}}:${{p(s)}}`;
  }}

  // Seek + play from a timestamp.
  function seek(sec, row) {{
    const go = () => {{ try {{ player.currentTime = sec; }} catch(e){{}}
      player.play().catch(()=>{{}}); }};
    if (player.readyState >= 1) go();
    else {{ player.load();
      player.addEventListener('loadedmetadata', go, {{once:true}}); }}
    nowAt.textContent = fmt(sec);
    document.querySelectorAll('tr.playing').forEach(r=>r.classList.remove('playing'));
    if (row) row.classList.add('playing');
  }}
  document.querySelectorAll('a.ts').forEach(a => {{
    const act = e => {{ e.preventDefault();
      seek(+a.dataset.t, a.closest('tr')); }};
    a.addEventListener('click', act);
    a.addEventListener('keydown', e => {{ if (e.key==='Enter'||e.key===' ') act(e); }});
  }});
  player.addEventListener('timeupdate', () => {{
    if (!player.paused) nowAt.textContent = fmt(player.currentTime);
  }});
  document.getElementById('warn').style.display='none';
  player.addEventListener('error', () =>
    document.getElementById('warn').style.display='block');

  // Correction box per row (persisted); note-row is the sibling after each row.
  function noteRowFor(el) {{
    let r = el.closest('tr'); let sib = r.nextElementSibling;
    return (sib && sib.classList.contains('note-row')) ? sib : null;
  }}
  function refreshNoteBtn(mainRow) {{
    const nr = mainRow.nextElementSibling;
    if (!nr || !nr.classList.contains('note-row')) return;
    const ta = nr.querySelector('textarea.corr');
    const btn = mainRow.querySelector('button.notebtn');
    if (btn) btn.classList.toggle('has-note', !!(ta && ta.value.trim()));
  }}
  document.querySelectorAll('tr.note-row').forEach(nr => {{
    const row = nr.dataset.row;
    const ta = nr.querySelector('textarea.corr');
    const saved = localStorage.getItem(NKEY(row));
    if (saved) {{ ta.value = saved; nr.classList.add('open'); }}
    ta.addEventListener('input', () => {{
      if (ta.value.trim()) localStorage.setItem(NKEY(row), ta.value);
      else localStorage.removeItem(NKEY(row));
      refreshNoteBtn(nr.previousElementSibling);
    }});
  }});
  document.querySelectorAll('button.notebtn').forEach(btn => {{
    btn.addEventListener('click', () => {{
      const nr = noteRowFor(btn);
      if (!nr) return;
      nr.classList.toggle('open');
      if (nr.classList.contains('open')) nr.querySelector('textarea').focus();
    }});
  }});

  // Verdict toggles (persisted). Marking ✘ opens the correction box.
  const STATES = ['', '\\u2714', '\\u2718'];
  const marks = document.querySelectorAll('button.mark');
  function apply(btn, state) {{
    btn.dataset.state = state; btn.textContent = state || '—';
    const row = btn.closest('tr').dataset.row;
    if (state) localStorage.setItem(KEY(row), state);
    else localStorage.removeItem(KEY(row));
  }}
  marks.forEach(btn => {{
    const mainRow = btn.closest('tr');
    const row = mainRow.dataset.row;
    const saved = localStorage.getItem(KEY(row));
    if (saved) apply(btn, saved);
    refreshNoteBtn(mainRow);
    btn.addEventListener('click', () => {{
      const next = STATES[(STATES.indexOf(btn.dataset.state)+1) % STATES.length];
      apply(btn, next);
      if (next === '\\u2718') {{
        const nr = noteRowFor(btn);
        if (nr) {{ nr.classList.add('open'); nr.querySelector('textarea').focus(); }}
      }}
      tally();
    }});
  }});
  function tally() {{
    let ok=0, no=0;
    marks.forEach(b => {{ if(b.dataset.state==='\\u2714') ok++;
      else if(b.dataset.state==='\\u2718') no++; }});
    document.getElementById('tally').innerHTML =
      `<b class="ok">${{ok}} ✔</b> · <b class="no">${{no}} ✘</b> · `+
      `${{marks.length-ok-no}} unmarked`;
  }}
  tally();

  function noteFor(row) {{
    const v = localStorage.getItem(NKEY(row));
    return v ? v.trim() : '';
  }}
  document.getElementById('copyBtn').addEventListener('click', () => {{
    const wrong=[], right=[], other=[];
    marks.forEach(b => {{
      const row = b.closest('tr').dataset.row;
      const st = b.dataset.state, note = noteFor(row);
      if (st === '\\u2718') wrong.push({{row, note}});
      else if (st === '\\u2714') {{ right.push(row); if(note) other.push({{row, note}}); }}
      else if (note) other.push({{row, note}});
    }});
    const L = [`Fact-check ${{DATE}}`, ''];
    L.push('WRONG (✘) — corrections:');
    if (wrong.length) wrong.forEach(w =>
      L.push(`  Row ${{w.row}}: ${{w.note || '(no correction text entered)'}}`));
    else L.push('  none');
    L.push('', `VERIFIED (✔): ${{right.join(', ') || 'none'}}`);
    if (other.length) {{
      L.push('', 'OTHER NOTES:');
      other.forEach(o => L.push(`  Row ${{o.row}}: ${{o.note}}`));
    }}
    const txt = L.join('\\n');
    const out = document.getElementById('copyOut');
    out.style.display='block'; out.value=txt; out.focus(); out.select();
    navigator.clipboard && navigator.clipboard.writeText(txt).catch(()=>{{}});
  }});
  document.getElementById('clearBtn').addEventListener('click', () => {{
    if(!confirm('Clear all verdicts and corrections on this page?')) return;
    marks.forEach(b => apply(b, ''));
    document.querySelectorAll('tr.note-row').forEach(nr => {{
      const ta = nr.querySelector('textarea.corr');
      ta.value=''; localStorage.removeItem(NKEY(nr.dataset.row));
      nr.classList.remove('open');
      refreshNoteBtn(nr.previousElementSibling);
    }});
    tally();
    document.getElementById('copyOut').style.display='none';
  }});
</script>
</body>
</html>
"""

def render_review(paths, date: str) -> pathlib.Path:
    """Render the worksheet for *date*. Returns the written HTML path."""
    src = paths.session(date) / FACTCHECK_NAME
    if not src.exists():
        raise UserError(
            f"no fact-check worksheet at {src}\n"
            f"  It is produced by the distillation step (see CLAUDE.md 1.5)."
        )
    dest = src.with_suffix(".html")   # transcript-distilled.factcheck.html
    dest.write_text(PAGE.format(date=date, body=render(src.read_text(encoding="utf-8"))),
                    encoding="utf-8")
    return dest


def recording_present(paths, date: str) -> bool:
    """The page links the raw audio; warn when it is not beside the worksheet."""
    return (paths.session(date) / "recording.m4a").exists()
