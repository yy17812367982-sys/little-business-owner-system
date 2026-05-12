import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import numpy as np
import os
import time
import random
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
# ✅ Sidebar collapse helper (SAFE: two-step flag -> execute in main flow)
# =========================================================
def collapse_sidebar():
    components.html(
        """
        <script>
        (function(){
          const selectors = [
            '[data-testid="stSidebarCollapseButton"]',
            '[data-testid="stSidebarCollapseButton"] button',
            'button[aria-label="Close sidebar"]',
            'button[title="Close sidebar"]'
          ];
          let btn = null;
          for (const s of selectors) {
            btn = window.parent.document.querySelector(s);
            if (btn) break;
          }
          if (btn) btn.click();
        })();
        </script>
        """,
        height=0,
        width=0,
    )

if "_do_collapse_sidebar" not in st.session_state:
    st.session_state["_do_collapse_sidebar"] = False

# ✅ Only execute collapse in main render flow (avoid SessionInfo init race)
if st.session_state.get("_do_collapse_sidebar", False):
    st.session_state["_do_collapse_sidebar"] = False
    collapse_sidebar()

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
.stMarkdown p{ color: rgba(255,255,255,0.65) !important; text-shadow: none !important; }
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
    "gemini-3-pro-preview",
    "gemini-2.5-pro",
    "gemini-3-flash-preview",
    "gemini-2.5-flash",
]

MODEL_CANDIDATES_FAST = [
    "gemini-3-flash-preview",
    "gemini-2.5-flash",
    "gemini-2.5-pro",
]

if "ai_quality" not in st.session_state:
    st.session_state.ai_quality = "pro"

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
                    return text
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
        "business_type": "Auto Parts Store",
        "stage": "Planning",
        "budget": 80000,
        "target_customer": "Local residents and small fleets",
        "differentiator": "Fast service + reliable stock",
        "city": "New York",
        "notes": ""
    }

if "site" not in st.session_state:
    st.session_state.site = {
        "address": "39-01 Main St, Flushing, NY 11354",
        "radius_miles": 1.0,
        "traffic": 30000,
        "competitors": 12,
        "parking": "Medium",
        "rent_level": "High",
        "foot_traffic_source": "Mixed (Transit + Street)",
        "risk_flags": []
    }

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

def ai_report_open_store() -> str:
    p = st.session_state.profile
    s = st.session_state.site
    inv = st.session_state.inventory
    pr = st.session_state.pricing

    inv_snapshot = st.session_state.outputs.get("inventory_summary", "No inventory summary available.")
    inv_df = inv.get("df", None)

    site_score = score_from_inputs_site(s["traffic"], s["competitors"], s["rent_level"], s["parking"])
    rec_price = pr["cost"] * (1 + pr["target_margin"] / 100.0)

    prompt = f"""
You are producing a professional decision report for an SME owner.
Output MUST be Markdown.

Use ONLY the provided inputs; do not assume outside data.

Report structure:
# Open-Store Decision Report
## 1) Executive Summary (3 bullets)
- Include Overall Score (0-100) and Confidence (Low/Med/High)

## 2) Key Inputs (table)
- Business, Site, Inventory/Cash, Pricing

## 3) Analysis
### Site viability
- cite traffic/competitors/rent/parking + computed site_score={site_score}

### Inventory & cash
- cite cash_target_days, lead_time_days, seasonality, inventory snapshot

### Pricing
- cite strategy, cost, competitor_price, target_margin, elasticity
- include recommended price = {rec_price:.2f}

## 4) Action Plan (10 bullets)
Group by Site / Inventory&Cash / Pricing.
Each bullet must include a metric/target or concrete next step.

## 5) Risks & Controls (6 bullets)
Each bullet must map to an input risk or an operational control.

Inputs:
Business: {p}
Site: {s}
Inventory: cash_target_days={inv['cash_target_days']}, lead_time_days={inv['supplier_lead_time_days']}, seasonality={inv['seasonality']}, notes={inv['notes'] if inv['notes'].strip() else 'None'}
Inventory snapshot: {inv_snapshot}
Inventory table:
{inv_df.to_string(index=False) if inv_df is not None else 'Not provided'}

Pricing: {pr}
"""
    return ask_ai(prompt, mode="open_store")

