import streamlit as st
import pandas as pd
import numpy as np
import os
import time
import random
import re
from datetime import datetime
from google import genai
from google.genai import types
import requests

from ai_reliability import AIServiceUnavailable, request_ai_text
from business_logic import (
    calculate_open_store_feasibility,
    score_from_inputs_site as calculate_site_score,
)

# =========================================================
# Page config
# =========================================================
_SUITE_PAGE_TITLES = {
    "open_store": "Open a Store · Small Business Decision Toolkit",
    "operations": "Operations Control Center · Small Business Decision Toolkit",
    "finance": "Financial Analysis · Small Business Decision Toolkit",
}
if "active_suite" not in st.session_state:
    st.session_state.active_suite = "open_store"

st.set_page_config(
    page_title=_SUITE_PAGE_TITLES.get(
        st.session_state.active_suite,
        _SUITE_PAGE_TITLES["open_store"],
    ),
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# =========================================================
# UI: CSS Only (Native Button Transformation)
# =========================================================
st.markdown(
    r"""
<style>
/* =============================
   0) Global Reset & Scroll
   ============================= */
html, body{ height: auto !important; overflow-x: hidden !important; }
div[data-testid="stAppViewContainer"]{ height: auto !important; min-height: 100vh !important; }
.stApp{ height: auto !important; overflow-y: visible !important; }
.block-container{
  width: min(1180px, calc(100% - 2rem)) !important;
  max-width: 1180px !important;
  padding-top: 4.5rem !important;
  padding-bottom: 3rem !important;
}

/* =============================
   1) Background
   ============================= */
.stApp{
  background-image:url("https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=2072&auto=format&fit=crop");
  background-size:cover;
  background-position:center;
  background-attachment:fixed;
}
.stApp::before{
  content:""; position: fixed; inset: 0;
  background: rgba(0,0,0,0.52); pointer-events: none; z-index: 0;
}
div[data-testid="stAppViewContainer"]{ position: relative; z-index: 1; }
div[data-testid="stAppViewContainer"], div[data-testid="stMain"],
div[data-testid="stHeader"], div[data-testid="stToolbar"]{
  background: transparent !important;
}
#MainMenu, [data-testid="stToolbarActions"], .stAppDeployButton{
  visibility: hidden !important;
  display: none !important;
}

/* =============================
   2) Typography
   ============================= */
div[data-testid="stAppViewContainer"] :where(h1,h2,h3,h4,p,label,small,li){
  color:#fff !important; text-shadow: 0 0 6px rgba(0,0,0,0.65);
}
div[data-testid="stCaption"], div[data-testid="stCaption"] *{
  color: rgba(255,255,255,0.55) !important; text-shadow: none !important;
}
.stMarkdown p{ 
  color: rgba(255,255,255,0.88) !important; 
  text-shadow: 0 2px 8px rgba(0,0,0,0.75) !important; 
}
a, a *{ color: rgba(180,220,255,0.95) !important; }

/* =============================
   3) Sidebar Styles
   ============================= */
section[data-testid="stSidebar"]{
  background: rgba(0,0,0,0.85) !important;
  backdrop-filter: blur(16px);
  border-right: 1px solid rgba(255,255,255,0.10);
  z-index: 99999 !important;
}

/* =============================
   ★ 核心：原生按钮整容术 ★
   ============================= */

/* 1) Header 不挡点击，但内部按钮可点 */
header[data-testid="stHeader"] {
  background: transparent !important;
  pointer-events: none !important;
  z-index: 1000000 !important;
}
header[data-testid="stHeader"] > div {
  pointer-events: auto !important;
}

/* 2) 改造原生打开按钮（collapsed 控件） */
[data-testid="stSidebarCollapsedControl"],
[data-testid="stExpandSidebarButton"]{
  position: fixed !important;
  top: 16px !important;
  left: 16px !important;
  z-index: 1000002 !important;

  width: 110px !important;
  height: 44px !important;

  background-color: rgba(0,0,0,0.6) !important;
  border: 1px solid rgba(255,255,255,0.3) !important;
  border-radius: 8px !important;

  display: block !important;
  visibility: visible !important;
  opacity: 1 !important;
  pointer-events: auto !important;
  cursor: pointer !important;
  transition: all 0.2s ease;

  margin: 0 !important;
  padding: 0 !important;
}

/* ✅关键：让真正可点击的 button 覆盖整个盒子 */
[data-testid="stSidebarCollapsedControl"] button,
[data-testid="stExpandSidebarButton"] button{
  position: absolute !important;
  inset: 0 !important;             /* top/right/bottom/left = 0 */
  width: 100% !important;
  height: 100% !important;
  margin: 0 !important;
  padding: 0 !important;

  background: transparent !important;
  border: none !important;

  display: flex !important;
  align-items: center !important;
  justify-content: center !important;

  cursor: pointer !important;
}

/* 隐藏原生 SVG 图标 */
[data-testid="stSidebarCollapsedControl"] button svg,
[data-testid="stSidebarCollapsedControl"] button img,
[data-testid="stExpandSidebarButton"] button svg,
[data-testid="stExpandSidebarButton"] button img{
  display: none !important;
}

/* ✅把“☰ Menu”画到 button 上（点击区域=整个按钮） */
[data-testid="stSidebarCollapsedControl"] button::before,
[data-testid="stExpandSidebarButton"] button::before{
  content: "☰ Menu";
  color: #ffffff !important;
  font-size: 16px !important;
  font-weight: 600 !important;
  font-family: "Source Sans Pro", sans-serif;
  letter-spacing: 0.5px;
}

/* Streamlit 1.50+ uses the button itself as stExpandSidebarButton. */
[data-testid="stExpandSidebarButton"] > *{
  display: none !important;
}
[data-testid="stExpandSidebarButton"]::before{
  content: "☰ Menu";
  color: #ffffff !important;
  font-size: 16px !important;
  font-weight: 600 !important;
  font-family: "Source Sans Pro", sans-serif;
  letter-spacing: 0.5px;
}

/* hover */
[data-testid="stSidebarCollapsedControl"]:hover,
[data-testid="stExpandSidebarButton"]:hover{
  background-color: rgba(0,0,0,0.8) !important;
  border-color: rgba(255,255,255,0.6) !important;
  transform: translateY(1px);
}


/* =============================
   ★ 隐藏展开侧边栏后的关闭按钮 (<) ★
   ============================= */
[data-testid="stSidebarExpandedControl"]{
  display: flex !important;
  opacity: 1 !important;
  pointer-events: auto !important;
}
section[data-testid="stSidebar"] [data-testid="stSidebarHeader"] button{
  display: flex !important;
}

/* =============================
   4) Other Components
   ============================= */
div[data-baseweb="input"], div[data-baseweb="base-input"], div[data-baseweb="select"], div[data-baseweb="textarea"],
div[data-baseweb="input"] > div, div[data-baseweb="base-input"] > div{
  background: rgba(0,0,0,0.33) !important;
  border: 1px solid rgba(255,255,255,0.14) !important;
  border-radius: 12px !important;
  backdrop-filter: blur(8px);
}
.stTextInput input, .stNumberInput input, .stTextArea textarea{
  background: transparent !important;
  color: rgba(255,255,255,0.95) !important;
}
.stTextInput input::placeholder, .stTextArea textarea::placeholder{
  color: rgba(255,255,255,0.50) !important;
}

div[data-baseweb="menu"], div[role="listbox"]{
  background: #ffffff !important;
  border-radius: 8px !important;
}
div[data-baseweb="menu"] *, div[role="listbox"] *{
  color: #111 !important; text-shadow: none !important;
}
div[data-baseweb="menu"] div[role="option"]:hover,
div[role="listbox"] div[role="option"]:hover{ background: #f0f2f6 !important; }
div[data-baseweb="menu"] div[role="option"][aria-selected="true"]{ background: #e6efff !important; }

.card{
  background: rgba(0,0,0,0.32);
  border: 1px solid rgba(255,255,255,0.12);
  border-radius: 16px;
  padding: 14px 16px;
  margin: 8px 0;
  backdrop-filter: blur(10px);
  color: rgba(255,255,255,0.90) !important;
  text-shadow: none !important;
}

.hero-card{
  background: linear-gradient(135deg, rgba(2,132,199,0.80), rgba(15,23,42,0.82));
  border: 1px solid rgba(186,230,253,0.40);
  border-radius: 22px;
  padding: 24px 26px;
  margin: 0 0 18px 0;
  box-shadow: 0 18px 46px rgba(0,0,0,0.34);
  backdrop-filter: blur(14px);
}
.hero-card h1{ margin: 0 0 8px 0 !important; font-size: clamp(2rem, 4vw, 3.25rem) !important; }
.hero-card p{ margin: 0 !important; font-size: 1.08rem; line-height: 1.55; max-width: 820px; }
.hero-points{ display:flex; flex-wrap:wrap; gap:8px; margin-top:16px; }
.hero-chip{
  background: rgba(255,255,255,0.12);
  border: 1px solid rgba(255,255,255,0.22);
  border-radius: 999px;
  padding: 7px 11px;
  color:#fff;
  font-size:.92rem;
  font-weight:700;
}
.trust-card{
  background: rgba(3,105,161,0.22);
  border: 1px solid rgba(125,211,252,0.35);
  border-radius: 14px;
  padding: 13px 15px;
  margin: 10px 0 16px 0;
}
.demo-badge{
  display:inline-flex;
  align-items:center;
  gap:6px;
  background: rgba(245,158,11,0.18);
  border: 1px solid rgba(251,191,36,0.50);
  border-radius:999px;
  padding:6px 10px;
  margin-bottom:10px;
  color:#fef3c7;
  font-size:.9rem;
  font-weight:800;
}

button{
  background: rgba(0,0,0,0.30) !important;
  border: 1px solid rgba(255,255,255,0.16) !important;
  color: rgba(255,255,255,0.95) !important;
  border-radius: 10px !important;
  backdrop-filter: blur(8px);
}
button:hover{ background: rgba(255,255,255,0.15) !important; }

::-webkit-scrollbar{ width:6px; height:6px; }
::-webkit-scrollbar-thumb{ background: rgba(255,255,255,0.25); border-radius:10px; }
::-webkit-scrollbar-track{ background: transparent; }

/* =============================
   Metrics visibility fix (A)
   ============================= */

/* 指标标题 */
div[data-testid="stMetricLabel"] *{
  color: rgba(255,255,255,0.92) !important;
  text-shadow: 0 2px 10px rgba(0,0,0,0.85) !important;
}

/* 指标数值 */
div[data-testid="stMetricValue"] *{
  color: rgba(255,255,255,0.98) !important;
  font-weight: 800 !important;
  text-shadow: 0 2px 14px rgba(0,0,0,0.95) !important;
}

/* 指标 delta（如果有） */
div[data-testid="stMetricDelta"] *{
  text-shadow: 0 2px 10px rgba(0,0,0,0.85) !important;
}

/* =============================
   Markdown table visibility fix
   ============================= */

/* Markdown 表格整体 */
div[data-testid="stMarkdownContainer"] table {
  background: rgba(0,0,0,0.55) !important;
  border-collapse: collapse !important;
  border: 1px solid rgba(255,255,255,0.25) !important;
  border-radius: 12px !important;
  overflow: hidden !important;
  width: 100% !important;
  margin: 12px 0 22px 0 !important;
  box-shadow: 0 10px 30px rgba(0,0,0,0.35) !important;
}

/* 表头 */
div[data-testid="stMarkdownContainer"] thead,
div[data-testid="stMarkdownContainer"] thead tr,
div[data-testid="stMarkdownContainer"] th {
  background: rgba(0,0,0,0.82) !important;
  color: rgba(255,255,255,0.98) !important;
  font-weight: 800 !important;
  text-shadow: 0 2px 10px rgba(0,0,0,0.95) !important;
}

/* 表格内容 */
div[data-testid="stMarkdownContainer"] td {
  background: rgba(0,0,0,0.52) !important;
  color: rgba(255,255,255,0.95) !important;
  font-weight: 550 !important;
  text-shadow: 0 2px 8px rgba(0,0,0,0.9) !important;
}

/* 表格边框 */
div[data-testid="stMarkdownContainer"] th,
div[data-testid="stMarkdownContainer"] td {
  border: 1px solid rgba(255,255,255,0.20) !important;
  padding: 10px 14px !important;
  vertical-align: top !important;
}

/* 表格里的加粗文字 */
div[data-testid="stMarkdownContainer"] table strong,
div[data-testid="stMarkdownContainer"] table b {
  color: #ffffff !important;
  font-weight: 900 !important;
}

/* 表格里的代码/公式 */
div[data-testid="stMarkdownContainer"] table code {
  background: rgba(255,255,255,0.92) !important;
  color: #0f172a !important;
  padding: 2px 6px !important;
  border-radius: 6px !important;
  text-shadow: none !important;
}

/* Markdown 表格外层滚动区域 */
div[data-testid="stMarkdownContainer"] {
  overflow-x: auto !important;
}

/* Dataframe/table fallback visibility */
div[data-testid="stDataFrame"] * {
  color: rgba(255,255,255,0.95) !important;
}


/* =============================
   Open Store segmented progress bar
   ============================= */
.open-step-wrap{
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
  margin: 14px 0 18px 0;
}
.open-step-pill{
  min-height: 42px;
  padding: 10px 12px;
  border: 1px solid rgba(255,255,255,0.20);
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-weight: 800;
  letter-spacing: .2px;
  box-shadow: 0 8px 24px rgba(0,0,0,0.22);
  backdrop-filter: blur(10px);
}
.open-step-badge{
  font-size: 14px;
  line-height: 1;
}
.open-step-text{
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  text-shadow: 0 2px 8px rgba(0,0,0,0.55);
}
@media (max-width: 760px){
  .open-step-wrap{ grid-template-columns: 1fr; }
  .open-step-pill{ justify-content: flex-start; }
  .block-container{
    width: 100% !important;
    max-width: 100% !important;
    padding: 4.25rem 1rem 2rem 1rem !important;
  }
  .stApp{ background-attachment: scroll !important; }
  section[data-testid="stSidebar"]{ width: min(88vw, 320px) !important; }
  div[data-testid="stHorizontalBlock"]{
    flex-wrap: wrap !important;
    gap: .75rem !important;
  }
  div[data-testid="stHorizontalBlock"] > div[data-testid="column"]{
    flex: 1 1 100% !important;
    width: 100% !important;
    min-width: 0 !important;
  }
  .hero-card{ padding: 19px 17px; border-radius: 16px; }
  .hero-card h1{ font-size: 2rem !important; line-height:1.08 !important; }
  .hero-card p{ font-size: 1rem; }
  .hero-points{ display:grid; grid-template-columns:1fr; }
  button, [role="button"]{ min-height:44px !important; }
  div[data-testid="stMetric"]{ min-width: 0 !important; }
  div[data-testid="stDataFrame"]{ overflow-x:auto !important; }
}

</style>
""",
    unsafe_allow_html=True
)

# =========================================================
# Language
# =========================================================
if "lang" not in st.session_state:
    st.session_state.lang = "en"

def t(zh: str, en: str) -> str:
    return zh if st.session_state.lang == "zh" else en

def toggle_language():
    st.session_state.lang = "en" if st.session_state.lang == "zh" else "zh"

# =========================================================
# API Key + client
# =========================================================
API_KEY = ""
try:
    API_KEY = st.secrets.get("GEMINI_API_KEY", "")
except Exception:
    API_KEY = ""

if not API_KEY:
    API_KEY = os.getenv("GEMINI_API_KEY", "")

client = genai.Client(api_key=API_KEY) if API_KEY else None

SYSTEM_POLICY = """
You are the Small Business Decision Assistant built into this SME decision platform.

Rules:
- NEVER mention any underlying model/provider/vendor or internal API names.
- If asked "Who are you?", "What model are you?", "Are you Gemini?" or similar:
  answer: "I'm the Small Business Decision Assistant built into this platform."
- Keep outputs structured and actionable; prefer bullet points, metrics, and next steps.
- If user requests sensitive/illegal help, refuse briefly and offer safe alternatives.
- Never invent local laws, permit requirements, market prices, vendor facts, traffic thresholds, or citations.
- Use only facts supplied by the user or the application. Clearly label all other numbers as estimates or general benchmarks.
- For local regulatory or market claims, add a "Verify with" note naming the appropriate official authority or primary source.
- State the data date when it is provided. If no date or source is available, say that the claim is not yet verified.
- Do not provide legal, tax, investment, or regulated financial advice.
"""

MODEL_CANDIDATES_PRO = [
    # Stable, low-latency models come first so the bounded retry window always
    # reaches production-accessible options before preview models.
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
    "gemini-2.5-pro",
    "gemini-3.1-pro-preview",
    "gemini-3-flash-preview",
]

MODEL_CANDIDATES_FAST = [
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
    "gemini-3-flash-preview",
    "gemini-3.1-flash-lite",
    "gemini-2.5-pro",
]

if "ai_quality" not in st.session_state:
    st.session_state.ai_quality = "pro"

def sanitize_ai_markdown_output(text: str) -> str:
    """
    Clean AI Markdown before display/download.
    Streamlit/Markdown treats dollar signs as math delimiters, which can make
    finance outputs italic, faint, or broken. We use USD instead.
    Also soften legal/accounting conclusions that require evidence beyond
    the uploaded SME workbook.
    """
    if text is None:
        return ""
    out = str(text)

    # Avoid Markdown math rendering caused by $ in currency amounts.
    out = out.replace("$", "USD ")

    # Clean common spacing glitches after replacing currency symbols.
    out = re.sub(r"USD\s+(-?\d)", r"USD \1", out)
    out = re.sub(r"USD\s+([A-Za-z])", r"USD \1", out)

    # Avoid over-legal conclusions. Use liquidity language unless actual legal
    # insolvency/balance-sheet evidence is provided and explicitly discussed.
    replacements = {
        r"\bInsolvency Crisis\b": "Severe Liquidity Risk",
        r"\bInsolvency Risk\b": "Critical Liquidity Risk",
        r"\binsolvency crisis\b": "severe liquidity risk",
        r"\binsolvency risk\b": "critical liquidity risk",
        r"\binsolvency\b": "severe liquidity risk",
        r"\binsolvent\b": "under severe liquidity pressure",
    }
    for pat, repl in replacements.items():
        out = re.sub(pat, repl, out, flags=re.IGNORECASE)

    return out


def ask_ai(user_prompt: str, mode: str = "general", raise_on_failure: bool = False) -> str:
    if not API_KEY or not client:
        error = AIServiceUnavailable(
            code="AI_NOT_CONFIGURED",
            user_message=t(
                "AI 服务尚未配置。您的输入仍已保存，请稍后重试。",
                "The AI service is not configured. Your inputs are still saved; please retry later.",
            ),
        )
        if raise_on_failure:
            raise error
        return error.user_message

    mode_hint = {
        "general": "General Q&A. Be concise and practical.",
        "open_store": "Focus on store-opening decisions: location, setup, launch checklist, risks, and actions.",
        "operations": "Focus on operations: inventory, staffing, SOPs, pricing execution, weekly review loops.",
        "finance": "Focus on financial analysis: cash flow, margins, runway, costs, scenario and controls.",
    }.get(mode, "General Q&A.")

    prompt = f"{SYSTEM_POLICY}\n\nContext:\n- Mode: {mode_hint}\n\nUser:\n{user_prompt}"

    models = MODEL_CANDIDATES_PRO if st.session_state.ai_quality == "pro" else MODEL_CANDIDATES_FAST
    timeout_ms = max(5_000, min(int(os.getenv("AI_REQUEST_TIMEOUT_MS", "30000")), 60_000))
    max_attempts = max(1, min(int(os.getenv("AI_MAX_MODEL_ATTEMPTS", "2")), 5))
    request_config = types.GenerateContentConfig(
        max_output_tokens=4096,
        thinking_config=types.ThinkingConfig(thinking_budget=0),
        http_options=types.HttpOptions(
            timeout=timeout_ms,
            retry_options=types.HttpRetryOptions(attempts=1),
        )
    )

    try:
        response_text = request_ai_text(
            client.models.generate_content,
            models,
            prompt,
            request_config,
            max_attempts=max_attempts,
        )
        return sanitize_ai_markdown_output(response_text)
    except AIServiceUnavailable as error:
        error.user_message = t(
            "AI 服务未能及时完成请求。您的输入仍已保存，请稍后重试。",
            error.user_message,
        )
        if raise_on_failure:
            raise error
        return error.user_message

# =========================================================
# Geocoding (fuzzy + multi provider)
# =========================================================
NOMINATIM_CONTACT_EMAIL = "yy17812367982@gmail.com"
NOMINATIM_UA = f"ProjectB-SME-BI-Platform/1.0 (contact: {NOMINATIM_CONTACT_EMAIL})"
MAPSCO_API_KEY = os.getenv("MAPSCO_API_KEY", "").strip()

def _normalize_query(q: str) -> str:
    q = (q or "").strip()
    q = " ".join(q.split())
    return q

def _fuzzy_queries(q: str):
    q0 = _normalize_query(q)
    if not q0:
        return []
    variants = [q0]

    q1 = q0.replace(",", " ").replace("  ", " ").strip()
    if q1 != q0:
        variants.append(q1)

    if "usa" not in q0.lower() and "united states" not in q0.lower():
        variants.append(q0 + " USA")
        variants.append(q1 + " USA")

    if ("watervliet" in q0.lower()) and ("ny" not in q0.lower()):
        variants.append(q0 + " NY")
        variants.append(q0 + " New York")

    tokens = q1.split()
    nums = [x for x in tokens if any(c.isdigit() for c in x)]
    words = [x for x in tokens if x.isalpha() or x.lower() in ["ct", "st", "ave", "rd", "dr", "blvd", "ny"]]
    loose = " ".join((nums + words)[:12]).strip()
    if loose and loose.lower() != q1.lower():
        variants.append(loose)
        if "usa" not in loose.lower():
            variants.append(loose + " USA")

    seen = set()
    out = []
    for v in variants:
        vv = _normalize_query(v)
        if vv and vv.lower() not in seen:
            seen.add(vv.lower())
            out.append(vv)
    return out

def _request_json(url: str, params: dict, headers: dict, timeout: int = 12):
    r = requests.get(url, params=params, headers=headers, timeout=timeout)
    dbg = {"status": r.status_code, "final_url": r.url, "text_head": (r.text[:260] if isinstance(r.text, str) else "")}
    r.raise_for_status()
    return r.json(), dbg

@st.cache_data(show_spinner=False, ttl=24 * 3600)
def geocode_candidates_multi_fuzzy(query: str, limit: int = 6):
    q = _normalize_query(query)
    if not q:
        return [], {"ok": False, "err": "empty query"}

    headers = {"User-Agent": NOMINATIM_UA}
    queries = _fuzzy_queries(q)

    time.sleep(0.6)

    providers = [{
        "name": "nominatim",
        "url": "https://nominatim.openstreetmap.org/search",
        "build_params": lambda qq: {
            "q": qq,
            "format": "json",
            "addressdetails": 1,
            "limit": int(limit),
            "email": NOMINATIM_CONTACT_EMAIL,
            "accept-language": "en",
        },
    }]

    if MAPSCO_API_KEY:
        providers.append({
            "name": "maps_co",
            "url": "https://geocode.maps.co/search",
            "build_params": lambda qq: {"q": qq, "api_key": MAPSCO_API_KEY},
        })

    last_debug = {"ok": False, "err": "no attempt"}

    for qq in queries:
        for p in providers:
            try:
                params = p["build_params"](qq)
                data, dbg = _request_json(p["url"], params=params, headers=headers, timeout=12)

                out = []
                if p["name"] == "nominatim":
                    if isinstance(data, list):
                        for d in data[:limit]:
                            if "lat" in d and "lon" in d:
                                out.append({
                                    "display_name": d.get("display_name", ""),
                                    "lat": float(d["lat"]),
                                    "lon": float(d["lon"]),
                                })
                else:
                    if isinstance(data, list):
                        for d in data[:limit]:
                            lat = d.get("lat")
                            lon = d.get("lon")
                            name = d.get("display_name") or d.get("label") or ""
                            if lat and lon:
                                out.append({
                                    "display_name": name,
                                    "lat": float(lat),
                                    "lon": float(lon),
                                })

                last_debug = {"ok": True, "provider": p["name"], "query_used": qq, "count": len(out), **dbg}
                if out:
                    return out, last_debug

            except Exception as e:
                last_debug = {"ok": False, "provider": p["name"], "query_used": qq, "err": str(e)}
                if "429" in str(e) or "Too Many Requests" in str(e):
                    time.sleep(1.2 + random.random())
                continue

    return [], last_debug

# =========================================================
# Overpass robust
# =========================================================
OVERPASS_ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.nchc.org.tw/api/interpreter",
]

