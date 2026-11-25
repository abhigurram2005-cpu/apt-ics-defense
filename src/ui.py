# UI helper module for the APT-ICS Defense Streamlit app
"""Provides a clean CSS theme (light/dark) and reusable HTML components.
All UI strings are escaped where needed; the functions return raw HTML that
Streamlit can render with ``unsafe_allow_html=True``.
"""

from html import escape as e

_BASE_CSS = """
/* Global */
html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
  background-color: var(--bg) !important;
  color: var(--text) !important;
}
[data-testid="stHeader"] {
  background-color: var(--bg) !important;
}
[data-testid="stSidebar"], [data-testid="stSidebarContent"] {
  background-color: var(--sidebar-bg) !important;
  color: var(--text) !important;
  border-right: 1px solid var(--border);
}
.stApp, .stApp p, .stApp li, .stApp td, .stApp th,
.stApp label, .stApp input, .stApp textarea, .stApp span, .stApp div {
  font-family: 'IBM Plex Sans', 'Segoe UI', Verdana, sans-serif;
}
.stApp p, .stApp li, .stApp label, [data-testid="stMarkdownContainer"] p,
[data-testid="stSidebar"] p, [data-testid="stSidebar"] label, [data-testid="stSidebar"] span {
  color: var(--text);
}

/* Headings & links */
.stApp a { color: var(--accent); text-decoration: none; }
.stApp a:hover { text-decoration: underline; }
.stApp h1, .stApp h2, .stApp h3 {
  color: var(--heading) !important;
  font-weight: 700;
  letter-spacing: -0.01em;
}

/* Buttons */
.stButton > button, .stDownloadButton > button {
  background-color: var(--accent) !important;
  color: #FFFFFF !important;
  border: none !important;
  border-radius: 8px !important;
  font-weight: 600 !important;
  padding: 0.45rem 1rem !important;
}
.stButton > button:hover, .stDownloadButton > button:hover {
  opacity: 0.92;
}

/* Inputs & Selectboxes in dark/light mode */
[data-baseweb="select"] > div,
.stTextArea textarea,
.stTextInput input {
  background-color: var(--card-bg) !important;
  color: var(--text) !important;
  border-color: var(--border) !important;
}
[data-testid="stExpander"],
[data-testid="stFileUploaderDropzone"] {
  background-color: var(--card-bg) !important;
  color: var(--text) !important;
  border: 1px solid var(--border) !important;
  border-radius: 10px !important;
}
[data-testid="stExpander"] summary,
[data-testid="stFileUploaderDropzone"] small,
[data-testid="stFileUploaderDropzone"] span {
  color: var(--text) !important;
}

/* Opcode frequency pills */
.pill-row { display: flex; flex-wrap: wrap; gap: 8px; margin: 0.4rem 0 1rem; }
.op-pill {
  background: var(--table-head-bg);
  border: 1px solid var(--border);
  color: var(--text);
  border-radius: 999px;
  padding: 4px 10px;
  font-size: 12.5px;
  font-family: 'IBM Plex Mono', Consolas, monospace;
}

/* Card component */
.card {
  background: var(--card-bg);
  color: var(--text);
  border: 1px solid var(--border);
  border-radius: 12px;
  box-shadow: 0 2px 8px var(--card-shadow);
  padding: 1.25rem;
  margin-bottom: 1.25rem;
}

/* Tables */
table.kv, table.data {
  border-collapse: collapse;
  width: 100%;
  margin: .2rem 0 .4rem;
  font-size: 14.5px;
  color: var(--text);
}
table.kv th, table.kv td,
table.data th, table.data td {
  border: 1px solid var(--border);
  padding: 8px 12px;
  vertical-align: top;
  text-align: left;
  color: var(--text);
}
table.kv th, table.data thead th {
  background: var(--table-head-bg);
  color: var(--heading);
  font-weight: 600;
}
table.data th.num, table.data td.num {
  text-align: right;
}

/* Misc helpers */
.mono   { font-family: 'IBM Plex Mono', Consolas, monospace; font-size: 13.5px; word-break: break-all; }
.bad    { color: var(--danger); font-weight: 600; }
.ok     { color: var(--safe); font-weight: 600; }
.muted  { color: var(--secondary); }
.lede   { font-size: 16px; color: var(--text); line-height: 1.55; }
.note   {
  font-size: 13.5px;
  color: var(--secondary);
  border-left: 3px solid var(--accent);
  padding: 6px 12px;
  background: var(--card-bg);
  border-radius: 0 6px 6px 0;
  margin: 0.6rem 0 1.2rem;
}
.verdict{ margin: .6rem 0; font-size: 16.5px; }
.strip  { display: flex; height: 28px; border: 1px solid var(--border); border-radius: 6px; overflow: hidden; margin: .3rem 0 .25rem; }
.strip span { flex: 1 1 0; }
.cap    { font-size: 13.5px; color: var(--secondary); margin: 0 0 1rem; max-width: 72ch; }

/* KPI Grid */
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 0.9rem;
  margin: 0.8rem 0 1.4rem;
}
.kpi-card {
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 1rem 1.1rem;
  box-shadow: 0 2px 8px var(--card-shadow);
}
.kpi-label { font-size: 12.5px; font-weight: 600; color: var(--secondary); text-transform: uppercase; letter-spacing: 0.04em; }
.kpi-val   { font-size: 24px; font-weight: 700; color: var(--heading); margin: 0.25rem 0 0.15rem; }
.kpi-sub   { font-size: 12.5px; color: var(--secondary); }

/* Confidence bars */
.bar-row { display: flex; align-items: center; gap: 8px; margin: 4px 0; }
.bar-lbl { min-width: 110px; font-weight: 500; }
.bar-track { flex: 1; height: 8px; background: var(--border); border-radius: 999px; overflow: hidden; min-width: 60px; }
.bar-fill { height: 100%; background: var(--accent); border-radius: 999px; }
.bar-score { min-width: 48px; text-align: right; font-size: 12.5px; color: var(--secondary); font-family: 'IBM Plex Mono', Consolas, monospace; }

/* Responsiveness */
@media (max-width: 900px) {
  .kpi-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
@media (max-width: 640px) {
  .stApp h1 { font-size: 25px; }
  .kpi-grid { grid-template-columns: 1fr; }
  table.kv th, table.kv td, table.data th, table.data td { font-size: 13.5px; }
}
"""


