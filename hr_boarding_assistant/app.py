import streamlit as st
from kb_loader import get_company_kb, list_companies
from prompt_builder import build_system_prompt
from chat_engine import get_response, parse_optional_pdf

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="HR Policy Assistant",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Session state init ────────────────────────────────────────────────────────
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "system_prompt" not in st.session_state:
    st.session_state.system_prompt = None
if "selected_company" not in st.session_state:
    st.session_state.selected_company = None
if "extra_context" not in st.session_state:
    st.session_state.extra_context = ""
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = True

# ── Theme palettes ────────────────────────────────────────────────────────────
if st.session_state.dark_mode:
    T = {
        "bg":           "#0f1117",
        "sidebar_bg":   "#161b27",
        "card_bg":      "#161b27",
        "card_bg2":     "#1e2436",
        "border":       "#2a2f3e",
        "text":         "#e8e8e8",
        "text_muted":   "#8892a4",
        "text_dim":     "#6b7280",
        "text_dimmer":  "#4b5563",
        "text_dimmest": "#374151",
        "sidebar_text": "#c9d1e0",
        "accent":       "#818cf8",
        "accent_rgb":   "99,102,241",
        "pink_rgb":     "236,72,153",
        "warn_text":    "#c9a84c",
        "hero_grad":    "linear-gradient(135deg,#1a1f2e 0%,#0f1117 50%,#1a1525 100%)",
        "fab_bg":       "#1e2436",
        "fab_shadow":   "rgba(0,0,0,0.4)",
        "toggle_icon":  "☀️",
        "toggle_label": "Light",
    }
else:
    T = {
        "bg":           "#f5f6fa",
        "sidebar_bg":   "#ffffff",
        "card_bg":      "#ffffff",
        "card_bg2":     "#f0f2f8",
        "border":       "#e2e5f0",
        "text":         "#1a1d2e",
        "text_muted":   "#4b5572",
        "text_dim":     "#6b7280",
        "text_dimmer":  "#9ca3af",
        "text_dimmest": "#d1d5db",
        "sidebar_text": "#374151",
        "accent":       "#6366f1",
        "accent_rgb":   "99,102,241",
        "pink_rgb":     "236,72,153",
        "warn_text":    "#92700a",
        "hero_grad":    "linear-gradient(135deg,#eef0ff 0%,#f5f6fa 50%,#fdf2ff 100%)",
        "fab_bg":       "#ffffff",
        "fab_shadow":   "rgba(0,0,0,0.12)",
        "toggle_icon":  "🌙",
        "toggle_label": "Dark",
    }

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@300;400;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

/* Base */
html, body, [data-testid="stAppViewContainer"] {{
    background-color: {T['bg']} !important;
    color: {T['text']} !important;
    font-family: 'Sora', sans-serif;
}}
[data-testid="stSidebar"] {{
    background: {T['sidebar_bg']} !important;
    border-right: 1px solid {T['border']} !important;
}}
[data-testid="stSidebar"] * {{ color: {T['sidebar_text']} !important; }}
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] h4 {{ color: {T['text']} !important; }}
#MainMenu, footer, header {{ visibility: hidden; }}

/* ── Force sidebar always visible ── */
[data-testid="stSidebar"] {{
    display: block !important;
    visibility: visible !important;
    opacity: 1 !important;
    min-width: 260px !important;
    max-width: 320px !important;
    transform: none !important;
}}
[data-testid="stSidebarCollapsedControl"] {{
    display: none !important;
}}

/* ── FAB theme toggle ── */
#theme-fab {{
    position: fixed;
    top: 18px;
    right: 28px;
    z-index: 99999;
    background: {T['fab_bg']};
    border: 1px solid {T['border']};
    border-radius: 50px;
    padding: 8px 18px;
    font-size: 0.82rem;
    font-family: 'Sora', sans-serif;
    font-weight: 600;
    color: {T['text']};
    cursor: pointer;
    box-shadow: 0 4px 18px {T['fab_shadow']};
    transition: transform 0.15s, box-shadow 0.15s;
    display: flex;
    align-items: center;
    gap: 6px;
    text-decoration: none;
    user-select: none;
}}
#theme-fab:hover {{
    transform: translateY(-1px);
    box-shadow: 0 6px 24px {T['fab_shadow']};
}}