def _miles_to_meters(mi: float) -> float:
    return float(mi) * 1609.344

def _clamp(x, lo, hi):
    return max(lo, min(hi, x))

def _business_to_competitor_osm_filters(business_type: str):
    bt = (business_type or "").lower()
    if "auto" in bt:
        return [
            '["shop"="car_parts"]',
            '["shop"="tyres"]',
            '["shop"="car_repair"]',
            '["amenity"="car_wash"]',
            '["amenity"="fuel"]'
        ]
    if "convenience" in bt:
        return [
            '["shop"="convenience"]',
            '["shop"="supermarket"]',
            '["shop"="grocery"]'
        ]
    if "coffee" in bt:
        return [
            '["amenity"="cafe"]',
            '["shop"="coffee"]',
            '["amenity"="fast_food"]'
        ]
    if "restaurant" in bt:
        return [
            '["amenity"="restaurant"]',
            '["amenity"="fast_food"]',
            '["amenity"="cafe"]'
        ]
    if "beauty" in bt or "salon" in bt:
        return [
            '["shop"="beauty"]',
            '["shop"="hairdresser"]',
            '["amenity"="spa"]'
        ]
    return [
        '["shop"]',
        '["amenity"="restaurant"]',
        '["amenity"="cafe"]'
    ]

def _overpass_post(query: str, timeout: int = 35):
    headers = {"User-Agent": NOMINATIM_UA}
    last_dbg = {"ok": False, "err": "no attempt"}
    body = query.encode("utf-8")

    for ep in OVERPASS_ENDPOINTS:
        time.sleep(0.25 + random.random() * 0.25)
        try:
            resp = requests.post(ep, data=body, headers=headers, timeout=timeout)
            if resp.status_code != 200:
                last_dbg = {
                    "ok": False,
                    "endpoint": ep,
                    "status": resp.status_code,
                    "text_head": (resp.text[:260] if isinstance(resp.text, str) else "")
                }
                if resp.status_code in (429, 502, 503, 504):
                    continue
                if resp.status_code in (400, 401, 403):
                    return None, last_dbg
                continue

            data = resp.json()
            return data, {"ok": True, "endpoint": ep, "status": resp.status_code}

        except Exception as e:
            last_dbg = {"ok": False, "endpoint": ep, "err": str(e)}
            continue

    return None, last_dbg

@st.cache_data(show_spinner=False, ttl=6*3600)
def estimate_competitors_overpass(lat: float, lon: float, radius_miles: float, business_type: str):
    r = int(_miles_to_meters(radius_miles))
    filters = _business_to_competitor_osm_filters(business_type)

    parts = []
    for f in filters:
        parts.append(f'nwr{f}(around:{r},{lat},{lon});')

    query = f"""
    [out:json][timeout:25];
    (
      {"".join(parts)}
    );
    out center;
    """

    data, dbg = _overpass_post(query, timeout=40)
    if data is None:
        return {"ok": False, "count": None, "sample": [], "debug": dbg}

    elements = data.get("elements", []) or []
    seen = set((e.get("type"), e.get("id")) for e in elements if e.get("type") and e.get("id"))

    sample = []
    for e in elements[:8]:
        tags = e.get("tags", {}) or {}
        name = tags.get("name", "")
        kind = None
        for k in ["shop", "amenity"]:
            if k in tags:
                kind = f"{k}={tags.get(k)}"
                break
        sample.append({"name": name, "kind": kind})

    return {"ok": True, "count": len(seen), "sample": sample, "debug": dbg}

@st.cache_data(show_spinner=False, ttl=6*3600)
def estimate_traffic_proxy_overpass(lat: float, lon: float, radius_miles: float):
    r = int(_miles_to_meters(radius_miles))

    query = f"""
    [out:json][timeout:25];
    (
      way["highway"](around:{r},{lat},{lon});
    );
    out tags;
    """

    data, dbg = _overpass_post(query, timeout=40)
    if data is None:
        return {"ok": False, "roads_count": None, "proxy_score": None, "traffic_est": None, "debug": dbg}

    elements = data.get("elements", []) or []
    weights = {
        "motorway": 10.0,
        "trunk": 8.0,
        "primary": 6.0,
        "secondary": 4.0,
        "tertiary": 2.5,
        "residential": 1.0,
        "unclassified": 1.0,
        "service": 0.6,
        "living_street": 0.5,
    }

    score = 0.0
    cnt = 0
    for e in elements:
        tags = e.get("tags", {}) or {}
        hw = tags.get("highway")
        if not hw:
            continue
        score += weights.get(hw, 0.8)
        cnt += 1

    traffic_est = int(_clamp(1000 + score * 120, 1000, 50000))
    return {"ok": True, "roads_count": cnt, "proxy_score": round(score, 2), "traffic_est": traffic_est, "debug": dbg}

