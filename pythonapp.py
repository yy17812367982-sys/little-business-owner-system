import streamlit as st
import pandas as pd
import numpy as np
import os
import time
import random
import re
from datetime import datetime
from google import genai
import requests

# =========================================================
# Page config
# =========================================================
st.set_page_config(
    page_title="SME Financial Research Framework",
    layout="wide",
    initial_sidebar_state="collapsed"
)
st.info(
    """
    📢 U.S. Small Business Financial Research Initiative (Development Stage)
        This platform is currently under research and development to explore structured financial data interpretation models for U.S. small businesses.
    
    **Objective:** Studying data-driven frameworks to improve financial transparency and operational decision-making efficiency.  
    **Developer:** Yang Yu (Quantitative Finance & Systems Research)  
    **Contact:** yy17812367982@gmail.com
    """
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
.block-container{ padding-top: 4.5rem !important; padding-bottom: 3rem !important; }

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
[data-testid="stSidebarCollapsedControl"]{
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
  pointer-events: auto !important;
  cursor: pointer !important;
  transition: all 0.2s ease;

  margin: 0 !important;
  padding: 0 !important;
}

/* ✅关键：让真正可点击的 button 覆盖整个盒子 */
[data-testid="stSidebarCollapsedControl"] button{
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
[data-testid="stSidebarCollapsedControl"] button img{
  display: none !important;
}

/* ✅把“☰ Menu”画到 button 上（点击区域=整个按钮） */
[data-testid="stSidebarCollapsedControl"] button::before{
  content: "☰ Menu";
  color: #ffffff !important;
  font-size: 16px !important;
  font-weight: 600 !important;
  font-family: "Source Sans Pro", sans-serif;
  letter-spacing: 0.5px;
}

/* hover */
[data-testid="stSidebarCollapsedControl"]:hover{
  background-color: rgba(0,0,0,0.8) !important;
  border-color: rgba(255,255,255,0.6) !important;
  transform: translateY(1px);
}


/* =============================
   ★ 隐藏展开侧边栏后的关闭按钮 (<) ★
   ============================= */
[data-testid="stSidebarExpandedControl"]{
  display: none !important;
  width: 0 !important;
  height: 0 !important;
  opacity: 0 !important;
  pointer-events: none !important;
}
section[data-testid="stSidebar"] [data-testid="stSidebarHeader"] button{
  display: none !important;
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
You are "Yangyu's AI" — an AI assistant branded for an SME decision platform.

Rules:
- NEVER mention any underlying model/provider/vendor or internal API names.
- If asked "Who are you?", "What model are you?", "Are you Gemini?" or similar:
  answer: "I'm Yangyu's AI assistant." (optionally: built into this platform to help SMEs).
- Keep outputs structured and actionable; prefer bullet points, metrics, and next steps.
- If user requests sensitive/illegal help, refuse briefly and offer safe alternatives.
"""

MODEL_CANDIDATES_PRO = [
    # Current Gemini 3 family first. If an account has not enabled these yet,
    # the app automatically falls back to stable Gemini 2.5 models.
    "gemini-3.1-pro-preview",
    "gemini-2.5-pro",
    "gemini-3-flash-preview",
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
]

MODEL_CANDIDATES_FAST = [
    "gemini-3-flash-preview",
    "gemini-3.1-flash-lite",
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
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


def ask_ai(user_prompt: str, mode: str = "general") -> str:
    if not API_KEY or not client:
        return t("AI 服务未配置（缺少 GEMINI_API_KEY 或未初始化 client）。",
                 "AI service is not configured (missing GEMINI_API_KEY or client).")

    mode_hint = {
        "general": "General Q&A. Be concise and practical.",
        "open_store": "Focus on store-opening decisions: location, setup, launch checklist, risks, and actions.",
        "operations": "Focus on operations: inventory, staffing, SOPs, pricing execution, weekly review loops.",
        "finance": "Focus on financial analysis: cash flow, margins, runway, costs, scenario and controls.",
    }.get(mode, "General Q&A.")

    prompt = f"{SYSTEM_POLICY}\n\nContext:\n- Mode: {mode_hint}\n\nUser:\n{user_prompt}"

    models = MODEL_CANDIDATES_PRO if st.session_state.ai_quality == "pro" else MODEL_CANDIDATES_FAST
    last_err = None

    for model_name in models:
        for _ in range(2):
            try:
                resp = client.models.generate_content(model=model_name, contents=prompt)
                text = getattr(resp, "text", None)
                if text and str(text).strip():
                    return sanitize_ai_markdown_output(text)
                last_err = f"Empty response from {model_name}"
            except Exception as e:
                msg = str(e)
                last_err = f"{model_name}: {msg}"
                if ("429" in msg) or ("RESOURCE_EXHAUSTED" in msg) or ("rate" in msg.lower()):
                    time.sleep(1.2 + random.random())
                    continue
                if ("Not available" in msg) or ("PERMISSION_DENIED" in msg) or ("403" in msg):
                    break
                break

    return t(
        f"AI 暂时不可用。可能原因：免费额度/限流、或所选模型需要开通 Paid。最后错误：{last_err}",
        f"AI temporarily unavailable. Possible causes: free quota/rate limit, or selected model requires Paid. Last error: {last_err}"
    )

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
if "active_suite" not in st.session_state:
    st.session_state.active_suite = "open_store"

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
        "cost": 100.0,
        "target_margin": 30,
        "competitor_price": 135.0,
        "elasticity": "Medium",
        "notes": ""
    }

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

if "site_geo" not in st.session_state:
    st.session_state.site_geo = {"status": "idle", "cands": [], "picked_idx": 0, "debug": {}}

# =========================================================
# Helpers
# =========================================================
def score_from_inputs_site(traffic: int, competitors: int, rent_level: str, parking: str) -> int:
    score = 55
    if traffic >= 40000: score += 10
    elif traffic >= 25000: score += 6
    else: score += 2

    if competitors <= 6: score += 12
    elif competitors <= 12: score += 6
    else: score -= 6

    if rent_level == "Low": score += 8
    elif rent_level == "Medium": score += 3
    else: score -= 6

    if parking == "High": score += 6
    elif parking == "Medium": score += 2
    else: score -= 4

    return int(max(0, min(100, score)))

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
    """Compute pre-launch feasibility metrics for the Open a Store suite."""
    p = st.session_state.profile
    s = st.session_state.site
    launch = st.session_state.launch
    pr = st.session_state.pricing

    budget = float(p.get("budget", 0) or 0)
    funding_available = float(launch.get("funding_available", budget) or budget)

    if "startup_cost_estimate" in launch:
        startup_cost = float(launch.get("startup_cost_estimate", 0) or 0)
    else:
        startup_cost = (
            float(launch.get("buildout_cost", 0) or 0)
            + float(launch.get("licenses_deposits", 0) or 0)
            + float(launch.get("equipment_cost", 0) or 0)
            + float(launch.get("initial_inventory_budget", 0) or 0)
            + float(launch.get("launch_marketing_budget", 0) or 0)
        )

    if "monthly_fixed_cost_estimate" in launch:
        monthly_fixed_cost = float(launch.get("monthly_fixed_cost_estimate", 0) or 0)
    else:
        monthly_fixed_cost = (
            float(launch.get("monthly_rent", 0) or 0)
            + float(launch.get("monthly_payroll", 0) or 0)
            + float(launch.get("monthly_utilities", 0) or 0)
            + float(launch.get("monthly_insurance", 0) or 0)
            + float(launch.get("other_monthly_fixed", 0) or 0)
        )

    remaining_cash = funding_available - startup_cost
    runway_months = remaining_cash / monthly_fixed_cost if monthly_fixed_cost > 0 else np.inf
    target_cash_need = monthly_fixed_cost * float(launch.get("cash_target_months", 3) or 3)
    funding_gap = max(0.0, startup_cost + target_cash_need - funding_available)

    expected_revenue = float(launch.get("expected_monthly_revenue", 0) or 0)
    expected_gm = float(launch.get("expected_gross_margin", 0) or 0) / 100.0
    contribution_profit = expected_revenue * expected_gm
    monthly_profit_after_fixed = contribution_profit - monthly_fixed_cost
    breakeven_revenue = monthly_fixed_cost / expected_gm if expected_gm > 0 else np.inf

    site_score = score_from_inputs_site(int(s["traffic"]), int(s["competitors"]), s["rent_level"], s["parking"])

    # Pricing sanity check. In the simplified workflow, users enter a planned price directly.
    cost = float(pr.get("cost", 0) or 0)
    competitor_price = float(pr.get("competitor_price", 0) or 0)
    target_margin_pct = float(pr.get("target_margin", 0) or 0)
    recommended_price = cost * (1 + target_margin_pct / 100.0)
    planned_price = float(pr.get("planned_price", recommended_price) or recommended_price)
    implied_margin = (planned_price - cost) / planned_price if planned_price > 0 else 0.0
    price_vs_competitor = (planned_price - competitor_price) / competitor_price if competitor_price > 0 else 0.0

    # Scores: deliberately simple and explainable for a pre-launch decision.
    cash_score = 100
    if runway_months < 1:
        cash_score = 20
    elif runway_months < 2:
        cash_score = 45
    elif runway_months < float(launch.get("cash_target_months", 3) or 3):
        cash_score = 65
    else:
        cash_score = 85
    if funding_gap > 0:
        cash_score = max(15, cash_score - 20)

    margin_score = 50
    if monthly_profit_after_fixed > 0 and expected_gm >= 0.55:
        margin_score = 85
    elif monthly_profit_after_fixed > 0:
        margin_score = 70
    elif expected_gm >= 0.55:
        margin_score = 55
    else:
        margin_score = 35

    competition_score = 80
    competitors = int(s.get("competitors", 0) or 0)
    if competitors > 20:
        competition_score = 35
    elif competitors > 12:
        competition_score = 55
    elif competitors > 6:
        competition_score = 70

    overall_score = int(round(site_score * 0.35 + cash_score * 0.35 + margin_score * 0.20 + competition_score * 0.10))
    if overall_score >= 75 and funding_gap <= 0 and monthly_profit_after_fixed >= 0:
        decision = "GO"
    elif overall_score >= 55:
        decision = "CAUTION"
    else:
        decision = "NO-GO"

    risks = []
    if funding_gap > 0:
        risks.append(f"Funding gap of USD {funding_gap:,.0f} against target cash runway")
    if runway_months < float(launch.get("cash_target_months", 3) or 3):
        risks.append(f"Cash runway is {runway_months:.1f} months, below the target of {launch.get('cash_target_months', 3)} months")
    if monthly_profit_after_fixed < 0:
        risks.append(f"Expected monthly gross profit does not cover fixed costs; estimated shortfall is USD {abs(monthly_profit_after_fixed):,.0f}/month")
    if s.get("rent_level") == "High":
        risks.append("Rent level is marked High, increasing break-even pressure")
    if competitors > 12:
        risks.append(f"Competitive density is high with {competitors} competitors in the selected radius")
    if price_vs_competitor > 0.10:
        risks.append(f"Recommended price is {price_vs_competitor:.1%} above competitor price")

    return {
        "startup_cost": startup_cost,
        "monthly_fixed_cost": monthly_fixed_cost,
        "remaining_cash": remaining_cash,
        "runway_months": runway_months,
        "target_cash_need": target_cash_need,
        "funding_gap": funding_gap,
        "expected_revenue": expected_revenue,
        "expected_gross_margin_pct": expected_gm * 100,
        "contribution_profit": contribution_profit,
        "monthly_profit_after_fixed": monthly_profit_after_fixed,
        "breakeven_revenue": breakeven_revenue,
        "site_score": site_score,
        "cash_score": cash_score,
        "margin_score": margin_score,
        "competition_score": competition_score,
        "overall_score": overall_score,
        "decision": decision,
        "recommended_price": planned_price,
        "implied_margin_pct": implied_margin * 100,
        "price_vs_competitor_pct": price_vs_competitor * 100,
        "risks": risks,
    }




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

    prompt = f"""
You are producing a professional pre-launch feasibility report for a U.S. small business owner.
Output MUST be Markdown.

Important rules:
- This is a PRE-LAUNCH decision report, not an operations report and not a full financial statement analysis.
- Use only the provided inputs and computed metrics.
- Do not use dollar signs. Use "USD" before amounts to avoid Markdown rendering issues.
- Do not overstate risk. Use "GO", "CAUTION", or "NO-GO" as the launch decision.
- Every key finding must cite at least one specific input or computed number.

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
    return clean_currency_for_markdown(ask_ai(prompt, mode="open_store"))


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
with st.sidebar:
    st.button(t("🌐 切换语言", "🌐 Switch Language"), on_click=toggle_language)
    st.markdown("---")

    st.markdown("### " + t("功能集合", "Suites"))
    suite_label = st.radio(
        "",
        options=[
            t("开店（决策流）", "Open a Store"),
            t("运营（跑起来）", "Operations"),
            t("财务（分析）", "Finance"),
        ],
        index={"open_store": 0, "operations": 1, "finance": 2}.get(st.session_state.active_suite, 0)
    )

    mapping = {
        t("开店（决策流）", "Open a Store"): "open_store",
        t("运营（跑起来）", "Operations"): "operations",
        t("财务（分析）", "Finance"): "finance",
    }
    new_suite = mapping[suite_label]
    if new_suite != st.session_state.active_suite:
        st.session_state.active_suite = new_suite
        # st.rerun() removed to avoid Streamlit Cloud SessionInfo race

    st.markdown("---")
    st.image("https://cdn-icons-png.flaticon.com/512/2362/2362378.png", width=48)

    st.text_input(
        t("用户名", "Username"),
        key="username",
        placeholder=t("输入用户名", "Enter a username"),
        on_change=on_username_submit
    )
    if st.session_state.register_msg:
        st.warning(st.session_state.register_msg)

    st.markdown("---")
    st.success(t("🟢 系统在线", "🟢 System Online"))
    st.caption("v6.0 Simplified Open-Store Feasibility + Operations Control Center + Finance Engine")

# =========================================================
# Header + Top Ask AI
# =========================================================
st.title("SME Financial Research Framework")

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

with st.expander(t("问 AI（入口）", "Ask AI (Top Entry)"), expanded=False):
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
            st.session_state.show_top_chat = False
            st.session_state.top_chat_collapsed = True
            # st.rerun() removed to avoid Streamlit Cloud SessionInfo race

    c1, c2, c3, c4 = st.columns([1.2, 1.2, 1.2, 6.4])
    with c1:
        if st.button(t("展示", "Show"), use_container_width=True):
            st.session_state.show_top_chat = True
            st.session_state.top_chat_collapsed = False
            # st.rerun() removed to avoid Streamlit Cloud SessionInfo race
    with c2:
        if st.button(t("收起", "Hide"), use_container_width=True):
            st.session_state.show_top_chat = False
            st.session_state.top_chat_collapsed = True
            # st.rerun() removed to avoid Streamlit Cloud SessionInfo race
    with c3:
        if st.button(t("清空", "Clear"), use_container_width=True):
            st.session_state.chat_history = []
            st.session_state.show_top_chat = False
            st.session_state.top_chat_collapsed = True
            st.session_state.top_last_status = ""
            # st.rerun() removed to avoid Streamlit Cloud SessionInfo race
    with c4:
        if st.session_state.top_last_status == "ready":
            st.success(t("已生成回答。点「展示」查看。", "Answer ready. Click “Show” to view."), icon="✅")

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
            ai_label = t("Yangyu 的 AI:", "Yangyu's AI:")
            st.markdown(
                "<div class='card'><b>{}</b><br>{}</div>".format(ai_label, safe_text),
                unsafe_allow_html=True
            )

# =========================================================
# Suite 1: Open a Store
# =========================================================
def render_open_store():
    # Keep legacy state safe if the user comes from an older 4-step version.
    if st.session_state.open_step > 3:
        st.session_state.open_step = 3

    st.header(t("开店可行性评估", "Open a Store Feasibility"))

    step_titles = [
        t("概念与选址", "Concept & Location"),
        t("预算与定价", "Budget & Pricing"),
        t("结论与报告", "Decision & Report"),
    ]
    st.write(f"{t('步骤', 'Step')} {st.session_state.open_step}/3 — {step_titles[st.session_state.open_step-1]}")
    st.progress(st.session_state.open_step / 3.0)

    nav1, nav2, nav3 = st.columns([1, 1, 2])
    with nav1:
        if st.button(t("◀ 上一步", "◀ Back"), use_container_width=True):
            st.session_state.open_step = max(1, st.session_state.open_step - 1)
    with nav2:
        if st.button(t("下一步 ▶", "Next ▶"), use_container_width=True):
            st.session_state.open_step = min(3, st.session_state.open_step + 1)
    with nav3:
        st.caption(t(
            "三页完成：先看生意和选址，再看钱和定价，最后给 Go / Caution / No-Go。",
            "Three pages only: concept & location, money & pricing, then Go / Caution / No-Go."
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

    # Page 1: Concept & Location
    if st.session_state.open_step == 1:
        p = st.session_state.profile
        s = st.session_state.site
        st.subheader(t("第 1 页：概念与选址", "Page 1: Concept & Location"))
        st.markdown(
            "<div class='card'>" + t(
                "这一页只问两个问题：你要开什么店？这个位置大概行不行？City 不再单独填写，避免和地址重复。",
                "This page asks only two questions: what are you opening, and does the location roughly work? City is no longer a separate input to avoid duplicating the address."
            ) + "</div>",
            unsafe_allow_html=True
        )

        left, right = st.columns([1, 1.25])
        with left:
            st.markdown("### " + t("业务概念", "Business Concept"))
            p["business_type"] = st.selectbox(
                t("业态", "Business Type"),
                ["Coffee Shop", "Restaurant", "Convenience Store", "Small Retail Store", "Beauty Salon", "Auto Parts Store", "Other"],
                index=["Coffee Shop", "Restaurant", "Convenience Store", "Small Retail Store", "Beauty Salon", "Auto Parts Store", "Other"].index(
                    p.get("business_type", "Coffee Shop") if p.get("business_type", "Coffee Shop") in ["Coffee Shop", "Restaurant", "Convenience Store", "Small Retail Store", "Beauty Salon", "Auto Parts Store", "Other"] else "Coffee Shop"
                )
            )
            p["target_customer"] = st.text_input(
                t("目标客户", "Target Customer"),
                p.get("target_customer", "Local residents, office workers, tourists, and weekend shoppers")
            )
            p["differentiator"] = st.text_input(
                t("差异化", "Differentiator"),
                p.get("differentiator", "Fast specialty coffee + grab-and-go breakfast + local Texas-style snacks")
            )
            p["notes"] = st.text_area(
                t("限制/备注（可选）", "Constraints / Notes (optional)"),
                p.get("notes", ""),
                placeholder=t("例如：只做早餐、缺少全职店长、房东给2个月免租等", "E.g., breakfast only, no full-time manager yet, two months free rent from landlord, etc.")
            )

        with right:
            st.markdown("### " + t("选址快评", "Location Quick Check"))
            s["address"] = st.text_input(
                t("地址或商圈", "Address or Trade Area"),
                s.get("address", DEFAULT_TEXAS_ADDRESS)
            )
            c1, c2 = st.columns([1, 1])
            with c1:
                s["traffic"] = st.slider(t("客流/车流估计", "Traffic Estimate"), 1000, 50000, int(s.get("traffic", 26000)), step=500)
                s["competitors"] = st.number_input(t("半径内竞品", "Competitors Nearby"), min_value=0, value=int(s.get("competitors", 9)), step=1)
                s["radius_miles"] = st.selectbox(t("半径（英里）", "Radius (miles)"), [0.5, 1.0, 3.0], index=[0.5, 1.0, 3.0].index(s.get("radius_miles", 1.0)))
            with c2:
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
                if st.button(t("重置德州默认点", "Reset Texas Default"), use_container_width=True):
                    s["address"] = DEFAULT_TEXAS_ADDRESS
                    s["lat"] = DEFAULT_TEXAS_LAT
                    s["lon"] = DEFAULT_TEXAS_LON
                    st.session_state.site_geo = {"status": "idle", "cands": [], "picked_idx": 0, "debug": {}}

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

    # Page 2: Budget & Pricing
    elif st.session_state.open_step == 2:
        p = st.session_state.profile
        launch = st.session_state.launch
        pr = st.session_state.pricing
        st.subheader(t("第 2 页：预算与定价", "Page 2: Budget & Pricing"))
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
            launch["funding_available"] = st.number_input(t("可用启动资金", "Available Launch Funding"), min_value=0.0, value=float(launch.get("funding_available", p.get("budget", 80000))), step=1000.0)
            p["budget"] = int(launch["funding_available"])
            launch["startup_cost_estimate"] = st.number_input(t("预计一次性启动成本", "Estimated One-Time Startup Cost"), min_value=0.0, value=float(launch.get("startup_cost_estimate", 62000)), step=1000.0)
            launch["monthly_fixed_cost_estimate"] = st.number_input(t("预计每月固定成本", "Estimated Monthly Fixed Cost"), min_value=0.0, value=float(launch.get("monthly_fixed_cost_estimate", 26500)), step=500.0)
            launch["expected_monthly_revenue"] = st.number_input(t("预期月收入", "Expected Monthly Revenue"), min_value=0.0, value=float(launch.get("expected_monthly_revenue", 52000)), step=1000.0)
            launch["expected_gross_margin"] = st.slider(t("预期毛利率（%）", "Expected Gross Margin (%)"), 10, 90, int(launch.get("expected_gross_margin", 62)))
            launch["cash_target_months"] = st.slider(t("目标现金跑道（月）", "Target Cash Runway (months)"), 1, 12, int(launch.get("cash_target_months", 3)))

        with col2:
            st.markdown("### " + t("代表性产品定价", "Representative Product Pricing"))
            pr["cost"] = st.number_input(t("单位成本", "Unit Cost"), min_value=0.0, value=float(pr.get("cost", 3.2)), step=0.1)
            pr["planned_price"] = st.number_input(t("计划售价", "Planned Price"), min_value=0.0, value=float(pr.get("planned_price", 5.25)), step=0.1)
            pr["competitor_price"] = st.number_input(t("竞品价格", "Competitor Price"), min_value=0.0, value=float(pr.get("competitor_price", 5.5)), step=0.1)
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

        if m["funding_gap"] > 0 or m["runway_months"] < launch["cash_target_months"]:
            st.warning(t("现金跑道偏紧：先降低启动成本、谈免租期/账期，或补充启动资金。", "Cash runway is tight: reduce startup cost, negotiate free rent/payment terms, or secure additional funding."))
        else:
            st.success(t("启动资金基本覆盖目标现金跑道。", "Available funding broadly covers the target cash runway."))

    # Page 3: Decision & Report
    else:
        st.subheader(t("第 3 页：结论与报告", "Page 3: Decision & Report"))
        m = open_store_feasibility_metrics()
        decision = m["decision"]
        decision_msg = {
            "GO": t("可以推进，但仍需完成开业前检查清单。", "Proceed, but complete the pre-launch checklist."),
            "CAUTION": t("谨慎推进，先修复主要风险。", "Proceed cautiously and fix the main risks first."),
            "NO-GO": t("暂不建议开店，先重做资金、选址或利润假设。", "Do not launch yet; revisit funding, location, or margin assumptions first."),
        }.get(decision, "")

        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric(t("最终判断", "Decision"), decision)
        c2.metric(t("总评分", "Overall"), int(m["overall_score"]))
        c3.metric(t("选址", "Site"), int(m["site_score"]))
        c4.metric(t("现金", "Cash"), int(m["cash_score"]))
        c5.metric(t("利润", "Margin"), int(m["margin_score"]))
        st.info(decision_msg)

        st.markdown("### " + t("核心依据", "Decision Evidence"))
        metric_df = pd.DataFrame([
            {"Metric": "Location Score", "Value": int(m["site_score"]), "Meaning": "Traffic, competition, rent pressure, and accessibility"},
            {"Metric": "Startup Cost", "Value": f"USD {m['startup_cost']:,.0f}", "Meaning": "One-time cost before opening"},
            {"Metric": "Monthly Fixed Cost", "Value": f"USD {m['monthly_fixed_cost']:,.0f}", "Meaning": "Fixed monthly cash burden"},
            {"Metric": "Cash Runway", "Value": f"{m['runway_months']:.1f} months", "Meaning": "Remaining cash after startup costs"},
            {"Metric": "Break-even Revenue", "Value": f"USD {m['breakeven_revenue']:,.0f}" if np.isfinite(m['breakeven_revenue']) else "N/A", "Meaning": "Revenue needed to cover fixed costs"},
            {"Metric": "Planned Price", "Value": f"USD {m['recommended_price']:,.2f}", "Meaning": "Representative product price"},
        ])
        st.dataframe(metric_df, use_container_width=True, hide_index=True)

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
        colA, colB = st.columns([1, 1])
        with colA:
            if st.button(t("生成开店决策报告", "Generate Launch Decision Report"), type="primary", use_container_width=True):
                with st.spinner(t("生成报告中…", "Generating report...")):
                    st.session_state.outputs["open_store_report_md"] = ai_report_open_store(open_store_question)
        with colB:
            if st.button(t("清空报告", "Clear Report"), use_container_width=True):
                st.session_state.outputs["open_store_report_md"] = ""
                st.session_state.outputs["final_open_store"] = None

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
            if st.button(t("运行运营诊断", "Run Operations Diagnosis"), type="primary", use_container_width=True):
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
        if st.button(t("生成运营报告", "Generate Operations Report"), type="primary", use_container_width=True):
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

    files = st.file_uploader(
        t("上传资料（可多选）", "Upload files (multi)"),
        type=["csv", "xlsx", "xls", "txt", "md"],
        accept_multiple_files=True
    )

    question = st.text_area(
        t("你希望重点分析什么？", "What should we focus on?"),
        placeholder=t("例如：现金流是否健康？成本哪里可降？毛利目标是否合理？", "E.g., is cash flow healthy? where to cut costs? is margin target realistic?")
    )

    col1, col2 = st.columns([1, 1])
    with col1:
        st.write(t("常用分析主题", "Common focus"))
        focus = st.selectbox(
            "",
            options=[
                t("现金流与跑道", "Cash flow & runway"),
                t("利润率与定价", "Margins & pricing"),
                t("费用结构与降本", "Cost structure & savings"),
                t("应收应付与周转", "AR/AP & working capital"),
                t("风险与内控建议", "Risk & controls")
            ]
        )
    with col2:
        st.write(t("输出风格", "Output style"))
        style = st.selectbox(
            "",
            options=[
                t("老板能执行的清单", "Owner-executable checklist"),
                t("财务经理风格（更细）", "Finance manager style (detailed)"),
                t("极简三段论", "Minimal: 3-part summary")
            ]
        )

    if st.button(t("开始分析", "Analyze"), type="primary"):
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
        if st.button(t("生成财务报告", "Generate Finance Report"), type="primary", use_container_width=True):
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