def get_css(dark_mode: bool = False) -> str:
    """Return the full stylesheet for either light or dark mode."""
    if dark_mode:
        vars_block = """
:root {
  --bg:            #0F172A;
  --sidebar-bg:    #1E293B;
  --card-bg:       #1E293B;
  --table-head-bg: #0F172A;
  --border:        #334155;
  --text:          #F1F5F9;
  --secondary:     #94A3B8;
  --heading:       #93C5FD;
  --accent:        #3B82F6;
  --safe:          #16A34A;
  --danger:        #DC2626;
  --card-shadow:   rgba(0, 0, 0, 0.35);
}
"""
    else:
        vars_block = """
:root {
  --bg:            #F1F5F9;
  --sidebar-bg:    #FFFFFF;
  --card-bg:       #FFFFFF;
  --table-head-bg: #EFF6FF;
  --border:        #E2E8F0;
  --text:          #0F172A;
  --secondary:     #475569;
  --heading:       #172554;
  --accent:        #2563EB;
  --safe:          #16A34A;
  --danger:        #DC2626;
  --card-shadow:   rgba(15, 23, 42, 0.06);
}
"""
    return vars_block + _BASE_CSS


CSS = get_css(False)


# ---------------------------------------------------------------------
# Visual components
# ---------------------------------------------------------------------

def _hue(i: int) -> str:
    """Stable pastel hue for a given opcode id (used in the strip)."""
    return f"hsl({(i * 137.508) % 360:.0f},58%,{44 if i % 2 else 60}%)"


def strip(tokens):
    """Render a horizontal strip of coloured cells for opcode ids.
    ``tokens`` is an iterable of integers where 0 = padding, 1 = UNK.
    """
    cells = []
    for pos, t in enumerate(map(int, tokens)):
        if t <= 0:
            cells.append('<span style="background:var(--card-bg)"></span>')
        else:
            raw = t - 2
            label = "UNK" if t == 1 else f"opcode id {raw}"
            cells.append(
                f'<span style="background:{_hue(max(raw,0))}" title="position {pos+1}: {label}"></span>'
            )
    return f'<div class="strip">{"".join(cells)}</div>'