# =========================================================
# Texas default location for Open a Store
# =========================================================
DEFAULT_TEXAS_ADDRESS = "1011 S Congress Ave, Austin, TX 78704"
DEFAULT_TEXAS_LAT = 30.2516
DEFAULT_TEXAS_LON = -97.7499
DEFAULT_TEXAS_LABEL = "South Congress, Austin, TX"

# =========================================================
# State init
# =========================================================
if "username" not in st.session_state:
    st.session_state.username = ""
if "register_msg" not in st.session_state:
    st.session_state.register_msg = ""

def on_username_submit():
    name = (st.session_state.username or "").strip()
    st.session_state.register_msg = t("目前不可注册。", "Currently unavailable to register.") if name else ""

if "open_step" not in st.session_state:
    st.session_state.open_step = 1

if "profile" not in st.session_state:
    st.session_state.profile = {
        "business_type": "Coffee Shop",
        "stage": "Planning",
        "budget": 80000,
        "target_customer": "Local residents, office workers, tourists, and weekend shoppers",
        "differentiator": "Fast specialty coffee + grab-and-go breakfast + local Texas-style snacks",
        "city": "Austin, Texas",
        "notes": ""
    }

if "site" not in st.session_state:
    st.session_state.site = {
        "address": "1011 S Congress Ave, Austin, TX 78704",
        "radius_miles": 1.0,
        "traffic": 28000,
        "competitors": 12,
        "parking": "Medium",
        "rent_level": "High",
        "foot_traffic_source": "Mixed (Transit + Street)",
        "lat": 30.2516,
        "lon": -97.7499,
        "risk_flags": []
    }

# If an older browser session still carries the old Flushing default, move it to the Texas default.
_old_addr = str(st.session_state.site.get("address", "")).lower() if "site" in st.session_state else ""
if ("flushing" in _old_addr) or ("39-01 main st" in _old_addr) or ("11354" in _old_addr):
    st.session_state.site["address"] = DEFAULT_TEXAS_ADDRESS
    st.session_state.site["lat"] = DEFAULT_TEXAS_LAT
    st.session_state.site["lon"] = DEFAULT_TEXAS_LON
    st.session_state.site["traffic"] = 28000
    st.session_state.site["competitors"] = 12
    st.session_state.site["rent_level"] = "High"
    st.session_state.site["parking"] = "Medium"
    st.session_state.site_geo = {"status": "idle", "cands": [], "picked_idx": 0, "debug": {}}

if "inventory" not in st.session_state:
    st.session_state.inventory = {
        "df": None,
        "cash_target_days": 45,
        "supplier_lead_time_days": 7,
        "seasonality": "Winter",
        "notes": ""
    }

if "pricing" not in st.session_state:
    st.session_state.pricing = {
        "strategy": "Competitive",
        "cost": 1.75,
        "planned_price": 5.25,
        "target_margin": 65,
        "competitor_price": 5.50,
        "elasticity": "Medium",
        "notes": ""
    }

# Migrate the original decimal-error demo values for sessions that were already open.
_legacy_cost = float(st.session_state.pricing.get("cost", 0) or 0)
_legacy_competitor = float(st.session_state.pricing.get("competitor_price", 0) or 0)
if abs(_legacy_cost - 100.0) < 0.001 and abs(_legacy_competitor - 135.0) < 0.001:
    st.session_state.pricing.update({
        "cost": 1.75,
        "planned_price": 5.25,
        "target_margin": 65,
        "competitor_price": 5.50,
    })

# Open-a-store launch feasibility inputs.
# This is intentionally lighter than the Operations and Finance suites:
# the goal is pre-launch go/no-go feasibility, not post-launch inventory or financial statement analysis.
if "launch" not in st.session_state:
    st.session_state.launch = {
        # Simplified pre-launch inputs for the 3-page workflow.
        "startup_cost_estimate": 62000.0,
        "monthly_fixed_cost_estimate": 26500.0,
        "expected_monthly_revenue": 52000.0,
        "expected_gross_margin": 62,
        "cash_target_months": 3,
        "funding_available": 80000.0,
        # Legacy/detail fields kept for compatibility with older reports.
        "buildout_cost": 22000.0,
        "licenses_deposits": 8000.0,
        "equipment_cost": 12000.0,
        "initial_inventory_budget": 15000.0,
        "launch_marketing_budget": 5000.0,
        "monthly_rent": 9500.0,
        "monthly_payroll": 12000.0,
        "monthly_utilities": 1800.0,
        "monthly_insurance": 700.0,
        "other_monthly_fixed": 2500.0,
        "notes": ""
    }

_OPEN_STORE_WIDGET_FIELDS = {
    "open_funding_widget": ("launch", "funding_available", 80000.0),
    "open_startup_cost_widget": ("launch", "startup_cost_estimate", 62000.0),
    "open_fixed_cost_widget": ("launch", "monthly_fixed_cost_estimate", 26500.0),
    "open_revenue_widget": ("launch", "expected_monthly_revenue", 52000.0),
    "open_gross_margin_widget": ("launch", "expected_gross_margin", 62),
    "open_cash_target_widget": ("launch", "cash_target_months", 3),
    "open_unit_cost_widget": ("pricing", "cost", 1.75),
    "open_planned_price_widget": ("pricing", "planned_price", 5.25),
    "open_competitor_price_widget": ("pricing", "competitor_price", 5.50),
}
if "outputs" not in st.session_state:
    st.session_state.outputs = {
        "final_open_store": None,
        "open_store_report_md": "",
        "inventory_summary": None,
        "ops_ai_output": "",
        "ops_report_md": "",
        "finance_ai_output": "",
        "finance_report_md": ""
    }

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "open_store_inputs_reviewed" not in st.session_state:
    st.session_state.open_store_inputs_reviewed = False

if "site_geo" not in st.session_state:
    st.session_state.site_geo = {"status": "idle", "cands": [], "picked_idx": 0, "debug": {}}

# =========================================================
# Helpers
# =========================================================
def score_from_inputs_site(traffic: int, competitors: int, rent_level: str, parking: str) -> int:
    return calculate_site_score(traffic, competitors, rent_level, parking)

def inventory_health(df: pd.DataFrame) -> dict:
    df2 = df.copy()
    df2["Total_Value"] = df2["Stock"] * df2["Cost"]
    df2["Months_Of_Cover"] = np.where(df2["Monthly_Sales"] > 0, df2["Stock"] / df2["Monthly_Sales"], np.inf)
    dead = df2[df2["Monthly_Sales"] < df2["Stock"] * 0.1]
    stockout = df2[(df2["Stock"] <= 10) & (df2["Monthly_Sales"] >= 10)]
    total_value = float(df2["Total_Value"].sum())
    dead_value = float(dead["Total_Value"].sum()) if len(dead) else 0.0
    return {
        "df2": df2,
        "total_value": total_value,
        "dead_items": dead,
        "stockout_items": stockout,
        "dead_value": dead_value
    }

def open_store_feasibility_metrics() -> dict:
    """Compute pre-launch metrics from one tested source of truth."""
    return calculate_open_store_feasibility(
        st.session_state.profile,
        st.session_state.site,
        st.session_state.launch,
        st.session_state.pricing,
    )




def clean_currency_for_markdown(text: str) -> str:
    """
    Normalize AI output so Streamlit Markdown does not interpret dollar amounts as LaTeX.
    Also soften over-strong legal/accounting terms for SME demo use.
    """
    if text is None:
        return ""
    text = str(text)

    # Convert common dollar patterns to USD-prefixed amounts.
    # Examples: $803,500 -> USD 803,500; ($86,300) -> (USD 86,300)
    text = re.sub(r"\$\s*([-+]?\d[\d,]*(?:\.\d+)?)", r"USD \1", text)
    text = re.sub(r"USD\s+USD\s+", "USD ", text)

    # Avoid unsupported hard legal/accounting labels in simple SME demo reports.
    replacements = {
        "Insolvency Crisis": "Critical Liquidity Risk",
        "Insolvency Risk": "Severe Liquidity Risk",
        "insolvency crisis": "critical liquidity risk",
        "insolvency risk": "severe liquidity risk",
        "bankruptcy": "severe liquidity pressure",
        "Bankruptcy": "Severe Liquidity Pressure",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)

    return text

def ai_report_open_store(user_question: str = "") -> str:
    p = st.session_state.profile
    s = st.session_state.site
    launch = st.session_state.launch
    pr = st.session_state.pricing
    m = open_store_feasibility_metrics()

    if not m.get("decision_ready", False):
        issues = "\n".join(f"- {item}" for item in m.get("input_errors", []))
        return (
            "# Review Inputs Before Generating a Report\n\n"
            "The application found blocking input errors:\n\n"
            f"{issues}\n\nCorrect these values and generate the report again."
        )

    prompt = f"""
You are producing a professional pre-launch feasibility report for a U.S. small business owner.
Output MUST be Markdown.

Important rules:
- This is a PRE-LAUNCH decision report, not an operations report and not a full financial statement analysis.
- Use only the provided inputs and computed metrics.
- Do not invent Austin laws, permit timelines, rent benchmarks, traffic thresholds, vendor facts, or other local claims.
- If a recommendation depends on local rules or market data, label it "Needs verification" and name the relevant official authority or primary source to check.
- Do not use dollar signs. Use "USD" before amounts to avoid Markdown rendering issues.
- Do not overstate risk. Use "GO", "CAUTION", or "NO-GO" as the launch decision.
- Every key finding must cite at least one specific input or computed number.
- Explicitly disclose any assumption warnings contained in the computed metrics.

Report structure:
# Open-Store Feasibility Report
## 1) Launch Decision
- Decision: GO / CAUTION / NO-GO
- Overall Score, Site Score, Cash Score, Margin Score
- 3 concise reasons

## 2) Key Inputs
Use a table: Business Concept / Location / Launch Budget / Pricing Assumptions.

## 3) Feasibility Analysis
### Location Feasibility
### Launch Budget & Cash Runway
### Margin and Break-even
### Pricing Sanity Check

## 4) Pre-Launch Risk Controls
6 bullets with owner + metric/target.

## 5) 30-Day Pre-Launch Action Plan
10 bullets. Each bullet must be executable and include timing or target.

User question or focus:
{user_question.strip() if user_question and user_question.strip() else "Please evaluate whether this store should be opened, identify the biggest risks, and provide a pre-launch action plan."}

Inputs:
Business Concept: {p}
Location: {s}
Launch Budget Inputs: {launch}
Pricing Inputs: {pr}
Computed Metrics: {m}
"""
    return clean_currency_for_markdown(
        ask_ai(prompt, mode="open_store", raise_on_failure=True)
    )


def normalize_inventory_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize uploaded operations inventory data.
    Required columns: Item, Stock, Cost, Monthly_Sales
    Optional columns: Category, Lead_Time_Days, MOQ, Shelf_Life_Days, Supplier
    """
    df2 = df.copy()
    df2.columns = [str(c).strip() for c in df2.columns]

    required = ["Item", "Stock", "Cost", "Monthly_Sales"]
    missing = [c for c in required if c not in df2.columns]
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(missing)}")

    for col in ["Stock", "Cost", "Monthly_Sales"]:
        df2[col] = pd.to_numeric(df2[col], errors="coerce").fillna(0)

    if "Category" not in df2.columns:
        df2["Category"] = "General"
    if "Lead_Time_Days" not in df2.columns:
        df2["Lead_Time_Days"] = 7
    if "MOQ" not in df2.columns:
        df2["MOQ"] = 1
    if "Shelf_Life_Days" not in df2.columns:
        df2["Shelf_Life_Days"] = 365
    if "Supplier" not in df2.columns:
        df2["Supplier"] = "Not provided"

    for col in ["Lead_Time_Days", "MOQ", "Shelf_Life_Days"]:
        df2[col] = pd.to_numeric(df2[col], errors="coerce").fillna(0)

    df2["Item"] = df2["Item"].astype(str)
    df2["Category"] = df2["Category"].astype(str)
    df2["Supplier"] = df2["Supplier"].astype(str)
    return df2


def operations_inventory_health(df: pd.DataFrame) -> dict:
    """Compute operational inventory diagnostics for SMEs."""
    df2 = normalize_inventory_df(df)
    df2["Total_Value"] = df2["Stock"] * df2["Cost"]
    df2["Daily_Sales"] = df2["Monthly_Sales"] / 30.0
    df2["Months_Of_Cover"] = np.where(df2["Monthly_Sales"] > 0, df2["Stock"] / df2["Monthly_Sales"], np.inf)
    df2["Days_Of_Cover"] = df2["Months_Of_Cover"] * 30.0
    df2["Reorder_Point"] = np.ceil(df2["Daily_Sales"] * df2["Lead_Time_Days"] * 1.30)

    # Preliminary reorder estimate. This is intentionally conservative and should be verified against storage and supplier terms.
    df2["Suggested_Order_Qty"] = np.maximum(np.ceil(df2["Reorder_Point"] + df2["Monthly_Sales"] * 0.50 - df2["Stock"]), 0)
    df2["Suggested_Order_Qty"] = np.where(
        (df2["Suggested_Order_Qty"] > 0) & (df2["MOQ"] > 1),
        np.ceil(df2["Suggested_Order_Qty"] / df2["MOQ"]) * df2["MOQ"],
        df2["Suggested_Order_Qty"]
    )
    df2["Suggested_Order_Value"] = df2["Suggested_Order_Qty"] * df2["Cost"]

    def classify(row):
        if row["Monthly_Sales"] <= 0:
            return "No Sales / Review"
        if row["Months_Of_Cover"] < 0.50 or row["Stock"] <= row["Reorder_Point"]:
            return "Critical Stockout Risk"
        if row["Months_Of_Cover"] < 1.50:
            return "Watchlist"
        if row["Months_Of_Cover"] >= 6.0:
            return "Dead / Overstock"
        if row["Months_Of_Cover"] >= 4.0:
            return "Overstock"
        return "Healthy"

    def action(row):
        status = row["Status"]
        if status == "Critical Stockout Risk":
            return "Reorder immediately; raise safety stock and verify supplier lead time."
        if status == "Watchlist":
            return "Monitor weekly; prepare reorder if demand continues or lead time increases."
        if status == "Overstock":
            return "Pause reorder; use bundles or targeted promotion."
        if status == "Dead / Overstock":
            return "Stop reorder; discount, bundle, return to vendor, or liquidate."
        if status == "No Sales / Review":
            return "Check listing, shelf placement, demand, and discontinuation options."
        return "Maintain normal replenishment rule."

    df2["Status"] = df2.apply(classify, axis=1)
    df2["Suggested_Action"] = df2.apply(action, axis=1)
    df2["Perishable_Risk"] = np.where(
        (df2["Shelf_Life_Days"] > 0) & (df2["Shelf_Life_Days"] <= 21) & (df2["Days_Of_Cover"] > df2["Shelf_Life_Days"]),
        "Perishable Waste Risk",
        ""
    )

    stockout = df2[df2["Status"].eq("Critical Stockout Risk")].copy()
    watchlist = df2[df2["Status"].eq("Watchlist")].copy()
    overstock = df2[df2["Status"].isin(["Overstock", "Dead / Overstock", "No Sales / Review"])].copy()
    perishable = df2[df2["Perishable_Risk"].ne("")].copy()

    total_value = float(df2["Total_Value"].sum())
    slow_value = float(overstock["Total_Value"].sum()) if len(overstock) else 0.0
    stockout_order_value = float(stockout["Suggested_Order_Value"].sum()) if len(stockout) else 0.0
    avg_moc = float(df2.replace([np.inf, -np.inf], np.nan)["Months_Of_Cover"].mean()) if len(df2) else 0.0

    summary = (
        f"Total inventory value: USD {total_value:,.0f}; "
        f"slow-moving/overstock value: USD {slow_value:,.0f}; "
        f"critical stockout-risk items: {len(stockout)}; "
        f"watchlist items: {len(watchlist)}; "
        f"overstock/dead items: {len(overstock)}; "
        f"perishable-risk items: {len(perishable)}; "
        f"average months of cover: {avg_moc:.2f}; "
        f"suggested immediate reorder value: USD {stockout_order_value:,.0f}."
    )

    return {
        "df2": df2,
        "total_value": total_value,
        "slow_value": slow_value,
        "stockout_order_value": stockout_order_value,
        "avg_months_of_cover": avg_moc,
        "stockout_items": stockout,
        "watchlist_items": watchlist,
        "overstock_items": overstock,
        "perishable_items": perishable,
        "summary": summary,
    }


def build_operations_context() -> str:
    inv = st.session_state.inventory
    inv_df = inv.get("df")
    if not isinstance(inv_df, pd.DataFrame):
        return "No inventory data has been uploaded or loaded."

    try:
        health = operations_inventory_health(inv_df)
        df2 = health["df2"]
        display_cols = [
            "Item", "Category", "Stock", "Monthly_Sales", "Cost", "Total_Value",
            "Months_Of_Cover", "Lead_Time_Days", "MOQ", "Shelf_Life_Days",
            "Reorder_Point", "Suggested_Order_Qty", "Suggested_Order_Value", "Status", "Perishable_Risk", "Suggested_Action"
        ]
        display_cols = [c for c in display_cols if c in df2.columns]
        return f"""