def ai_report_operations() -> str:
    out = st.session_state.outputs
    ops_ai = out.get("ops_ai_output", "")
    if ops_ai is None:
        ops_ai = ""
    elif not isinstance(ops_ai, str):
        ops_ai = str(ops_ai)

    inv = st.session_state.inventory
    inv_df = inv.get("df")
    inv_table = inv_df.to_string(index=False) if isinstance(inv_df, pd.DataFrame) else "Not provided"
    inv_snapshot = out.get("inventory_summary", "No inventory summary available.")

    prompt = f"""
Return Markdown.

# Operations Report
## Current Snapshot
- Inventory snapshot: {inv_snapshot}

## Key Signals from Data
- Use only provided inputs.

## Ops Advisor Notes (if any)
{ops_ai.strip() if ops_ai.strip() else "[None]"}

## Inventory Rules
## Pricing Execution Rules
## KPIs (8)
## Next 14 Days Action Plan (owner/metric)
## Data Gaps

Inventory table:
{inv_table}
"""
    return ask_ai(prompt, mode="operations")

def ai_report_finance(doc_text: str, focus: str, style: str, question: str) -> str:
    finance_ai = st.session_state.outputs.get("finance_ai_output", "")
    prompt = f"""
You are producing a Finance Analysis Report for an SME owner. Output MUST be Markdown.

Focus={focus}
Style={style}
User question={question if question.strip() else 'None'}

Report structure:
# Finance Analysis Report
## 1) Executive Summary (5 bullets)
## 2) What the data suggests (tables/bullets)
- Only compute what you can from provided data excerpts

## 3) Risks & Controls (8 bullets)
## 4) Action Plan (12 bullets)
- Each bullet must include owner + metric/target

## 5) Follow-up Questions (5 items)

User documents (excerpts):
{doc_text}

Previous AI output (if any):
{finance_ai if finance_ai.strip() else '[None]'}
"""
    return ask_ai(prompt, mode="finance")