/* ── Hero ── */
.hero {{
    background: {T['hero_grad']};
    border: 1px solid {T['border']};
    border-radius: 16px;
    padding: 40px 48px;
    margin-bottom: 28px;
    position: relative;
    overflow: hidden;
}}
.hero::before {{
    content: '';
    position: absolute;
    top: -60px; right: -60px;
    width: 220px; height: 220px;
    background: radial-gradient(circle, rgba({T['accent_rgb']},0.15) 0%, transparent 70%);
    border-radius: 50%;
}}
.hero::after {{
    content: '';
    position: absolute;
    bottom: -40px; left: 30%;
    width: 160px; height: 160px;
    background: radial-gradient(circle, rgba({T['pink_rgb']},0.08) 0%, transparent 70%);
    border-radius: 50%;
}}
.hero-tag {{
    display: inline-block;
    background: rgba({T['accent_rgb']},0.12);
    color: {T['accent']};
    border: 1px solid rgba({T['accent_rgb']},0.3);
    border-radius: 20px;
    padding: 4px 14px;
    font-size: 11px;
    font-family: 'JetBrains Mono', monospace;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin-bottom: 14px;
}}
.hero h1 {{
    font-size: 2.4rem;
    font-weight: 700;
    color: {T['text']};
    margin: 0 0 10px 0;
    line-height: 1.2;
}}
.hero h1 span {{
    background: linear-gradient(90deg, {T['accent']}, #ec4899);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}}
.hero p {{
    color: {T['text_muted']};
    font-size: 0.95rem;
    margin: 0;
    max-width: 560px;
    line-height: 1.6;
}}

/* ── Stats ── */
.stats-row {{
    display: flex;
    gap: 16px;
    margin-bottom: 28px;
}}
.stat-card {{
    background: {T['card_bg']};
    border: 1px solid {T['border']};
    border-radius: 12px;
    padding: 18px 24px;
    flex: 1;
    text-align: center;
}}
.stat-card .num {{
    font-size: 1.6rem;
    font-weight: 700;
    color: {T['accent']};
    font-family: 'JetBrains Mono', monospace;
}}
.stat-card .label {{
    font-size: 0.75rem;
    color: {T['text_dim']};
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-top: 4px;
}}

/* ── Chips label ── */
.chips-label {{
    font-size: 0.78rem;
    color: {T['text_dim']};
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 10px;
    font-family: 'JetBrains Mono', monospace;
}}

/* ── Chat messages ── */
[data-testid="stChatMessage"] {{
    background: {T['card_bg']} !important;
    border: 1px solid {T['border']} !important;
    border-radius: 12px !important;
    margin-bottom: 12px !important;
    padding: 16px !important;
}}
[data-testid="stChatMessage"] p {{ color: {T['text']} !important; }}

/* ── Chat input ── */
[data-testid="stChatInput"] textarea {{
    background: {T['card_bg']} !important;
    border: 1px solid {T['border']} !important;
    border-radius: 12px !important;
    color: {T['text']} !important;
    font-family: 'Sora', sans-serif !important;
}}
[data-testid="stChatInput"] textarea:focus {{
    border-color: {T['accent']} !important;
    box-shadow: 0 0 0 3px rgba({T['accent_rgb']},0.15) !important;
}}

/* ── Selectbox ── */
[data-testid="stSelectbox"] > div > div {{
    background: {T['card_bg2']} !important;
    border: 1px solid {T['border']} !important;
    border-radius: 10px !important;
    color: {T['text']} !important;
}}

/* ── All buttons (accent) ── */
.stButton > button {{
    background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-family: 'Sora', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.82rem !important;
    transition: opacity 0.2s !important;
}}
.stButton > button:hover {{ opacity: 0.85 !important; }}

/* ── Info / warn boxes ── */
.info-box {{
    background: rgba({T['accent_rgb']},0.08);
    border: 1px solid rgba({T['accent_rgb']},0.2);
    border-left: 3px solid {T['accent']};
    border-radius: 8px;
    padding: 12px 16px;
    font-size: 0.82rem;
    color: {T['text_muted']};
    margin-bottom: 20px;
    line-height: 1.5;
}}
.warn-box {{
    background: rgba(245,158,11,0.08);
    border: 1px solid rgba(245,158,11,0.2);
    border-left: 3px solid #f59e0b;
    border-radius: 8px;
    padding: 12px 16px;
    font-size: 0.82rem;
    color: {T['warn_text']};
    margin-bottom: 20px;
}}

/* ── Divider ── */
.custom-divider {{
    border: none;
    border-top: 1px solid {T['border']};
    margin: 20px 0;
}}

/* ── Empty state ── */
.empty-state {{ text-align: center; padding: 60px 20px; }}
.empty-state .icon {{ font-size: 3rem; margin-bottom: 16px; }}
.empty-state h3 {{ color: {T['text_dim']}; font-size: 1.1rem; font-weight: 500; margin-bottom: 8px; }}
.empty-state p {{ font-size: 0.85rem; line-height: 1.6; color: {T['text_dimmer']}; }}

[data-testid="stMarkdownContainer"] p {{ color: {T['text']} !important; }}
</style>
""", unsafe_allow_html=True)

# ── Floating theme toggle FAB (pure HTML form — no Streamlit button needed) ───
# We use a query param trick: clicking the FAB submits ?toggle=1
# Then we read it at the top and flip dark_mode
params = st.query_params
if "toggle" in params:
    st.session_state.dark_mode = not st.session_state.dark_mode
    st.query_params.clear()
    st.rerun()

st.markdown(f"""
<a id="theme-fab" href="?toggle=1">
    {T['toggle_icon']} &nbsp;{T['toggle_label']} Mode
</a>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🏢 HR Bot")
    st.markdown(f"<p style='color:{T['text_dim']};font-size:0.78rem;margin-top:-10px;'>Powered by Gemini 1.5 Flash</p>", unsafe_allow_html=True)
    st.markdown("<hr class='custom-divider'>", unsafe_allow_html=True)

    st.markdown("#### Select Company")
    companies = list_companies()
    display_names = {c: c.replace("_", " ").title() for c in companies}
    options = ["— Select a company —"] + companies

    selected_raw = st.selectbox(
        "Company",
        options,
        format_func=lambda x: "— Select a company —" if x == "— Select a company —" else display_names.get(x, x),
        label_visibility="collapsed"
    )

    if selected_raw != "— Select a company —" and selected_raw != st.session_state.selected_company:
        st.session_state.selected_company = selected_raw
        kb_text = get_company_kb(selected_raw)
        if st.session_state.extra_context:
            kb_text += "\n\n--- ADDITIONAL DOCUMENT ---\n" + st.session_state.extra_context
        st.session_state.system_prompt = build_system_prompt(selected_raw, kb_text)
        st.session_state.chat_history = []
        st.rerun()

    st.markdown("<hr class='custom-divider'>", unsafe_allow_html=True)

    st.markdown("#### Upload Additional Document")
    st.markdown(f"<p style='color:{T['text_dim']};font-size:0.78rem;'>Optional — supplements the built-in knowledge base</p>", unsafe_allow_html=True)
    uploaded_file = st.file_uploader("Upload PDF", type=["pdf"], label_visibility="collapsed")
    if uploaded_file:
        extra_text = parse_optional_pdf(uploaded_file)
        if extra_text and extra_text != st.session_state.extra_context:
            st.session_state.extra_context = extra_text
            if st.session_state.selected_company:
                kb_text = get_company_kb(st.session_state.selected_company)
                kb_text += "\n\n--- ADDITIONAL DOCUMENT ---\n" + extra_text
                st.session_state.system_prompt = build_system_prompt(st.session_state.selected_company, kb_text)
            st.success("Document added to knowledge base.")

    st.markdown("<hr class='custom-divider'>", unsafe_allow_html=True)

    st.markdown("#### Session")
    if st.session_state.selected_company:
        cdisplay = display_names.get(st.session_state.selected_company, st.session_state.selected_company)
        st.markdown(f"<p style='color:{T['accent']};font-size:0.85rem;'>🟢 {cdisplay}</p>", unsafe_allow_html=True)
        st.markdown(f"<p style='color:{T['text_dim']};font-size:0.78rem;'>{len(st.session_state.chat_history)} messages</p>", unsafe_allow_html=True)
    else:
        st.markdown(f"<p style='color:{T['text_dimmer']};font-size:0.82rem;'>No company selected</p>", unsafe_allow_html=True)

    if st.session_state.chat_history:
        if st.button("🗑 Clear Chat"):
            st.session_state.chat_history = []
            st.rerun()

    st.markdown("<hr class='custom-divider'>", unsafe_allow_html=True)
    st.markdown(f"<p style='color:{T['text_dimmest']};font-size:0.72rem;text-align:center;'>Informational use only.<br>No approvals or data processing.</p>", unsafe_allow_html=True)

# ── Main area ─────────────────────────────────────────────────────────────────
if st.session_state.selected_company:
    company_display = st.session_state.selected_company.replace("_", " ").title()

    st.markdown(f"""
    <div class="hero">
        <div class="hero-tag">HR Policy Assistant</div>
        <h1>Ask anything about <span>{company_display}</span></h1>
        <p>Get instant answers on onboarding steps, leave policies, attendance rules, and employee benefits — powered by the official HR knowledge base.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="stats-row">
        <div class="stat-card"><div class="num">6</div><div class="label">Companies</div></div>
        <div class="stat-card"><div class="num">{len(st.session_state.chat_history)}</div><div class="label">Messages</div></div>
        <div class="stat-card"><div class="num">24/7</div><div class="label">Available</div></div>
        <div class="stat-card"><div class="num">0</div><div class="label">Approvals Granted</div></div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div class='chips-label'>Try asking</div>", unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)
    quick_questions = [
        "What are the onboarding steps?",
        "Explain the leave policy",
        "What are the attendance rules?",
        "What benefits are provided?",
    ]
    for col, q in zip([col1, col2, col3, col4], quick_questions):
        with col:
            if st.button(q, use_container_width=True):
                st.session_state.chat_history.append({"role": "user", "content": q})
                with st.spinner("Thinking..."):
                    response = get_response(q, st.session_state.system_prompt, st.session_state.chat_history[:-1])
                st.session_state.chat_history.append({"role": "assistant", "content": response})
                st.rerun()

    st.markdown("<hr class='custom-divider'>", unsafe_allow_html=True)

    for msg in st.session_state.chat_history:
        with st.chat_message("user" if msg["role"] == "user" else "assistant"):
            st.markdown(msg["content"])

    user_input = st.chat_input(f"Ask an HR policy question about {company_display}...")
    if user_input:
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = get_response(user_input, st.session_state.system_prompt, st.session_state.chat_history[:-1])
            st.markdown(response)
        st.session_state.chat_history.append({"role": "assistant", "content": response})

else:
    st.markdown("""
    <div class="hero">
        <div class="hero-tag">HR Policy Assistant</div>
        <h1>Your <span>HR Knowledge</span> Hub</h1>
        <p>Select a company from the sidebar to get instant answers on onboarding, leave policies, attendance rules, and employee benefits.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="stats-row">
        <div class="stat-card"><div class="num">6</div><div class="label">Companies</div></div>
        <div class="stat-card"><div class="num">∞</div><div class="label">Questions</div></div>
        <div class="stat-card"><div class="num">24/7</div><div class="label">Available</div></div>
        <div class="stat-card"><div class="num">0</div><div class="label">HR Tickets Needed</div></div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="info-box">
        👈 <strong>Get started:</strong> Select a company from the sidebar to load its HR knowledge base and start asking questions.
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="warn-box">
        ⚠️ <strong>Informational only:</strong> This bot cannot approve leaves, process payroll, or make HR exceptions.
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="empty-state">
        <div class="icon">🏢</div>
        <h3>No company selected yet</h3>
        <p>Choose from Accenture, Cisco, Google, Infosys,<br>Microsoft, or TCS to get started.</p>
    </div>
    """, unsafe_allow_html=True)