Operations inventory summary:
{health['summary']}

Detailed inventory diagnostics:
{df2[display_cols].to_string(index=False)}
"""
    except Exception as e:
        return f"Inventory data is present but could not be analyzed: {e}"


def ai_operations_diagnosis(user_question: str = "") -> str:
    context = build_operations_context()
    prompt = f"""
You are Yangyu's AI assistant for SME operations management.
Output MUST be Markdown.

Rules:
- Use the uploaded inventory diagnostics as the primary evidence.
- Every key finding must cite item names and actual numbers where available.
- Do NOT invent sales, costs, suppliers, spoilage, customer behavior, or demand channels.
- If a metric is unavailable, write "Not available from uploaded data."
- Do NOT use dollar signs. Use "USD" before amounts.
- Focus on operations, not generic business strategy.
- Distinguish critical stockout risk from watchlist risk and overstock risk.
- Suggested order quantities are preliminary estimates; if storage capacity, supplier delivery frequency, or MOQ constraints are unavailable, say they should be confirmed before ordering.
- Proofread the final output for spelling and formatting.

User question:
{user_question if user_question.strip() else 'Please run a full operations diagnosis.'}

Uploaded data and computed operations diagnostics:
{context}

Report structure:
# Operations Diagnosis

## 1) Executive Summary
- 5 bullets.
- Each bullet must include an actual item, count, value, or months-of-cover number.

## 2) Inventory Health Dashboard
Metric | Actual Result | Interpretation
Include total inventory value, slow-moving value, critical stockout-risk count, watchlist count, overstock/dead count, perishable-risk count, average months of cover, and suggested immediate reorder value when available.

## 3) Replenishment Priority
Item | Status | Months of Cover | Suggested Order Qty | Suggested Action
List the most urgent critical stockout/watchlist items first.

## 4) Overstock / Cash-Tied Items
Item | Stock | Monthly Sales | Months of Cover | Cash Tied | Action
List slow-moving or dead-stock items.

## 5) 7-Day Action Plan
- 10 owner-executable actions.
- Each action must include owner + metric/target + timing.

## 6) 30-Day Operating Controls
- Replenishment rule, promotion rule, waste log, supplier review, weekly review rhythm.

## 7) Follow-up Questions
- 5 questions that would materially improve the analysis.
"""
    return clean_currency_for_markdown(ask_ai(prompt, mode="operations"))


def ai_report_operations() -> str:
    ops_ai = st.session_state.outputs.get("ops_ai_output", "")
    context = build_operations_context()
    prompt = f"""
You are producing a professional Operations Report for a U.S. small business owner.
Output MUST be Markdown.

Rules:
- Use uploaded inventory data and computed diagnostics as primary evidence.
- Every recommendation must map to either stockout risk, overstock/cash-tied risk, perishable risk, supplier lead time, MOQ, or weekly operating control.
- Do NOT invent data. If unavailable, say "Not available from uploaded data."
- Do NOT use dollar signs. Use "USD" before amounts.

Uploaded data and computed diagnostics:
{context}

Previous advisor output, if any:
{ops_ai if isinstance(ops_ai, str) and ops_ai.strip() else '[None]'}

Report structure:
# Operations Control Report
## 1) Current Inventory Snapshot
## 2) Critical Stockout Risks
## 3) Overstock and Cash-Tied Items
## 4) Replenishment Rules
## 5) Promotion and Liquidation Rules
## 6) Weekly SOP Checklist
## 7) KPIs to Track
## 8) Next 14 Days Action Plan
"""
    return clean_currency_for_markdown(ask_ai(prompt, mode="operations"))

def ai_report_finance(doc_text: str, focus: str, style: str, question: str) -> str:
    finance_ai = st.session_state.outputs.get("finance_ai_output", "")
    prompt = f"""
You are producing a Finance Analysis Report for a U.S. small business owner.
Output MUST be Markdown.

Critical evidence rules:
- Use the computed metrics and uploaded data excerpts below as the primary evidence.
- Every key finding must cite at least one actual number from the uploaded data or computed metrics.
- Do NOT invent revenue, costs, margins, customer behavior, platform order mix, commissions, or cash balances.
- If a metric cannot be calculated from uploaded data, write: "Not available from uploaded data."
- If using a general industry benchmark, label it clearly as "General benchmark", not as company-specific fact.
- Separate actual-data findings from assumptions and recommendations.
- Do not provide investment, legal, tax, or regulated financial advice. This is business analysis support only.
- Do NOT use dollar signs in the output. Use "USD" before amounts, for example "USD 803,500", to avoid Markdown math rendering issues.
- Do NOT use legal/accounting conclusions such as "insolvency" unless the uploaded data includes sufficient balance-sheet/legal evidence. Use "liquidity risk" or "cash-flow deficit" instead.
- When comparing inventory purchases and COGS, state that differences may reflect timing, beginning/ending inventory, prepayments, or purchasing inefficiency; do not present it as confirmed waste without reconciliation.

Focus={focus}
Style={style}
User question={question if question.strip() else 'None'}

Uploaded data and computed metrics:
{doc_text}

Previous AI output, if any:
{finance_ai if isinstance(finance_ai, str) and finance_ai.strip() else '[None]'}

Report structure:
# Finance Analysis Report

## 1) Executive Summary
- 5 bullets.
- Each bullet must include at least one actual number.

## 2) Actual Data Summary
Include a compact table where available:
Metric | Actual Result | Source/Formula | Interpretation

Required rows if available:
- Total Revenue
- Gross Margin
- Delivery/App Fees Ratio
- Rent Ratio
- Payroll Ratio
- Marketing Ratio
- EBITDA or Estimated Operating Margin
- Net Cash Flow
- Cash Balance Trend

## 3) Diagnosis
Explain why the business is healthy or unhealthy.
Use uploaded numbers, not vague language.

## 4) Risks & Red Flags
- 8 bullets.
- Mark each as either "Actual data risk" or "Benchmark-based concern".

## 5) Action Plan
- 12 bullets.
- Each bullet must include owner + metric/target + timing.