def kv(rows):
    """Key-value table – *rows* is a list of ``(label, html)`` tuples.
    Values are assumed to be safe HTML already (e.g. escaped via ``e``).
    """
    body = "".join(
        f"<tr><th>{e(str(k))}</th><td>{v}</td></tr>" for k, v in rows
    )
    return f'<table class="kv">{body}</table>'


def table(header, rows, num_cols=()):
    """Generic data table.
    ``header`` – list of column names.
    ``rows``   – list of rows (each a list of cell strings).
    ``num_cols`` – indices of columns that should be right-aligned (numeric).
    """
    num_set = set(num_cols)
    hdr = "".join(
        f'<th class="{"num" if i in num_set else ""}">{e(str(c))}</th>'
        for i, c in enumerate(header)
    )
    body = "".join(
        "<tr>" + "".join(
            f'<td class="{"num" if i in num_set else ""}">{c}</td>'
            for i, c in enumerate(r)
        ) + "</tr>"
        for r in rows
    )
    return f'<table class="data"><thead><tr>{hdr}</tr></thead><tbody>{body}</tbody></table>'


def status_chip(is_ok: bool, ok_text: str = "Ready", bad_text: str = "Missing") -> str:
    """Return a small status chip – green if *is_ok*, red otherwise."""
    colour, txt = ("#16A34A", ok_text) if is_ok else ("#DC2626", bad_text)
    return (
        f'<span style="background:{colour};color:#FFFFFF;padding:2px 8px;'
        f'border-radius:999px;font-size:12px;font-weight:600;display:inline-block;">'
        f'{e(txt)}</span>'
    )


def card(content: str) -> str:
    """Wrap arbitrary HTML in a card container for visual grouping."""
    return f'<div class="card">{content}</div>'


def candidates(top):
    """Render the top-3 predictions – ``top`` is a list of ``(label, score)``."""
    return "<br>".join(
        f"{e(f)} <span class='muted'>({s:.2f})</span>" for f, s in top
    )


def confidence_bars(top, is_prob: bool = True) -> str:
    """Render top-3 predictions with horizontal confidence bars."""
    if not top:
        return '<span class="muted">none</span>'
    if is_prob:
        pcts = [max(0.0, min(100.0, s * 100.0)) for _, s in top]
    else:
        scores = [s for _, s in top]
        lo, hi = min(scores), max(scores)
        span = (hi - lo) if hi > lo else 1.0
        pcts = [max(12.0, ((s - lo) / span) * 100.0) for s in scores]
    rows = []
    for (label, score), pct in zip(top, pcts):
        rows.append(
            f"<div class='bar-row'>"
            f"<span class='bar-lbl'>{e(label)}</span>"
            f"<div class='bar-track'><div class='bar-fill' style='width:{pct:.1f}%'></div></div>"
            f"<span class='bar-score'>{score:.2f}</span>"
            f"</div>"
        )
    return "".join(rows)


def kpi_row(items) -> str:
    """Render a 4-column KPI card row. *items* is a list of ``(label, value, sub)``."""
    cards = []
    for label, value, sub in items:
        cards.append(
            f"<div class='kpi-card'>"
            f"<div class='kpi-label'>{e(str(label))}</div>"
            f"<div class='kpi-val'>{e(str(value))}</div>"
            f"<div class='kpi-sub'>{e(str(sub))}</div>"
            f"</div>"
        )
    return f"<div class='kpi-grid'>{''.join(cards)}</div>"


def listing(items):
    """Comma-separated list for ATT&CK techniques, sources, etc."""
    return e(", ".join(map(str, items))) if items else '<span class="muted">none recorded</span>'


ok = status_chip(True, ok_text="Match")
bad = status_chip(False, bad_text="Mismatch")


def fmt_time(seconds: float) -> str:
    """Format a duration in seconds to HH:MM:SS (or MM:SS if < 1 hour)."""
    try:
        secs = int(seconds)
        hours, rem = divmod(secs, 3600)
        minutes, secs_final = divmod(rem, 60)
        if hours:
            return f"{hours:02d}:{minutes:02d}:{secs_final:02d}"
        return f"{minutes:02d}:{secs_final:02d}"
    except Exception:
        return "--:--"
