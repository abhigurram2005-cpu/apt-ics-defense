"""HTML/CSS pieces for the dashboard. Pure functions, no Streamlit imports, so they can be tested alone.
Visual reference: plain sample-entry pages such as abuse.ch MalwareBazaar (key/value tables, plain verdict text)
and classic hand-written malware-analysis write-ups. One custom element: the opcode strip."""
from html import escape as e

CSS = """
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;600&family=IBM+Plex+Mono:wght@400&display=swap');
html, body, .stApp, [data-testid="stAppViewContainer"] { background:#fff; }
.stApp, .stApp p, .stApp li, .stApp td, .stApp th, .stApp label, .stApp input, .stApp textarea {
  font-family:'IBM Plex Sans','Segoe UI',Verdana,sans-serif; }
.stApp { color:#202124; font-size:15.5px; line-height:1.55; }
header[data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stDecoration"], #MainMenu, footer { display:none !important; }
.block-container { max-width:920px; padding-top:2.2rem; padding-bottom:4rem; }
.stApp h1 { font-family:'IBM Plex Sans',Verdana,sans-serif; font-size:30px; font-weight:600; letter-spacing:-0.01em; margin:0 0 .4rem; padding:0; }
.stApp h2 { font-size:20px; font-weight:600; margin:2.4rem 0 .7rem; padding:0 0 .3rem; border-bottom:1px solid #C8CCD0; }
.lede { max-width:64ch; margin:.2rem 0 .8rem; }
.note { max-width:64ch; margin:.2rem 0 0; padding-left:.8rem; border-left:3px solid #C8CCD0; color:#444; }
table.kv, table.data { border-collapse:collapse; width:100%; margin:.4rem 0 .8rem; font-size:15px; }
table.kv th, table.kv td, table.data th, table.data td { border:1px solid #C8CCD0; padding:6px 10px; vertical-align:top; text-align:left; }
table.kv th { width:26%; background:#EDF0F3; font-weight:600; }
table.data thead th { background:#EDF0F3; font-weight:600; }
table.data td.num { text-align:right; font-variant-numeric:tabular-nums; }
table.data th.num { text-align:right; }
.mono { font-family:'IBM Plex Mono',Consolas,monospace; font-size:13.5px; word-break:break-all; }
.bad { color:#A61B1B; font-weight:600; }
.ok { color:#202124; font-weight:600; }
.muted { color:#5f6368; }
.verdict { margin:.6rem 0; font-size:16.5px; }
.strip { display:flex; height:28px; border:1px solid #C8CCD0; margin:.3rem 0 .15rem; }
.strip span { flex:1 1 0; }
.cap { font-size:13.5px; color:#5f6368; margin:0 0 1rem; max-width:64ch; }
.stApp a { color:#0B57A4; }
details summary { cursor:pointer; color:#0B57A4; }
@media (max-width:640px){ table.kv th { width:34%; } .stApp h1 { font-size:25px; } }
"""

def _hue(i):
    return f"hsl({(i * 137.508) % 360:.0f},58%,{44 if i % 2 else 60}%)"

def strip(tokens):
    """One cell per opcode. tokens: array of token ids (0 = padding, 2.. = opcode id + 2)."""
    cells = []
    for pos, t in enumerate(int(x) for x in tokens):
        if t <= 0:
            cells.append('<span style="background:#fff"></span>')
        else:
            raw = t - 2
            cells.append(f'<span style="background:{_hue(max(raw, 0))}" title="position {pos + 1}: opcode id {raw}"></span>')
    return '<div class="strip">' + "".join(cells) + "</div>"

def kv(rows):
    """rows: list of (label, html_value). Values are inserted as-is; escape before passing."""
    return '<table class="kv">' + "".join(f"<tr><th>{e(str(k))}</th><td>{v}</td></tr>" for k, v in rows) + "</table>"

def table(header, rows, num_cols=()):
    h = "".join(f'<th class="{"num" if i in num_cols else ""}">{e(str(c))}</th>' for i, c in enumerate(header))
    b = "".join("<tr>" + "".join(f'<td class="{"num" if i in num_cols else ""}">{c}</td>' for i, c in enumerate(r)) + "</tr>" for r in rows)
    return f'<table class="data"><thead><tr>{h}</tr></thead><tbody>{b}</tbody></table>'

def fmt_time(s):
    return f"{s:.1f} s" if s < 60 else f"{s / 60:.1f} min"

def candidates(top):
    return "<br>".join(f"{e(f)} <span class='muted'>({s:.2f})</span>" for f, s in top)

def listing(items):
    return e(", ".join(str(i) for i in items)) if items else '<span class="muted">none recorded</span>'