## 6) Follow-up Questions
- 5 questions that would materially improve accuracy.
"""
    return ask_ai(prompt, mode="finance")


def _safe_numeric(series: pd.Series) -> pd.Series:
    """Convert common accounting strings to numeric safely."""
    if series is None:
        return pd.Series(dtype="float64")
    s = series.astype(str).str.replace(",", "", regex=False).str.replace("$", "", regex=False)
    s = s.str.replace("%", "", regex=False).str.replace("(", "-", regex=False).str.replace(")", "", regex=False)
    return pd.to_numeric(s, errors="coerce")


def _fmt_money(x) -> str:
    try:
        if pd.isna(x):
            return "Not available"
        return f"${float(x):,.2f}"
    except Exception:
        return "Not available"


def _fmt_pct(x) -> str:
    try:
        if pd.isna(x):
            return "Not available"
        return f"{float(x):.1%}"
    except Exception:
        return "Not available"


def _find_col(df: pd.DataFrame, aliases: list[str]):
    """Find a column by flexible aliases, ignoring spaces, underscores, hyphens and case."""
    def norm(x):
        return str(x).strip().lower().replace(" ", "").replace("_", "").replace("-", "")
    col_map = {norm(c): c for c in df.columns}
    for a in aliases:
        key = norm(a)
        if key in col_map:
            return col_map[key]
    # partial matching fallback
    for c in df.columns:
        c_norm = norm(c)
        for a in aliases:
            a_norm = norm(a)
            if a_norm and (a_norm in c_norm or c_norm in a_norm):
                return c
    return None


def _build_sheet_preview(df: pd.DataFrame, max_rows: int = 25) -> str:
    if df is None or df.empty:
        return "[Empty sheet]"
    safe_df = df.copy()
    if len(safe_df) > max_rows:
        safe_df = safe_df.head(max_rows)
    return safe_df.to_string(index=False)


def analyze_financial_dataframe(df: pd.DataFrame, sheet_name: str = "Uploaded Data") -> str:
    """
    Compute SME finance metrics before sending the result to AI.
    AI should interpret these metrics, not guess them from raw table text.
    """
    if df is None or df.empty:
        return f"## Sheet: {sheet_name}\n[Empty sheet]\n"

    outputs = []
    outputs.append(f"## Sheet: {sheet_name}")
    outputs.append(f"- Rows: {len(df)}")
    outputs.append(f"- Columns: {', '.join([str(c) for c in df.columns])}")

    revenue_col = _find_col(df, [
        "Revenue", "Total Revenue", "Total_Revenue", "Sales", "Total Sales", "Net Sales",
        "Platform Sales", "Store Sales", "Monthly Revenue"
    ])
    cogs_col = _find_col(df, [
        "COGS", "Cost of Goods Sold", "Cost_of_Goods_Sold", "Cost", "Product Cost", "Ingredient Cost"
    ])
    gross_profit_col = _find_col(df, ["Gross Profit", "Gross_Profit", "GP"])
    delivery_col = _find_col(df, [
        "Delivery App Fees", "Delivery_App_Fees", "Delivery Fees", "Platform Fees", "App Fees",
        "Third Party Fees", "Commission"
    ])
    rent_col = _find_col(df, ["Rent", "Monthly Rent", "Occupancy", "Occupancy Cost"])
    payroll_col = _find_col(df, ["Payroll", "Labor", "Labor Cost", "Staff Cost", "Wages"])
    marketing_col = _find_col(df, ["Marketing", "Marketing Spend", "Ads", "Advertising"])
    other_exp_col = _find_col(df, ["Other Expenses", "Other_Expenses", "Operating Expenses", "Opex"])
    ebitda_col = _find_col(df, ["EBITDA", "Operating Profit", "Operating Income"])
    net_income_col = _find_col(df, ["Net Income", "Net_Income", "Profit", "Net Profit"])
    cashflow_col = _find_col(df, ["Net Cash Flow", "Net_Cash_Flow", "Cash Flow", "Monthly Cash Flow"])
    ending_cash_col = _find_col(df, ["Ending Cash", "Ending_Cash", "Cash Balance", "Ending Cash Balance"])
    month_col = _find_col(df, ["Month", "Date", "Period"])

    metric_lines = []
    ratio_rows = []

    def add_metric(name, value, formula="", interpretation=""):
        ratio_rows.append((name, formula, value, interpretation))

    if revenue_col:
        revenue_series = _safe_numeric(df[revenue_col])
        total_revenue = revenue_series.sum(skipna=True)
        metric_lines.append(f"- Total Revenue: {_fmt_money(total_revenue)}")

        if cogs_col:
            cogs_series = _safe_numeric(df[cogs_col])
            total_cogs = cogs_series.sum(skipna=True)
            gross_profit_calc = total_revenue - total_cogs
            gross_margin_calc = gross_profit_calc / total_revenue if total_revenue else np.nan
            metric_lines.append(f"- Total COGS: {_fmt_money(total_cogs)}")
            metric_lines.append(f"- Calculated Gross Profit: {_fmt_money(gross_profit_calc)}")
            metric_lines.append(f"- Calculated Gross Margin: {_fmt_pct(gross_margin_calc)}")
            add_metric("Gross Margin", "Calculated Gross Profit / Total Revenue", _fmt_pct(gross_margin_calc),
                       "Core profitability after direct costs.")

            gm_series = (revenue_series - cogs_series) / revenue_series.replace(0, np.nan)
            gm_series = gm_series.dropna()
            if len(gm_series) >= 2:
                metric_lines.append(f"- Gross Margin Trend: {_fmt_pct(gm_series.iloc[0])} → {_fmt_pct(gm_series.iloc[-1])}")

        if gross_profit_col:
            gp_series = _safe_numeric(df[gross_profit_col])
            total_gp = gp_series.sum(skipna=True)
            gp_margin = total_gp / total_revenue if total_revenue else np.nan
            metric_lines.append(f"- Reported Gross Profit: {_fmt_money(total_gp)}")
            metric_lines.append(f"- Reported Gross Margin: {_fmt_pct(gp_margin)}")
            add_metric("Reported Gross Margin", "Reported Gross Profit / Total Revenue", _fmt_pct(gp_margin),
                       "Uses the uploaded gross profit column.")

        expense_cols = [
            ("Delivery/App Fees", delivery_col, "Delivery/App Fees / Total Revenue"),
            ("Rent", rent_col, "Rent / Total Revenue"),
            ("Payroll", payroll_col, "Payroll / Total Revenue"),
            ("Marketing", marketing_col, "Marketing / Total Revenue"),
            ("Other Expenses", other_exp_col, "Other Expenses / Total Revenue"),
        ]

        for label, col, formula in expense_cols:
            if col:
                amount = _safe_numeric(df[col]).sum(skipna=True)
                pct = amount / total_revenue if total_revenue else np.nan
                metric_lines.append(f"- {label}: {_fmt_money(amount)} ({_fmt_pct(pct)} of revenue)")
                add_metric(f"{label} Ratio", formula, _fmt_pct(pct), "Shows cost pressure relative to revenue.")

        if ebitda_col:
            ebitda = _safe_numeric(df[ebitda_col]).sum(skipna=True)
            ebitda_margin = ebitda / total_revenue if total_revenue else np.nan
            metric_lines.append(f"- EBITDA: {_fmt_money(ebitda)} ({_fmt_pct(ebitda_margin)} EBITDA margin)")
            add_metric("EBITDA Margin", "EBITDA / Total Revenue", _fmt_pct(ebitda_margin),
                       "Operating cash profitability before financing/tax/depreciation assumptions.")
        else:
            # If EBITDA is not provided, try a rough operating profit from available columns.
            available_expenses = []
            for col in [cogs_col, delivery_col, rent_col, payroll_col, marketing_col, other_exp_col]:
                if col:
                    available_expenses.append(_safe_numeric(df[col]).sum(skipna=True))
            if available_expenses:
                rough_ebitda = total_revenue - sum(available_expenses)
                rough_margin = rough_ebitda / total_revenue if total_revenue else np.nan
                metric_lines.append(f"- Estimated Operating Profit from Available Expense Columns: {_fmt_money(rough_ebitda)} ({_fmt_pct(rough_margin)} margin)")
                add_metric("Estimated Operating Margin", "Revenue - available expense columns / Revenue", _fmt_pct(rough_margin),
                           "Approximate only; depends on uploaded expense columns.")

        if net_income_col:
            ni = _safe_numeric(df[net_income_col]).sum(skipna=True)
            ni_margin = ni / total_revenue if total_revenue else np.nan
            metric_lines.append(f"- Net Income: {_fmt_money(ni)} ({_fmt_pct(ni_margin)} net margin)")
            add_metric("Net Margin", "Net Income / Total Revenue", _fmt_pct(ni_margin), "Bottom-line profitability.")

        if cashflow_col:
            ncf_series = _safe_numeric(df[cashflow_col])
            total_ncf = ncf_series.sum(skipna=True)
            metric_lines.append(f"- Net Cash Flow: {_fmt_money(total_ncf)}")
            add_metric("Net Cash Flow", "Sum of uploaded net cash flow", _fmt_money(total_ncf),
                       "Shows whether cash increased or decreased over the period.")

        if ending_cash_col:
            cash_series = _safe_numeric(df[ending_cash_col]).dropna()
            if len(cash_series) > 0:
                metric_lines.append(f"- Latest Ending Cash: {_fmt_money(cash_series.iloc[-1])}")
                if len(cash_series) >= 2:
                    metric_lines.append(f"- Cash Balance Trend: {_fmt_money(cash_series.iloc[0])} → {_fmt_money(cash_series.iloc[-1])}")
                    add_metric("Cash Balance Change", "Latest ending cash - first ending cash",
                               _fmt_money(cash_series.iloc[-1] - cash_series.iloc[0]),
                               "Shows cash runway deterioration or improvement.")

        if month_col and revenue_col and len(df) >= 2:
            first_rev = revenue_series.dropna().iloc[0] if len(revenue_series.dropna()) else np.nan
            last_rev = revenue_series.dropna().iloc[-1] if len(revenue_series.dropna()) else np.nan
            if pd.notna(first_rev) and pd.notna(last_rev) and first_rev != 0:
                growth = (last_rev / first_rev) - 1
                metric_lines.append(f"- Revenue Trend: {_fmt_money(first_rev)} → {_fmt_money(last_rev)} ({_fmt_pct(growth)} change)")

    else:
        metric_lines.append("- Revenue column not detected. Financial ratios requiring revenue are not available from uploaded data.")

    outputs.append("\n### Computed Metrics")
    outputs.extend(metric_lines)

    if ratio_rows:
        ratio_df = pd.DataFrame(ratio_rows, columns=["Metric", "Formula", "Actual Result", "Interpretation"])
        outputs.append("\n### Metrics/Ratios Table")
        outputs.append(ratio_df.to_string(index=False))

    outputs.append("\n### Data Preview")
    outputs.append(_build_sheet_preview(df, max_rows=25))

    return "\n".join(outputs) + "\n"


def analyze_financial_excel(file) -> str:
    """Read all workbook sheets and compute available metrics for each sheet."""
    try:
        # Important: reset pointer before reading. Streamlit UploadedFile behaves like a file object.
        try:
            file.seek(0)
        except Exception:
            pass
        sheets = pd.read_excel(file, sheet_name=None)
    except Exception as e:
        return f"[Failed to read Excel workbook: {e}]"

    outputs = []
    outputs.append("## Workbook Overview")
    outputs.append(f"- Sheets detected: {', '.join(list(sheets.keys()))}")

    for sheet_name, df in sheets.items():
        outputs.append(analyze_financial_dataframe(df, sheet_name=str(sheet_name)))

    return "\n".join(outputs)


def read_uploaded_to_text(files) -> str:
    """
    Convert uploaded files into evidence-rich text.
    Key upgrade:
    - Excel workbooks: read ALL sheets, compute ratios before AI.
    - CSV: compute ratios directly if financial columns are detected.
    """
    chunks = []
    for f in files:
        name = f.name.lower()
        try:
            if name.endswith(".csv"):
                try:
                    f.seek(0)
                except Exception:
                    pass
                df = pd.read_csv(f)
                chunks.append(f"# File: {f.name}\n")
                chunks.append(analyze_financial_dataframe(df, sheet_name=f.name))
            elif name.endswith(".xlsx") or name.endswith(".xls"):
                chunks.append(f"# File: {f.name}\n")
                chunks.append(analyze_financial_excel(f))
            elif name.endswith(".txt") or name.endswith(".md"):
                try:
                    f.seek(0)
                except Exception:
                    pass
                text = f.read().decode("utf-8", errors="ignore")
                chunks.append(f"# File: {f.name}\n{text[:10000]}\n")
            else:
                chunks.append(f"# File: {f.name}\n[Unsupported file type for text extraction in this version]\n")
        except Exception as e:
            chunks.append(f"# File: {f.name}\n[Failed to parse: {e}]\n")
    return "\n".join(chunks)

# =========================================================
# Sidebar
# =========================================================
def _select_suite():
    st.session_state.active_suite = {
        t("开店（决策流）", "Open a Store"): "open_store",
        t("运营（跑起来）", "Operations"): "operations",
        t("财务（分析）", "Finance"): "finance",
    }[st.session_state.suite_selector]


with st.sidebar:
    st.button(t("🌐 切换语言", "🌐 Switch Language"), on_click=toggle_language)
    st.markdown("---")

    st.markdown("### " + t("功能集合", "Suites"))
    st.radio(
        t("选择功能", "Choose a suite"),
        options=[
            t("开店（决策流）", "Open a Store"),
            t("运营（跑起来）", "Operations"),
            t("财务（分析）", "Finance"),
        ],
        index={"open_store": 0, "operations": 1, "finance": 2}.get(
            st.session_state.active_suite,
            0,
        ),
        label_visibility="collapsed",
        key="suite_selector",
        on_change=_select_suite,
    )

    st.markdown("---")
    st.success(t("🟢 系统在线", "🟢 System Online"))
    st.caption(t(
        "研究原型。请勿上传社会安全号码、税号、银行卡号或密码。",
        "Research prototype. Do not upload Social Security numbers, tax IDs, payment-card data, or passwords."
    ))

# =========================================================
# Header + Top Ask AI
# =========================================================
st.markdown(
    """
    <section class="hero-card">
      <h1>{}</h1>
      <p>{}</p>
      <div class="hero-points">
        <span class="hero-chip">{}</span>
        <span class="hero-chip">{}</span>
        <span class="hero-chip">{}</span>
      </div>
    </section>
    """.format(
        t("在投入资金前，看清你的小生意是否可行", "Know whether your small-business idea can work before you invest"),
        t(
            "用四步梳理选址、启动资金、现金跑道和定价，并生成一份可执行的风险报告。通常约 5 分钟。",
            "Review location, launch funding, cash runway, and pricing in four steps, then get an actionable risk report. Usually about five minutes."
        ),
        t("✓ 4 步可行性检查", "✓ Four-step feasibility check"),
        t("✓ 清晰展示假设与评分", "✓ Transparent assumptions and scores"),
        t("✓ 可下载行动报告", "✓ Downloadable action report"),
    ),
    unsafe_allow_html=True,
)

with st.expander(t("关于本研究原型", "About this research prototype"), expanded=False):
    st.markdown(t(
        "本工具由 Yang Yu 开发，用于研究美国小企业的结构化决策方法。它提供信息与研究支持，不构成法律、税务、投资或受监管的财务建议。联系：yy17812367982@gmail.com",
        "Developed by Yang Yu to research structured decision methods for U.S. small businesses. It provides informational research support, not legal, tax, investment, or regulated financial advice. Contact: yy17812367982@gmail.com"
    ))

if "show_top_chat" not in st.session_state:
    st.session_state.show_top_chat = False
if "top_chat_collapsed" not in st.session_state:
    st.session_state.top_chat_collapsed = True
if "top_submit_id" not in st.session_state:
    st.session_state.top_submit_id = 0
if "last_handled_submit_id" not in st.session_state:
    st.session_state.last_handled_submit_id = -1
if "clear_top_ask_ai" not in st.session_state:
    st.session_state.clear_top_ask_ai = False
if "top_last_status" not in st.session_state:
    st.session_state.top_last_status = ""

with st.expander(t("咨询小企业决策助手", "Ask the Small Business Decision Assistant"), expanded=False):
    if st.session_state.clear_top_ask_ai:
        st.session_state.clear_top_ask_ai = False
        st.session_state["top_ask_ai"] = ""

    with st.form("top_ai_form", clear_on_submit=False):
        colA, colB = st.columns([3, 1])
        with colA:
            user_q = st.text_input(
                t("你想问什么？", "Ask anything..."),
                key="top_ask_ai",
                placeholder=t("例如：这个地址适合开店吗？我该怎么降库存？",
                              "E.g., Is this site viable? How do I reduce dead stock?")
            )
        with colB:
            submitted = st.form_submit_button(t("发送", "Send"), use_container_width=True)

    if submitted:
        st.session_state.top_submit_id += 1

    if submitted and st.session_state.top_submit_id != st.session_state.last_handled_submit_id:
        st.session_state.last_handled_submit_id = st.session_state.top_submit_id
        q = (st.session_state.get("top_ask_ai") or "").strip()
        if q:
            st.session_state.chat_history.append({"role": "user", "text": q})
            mode = st.session_state.active_suite
            with st.spinner(t("分析中…", "Analyzing...")):
                ans = ask_ai(q, mode=mode)
            st.session_state.chat_history.append({"role": "ai", "text": ans})
            st.session_state.clear_top_ask_ai = True
            st.session_state.top_last_status = "ready"
            st.session_state.show_top_chat = True
            st.session_state.top_chat_collapsed = False
            # st.rerun() removed to avoid Streamlit Cloud SessionInfo race

    c1, c2, c3 = st.columns([1.5, 1.2, 6.3])
    with c1:
        if st.session_state.chat_history:
            toggle_label = t("收起回答", "Hide answer") if st.session_state.show_top_chat else t("显示回答", "Show answer")
            if st.button(toggle_label, use_container_width=True):
                st.session_state.show_top_chat = not st.session_state.show_top_chat
                st.session_state.top_chat_collapsed = not st.session_state.show_top_chat
                # st.rerun() removed to avoid Streamlit Cloud SessionInfo race
    with c2:
        if st.session_state.chat_history and st.button(t("清空", "Clear"), use_container_width=True):
            st.session_state.chat_history = []
            st.session_state.show_top_chat = False
            st.session_state.top_chat_collapsed = True
            st.session_state.top_last_status = ""
            # st.rerun() removed to avoid Streamlit Cloud SessionInfo race
    with c3:
        if st.session_state.top_last_status == "ready":
            st.success(t("回答已生成并显示在下方。", "Answer ready and shown below."), icon="✅")

if st.session_state.show_top_chat and st.session_state.chat_history:
    st.markdown("### " + t("对话记录", "Conversation"))
    recent = st.session_state.chat_history[-6:]
    st.markdown("---")
    for m in recent:
        role = m.get("role", "")
        text = (m.get("text") or "")
        safe_text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        if role == "user":
            st.markdown(
                "<div class='card'><b>{}</b><br>{}</div>".format(t("你:", "You:"), safe_text),
                unsafe_allow_html=True
            )
        else:
            ai_label = t("小企业决策助手：", "Small Business Decision Assistant:")
            with st.container(border=True):
                st.markdown(f"**{ai_label}**")
                st.markdown(text)

# =========================================================
# Suite 1: Open a Store
# =========================================================
def render_open_store():
    # Four-page workflow: Concept -> Location -> Budget/Pricing -> Decision/Report.
    if st.session_state.open_step > 4:
        st.session_state.open_step = 4

    # Keyed widgets are updated before this script reruns. Synchronizing them
    # here lets navigation reflect blocking errors immediately, even though the
    # Budget & Pricing controls are rendered below the navigation bar.
    for widget_key, (bucket, field, _default) in _OPEN_STORE_WIDGET_FIELDS.items():
        if widget_key in st.session_state:
            st.session_state[bucket][field] = st.session_state[widget_key]
    st.session_state.profile["budget"] = int(st.session_state.launch["funding_available"])

    st.header(t("开店可行性评估", "Open a Store Feasibility"))
    st.markdown(
        '<span class="demo-badge">🧪 {}</span>'.format(
            t("已预载演示场景", "Preloaded demo scenario")
        ),
        unsafe_allow_html=True,
    )
    st.caption(t(
        "当前字段是 Austin 咖啡店示例，不是你的真实业务数据。请逐项替换；最终报告生成前需要确认。",
        "The current fields are an Austin coffee-shop example, not your business data. Replace each assumption and confirm it before generating a final report."
    ))

    step_titles = [
        t("业务概念", "Concept"),
        t("选址地图", "Location"),
        t("预算定价", "Budget & Pricing"),
        t("结论报告", "Decision & Report"),
    ]
    # Cute segmented progress bar: one colored segment per page, instead of a single continuous bar.
    progress_colors = [
        ("#38bdf8", "#075985"),  # blue: concept
        ("#f59e0b", "#92400e"),  # amber: location
        ("#a78bfa", "#4c1d95"),  # purple: budget/pricing
        ("#34d399", "#064e3b"),  # green: decision/report
    ]
    # Robust segmented progress bar. Keep HTML compact (single-line tags) to avoid Streamlit
    # occasionally rendering part of the markup as literal text.
    import html as _html
    pills = []
    for i, title in enumerate(step_titles, start=1):
        active = i <= st.session_state.open_step
        current = i == st.session_state.open_step
        bg, border = progress_colors[i-1]
        if active:
            style = f"background: linear-gradient(135deg, {bg}, {border}); border-color: rgba(255,255,255,0.45); color:#fff;"
        else:
            style = "background: rgba(255,255,255,0.12); border-color: rgba(255,255,255,0.16); color: rgba(255,255,255,0.62);"
        badge = "●" if current else "✓" if active else "○"
        safe_title = _html.escape(str(title), quote=True)
        pills.append(
            '<div class="open-step-pill" style="{}">'
            '<span class="open-step-badge">{}</span>'
            '<span class="open-step-text">{}/4 · {}</span>'
            '</div>'.format(style, badge, i, safe_title)
        )
    progress_html = '<div class="open-step-wrap">' + ''.join(pills) + '</div>'
    st.markdown(progress_html, unsafe_allow_html=True)

    # Navigation uses callbacks instead of mutating session_state mid-render.
    # This keeps the segmented progress bar and page content perfectly aligned
    # without reintroducing forced st.rerun() calls.
    def _open_store_prev():
        st.session_state.open_step = max(1, int(st.session_state.get("open_step", 1)) - 1)
        st.session_state.open_nav_error = ""

    def _open_store_next():
        current_step = int(st.session_state.get("open_step", 1))
        if current_step == 3:
            check = open_store_feasibility_metrics()
            if not check.get("decision_ready", False):
                st.session_state.open_nav_error = t(
                    "请先修正预算与定价页中的输入错误。",
                    "Correct the input errors on the Budget & Pricing page before continuing."
                )
                return
        st.session_state.open_nav_error = ""
        st.session_state.open_step = min(4, current_step + 1)

    next_is_blocked = bool(
        st.session_state.open_step == 3
        and not open_store_feasibility_metrics().get("decision_ready", False)
    )

    nav1, nav2, nav3 = st.columns([1, 1, 2])
    with nav1:
        st.button(
            t("◀ 上一步", "◀ Back"),
            use_container_width=True,
            disabled=st.session_state.open_step <= 1,
            on_click=_open_store_prev,
            key="open_store_back_btn",
        )
    with nav2:
        if st.session_state.open_step < 4:
            st.button(
                t("下一步 ▶", "Next ▶"),
                use_container_width=True,
                on_click=_open_store_next,
                key="open_store_next_btn",
                disabled=next_is_blocked,
            )
        else:
            st.button(t("已到最后一页", "Final Page"), use_container_width=True, disabled=True)
    with nav3:
        st.caption(t(
            "共 4 段：①业务概念 → ②选址地图 → ③预算定价 → ④结论报告。每段对应一个页面。",
            "4 segments total: ① Concept → ② Location Map → ③ Budget & Pricing → ④ Decision & Report. Each segment matches one page."
        ))

    if st.session_state.get("open_nav_error"):
        st.error(st.session_state.open_nav_error)
    if next_is_blocked:
        st.caption(t(
            "修正下方标出的输入错误后，才可继续。",
            "Fix the input errors highlighted below to continue."
        ))

    def show_location_map(lat, lon, label="Target Location"):
        """Show a cleaner, darker Texas-centered location map with graceful fallback."""
        lat = float(lat)
        lon = float(lon)
        label = label or DEFAULT_TEXAS_LABEL
        try:
            import pydeck as pdk
            df = pd.DataFrame([{
                "lat": lat,
                "lon": lon,
                "label": label,
                "radius": 95,
            }])

            point_layer = pdk.Layer(
                "ScatterplotLayer",
                data=df,
                get_position="[lon, lat]",
                get_radius="radius",
                get_fill_color=[37, 99, 235, 210],
                get_line_color=[255, 255, 255, 230],
                line_width_min_pixels=2,
                pickable=True,
            )
            halo_layer = pdk.Layer(
                "ScatterplotLayer",
                data=df,
                get_position="[lon, lat]",
                get_radius=420,
                get_fill_color=[37, 99, 235, 45],
                get_line_color=[125, 211, 252, 120],
                line_width_min_pixels=1,
                pickable=False,
            )
            text_layer = pdk.Layer(
                "TextLayer",
                data=df,
                get_position="[lon, lat]",
                get_text="label",
                get_size=14,
                get_color=[255, 255, 255, 230],
                get_angle=0,
                get_alignment_baseline="bottom",
                get_pixel_offset=[0, -22],
            )

            view_state = pdk.ViewState(
                latitude=lat,
                longitude=lon,
                zoom=14,
                pitch=42,
                bearing=-12,
            )
            deck = pdk.Deck(
                layers=[halo_layer, point_layer, text_layer],
                initial_view_state=view_state,
                tooltip={"text": "{label}"},
                map_style="https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json",
            )
            st.pydeck_chart(deck, use_container_width=True, height=360)
        except Exception:
            st.map(pd.DataFrame({"lat": [lat], "lon": [lon]}), zoom=14)

    # Page 1: Concept
    if st.session_state.open_step == 1:
        p = st.session_state.profile
        st.subheader(t("第 1 页：业务概念", "Page 1: Business Concept"))
        st.markdown(
            "<div class='card'>" + t(
                "先讲清楚你要开什么店、卖给谁、凭什么赢。选址放到第 2 页，避免一页塞太满。",
                "First define what you are opening, who you serve, and why customers would choose you. Location is on Page 2 to keep this page light."
            ) + "</div>",
            unsafe_allow_html=True
        )

        col1, col2 = st.columns([1, 1])
        with col1:
            p["business_type"] = st.selectbox(
                t("业态", "Business Type"),
                ["Coffee Shop", "Restaurant", "Convenience Store", "Small Retail Store", "Beauty Salon", "Auto Parts Store", "Other"],
                index=["Coffee Shop", "Restaurant", "Convenience Store", "Small Retail Store", "Beauty Salon", "Auto Parts Store", "Other"].index(
                    p.get("business_type", "Coffee Shop") if p.get("business_type", "Coffee Shop") in ["Coffee Shop", "Restaurant", "Convenience Store", "Small Retail Store", "Beauty Salon", "Auto Parts Store", "Other"] else "Coffee Shop"
                )
            )
            p["target_customer"] = st.text_input(
                t("目标客户", "Target Customer"),
                p.get("target_customer", "Downtown office workers, tourists, students, and weekend visitors")
            )
        with col2:
            p["differentiator"] = st.text_input(
                t("差异化", "Differentiator"),
                p.get("differentiator", "Fast specialty coffee, grab-and-go breakfast, and locally inspired snacks")
            )
            p["notes"] = st.text_area(
                t("限制/备注（可选）", "Constraints / Notes (optional)"),
                p.get("notes", ""),
                placeholder=t("例如：只做早餐、缺少全职店长、房东给2个月免租等", "E.g., breakfast only, no full-time manager yet, two months free rent from landlord, etc."),
                height=140
            )

    # Page 2: Location Map
    elif st.session_state.open_step == 2:
        s = st.session_state.site
        st.subheader(t("第 2 页：选址地图", "Page 2: Location Map"))
        st.markdown(
            "<div class='card'>" + t(
                "这里只看选址是否大致成立：地址、客流、竞品、租金压力、停车/可达性。默认点已放到 Austin, Texas。",
                "This page checks whether the location roughly works: address, traffic, competitors, rent pressure, and accessibility. Default location is Austin, Texas."
            ) + "</div>",
            unsafe_allow_html=True
        )

        left, right = st.columns([1, 1.35])
        with left:
            s["address"] = st.text_input(
                t("地址或商圈", "Address or Trade Area"),
                s.get("address", DEFAULT_TEXAS_ADDRESS)
            )
            s["radius_miles"] = st.selectbox(t("半径（英里）", "Radius (miles)"), [0.5, 1.0, 3.0], index=[0.5, 1.0, 3.0].index(s.get("radius_miles", 1.0)))
            s["traffic"] = st.slider(t("客流/车流估计", "Traffic Estimate"), 1000, 50000, int(s.get("traffic", 26000)), step=500)
            s["competitors"] = st.number_input(t("半径内竞品", "Competitors Nearby"), min_value=0, value=int(s.get("competitors", 9)), step=1)
            s["rent_level"] = st.selectbox(t("租金压力", "Rent Pressure"), ["Low", "Medium", "High"], index=["Low", "Medium", "High"].index(s.get("rent_level", "Medium")))
            s["parking"] = st.selectbox(t("停车/可达性", "Parking / Accessibility"), ["Low", "Medium", "High"], index=["Low", "Medium", "High"].index(s.get("parking", "Medium")))
            s["foot_traffic_source"] = st.selectbox(
                t("客流来源", "Foot Traffic Source"),
                ["Mixed (Transit + Street)", "Street Dominant", "Transit Dominant", "Destination Only"],
                index=["Mixed (Transit + Street)", "Street Dominant", "Transit Dominant", "Destination Only"].index(s.get("foot_traffic_source", "Mixed (Transit + Street)"))
            )
            b1, b2 = st.columns([1, 1])
            with b1:
                do_search = st.button("🔎 " + t("定位地址", "Locate Address"), use_container_width=True)
            with b2:
                if st.button(t("德州默认点", "Texas Default"), use_container_width=True):
                    s["address"] = DEFAULT_TEXAS_ADDRESS
                    s["lat"] = DEFAULT_TEXAS_LAT
                    s["lon"] = DEFAULT_TEXAS_LON
                    st.session_state.site_geo = {"status": "idle", "cands": [], "picked_idx": 0, "debug": {}}

        with right:
            if do_search:
                query = (s.get("address") or "").strip()
                cands, dbg = geocode_candidates_multi_fuzzy(query, limit=6)
                st.session_state.site_geo = {"status": "ok" if cands else "fail", "cands": cands, "picked_idx": 0, "debug": dbg}

            geo = st.session_state.site_geo
            cands = geo.get("cands", []) or []
            if geo.get("status") == "ok" and cands:
                labels = [c["display_name"] for c in cands]
                picked_label = st.selectbox(t("选择匹配地址", "Pick matched address"), labels, index=0)
                chosen = cands[labels.index(picked_label)]
                s["lat"], s["lon"] = float(chosen["lat"]), float(chosen["lon"])
                st.caption(t(f"已定位：{s['lat']:.5f}, {s['lon']:.5f}", f"Located: {s['lat']:.5f}, {s['lon']:.5f}"))
            elif geo.get("status") == "fail":
                st.warning(t("地址未定位成功。可继续使用手工指标完成判断。", "Address was not located. You can still proceed using manual metrics."))

            lat = float(s.get("lat", DEFAULT_TEXAS_LAT) or DEFAULT_TEXAS_LAT)
            lon = float(s.get("lon", DEFAULT_TEXAS_LON) or DEFAULT_TEXAS_LON)
            show_location_map(lat, lon, s.get("address", "Target Location"))

        score = score_from_inputs_site(int(s["traffic"]), int(s["competitors"]), s["rent_level"], s["parking"])
        risk_flags = []
        if int(s["competitors"]) > 15:
            risk_flags.append(t("竞品密度偏高", "High competitive density"))
        if s["rent_level"] == "High":
            risk_flags.append(t("租金压力高", "High rent pressure"))
        if s["parking"] == "Low":
            risk_flags.append(t("停车/可达性弱", "Weak parking/accessibility"))
        s["risk_flags"] = risk_flags

        m1, m2, m3, m4 = st.columns(4)
        m1.metric(t("选址评分", "Site Score"), score)
        m2.metric(t("竞品数", "Competitors"), int(s["competitors"]))
        m3.metric(t("客流估计", "Traffic"), int(s["traffic"]))
        m4.metric(t("租金压力", "Rent"), s["rent_level"])
        if risk_flags:
            st.warning(t("选址风险：", "Location risks: ") + "，".join(risk_flags))
        else:
            st.success(t("当前选址输入下没有明显红旗。", "No major location red flags from current inputs."))

    # Page 3: Budget & Pricing
    elif st.session_state.open_step == 3:
        p = st.session_state.profile
        launch = st.session_state.launch
        pr = st.session_state.pricing
        st.subheader(t("第 3 页：预算与定价", "Page 3: Budget & Pricing"))
        st.markdown(
            "<div class='card'>" + t(
                "把细项合并成几个关键假设：启动成本、每月固定成本、预期收入、毛利率和代表性产品定价。别做成会计考试。",
                "This combines details into a few key assumptions: startup cost, monthly fixed cost, expected revenue, gross margin, and representative product pricing. No accounting exam here."
            ) + "</div>",
            unsafe_allow_html=True
        )

        col1, col2 = st.columns([1, 1])
        with col1:
            st.markdown("### " + t("资金与收入假设", "Funding & Revenue Assumptions"))
            launch["funding_available"] = st.number_input(t("可用启动资金", "Available Launch Funding"), min_value=0.0, value=float(launch.get("funding_available", p.get("budget", 80000))), step=1000.0, key="open_funding_widget")
            p["budget"] = int(launch["funding_available"])
            launch["startup_cost_estimate"] = st.number_input(t("预计一次性启动成本", "Estimated One-Time Startup Cost"), min_value=0.0, value=float(launch.get("startup_cost_estimate", 62000)), step=1000.0, key="open_startup_cost_widget")
            launch["monthly_fixed_cost_estimate"] = st.number_input(t("预计每月固定成本", "Estimated Monthly Fixed Cost"), min_value=0.0, value=float(launch.get("monthly_fixed_cost_estimate", 26500)), step=500.0, key="open_fixed_cost_widget")
            launch["expected_monthly_revenue"] = st.number_input(t("预期月收入", "Expected Monthly Revenue"), min_value=0.0, value=float(launch.get("expected_monthly_revenue", 52000)), step=1000.0, key="open_revenue_widget")
            launch["expected_gross_margin"] = st.slider(t("预期毛利率（%）", "Expected Gross Margin (%)"), 10, 90, int(launch.get("expected_gross_margin", 62)), key="open_gross_margin_widget")
            launch["cash_target_months"] = st.slider(t("目标现金跑道（月）", "Target Cash Runway (months)"), 1, 12, int(launch.get("cash_target_months", 3)), key="open_cash_target_widget")

        with col2:
            st.markdown("### " + t("代表性产品定价", "Representative Product Pricing"))
            pr["cost"] = st.number_input(t("单位成本", "Unit Cost"), min_value=0.0, value=float(pr.get("cost", 1.75)), step=0.05, key="open_unit_cost_widget")
            pr["planned_price"] = st.number_input(t("计划售价", "Planned Price"), min_value=0.0, value=float(pr.get("planned_price", 5.25)), step=0.1, key="open_planned_price_widget")
            pr["competitor_price"] = st.number_input(t("竞品价格", "Competitor Price"), min_value=0.0, value=float(pr.get("competitor_price", 5.5)), step=0.1, key="open_competitor_price_widget")
            pr["strategy"] = st.selectbox(
                t("定价策略", "Pricing Strategy"),
                ["Competitive", "Value-based", "Premium", "Penetration"],
                index=["Competitive", "Value-based", "Premium", "Penetration"].index(pr.get("strategy", "Competitive"))
            )
            pr["elasticity"] = st.selectbox(t("价格敏感度", "Price Sensitivity"), ["Low", "Medium", "High"], index=["Low", "Medium", "High"].index(pr.get("elasticity", "Medium")))
            pr["target_margin"] = int(round(((float(pr.get("planned_price", 0)) / float(pr.get("cost", 1))) - 1) * 100)) if float(pr.get("cost", 0) or 0) > 0 else 0
            st.caption(t(f"隐含加成率：{pr['target_margin']}%", f"Implied markup: {pr['target_margin']}%"))
            launch["notes"] = st.text_area(t("备注（可选）", "Notes (optional)"), launch.get("notes", ""), placeholder=t("例如：免租期、供应商账期、设备租赁等", "Free-rent period, supplier credit terms, equipment lease, etc."))

        m = open_store_feasibility_metrics()
        c1, c2, c3, c4 = st.columns(4)
        c1.metric(t("启动成本", "Startup Cost"), f"USD {m['startup_cost']:,.0f}")
        c2.metric(t("现金跑道", "Cash Runway"), f"{m['runway_months']:.1f} mo")
        c3.metric(t("打平收入", "Break-even Revenue"), f"USD {m['breakeven_revenue']:,.0f}" if np.isfinite(m['breakeven_revenue']) else "N/A")
        c4.metric(t("预估月结果", "Monthly Result"), f"USD {m['monthly_profit_after_fixed']:,.0f}")

        c5, c6, c7 = st.columns(3)
        c5.metric(t("资金缺口", "Funding Gap"), f"USD {m['funding_gap']:,.0f}")
        c6.metric(t("计划售价", "Planned Price"), f"USD {m['recommended_price']:,.2f}")
        c7.metric(t("计划毛利率", "Product Margin"), f"{m['implied_margin_pct']:.1f}%")

        if m.get("input_errors"):
            st.error(t("请先修正以下输入：", "Correct these inputs before continuing:") + "\n\n- " + "\n- ".join(m["input_errors"]))
        for warning in m.get("input_warnings", []):
            st.warning(warning)

        if m["funding_gap"] > 0 or m["runway_months"] < launch["cash_target_months"]:
            st.warning(t("现金跑道偏紧：先降低启动成本、谈免租期/账期，或补充启动资金。", "Cash runway is tight: reduce startup cost, negotiate free rent/payment terms, or secure additional funding."))
        else:
            st.success(t("启动资金基本覆盖目标现金跑道。", "Available funding broadly covers the target cash runway."))

    # Page 4: Decision & Report
    else:
        st.subheader(t("第 4 页：结论与报告", "Page 4: Decision & Report"))
        m = open_store_feasibility_metrics()
        decision = m["decision"]
        decision_msg = {
            "GO": t("可以推进，但仍需完成开业前检查清单。", "Proceed, but complete the pre-launch checklist."),
            "CAUTION": t("谨慎推进，先修复主要风险。", "Proceed cautiously and fix the main risks first."),
            "NO-GO": t("暂不建议开店，先重做资金、选址或利润假设。", "Do not launch yet; revisit funding, location, or margin assumptions first."),
            "REVIEW INPUTS": t("当前输入存在错误，系统不会生成决策报告。请返回预算与定价页修正。", "The current inputs contain errors. No decision report will be generated until they are corrected."),
        }.get(decision, "")

        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric(t("最终判断", "Decision"), decision)
        c2.metric(t("总评分", "Overall"), int(m["overall_score"]))
        c3.metric(t("选址", "Site"), int(m["site_score"]))
        c4.metric(t("现金", "Cash"), int(m["cash_score"]))
        c5.metric(t("利润", "Margin"), int(m["margin_score"]))
        if decision == "REVIEW INPUTS":
            st.error(decision_msg)
        else:
            st.info(decision_msg)

        st.markdown("### " + t("核心依据", "Decision Evidence"))
        metric_df = pd.DataFrame([
            {"Metric": "Location Score", "Value": int(m["site_score"]), "Meaning": "Traffic, competition, rent pressure, and accessibility"},
            {"Metric": "Startup Cost", "Value": f"USD {m['startup_cost']:,.0f}", "Meaning": "One-time cost before opening"},
            {"Metric": "Monthly Fixed Cost", "Value": f"USD {m['monthly_fixed_cost']:,.0f}", "Meaning": "Fixed monthly cash burden"},
            {"Metric": "Cash Runway", "Value": f"{m['runway_months']:.1f} months", "Meaning": "Remaining cash after startup costs"},
            {"Metric": "Break-even Revenue", "Value": f"USD {m['breakeven_revenue']:,.0f}" if np.isfinite(m['breakeven_revenue']) else "N/A", "Meaning": "Revenue needed to cover fixed costs"},
            {"Metric": "Unit Cost", "Value": f"USD {m['unit_cost']:,.2f}", "Meaning": "Representative product cost"},
            {"Metric": "Planned Price", "Value": f"USD {m['recommended_price']:,.2f}", "Meaning": "Representative product price"},
            {"Metric": "Product Margin", "Value": f"{m['implied_margin_pct']:.1f}%", "Meaning": "(Price - unit cost) / price"},
            {"Metric": "Expected Business Gross Margin", "Value": f"{m['expected_gross_margin_pct']:.1f}%", "Meaning": "User-provided total-business assumption"},
        ])
        st.dataframe(metric_df, use_container_width=True, hide_index=True)

        with st.expander(t("评分方法", "How the score is calculated"), expanded=False):
            score_df = pd.DataFrame([
                {"Component": "Site", "Score": int(m["site_score"]), "Weight": "35%"},
                {"Component": "Cash", "Score": int(m["cash_score"]), "Weight": "35%"},
                {"Component": "Margin", "Score": int(m["margin_score"]), "Weight": "20%"},
                {"Component": "Competition", "Score": int(m["competition_score"]), "Weight": "10%"},
            ])
            st.dataframe(score_df, use_container_width=True, hide_index=True)
            score_status = t(
                "当前没有阻止最终判断的输入错误。",
                "There are currently no blocking input errors.",
            ) if m.get("decision_ready", False) else t(
                "当前输入错误会阻止最终判断。",
                "Current input errors prevent a final decision.",
            )
            st.caption(t(
                "总分 = 选址×35% + 现金×35% + 利润×20% + 竞争×10%。",
                "Overall = Site×35% + Cash×35% + Margin×20% + Competition×10%.",
            ) + " " + score_status)

        if m["risks"]:
            st.markdown("### " + t("主要风险", "Main Risks"))
            for r in m["risks"]:
                st.warning(r)
        else:
            st.success(t("当前输入下没有明显阻断性风险。", "No obvious blocking risks from current inputs."))

        st.divider()
        st.subheader(t("AI 开店决策报告", "AI Launch Decision Report"))
        st.caption(t(
            "你可以让 AI 围绕一个具体问题生成报告；它会结合前两页的选址、预算、现金跑道和定价假设。",
            "Ask the AI to analyze a specific launch question; it will use the location, budget, cash runway, and pricing assumptions from the previous pages."
        ))
        default_launch_q = (
            "Please evaluate whether I should open this store, identify the biggest risks, "
            "and give me a pre-launch action plan."
        )
        open_store_question = st.text_area(
            t("测试问题 / 分析重点", "Test question / analysis focus"),
            value=st.session_state.get("open_store_question", default_launch_q),
            key="open_store_question",
            height=120
        )
        st.session_state.open_store_inputs_reviewed = st.checkbox(
            t(
                "我已检查所有示例字段，并确认它们现在代表我的业务场景。",
                "I reviewed every demo field and confirm that the inputs now represent my business scenario."
            ),
            value=bool(st.session_state.get("open_store_inputs_reviewed", False)),
            key="open_store_inputs_reviewed_checkbox",
        )
        report_ready = bool(st.session_state.open_store_inputs_reviewed and m.get("decision_ready", False))
        if not report_ready:
            st.caption(t(
                "修正所有输入错误并勾选确认后，才可生成 AI 报告。",
                "Correct all input errors and confirm the assumptions before generating an AI report."
            ))
        report_error = st.session_state.get("open_store_report_error", "")
        if report_error:
            st.error(report_error)
            st.caption(t(
                "您可以直接重试；已填写的业务数据不会丢失。",
                "You can retry now; the business inputs you entered have been preserved."
            ))
        colA, colB = st.columns([1, 1])
        with colA:
            if st.button(
                t(
                    "重试生成开店决策报告" if report_error else "生成开店决策报告",
                    "Retry Launch Decision Report" if report_error else "Generate Launch Decision Report",
                ),
                type="primary",
                use_container_width=True,
                disabled=not report_ready,
            ):
                st.session_state.open_store_report_error = ""
                with st.spinner(t("生成报告中…", "Generating report...")):
                    try:
                        st.session_state.outputs["open_store_report_md"] = ai_report_open_store(open_store_question)
                    except AIServiceUnavailable as error:
                        st.session_state.open_store_report_error = error.user_message
                        st.rerun()
                    except Exception:
                        st.session_state.open_store_report_error = t(
                            "报告暂时无法生成。您的输入仍已保存，请稍后重试。",
                            "The report could not be generated right now. Your inputs are still saved; please retry in a moment.",
                        )
                        st.rerun()
        with colB:
            if st.button(t("清空报告", "Clear Report"), use_container_width=True):
                st.session_state.outputs["open_store_report_md"] = ""
                st.session_state.outputs["final_open_store"] = None
                st.session_state.open_store_report_error = ""

        if st.session_state.outputs.get("open_store_report_md", ""):
            st.markdown(st.session_state.outputs["open_store_report_md"])
            st.download_button(
                label=t("下载 open_store_report.md", "Download open_store_report.md"),
                data=st.session_state.outputs["open_store_report_md"],
                file_name="open_store_report.md",
                mime="text/markdown"
            )


# =========================================================
# Suite 2: Operations
# =========================================================
def render_operations():
    st.header(t("运营控制中心", "Operations Control Center"))

    st.markdown(
        "<div class='card'>{}</div>".format(
            t("这一模块用于把库存、补货、滞销、现金占用和行动清单串起来，帮助小企业做日常运营诊断。",
              "This suite connects inventory, replenishment, overstock, cash tied in stock, and action plans for day-to-day SME operations diagnosis.")
        ),
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div class="trust-card"><b>{}</b><br>{}<br><br><b>{}</b> {}</div>
        """.format(
            t("上传前请阅读", "Before you upload"),
            t(
                "本应用代码不会把上传文件写入数据库或磁盘。只有点击“分析”或“生成报告”后，解析后的内容才会发送到已配置的 Google Gemini API。托管平台和 AI 服务仍可能按各自条款处理数据。",
                "This application does not write uploaded files to a database or disk. Parsed content is sent to the configured Google Gemini API only after you click Analyze or Generate Report. The hosting platform and AI service may still process data under their own terms."
            ),
            t("请勿上传：", "Do not upload:"),
            t(
                "社会安全号码、税号、银行账户或银行卡号、密码、医疗信息，或任何不必要的个人身份信息。",
                "Social Security numbers, tax IDs, bank or payment-card numbers, passwords, medical data, or unnecessary personal identifiers."
            ),
        ),
        unsafe_allow_html=True,
    )

    operations_consent = st.checkbox(
        t(
            "我已删除敏感个人信息，并同意将解析后的运营数据发送给已配置的 AI 服务进行分析。",
            "I removed sensitive personal information and consent to sending parsed operations data to the configured AI service for analysis.",
        ),
        key="operations_ai_consent",
    )
    if not operations_consent:
        st.caption(t(
            "本地库存仪表盘仍可使用；勾选授权后才能运行 AI 诊断或生成 AI 报告。",
            "The local inventory dashboard remains available. Consent is required only for AI diagnosis and AI report generation.",
        ))

    inv = st.session_state.inventory
    if "ops_diagnosis_md" not in st.session_state.outputs:
        st.session_state.outputs["ops_diagnosis_md"] = ""

    st.subheader(t("1. 上传或加载库存运营数据", "1. Upload or Load Operations Inventory Data"))
    st.caption(t(
        "必需字段：Item, Stock, Cost, Monthly_Sales。可选字段：Category, Lead_Time_Days, MOQ, Shelf_Life_Days, Supplier。",
        "Required columns: Item, Stock, Cost, Monthly_Sales. Optional: Category, Lead_Time_Days, MOQ, Shelf_Life_Days, Supplier."
    ))

    colA, colB, colC = st.columns([1, 1.4, 1])
    with colA:
        if st.button(t("加载咖啡店示例数据", "Load café sample data"), key="ops_load_cafe_sample", use_container_width=True):
            sample_data = {
                "Item": [
                    "Milk Gallons", "Paper Cups", "Cup Lids", "Napkins", "Croissants",
                    "Sandwich Packs", "Branded Tumblers", "Tea Leaves", "Pumpkin Spice Syrup", "Bagged Coffee Beans"
                ],
                "Category": [
                    "Perishable", "Packaging", "Packaging", "Packaging", "Perishable",
                    "Perishable", "Merchandise", "Dry Goods", "Seasonal", "Retail"
                ],
                "Stock": [28, 420, 390, 600, 36, 22, 130, 80, 48, 32],
                "Cost": [4.20, 0.08, 0.05, 0.02, 1.15, 2.75, 13.20, 8.40, 9.50, 7.20],
                "Monthly_Sales": [42, 500, 460, 500, 120, 70, 13, 12, 8, 8],
                "Lead_Time_Days": [2, 5, 5, 5, 1, 2, 21, 14, 10, 7],
                "MOQ": [10, 100, 100, 200, 24, 20, 50, 20, 12, 12],
                "Shelf_Life_Days": [7, 365, 365, 365, 3, 4, 999, 365, 180, 120],
                "Supplier": [
                    "Local Dairy", "Packaging Supplier", "Packaging Supplier", "Packaging Supplier", "Bakery",
                    "Kitchen Prep", "Merch Vendor", "Tea Vendor", "Seasonal Vendor", "Roaster"
                ]
            }
            inv["df"] = pd.DataFrame(sample_data)
            st.session_state.outputs["ops_ai_output"] = ""
            st.session_state.outputs["ops_diagnosis_md"] = ""
            # st.rerun() removed to avoid Streamlit Cloud SessionInfo race

    with colB:
        uploaded = st.file_uploader(
            t("上传 CSV 库存表", "Upload inventory CSV"),
            type=["csv"],
            key="ops_control_csv"
        )
        if uploaded is not None:
            try:
                inv["df"] = pd.read_csv(uploaded)
                st.session_state.outputs["ops_ai_output"] = ""
                st.session_state.outputs["ops_diagnosis_md"] = ""
                st.success(t("已读取 CSV。", "CSV loaded."))
                # st.rerun() removed to avoid Streamlit Cloud SessionInfo race
            except Exception as e:
                st.error(t(f"CSV 读取失败：{e}", f"Failed to read CSV: {e}"))

    with colC:
        if st.button(t("清空运营数据", "Clear operations data"), use_container_width=True):
            inv["df"] = None
            st.session_state.outputs["ops_ai_output"] = ""
            st.session_state.outputs["ops_report_md"] = ""
            st.session_state.outputs["ops_diagnosis_md"] = ""
            # st.rerun() removed to avoid Streamlit Cloud SessionInfo race

    if inv.get("df") is None:
        st.info(t("请先加载示例数据或上传 CSV。", "Load sample data or upload a CSV first."))
        return

    try:
        health = operations_inventory_health(inv["df"])
        df2 = health["df2"]
        st.session_state.outputs["inventory_summary"] = health["summary"]
    except Exception as e:
        st.error(t(f"库存数据结构不符合要求：{e}", f"Inventory data format error: {e}"))
        return

    st.subheader(t("2. 库存健康仪表盘", "2. Inventory Health Dashboard"))
    m1, m2, m3, m4 = st.columns(4)
    m1.metric(t("库存总价值", "Total Inventory Value"), f"USD {health['total_value']:,.0f}")
    m2.metric(t("慢动销/积压金额", "Slow-Moving Value"), f"USD {health['slow_value']:,.0f}")
    m3.metric(t("缺货风险 SKU", "Stockout-Risk SKUs"), len(health["stockout_items"]))
    m4.metric(t("平均覆盖月数", "Avg. Months Cover"), f"{health['avg_months_of_cover']:.2f}")

    m5, m6, m7, m8 = st.columns(4)
    m5.metric(t("积压/滞销 SKU", "Overstock/Dead SKUs"), len(health["overstock_items"]))
    m6.metric(t("易腐风险 SKU", "Perishable-Risk SKUs"), len(health["perishable_items"]))
    m7.metric(t("建议即时补货额", "Immediate Reorder Value"), f"USD {health['stockout_order_value']:,.0f}")
    cash_tied_ratio = (health["slow_value"] / health["total_value"] * 100.0) if health["total_value"] else 0.0
    m8.metric(t("库存现金占压率", "Cash-Tied Ratio"), f"{cash_tied_ratio:.1f}%")

    st.markdown("#### " + t("运营诊断表", "Operations Diagnostic Table"))
    display_cols = [
        "Item", "Category", "Stock", "Monthly_Sales", "Cost", "Total_Value",
        "Months_Of_Cover", "Lead_Time_Days", "MOQ", "Shelf_Life_Days",
        "Reorder_Point", "Suggested_Order_Qty", "Suggested_Order_Value", "Status", "Perishable_Risk", "Suggested_Action"
    ]
    display_cols = [c for c in display_cols if c in df2.columns]
    st.dataframe(df2[display_cols], use_container_width=True)

    tab1, tab2, tab3 = st.tabs([
        t("补货优先级", "Replenishment Priority"),
        t("积压/促销处理", "Overstock & Promotion"),
        t("AI 运营诊断", "AI Operations Diagnosis")
    ])

    with tab1:
        st.subheader(t("补货优先级", "Replenishment Priority"))
        priority = df2[df2["Status"].isin(["Stockout Risk", "Watchlist"])].copy()
        if len(priority) == 0:
            st.success(t("当前没有明显缺货风险。", "No obvious stockout risk based on current data."))
        else:
            priority = priority.sort_values(["Status", "Months_Of_Cover"], ascending=[False, True])
            st.dataframe(priority[[
                "Item", "Category", "Stock", "Monthly_Sales", "Months_Of_Cover", "Lead_Time_Days",
                "Reorder_Point", "Suggested_Order_Qty", "Suggested_Order_Value", "Suggested_Action"
            ]], use_container_width=True)
            st.warning(t(
                "优先处理低覆盖月数和交期较长的 SKU，避免旺日断货。",
                "Prioritize low-cover and longer-lead-time SKUs to avoid busy-day stockouts."
            ))

    with tab2:
        st.subheader(t("积压/促销处理", "Overstock & Promotion"))
        overstock = health["overstock_items"].copy()
        if len(overstock) == 0:
            st.success(t("当前没有明显积压或滞销品。", "No obvious overstock or dead-stock items."))
        else:
            overstock = overstock.sort_values(["Months_Of_Cover", "Total_Value"], ascending=[False, False])
            st.dataframe(overstock[[
                "Item", "Category", "Stock", "Monthly_Sales", "Months_Of_Cover", "Total_Value", "MOQ", "Suggested_Action"
            ]], use_container_width=True)
            st.info(t(
                "对高覆盖月数 SKU 暂停补货，并通过捆绑、折扣、退货或清仓释放现金。",
                "Pause replenishment for high-cover SKUs and release cash through bundles, discounts, returns, or liquidation."
            ))

    with tab3:
        st.subheader(t("AI 运营诊断", "AI Operations Diagnosis"))
        default_q = t(
            "请基于上传的库存数据，分析缺货风险、积压库存、现金占用，并给出7天行动计划。",
            "Please analyze stockout risk, overstock, cash tied in inventory, and provide a 7-day action plan based on the uploaded inventory data."
        )
        q = st.text_area(
            t("描述你的运营问题", "Describe your operations problem"),
            value=st.session_state.get("ops_question", default_q),
            key="ops_question",
            height=120
        )
        c1, c2 = st.columns([1, 1])
        with c1:
            if st.button(
                t("运行运营诊断", "Run Operations Diagnosis"),
                type="primary",
                use_container_width=True,
                disabled=not operations_consent,
            ):
                with st.spinner(t("分析中…", "Analyzing...")):
                    out = ai_operations_diagnosis(q)
                st.session_state.outputs["ops_ai_output"] = out
                st.session_state.outputs["ops_diagnosis_md"] = out
                # st.rerun() removed to avoid Streamlit Cloud SessionInfo race
        with c2:
            if st.button(t("清空诊断", "Clear Diagnosis"), use_container_width=True):
                st.session_state.outputs["ops_ai_output"] = ""
                st.session_state.outputs["ops_diagnosis_md"] = ""
                # st.rerun() removed to avoid Streamlit Cloud SessionInfo race

        if st.session_state.outputs.get("ops_diagnosis_md", ""):
            st.markdown(st.session_state.outputs["ops_diagnosis_md"])

    st.divider()
    st.subheader(t("可交付物：运营报告", "Deliverable: Operations Report"))
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button(
            t("生成运营报告", "Generate Operations Report"),
            type="primary",
            use_container_width=True,
            disabled=not operations_consent,
        ):
            with st.spinner(t("生成中…", "Generating...")):
                st.session_state.outputs["ops_report_md"] = ai_report_operations()
            # st.rerun() removed to avoid Streamlit Cloud SessionInfo race
    with col2:
        if st.button(t("清空运营报告", "Clear Operations Report"), use_container_width=True):
            st.session_state.outputs["ops_report_md"] = ""
            # st.rerun() removed to avoid Streamlit Cloud SessionInfo race

    if st.session_state.outputs.get("ops_report_md", ""):
        st.markdown(st.session_state.outputs["ops_report_md"])
        st.download_button(
            label=t("下载 operations_report.md", "Download operations_report.md"),
            data=st.session_state.outputs["ops_report_md"],
            file_name="operations_report.md",
            mime="text/markdown"
        )