def read_uploaded_to_text(files) -> str:
    chunks = []
    for f in files:
        name = f.name.lower()
        try:
            if name.endswith(".csv"):
                df = pd.read_csv(f)
                chunks.append(f"## {f.name}\n{df.head(50).to_string(index=False)}\n")
            elif name.endswith(".xlsx") or name.endswith(".xls"):
                df = pd.read_excel(f)
                chunks.append(f"## {f.name}\n{df.head(50).to_string(index=False)}\n")
            elif name.endswith(".txt") or name.endswith(".md"):
                text = f.read().decode("utf-8", errors="ignore")
                chunks.append(f"## {f.name}\n{text[:8000]}\n")
            else:
                chunks.append(f"## {f.name}\n[Unsupported file type for text extraction in this version]\n")
        except Exception as e:
            chunks.append(f"## {f.name}\n[Failed to parse: {e}]\n")
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
        # ✅ 选中后让 sidebar 自动收回（用 SAFE flag，下一轮主流程执行 collapse）
        st.session_state["_do_collapse_sidebar"] = True
        st.rerun()

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
    st.caption("v5.3 Geocoding + Overpass (robust)")

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
            st.rerun()

    c1, c2, c3, c4 = st.columns([1.2, 1.2, 1.2, 6.4])
    with c1:
        if st.button(t("展示", "Show"), use_container_width=True):
            st.session_state.show_top_chat = True
            st.session_state.top_chat_collapsed = False
            st.rerun()
    with c2:
        if st.button(t("收起", "Hide"), use_container_width=True):
            st.session_state.show_top_chat = False
            st.session_state.top_chat_collapsed = True
            st.rerun()
    with c3:
        if st.button(t("清空", "Clear"), use_container_width=True):
            st.session_state.chat_history = []
            st.session_state.show_top_chat = False
            st.session_state.top_chat_collapsed = True
            st.session_state.top_last_status = ""
            st.rerun()
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
    st.header(t("开店（决策流）", "Open a Store (Decision Flow)"))

    step_titles = [
        t("业务画像", "Profile"),
        t("选址检查", "Site Check"),
        t("库存与现金", "Inventory & Cash"),
        t("定价 & 总结", "Pricing & Summary")
    ]
    st.write(f"{t('步骤', 'Step')} {st.session_state.open_step}/4 — {step_titles[st.session_state.open_step-1]}")
    st.progress(st.session_state.open_step / 4.0)

    nav1, nav2, nav3 = st.columns([1, 1, 2])
    with nav1:
        if st.button(t("◀ 上一步", "◀ Back"), use_container_width=True):
            st.session_state.open_step = max(1, st.session_state.open_step - 1)
            st.rerun()
    with nav2:
        if st.button(t("下一步 ▶", "Next ▶"), use_container_width=True):
            st.session_state.open_step = min(4, st.session_state.open_step + 1)
            st.rerun()
    with nav3:
        st.caption(t("提示：这部分专注“开店决策”。运营和财务在其他集合里更细。",
                     "Tip: This suite focuses on launch decisions. Operations & finance are in other suites."))

    # Step 1
    if st.session_state.open_step == 1:
        p = st.session_state.profile
        st.subheader(t("第 1 步：业务画像", "Step 1: Business Profile"))
        col1, col2 = st.columns([1, 1])
        with col1:
            p["business_type"] = st.selectbox(
                t("业态类型", "Business Type"),
                ["Auto Parts Store", "Convenience Store", "Coffee Shop", "Restaurant", "Beauty Salon", "Other"],
                index=["Auto Parts Store","Convenience Store","Coffee Shop","Restaurant","Beauty Salon","Other"].index(
                    p["business_type"] if p["business_type"] in ["Auto Parts Store","Convenience Store","Coffee Shop","Restaurant","Beauty Salon","Other"] else "Other"
                )
            )
            p["stage"] = st.selectbox(
                t("阶段", "Stage"),
                ["Planning", "Open Soon", "Operating", "Expansion"],
                index=["Planning","Open Soon","Operating","Expansion"].index(p["stage"]) if p["stage"] in ["Planning","Open Soon","Operating","Expansion"] else 0
            )
            p["city"] = st.text_input(t("城市", "City"), p["city"])
        with col2:
            p["budget"] = st.number_input(t("初始预算（美元）", "Initial Budget (USD)"), min_value=0, value=int(p["budget"]), step=1000)
            p["target_customer"] = st.text_input(t("目标客户", "Target Customer"), p["target_customer"])
            p["differentiator"] = st.text_input(t("差异化", "Differentiator"), p["differentiator"])

        p["notes"] = st.text_area(
            t("备注（可选）", "Notes (optional)"),
            p["notes"],
            placeholder=t("例如：营业时间、人员配置、服务范围、限制条件等", "Constraints, hours, staffing, services, etc.")
        )

    # Step 2
    elif st.session_state.open_step == 2:
        s = st.session_state.site
        p = st.session_state.profile

        st.subheader(t("第 2 步：选址检查", "Step 2: Site Check"))
        colA, colB = st.columns([1, 2])

        with colA:
            s["address"] = st.text_input(t("地址（支持模糊）", "Address (fuzzy supported)"), s["address"])
            s["radius_miles"] = st.selectbox(
                t("半径（英里）", "Radius (miles)"),
                [0.5, 1.0, 3.0],
                index=[0.5, 1.0, 3.0].index(s["radius_miles"])
            )

            s["traffic"] = st.slider(t("人流/车流（估计）", "Traffic (estimated)"), 1000, 50000, int(s["traffic"]), step=500)
            s["competitors"] = st.number_input(t("竞品数量（估计）", "Competitors (estimated)"), min_value=0, value=int(s["competitors"]), step=1)
            s["parking"] = st.selectbox(t("停车便利", "Parking"), ["Low", "Medium", "High"], index=["Low","Medium","High"].index(s["parking"]))
            s["rent_level"] = st.selectbox(t("租金水平", "Rent Level"), ["Low", "Medium", "High"], index=["Low","Medium","High"].index(s["rent_level"]))
            s["foot_traffic_source"] = st.selectbox(
                t("客流来源", "Foot Traffic Source"),
                ["Mixed (Transit + Street)", "Street Dominant", "Transit Dominant", "Destination Only"],
                index=["Mixed (Transit + Street)","Street Dominant","Transit Dominant","Destination Only"].index(s["foot_traffic_source"])
            )

        with colB:
            st.subheader(t("地图预览（输入地址→点击搜索→定位）", "Map Preview (address → click search → locate)"))

            b1, b2 = st.columns([1, 1])
            with b1:
                do_search = st.button("🔎 " + t("Search / Locate", "Search / Locate"), use_container_width=True)
            with b2:
                do_clear = st.button(t("Clear Results", "Clear Results"), use_container_width=True)

            if do_clear:
                st.session_state.site_geo = {"status": "idle", "cands": [], "picked_idx": 0, "debug": {}}
                s.pop("lat", None)
                s.pop("lon", None)
                s.pop("competitors_debug", None)
                s.pop("traffic_debug", None)
                st.rerun()

            if do_search:
                query = (s.get("address") or "").strip()
                cands, dbg = geocode_candidates_multi_fuzzy(query, limit=6)
                st.session_state.site_geo["cands"] = cands
                st.session_state.site_geo["debug"] = dbg
                st.session_state.site_geo["status"] = "ok" if cands else "fail"
                st.session_state.site_geo["picked_idx"] = 0
                st.rerun()

            geo = st.session_state.site_geo
            cands = geo.get("cands", []) or []

            if geo.get("status") == "idle":
                st.info(t("还没有搜索结果。请点击「Search/Locate」。", "No results yet. Click “Search/Locate”."))
                base_lat, base_lon = 40.7590, -73.8290
                st.map(pd.DataFrame({"lat": [base_lat], "lon": [base_lon]}), zoom=12)

            elif not cands:
                st.warning(t("没搜到该地址。建议输入更短/更模糊的关键词，例如：'7 Champagne Ct 12189'。",
                             "No matches. Try shorter input, e.g., '7 Champagne Ct 12189'."))
                base_lat, base_lon = 40.7590, -73.8290
                st.map(pd.DataFrame({"lat": [base_lat], "lon": [base_lon]}), zoom=12)

            else:
                labels = [c["display_name"] for c in cands]
                idx = int(geo.get("picked_idx", 0))
                idx = max(0, min(idx, len(labels) - 1))

                picked_label = st.selectbox(
                    t("匹配到多个地址（请选择）", "Multiple matches (pick one)"),
                    labels,
                    index=idx
                )
                chosen = cands[labels.index(picked_label)]
                lat, lon = chosen["lat"], chosen["lon"]

                s["lat"] = float(lat)
                s["lon"] = float(lon)

                st.caption(t(f"已定位坐标：{lat:.6f}, {lon:.6f}", f"Located at: {lat:.6f}, {lon:.6f}"))
                st.map(pd.DataFrame({"lat": [lat], "lon": [lon]}), zoom=14)

                if st.button(t("用标准地址覆盖输入框", "Replace input with normalized address")):
                    s["address"] = chosen.get("display_name", s["address"])
                    st.rerun()

                st.divider()
                e1, e2 = st.columns([1, 1])

                with e1:
                    if st.button(t("自动估算竞品&交通", "Auto-estimate competitors & traffic"), use_container_width=True):
                        bt = p.get("business_type", "Other")
                        rad = float(s.get("radius_miles", 1.0))

                        comp = estimate_competitors_overpass(lat, lon, rad, bt)
                        s["competitors_debug"] = comp
                        if comp.get("ok"):
                            s["competitors"] = int(comp["count"])
                        else:
                            st.warning(t("竞品自动估算失败（Overpass 不稳定/限流很常见），已保留你手动输入的数值。",
                                         "Competitor auto-estimation failed (Overpass is often rate-limited). Keeping your manual value."))

                        tp = estimate_traffic_proxy_overpass(lat, lon, rad)
                        s["traffic_debug"] = tp
                        if tp.get("ok"):
                            s["traffic"] = int(tp["traffic_est"])
                        else:
                            st.warning(t("交通自动估算失败（Overpass 不稳定/限流很常见），已保留你手动输入的数值。",
                                         "Traffic auto-estimation failed (Overpass is often rate-limited). Keeping your manual value."))

                        st.rerun()

                with e2:
                    if st.button(t("清空估算结果", "Clear estimates"), use_container_width=True):
                        s.pop("competitors_debug", None)
                        s.pop("traffic_debug", None)
                        st.rerun()

            with st.expander(t("Geocode Debug（排查用）", "Geocode Debug (troubleshooting)"), expanded=False):
                st.write(geo.get("debug", {}))

            with st.expander(t("估算调试信息（可选）", "Estimation Debug (optional)"), expanded=False):
                st.write("competitors_debug =", s.get("competitors_debug", None))
                st.write("traffic_debug =", s.get("traffic_debug", None))

            st.caption(t("说明：地图=地理编码（地址→坐标）；竞品/交通=基于 OSM 的近似估算，失败很常见但不会影响手工输入。",
                         "Note: Map is geocoding (address→coords). Competitors/traffic are OSM-based estimates; failures are common but won't break manual inputs."))

        score = score_from_inputs_site(int(s["traffic"]), int(s["competitors"]), s["rent_level"], s["parking"])
        risk_flags = []
        if int(s["competitors"]) > 15: risk_flags.append(t("竞品密度偏高", "High competitive density"))
        if s["rent_level"] == "High": risk_flags.append(t("固定成本偏高（租金）", "High fixed cost (rent)"))
        if s["parking"] == "Low": risk_flags.append(t("停车不便可能影响转化", "Low parking convenience"))
        s["risk_flags"] = risk_flags

        c1, c2, c3 = st.columns(3)
        c1.metric(t("选址评分", "Site Score"), score)
        c2.metric(t("竞品数", "Competitors"), int(s["competitors"]))
        c3.metric(t("流量", "Traffic"), int(s["traffic"]))

        if risk_flags:
            st.warning(t("风险提示：", "Risk flags: ") + "，".join(risk_flags))
        else:
            st.success(t("当前输入下未发现明显风险标记。", "No major risk flags from current inputs."))

    # Step 3
    elif st.session_state.open_step == 3:
        inv = st.session_state.inventory
        st.subheader(t("第 3 步：库存与现金（不跑 AI）", "Step 3: Inventory & Cash "))

        col1, col2 = st.columns([1, 1])
        with col1:
            inv["cash_target_days"] = st.slider(t("目标现金周转天数", "Cash target (days)"), 10, 120, int(inv["cash_target_days"]))
            inv["supplier_lead_time_days"] = st.slider(t("供应商交期（天）", "Supplier lead time (days)"), 1, 30, int(inv["supplier_lead_time_days"]))
            inv["seasonality"] = st.selectbox(t("季节因素", "Seasonality"), ["Winter", "Spring", "Summer", "Fall"],
                                            index=["Winter","Spring","Summer","Fall"].index(inv["seasonality"]))
        with col2:
            inv["notes"] = st.text_area(t("备注（可选）", "Notes (optional)"), inv["notes"],
                                     placeholder=t("例如：仓储限制、现金压力、最小起订量等", "Constraints: storage, cash pressure, MOQ, etc."))

        st.subheader(t("ERP 数据", "ERP Data"))
        cA, cB = st.columns([1, 1])
        with cA:
            if st.button(t("加载示例数据", "Load sample data")):
                data = {
                    "Item": ["Synthetic Oil", "Wiper Blades", "Brake Pads", "Tires", "Air Filter"],
                    "Stock": [120, 450, 30, 8, 200],
                    "Cost": [25, 8, 45, 120, 5],
                    "Monthly_Sales": [40, 5, 25, 6, 15]
                }
                inv["df"] = pd.DataFrame(data)
                st.rerun()
        with cB:
            uploaded = st.file_uploader(t("上传 CSV（Item,Stock,Cost,Monthly_Sales）", "Upload CSV (Item,Stock,Cost,Monthly_Sales)"),
                                        type=["csv"])
            if uploaded is not None:
                inv["df"] = pd.read_csv(uploaded)
                st.rerun()

        if inv["df"] is None:
            st.info(t("请先加载示例数据或上传 CSV。", "Load sample data or upload a CSV to continue."))
            return

        df = inv["df"]
        st.dataframe(df, use_container_width=True)

        health = inventory_health(df)
        st.metric(t("库存总价值", "Total Inventory Value"), f"${health['total_value']:,.0f}")
        st.metric(t("滞销库存价值", "Dead Stock Value"), f"${health['dead_value']:,.0f}")

        dead_n = len(health["dead_items"])
        stockout_n = len(health["stockout_items"])
        summary = f"total_value=${health['total_value']:,.0f}; dead_value=${health['dead_value']:,.0f}; dead_items={dead_n}; stockout_risk_items={stockout_n}"
        st.session_state.outputs["inventory_summary"] = summary

        if dead_n > 0:
            st.warning(t(f"发现滞销品：{dead_n} 个", f"Dead stock items detected: {dead_n}"))
            with st.expander(t("查看滞销明细", "View dead stock details")):
                st.dataframe(health["dead_items"], use_container_width=True)

        if stockout_n > 0:
            st.error(t(f"发现缺货风险：{stockout_n} 个", f"Stockout-risk items detected: {stockout_n}"))
            with st.expander(t("查看缺货风险明细", "View stockout-risk details")):
                st.dataframe(health["stockout_items"], use_container_width=True)

    # Step 4
    else:
        pr = st.session_state.pricing
        st.subheader(t("第 4 步：定价 & 一键总分析", "Step 4: Pricing & One-click Final Analysis"))

        col1, col2 = st.columns([1, 1])
        with col1:
            pr["strategy"] = st.selectbox(
                t("定价策略", "Strategy"),
                ["Competitive", "Value-based", "Premium", "Penetration"],
                index=["Competitive","Value-based","Premium","Penetration"].index(pr["strategy"])
            )
            pr["cost"] = st.number_input(t("单位成本（美元）", "Unit Cost (USD)"), min_value=0.0, value=float(pr["cost"]), step=1.0)
            pr["competitor_price"] = st.number_input(t("竞品价格（美元）", "Competitor Price (USD)"), min_value=0.0, value=float(pr["competitor_price"]), step=1.0)

        with col2:
            pr["target_margin"] = st.slider(t("目标毛利率（%）", "Target Margin (%)"), 0, 80, int(pr["target_margin"]))
            pr["elasticity"] = st.selectbox(t("需求弹性", "Demand Elasticity"), ["Low", "Medium", "High"],
                                          index=["Low","Medium","High"].index(pr["elasticity"]))
            pr["notes"] = st.text_area(t("备注（可选）", "Notes (optional)"), pr["notes"],
                                     placeholder=t("例如：促销限制、捆绑策略、最低标价等", "Constraints: promos, bundles, MAP, etc."))

        rec_price = pr["cost"] * (1 + pr["target_margin"] / 100.0)
        st.metric(t("推荐价格（简单计算）", "Recommended Price "), f"${rec_price:,.2f}")

        st.divider()
        st.subheader(t("最终输出（结论/证据/行动/风控）", "Final Output (Conclusion/Evidence/Actions/Risk)"))

        if st.button(t("运行最终分析（开店）", "Run Final Analysis (Open a Store)"), type="primary"):
            p = st.session_state.profile
            s = st.session_state.site
            inv = st.session_state.inventory
            inv_df = inv["df"]
            inv_snapshot = st.session_state.outputs.get("inventory_summary", "No inventory summary available.")

            prompt = f"""
Make a store-opening decision output using ONLY provided inputs.
Return plain text with clear headings:

A) Executive Summary
- 3 bullet conclusions
- Overall Score (0-100) and Confidence (Low/Med/High)

B) Evidence (5-8 bullets)
- Each bullet must cite a specific provided input (traffic/competitors/rent, inventory snapshot, pricing inputs, etc.)

C) Action Plan (10 bullets)
- Group by: Site / Inventory & Cash / Pricing
- Each action must include a metric/target or a next-step instruction

D) Risk Controls (4 bullets)

Inputs:
Business: type={p['business_type']}, stage={p['stage']}, city={p['city']}, budget=${p['budget']},
target_customer={p['target_customer']}, differentiator={p['differentiator']}, notes={p['notes'] if p['notes'].strip() else 'None'}

Site: address={s['address']}, radius={s['radius_miles']} miles, traffic={s['traffic']}, competitors={s['competitors']},
parking={s['parking']}, rent={s['rent_level']}, source={s['foot_traffic_source']}, risk_flags={', '.join(s['risk_flags']) if s['risk_flags'] else 'None'}

Inventory: cash_target_days={inv['cash_target_days']}, lead_time_days={inv['supplier_lead_time_days']},
seasonality={inv['seasonality']}, notes={inv['notes'] if inv['notes'].strip() else 'None'}
Inventory snapshot: {inv_snapshot}
Inventory table:
{inv_df.to_string(index=False) if inv_df is not None else 'Not provided'}

Pricing: strategy={pr['strategy']}, cost={pr['cost']}, competitor_price={pr['competitor_price']},
target_margin={pr['target_margin']}%, elasticity={pr['elasticity']}, notes={pr['notes'] if pr['notes'].strip() else 'None'}
"""
            with st.spinner(t("分析中…", "Analyzing...")):
                out = ask_ai(prompt, mode="open_store")
            st.session_state.outputs["final_open_store"] = out
            st.success(t("完成。", "Done."))
            st.write(out)

        if st.session_state.outputs["final_open_store"]:
            with st.expander(t("上一次输出", "Last output"), expanded=False):
                st.write(st.session_state.outputs["final_open_store"])
                st.divider()

        st.subheader(t("可交付物：AI 报告", "Deliverable: AI Report"))
        colA, colB, colC = st.columns([1, 1, 2])

        with colA:
            if st.button(t("生成 AI 报告", "Generate AI Report"), use_container_width=True):
                with st.spinner(t("生成报告中…", "Generating report...")):
                    report_md = ai_report_open_store()
                st.session_state.outputs["open_store_report_md"] = report_md
                st.rerun()

        with colB:
            if st.button(t("清空报告", "Clear Report"), use_container_width=True):
                st.session_state.outputs["open_store_report_md"] = ""
                st.rerun()

        with colC:
            st.caption(t("说明：报告会基于你前面选择的业务画像/选址/库存/定价生成，不依赖你是否点过“最终分析”。",
                         "Note: Report uses your inputs across steps; independent from the final analysis button."))

        if st.session_state.outputs.get("open_store_report_md", ""):
            st.text_area(t("报告预览", "Report Preview"), st.session_state.outputs["open_store_report_md"], height=520)
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
    st.header(t("运营（帮助企业跑起来）", "Operations (Run the business)"))

    st.markdown(
        "<div class='card'>{}</div>".format(
            t("这里更偏“日常运营”：库存周报、补货策略、促销触发、SOP 检查表等。",
              "This suite focuses on day-to-day operations: weekly inventory review, replenishment rules, promo triggers, SOP checklists.")
        ),
        unsafe_allow_html=True
    )

    tab_ops1, tab_ops2, tab_ops3 = st.tabs([
        t("库存周检", "Inventory Weekly Review"),
        t("定价执行", "Pricing Execution"),
        t("运营问诊", "Ops Advisor")
    ])

    with tab_ops1:
        inv = st.session_state.inventory
        st.subheader(t("库存周检（数据+指标）", "Inventory Weekly Review (Data + Metrics)"))

        colA, colB = st.columns([1, 1])
        with colA:
            if st.button(t("加载示例数据", "Load sample data"), key="ops_load_sample"):
                data = {
                    "Item": ["Synthetic Oil", "Wiper Blades", "Brake Pads", "Tires", "Air Filter"],
                    "Stock": [120, 450, 30, 8, 200],
                    "Cost": [25, 8, 45, 120, 5],
                    "Monthly_Sales": [40, 5, 25, 6, 15]
                }
                inv["df"] = pd.DataFrame(data)
                st.rerun()
        with colB:
            uploaded = st.file_uploader(t("上传 CSV", "Upload CSV"), type=["csv"], key="ops_inv_csv")
            if uploaded is not None:
                inv["df"] = pd.read_csv(uploaded)
                st.rerun()

        if inv["df"] is None:
            st.info(t("请先加载或上传库存数据。", "Load or upload inventory data first."))
        else:
            df = inv["df"]
            health = inventory_health(df)
            st.dataframe(health["df2"], use_container_width=True)

            st.metric(t("库存总价值", "Total Inventory Value"), f"${health['total_value']:,.0f}")
            st.metric(t("滞销库存价值", "Dead Stock Value"), f"${health['dead_value']:,.0f}")

            dead_n = len(health["dead_items"])
            stockout_n = len(health["stockout_items"])
            if dead_n > 0:
                st.warning(t(f"滞销品 {dead_n} 个：建议清仓/捆绑/退换货。", f"Dead stock {dead_n}: consider clearance/bundles/returns."))
            if stockout_n > 0:
                st.error(t(f"缺货风险 {stockout_n} 个：建议提高安全库存。", f"Stockout risk {stockout_n}: increase safety stock."))

            st.markdown("#### " + t("本周动作清单（可勾选）", "This week’s action checklist"))
            st.checkbox(t("清点滞销 Top 10 并制定清仓价", "Identify top 10 dead-stock SKUs and set clearance prices"))
            st.checkbox(t("设置补货阈值（销量×交期×安全系数）", "Set replenishment thresholds (sales × lead time × safety factor)"))
            st.checkbox(t("把库存周报发给负责人并约 15 分钟复盘", "Send weekly report and run a 15-min review"))

    with tab_ops2:
        pr = st.session_state.pricing
        st.subheader(t("定价执行（从策略到动作）", "Pricing Execution (From strategy to actions)"))

        col1, col2 = st.columns([1, 1])
        with col1:
            pr["strategy"] = st.selectbox(
                t("定价策略", "Strategy"),
                ["Competitive", "Value-based", "Premium", "Penetration"],
                index=["Competitive","Value-based","Premium","Penetration"].index(pr["strategy"]),
                key="ops_strategy"
            )
            pr["cost"] = st.number_input(t("单位成本", "Unit Cost"), min_value=0.0, value=float(pr["cost"]), step=1.0, key="ops_cost")
            pr["competitor_price"] = st.number_input(t("竞品价格", "Competitor Price"), min_value=0.0, value=float(pr["competitor_price"]), step=1.0, key="ops_comp")
        with col2:
            pr["target_margin"] = st.slider(t("目标毛利率（%）", "Target Margin (%)"), 0, 80, int(pr["target_margin"]), key="ops_margin")
            pr["elasticity"] = st.selectbox(t("需求弹性", "Demand Elasticity"), ["Low", "Medium", "High"],
                                          index=["Low","Medium","High"].index(pr["elasticity"]), key="ops_elasticity")

        rec_price = pr["cost"] * (1 + pr["target_margin"] / 100.0)
        st.metric(t("建议价（简单）", "Suggested Price (simple)"), f"${rec_price:,.2f}")

        st.markdown("#### " + t("执行规则（你可以按业务调整）", "Execution rules (tune per business)"))
        st.write(t("- 若竞品价明显低于建议价：优先做捆绑/赠品，而不是硬降价。", "- If competitor is far lower: prefer bundles/freebies before cutting price."))
        st.write(t("- 每周固定一天复盘：销量、毛利、投诉、缺货率。", "- Weekly review: sales, margin, complaints, stockout rate."))
        st.write(t("- 促销触发：滞销>2个月 或 库存周转>目标两倍。", "- Promo triggers: dead-stock >2 months or turnover >2× target."))

    with tab_ops3:
        st.subheader(t("运营问诊（AI）", "Operations Advisor (AI)"))
        q = st.text_area(
            t("描述你的运营问题", "Describe your ops problem"),
            placeholder=t("例如：库存占压严重，但又怕缺货；我该怎么设补货阈值？", "E.g., cash tied in inventory but afraid of stockouts. How should I set thresholds?")
        )
        if st.button(t("获取建议", "Get advice"), type="primary"):
            with st.spinner(t("分析中…", "Analyzing...")):
                out = ask_ai(q, mode="operations")
            st.session_state.outputs["ops_ai_output"] = out
            st.write(out)

    st.divider()
    st.subheader(t("可交付物：运营报告（AI）", "Deliverable: Operations Report (AI)"))

    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button(t("生成运营报告", "Generate Ops Report"), type="primary", use_container_width=True):
            with st.spinner(t("生成中…", "Generating...")):
                st.session_state.outputs["ops_report_md"] = ai_report_operations()
            st.rerun()
    with col2:
        if st.button(t("清空运营报告", "Clear Ops Report"), use_container_width=True):
            st.session_state.outputs["ops_report_md"] = ""
            st.rerun()

    if st.session_state.outputs.get("ops_report_md", ""):
        st.text_area(t("运营报告预览", "Ops Report Preview"), st.session_state.outputs["ops_report_md"], height=520)
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
Focus={focus}; Style={style}
User question: {question if question.strip() else 'None'}

User documents (excerpts):
{doc_text}

Return:
1) Key findings (5 bullets)
2) Metrics/ratios you can compute from provided data (if any)
3) Risks & red flags (5 bullets)
4) Action plan (10 bullets with owners/metrics)
5) 3 follow-up questions to improve accuracy
"""
        with st.spinner(t("分析中…", "Analyzing...")):
            out = ask_ai(prompt, mode="finance")
        st.session_state.outputs["finance_ai_output"] = out
        st.write(out)

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
            st.rerun()

    with colB:
        if st.button(t("清空财务报告", "Clear Finance Report"), use_container_width=True):
            st.session_state.outputs["finance_report_md"] = ""
            st.rerun()

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