# =========================================================
# Suite 3: Finance
# =========================================================
def render_finance():
    st.header(t("财务分析（上传资料 → AI 指导）", "Financial Analysis (Upload docs → AI guidance)"))

    st.markdown(
        "<div class='card'>{}</div>".format(
            t("上传你自己的财务资料（CSV/XLSX/TXT），AI 会做结构化分析：现金流、利润率、成本项、风险点、下一步动作。",
              "Upload your own finance materials (CSV/XLSX/TXT). AI will produce a structured analysis: cash flow, margins, costs, risks, next actions.")
        ),
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div class="trust-card"><b>{}</b><br>{}<br><br><b>{}</b> {}</div>
        """.format(
            t("上传前请阅读", "Before you upload"),
            t(
                "本应用代码不会把上传文件写入数据库或磁盘。只有点击“分析”或“生成报告”后，解析后的内容才会发送到已配置的 Google Gemini API。托管平台和 AI 服务仍可能按各自条款处理数据。",
                "This application does not write uploaded files to a database or disk. Parsed content is sent to the configured Google Gemini API only after you click Analyze or Generate Report. The hosting platform and AI service may still process data under their own terms."
            ),
            t("请勿上传：", "Do not upload:"),
            t(
                "社会安全号码、税号、银行账户或银行卡号、密码、医疗信息，或任何不必要的个人身份信息。",
                "Social Security numbers, tax IDs, bank or payment-card numbers, passwords, medical data, or unnecessary personal identifiers."
            ),
        ),
        unsafe_allow_html=True,
    )

    files = st.file_uploader(
        t("上传资料（可多选）", "Upload files (multi)"),
        type=["csv", "xlsx", "xls", "txt", "md"],
        accept_multiple_files=True
    )
    finance_consent = st.checkbox(t(
        "我已删除敏感个人信息，并同意将解析后的内容发送给已配置的 AI 服务进行分析。",
        "I removed sensitive personal information and consent to sending parsed content to the configured AI service for analysis."
    ))
    finance_ready = bool(files and finance_consent)
    if not files:
        st.caption(t("请先上传至少一个文件。单个文件上限为 25MB。", "Upload at least one file first. The per-file limit is 25MB."))

    question = st.text_area(
        t("你希望重点分析什么？", "What should we focus on?"),
        placeholder=t("例如：现金流是否健康？成本哪里可降？毛利目标是否合理？", "E.g., is cash flow healthy? where to cut costs? is margin target realistic?")
    )

    col1, col2 = st.columns([1, 1])
    with col1:
        st.write(t("常用分析主题", "Common focus"))
        focus = st.selectbox(
            t("常用分析主题", "Common focus"),
            options=[
                t("现金流与跑道", "Cash flow & runway"),
                t("利润率与定价", "Margins & pricing"),
                t("费用结构与降本", "Cost structure & savings"),
                t("应收应付与周转", "AR/AP & working capital"),
                t("风险与内控建议", "Risk & controls")
            ],
            label_visibility="collapsed",
        )
    with col2:
        st.write(t("输出风格", "Output style"))
        style = st.selectbox(
            t("输出风格", "Output style"),
            options=[
                t("老板能执行的清单", "Owner-executable checklist"),
                t("财务经理风格（更细）", "Finance manager style (detailed)"),
                t("极简三段论", "Minimal: 3-part summary")
            ],
            label_visibility="collapsed",
        )

    if st.button(t("开始分析", "Analyze"), type="primary", disabled=not finance_ready):
        doc_text = read_uploaded_to_text(files) if files else "[No files uploaded]"
        prompt = f"""
You are analyzing uploaded financial data for a U.S. small business owner.

Critical evidence rules:
- Use the computed metrics and uploaded data excerpts below as the primary evidence.
- Every key finding must cite at least one actual number from the uploaded data or computed metrics.
- Do NOT invent revenue, costs, margins, customer behavior, platform order mix, commissions, or cash balances.
- If a metric cannot be calculated from uploaded data, write: "Not available from uploaded data."
- If using a general industry benchmark, label it clearly as "General benchmark", not as company-specific fact.
- Separate actual-data findings from assumptions and recommendations.
- Do not provide investment, legal, tax, or regulated financial advice. This is business analysis support only.
- Do NOT use dollar signs in the output. Use "USD" before amounts, for example "USD 803,500", to avoid Markdown math rendering issues.
- Do NOT use legal/accounting conclusions such as "insolvency" unless the uploaded data includes sufficient balance-sheet/legal evidence. Use "liquidity risk" or "cash-flow deficit" instead.
- When comparing inventory purchases and COGS, state that differences may reflect timing, beginning/ending inventory, prepayments, or purchasing inefficiency; do not present it as confirmed waste without reconciliation.

Focus={focus}
Style={style}
User question: {question if question.strip() else 'None'}

Uploaded data and computed metrics:
{doc_text}

Return:
1) Actual Data Summary
- Revenue, gross margin, delivery/app fees, rent, payroll, marketing, EBITDA/operating margin, cash flow, and cash balance trend if available.

2) Key Findings
- 5 bullets.
- Each bullet must include actual numbers.

3) Metrics/Ratios Table
- Metric | Formula | Actual Result | Interpretation

4) Risks & Red Flags
- 5 bullets.
- Clearly distinguish actual-data risks from benchmark-based concerns.

5) Action Plan
- 10 bullets with owner + metric/target + timing.

6) Follow-up Questions
- 3 questions to improve accuracy.
"""
        with st.spinner(t("分析中…", "Analyzing...")):
            out = ask_ai(prompt, mode="finance")
        st.session_state.outputs["finance_ai_output"] = out
        st.markdown(out)

    st.divider()
    st.subheader(t("可交付物：财务报告（AI）", "Deliverable: Finance Report (AI)"))

    colA, colB = st.columns([1, 1])
    with colA:
        if st.button(
            t("生成财务报告", "Generate Finance Report"),
            type="primary",
            use_container_width=True,
            disabled=not finance_ready,
        ):
            doc_text = read_uploaded_to_text(files) if files else "[No files uploaded]"
            with st.spinner(t("生成中…", "Generating...")):
                st.session_state.outputs["finance_report_md"] = ai_report_finance(
                    doc_text=doc_text,
                    focus=focus,
                    style=style,
                    question=question
                )
            # st.rerun() removed to avoid Streamlit Cloud SessionInfo race

    with colB:
        if st.button(t("清空财务报告", "Clear Finance Report"), use_container_width=True):
            st.session_state.outputs["finance_report_md"] = ""
            # st.rerun() removed to avoid Streamlit Cloud SessionInfo race

    if st.session_state.outputs.get("finance_report_md", ""):
        st.text_area(t("财务报告预览", "Finance Report Preview"), st.session_state.outputs["finance_report_md"], height=520)
        st.download_button(
            label=t("下载 finance_report.md", "Download finance_report.md"),
            data=st.session_state.outputs["finance_report_md"],
            file_name="finance_report.md",
            mime="text/markdown"
        )

# =========================================================
# Router
# =========================================================
if st.session_state.active_suite == "open_store":
    render_open_store()
elif st.session_state.active_suite == "operations":
    render_operations()
else:
    render_finance()

# =========================================================
# Footer: Research & Compliance Notice
# =========================================================
st.markdown("---")
st.markdown(
    """
    <div style="text-align: center; font-size: 13px; color: rgba(255,255,255,0.55); line-height: 1.5; padding-bottom: 20px;">
        <b>Research & Compliance Notice</b><br>
        This system is developed for research and analytical framework demonstration purposes only.<br>
        It does not provide investment advice, financial advisory services, or regulated commercial services.<br>
        Any outputs are for informational and research discussion purposes only.
    </div>
    """,
    unsafe_allow_html=True
)
