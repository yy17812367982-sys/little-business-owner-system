import streamlit as st
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
    page_title="Project B: SME BI Platform",
    layout="wide",
    initial_sidebar_state="collapsed",  # ✅ 桌面端默认收起
)

# =========================================================
# CSS (NO hard overflow hacks; mobile-friendly)
# =========================================================
st.markdown(r"""
<style>
/* ========= Base background ========= */
.stApp{
  background-image:url("https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=2072&auto=format&fit=crop");
  background-size:cover;
  background-position:center;
  background-attachment:fixed; /* desktop ok */
}

/* Dark overlay */
.stApp::before{
  content:"";
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.52);
  pointer-events: none;
  z-index: 0;
}

/* Ensure content above overlay */
div[data-testid="stAppViewContainer"]{
  position: relative;
  z-index: 1;
}

/* Padding: kill bottom empty area */
.block-container{
  padding-top: 1.0rem !important;
  padding-bottom: 0.2rem !important;
}

/* Hide footer to avoid extra whitespace */
footer{ display:none !important; }

/* ========= Typography ========= */
div[data-testid="stAppViewContainer"] :where(h1,h2,h3,h4,p,label,small,li){
  color:#fff !important;
  text-shadow: 0 0 6px rgba(0,0,0,0.65);
}

.stMarkdown p{
  color: rgba(255,255,255,0.75) !important;
  text-shadow: none !important;
}

a, a *{
  color: rgba(180,220,255,0.95) !important;
}

/* ========= Sidebar glass (desktop) ========= */
section[data-testid="stSidebar"]{
  background: rgba(0,0,0,0.42) !important;
  backdrop-filter: blur(12px);
  border-right: 1px solid rgba(255,255,255,0.10);
}

/* ========= Inputs glass ========= */
div[data-baseweb="input"],
div[data-baseweb="base-input"],
div[data-baseweb="select"],
div[data-baseweb="textarea"],
div[data-baseweb="input"] > div,
div[data-baseweb="base-input"] > div{
  background: rgba(0,0,0,0.33) !important;
  border: 1px solid rgba(255,255,255,0.14) !important;
  border-radius: 14px !important;
  backdrop-filter: blur(10px);
  box-shadow: none !important;
}

.stTextInput input,
.stNumberInput input,
.stTextArea textarea{
  background: transparent !important;
  color: rgba(255,255,255,0.95) !important;
}

.stTextInput input::placeholder,
.stTextArea textarea::placeholder{
  color: rgba(255,255,255,0.50) !important;
}

/* Dropdown menu */
div[data-baseweb="menu"],
div[role="listbox"]{
  background: #ffffff !important;
  border: 1px solid rgba(0,0,0,0.18) !important;
  border-radius: 12px !important;
  box-shadow: 0 12px 34px rgba(0,0,0,0.28) !important;
  overflow: hidden !important;
}
div[data-baseweb="menu"] *,
div[role="listbox"] *{
  color: #111 !important;
  text-shadow: none !important;
}

/* Buttons */
button{
  background: rgba(0,0,0,0.30) !important;
  border: 1px solid rgba(255,255,255,0.16) !important;
  color: rgba(255,255,255,0.95) !important;
  border-radius: 14px !important;
  backdrop-filter: blur(10px);
}
button:hover{ background: rgba(255,255,255,0.12) !important; }

/* Card */
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

/* DataFrame */
div[data-testid="stDataFrame"]{
  background: rgba(0,0,0,0.28) !important;
  border: 1px solid rgba(255,255,255,0.10) !important;
  border-radius: 14px !important;
  backdrop-filter: blur(10px);
}

/* ========= Mobile: hide sidebar (avoid overlay), reduce heavy effects ========= */
@media (max-width: 900px){
  /* Hide sidebar completely on mobile to prevent covering content */
  section[data-testid="stSidebar"]{ display:none !important; }

  /* Reduce jank on mobile */
  .stApp{ background-attachment: scroll !important; }
  .card,
  div[data-testid="stMetric"],
  div[data-testid="stDataFrame"],
  div[data-baseweb="tab-list"],
  div[data-baseweb="input"],
  div[data-baseweb="base-input"],
  div[data-baseweb="select"],
  div[data-baseweb="textarea"]{
    backdrop-filter: none !important;
  }
}
</style>
""", unsafe_allow_html=True)

# =========================================================
# Small JS helpers: scroll top / bottom
# =========================================================
def js_scroll_top():
    st.components.v1.html("<script>window.scrollTo({top:0,behavior:'smooth'});</script>", height=0)

def js_scroll_bottom():
    st.components.v1.html("<script>window.scrollTo({top:document.body.scrollHeight,behavior:'smooth'});</script>", height=0)

# =========================================================
# Language
# =========================================================
if "lang" not in st.session_state:
    st.session_state.lang = "en"

def t(zh: str, en: str) -> str:
    return zh if st.session_state.lang == "zh" else en

def toggle_language():
    st.session_state.lang = "en" if st.session_state.lang == "zh" else "zh"
    st.rerun()

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
  answer: "I'm Yangyu's AI assistant."
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
        f"AI 暂时不可用。可能原因：额度/限流、或所选模型需要 Paid。最后错误：{last_err}",
        f"AI temporarily unavailable. Possible causes: quota/rate limit, or model requires Paid. Last error: {last_err}"
    )

# =========================================================
# Geocoding (Nominatim + optional maps.co)
# =========================================================
NOMINATIM_CONTACT_EMAIL = "yy17812367982@gmail.com"
NOMINATIM_UA = f"ProjectB-SME-BI-Platform/1.0 (contact: {NOMINATIM_CONTACT_EMAIL})"
MAPSCO_API_KEY = os.getenv("MAPSCO_API_KEY", "").strip()

def _normalize_query(q: str) -> str:
    q = (q or "").strip()
    return " ".join(q.split())

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
    time.sleep(0.3)

    providers = [{
        "name": "nominatim",
        "url": "https://nominatim.openstreetmap.org/search",
        "build_params": lambda qq: {
            "q": qq, "format": "json", "addressdetails": 1,
            "limit": int(limit), "email": NOMINATIM_CONTACT_EMAIL,
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
                if isinstance(data, list):
                    for d in data[:limit]:
                        lat = d.get("lat")
                        lon = d.get("lon")
                        name = d.get("display_name") or d.get("label") or ""
                        if lat and lon:
                            out.append({"display_name": name, "lat": float(lat), "lon": float(lon)})

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
# Overpass: competitor & traffic estimation (robust)
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
    return ['["shop"]', '["amenity"="restaurant"]', '["amenity"="cafe"]']

def _overpass_post(query: str, timeout: int = 35):
    headers = {"User-Agent": NOMINATIM_UA}
    last_dbg = {"ok": False, "err": "no attempt"}
    body = query.encode("utf-8")

    for ep in OVERPASS_ENDPOINTS:
        time.sleep(0.15 + random.random() * 0.25)
        try:
            resp = requests.post(ep, data=body, headers=headers, timeout=timeout)
            if resp.status_code != 200:
                last_dbg = {"ok": False, "endpoint": ep, "status": resp.status_code,
                            "text_head": (resp.text[:260] if isinstance(resp.text, str) else "")}
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

@st.cache_data(show_spinner=False, ttl=6 * 3600)
def estimate_competitors_overpass(lat: float, lon: float, radius_miles: float, business_type: str):
    r = int(_miles_to_meters(radius_miles))
    filters = _business_to_competitor_osm_filters(business_type)
    parts = [f'nwr{f}(around:{r},{lat},{lon});' for f in filters]

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

@st.cache_data(show_spinner=False, ttl=6 * 3600)
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
        "motorway": 10.0, "trunk": 8.0, "primary": 6.0, "secondary": 4.0,
        "tertiary": 2.5, "residential": 1.0, "unclassified": 1.0,
        "service": 0.6, "living_street": 0.5,
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
    return {"df2": df2, "total_value": total_value, "dead_items": dead, "stockout_items": stockout, "dead_value": dead_value}

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
                chunks.append(f"## {f.name}\n[Unsupported file type]\n")
        except Exception as e:
            chunks.append(f"## {f.name}\n[Failed to parse: {e}]\n")
    return "\n".join(chunks)

# =========================================================
# Sidebar (DESKTOP only; mobile hidden by CSS)
# =========================================================
with st.sidebar:
    st.button(t("🌐 切换语言", "🌐 Switch Language"), on_click=toggle_language)
    st.markdown("---")
    st.markdown("### " + t("功能集合", "Suites"))

    suite_label = st.radio(
        "",
        options=[t("开店（决策流）", "Open a Store"),
                 t("运营（跑起来）", "Operations"),
                 t("财务（分析）", "Finance")],
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
        st.rerun()

    st.markdown("---")
    st.caption("v6.0 Mobile Nav + Smooth Scroll")

# =========================================================
# TOP NAV (always visible; mobile-friendly)
# =========================================================
st.title("Project B: SME BI Platform")

top1, top2, top3, top4, top5 = st.columns([1.2, 1.2, 1.2, 1.2, 2.2])
with top1:
    if st.button(t("🏠 主页", "🏠 Home"), use_container_width=True):
        st.session_state.active_suite = "open_store"
        st.session_state.open_step = 1
        js_scroll_top()
        st.rerun()
with top2:
    if st.button(t("🧭 开店", "🧭 Open"), use_container_width=True):
        st.session_state.active_suite = "open_store"
        st.rerun()
with top3:
    if st.button(t("⚙️ 运营", "⚙️ Ops"), use_container_width=True):
        st.session_state.active_suite = "operations"
        st.rerun()
with top4:
    if st.button(t("💰 财务", "💰 Finance"), use_container_width=True):
        st.session_state.active_suite = "finance"
        st.rerun()
with top5:
    cA, cB = st.columns(2)
    with cA:
        if st.button(t("⬆️ 顶部", "⬆️ Top"), use_container_width=True):
            js_scroll_top()
    with cB:
        if st.button(t("⬇️ 底部", "⬇️ Bottom"), use_container_width=True):
            js_scroll_bottom()

st.markdown("---")

# =========================================================
# Ask AI (top entry)
# =========================================================
with st.expander(t("问 AI（入口）", "Ask AI (Top Entry)"), expanded=False):
    with st.form("top_ai_form", clear_on_submit=True):
        q = st.text_input(t("你想问什么？", "Ask anything..."),
                          placeholder=t("例如：这个地址适合开店吗？我该怎么降库存？",
                                        "E.g., Is this site viable? How do I reduce dead stock?"))
        submitted = st.form_submit_button(t("发送", "Send"), use_container_width=True)

    if submitted and q.strip():
        st.session_state.chat_history.append({"role": "user", "text": q.strip()})
        with st.spinner(t("分析中…", "Analyzing...")):
            ans = ask_ai(q.strip(), mode=st.session_state.active_suite)
        st.session_state.chat_history.append({"role": "ai", "text": ans})

    if st.session_state.chat_history:
        st.markdown("---")
        for m in st.session_state.chat_history[-6:]:
            role = m.get("role")
            txt = (m.get("text") or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            if role == "user":
                st.markdown(f"<div class='card'><b>{t('你', 'You')}:</b><br>{txt}</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div class='card'><b>{t('Yangyu 的 AI', 'Yangyu\\'s AI')}:</b><br>{txt}</div>", unsafe_allow_html=True)

# =========================================================
# Suite 1: Open Store
# =========================================================
def render_open_store():
    st.header(t("开店（决策流）", "Open a Store (Decision Flow)"))

    step_titles = [t("业务画像", "Profile"), t("选址检查", "Site Check"),
                   t("库存与现金", "Inventory & Cash"), t("定价 & 总结", "Pricing & Summary")]
    st.write(f"{t('步骤', 'Step')} {st.session_state.open_step}/4 — {step_titles[st.session_state.open_step-1]}")
    st.progress(st.session_state.open_step / 4.0)

    nav1, nav2, nav3 = st.columns([1, 1, 2])
    with nav1:
        if st.button(t("◀ 上一步", "◀ Back"), use_container_width=True):
            st.session_state.open_step = max(1, st.session_state.open_step - 1)
            js_scroll_top()
            st.rerun()
    with nav2:
        if st.button(t("下一步 ▶", "Next ▶"), use_container_width=True):
            st.session_state.open_step = min(4, st.session_state.open_step + 1)
            js_scroll_top()
            st.rerun()
    with nav3:
        st.caption(t("提示：手机端不使用侧边栏，避免遮挡；顶部导航统一入口。",
                     "Tip: On mobile we avoid sidebar overlay; use top navigation."))

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
        p["notes"] = st.text_area(t("备注（可选）", "Notes (optional)"), p["notes"])

    # Step 2
    elif st.session_state.open_step == 2:
        s = st.session_state.site
        p = st.session_state.profile

        st.subheader(t("第 2 步：选址检查", "Step 2: Site Check"))
        colA, colB = st.columns([1, 2])

        with colA:
            s["address"] = st.text_input(t("地址（支持模糊）", "Address (fuzzy supported)"), s["address"])
            s["radius_miles"] = st.selectbox(t("半径（英里）", "Radius (miles)"), [0.5, 1.0, 3.0],
                                            index=[0.5, 1.0, 3.0].index(s["radius_miles"]))
            s["traffic"] = st.slider(t("人流/车流（估计）", "Traffic (estimated)"), 1000, 50000, int(s["traffic"]), step=500)
            s["competitors"] = st.number_input(t("竞品数量（估计）", "Competitors (estimated)"), min_value=0, value=int(s["competitors"]), step=1)
            s["parking"] = st.selectbox(t("停车便利", "Parking"), ["Low", "Medium", "High"], index=["Low","Medium","High"].index(s["parking"]))
            s["rent_level"] = st.selectbox(t("租金水平", "Rent Level"), ["Low", "Medium", "High"], index=["Low","Medium","High"].index(s["rent_level"]))

        with colB:
            b1, b2 = st.columns([1, 1])
            with b1:
                do_search = st.button("🔎 " + t("Search / Locate", "Search / Locate"), use_container_width=True)
            with b2:
                do_clear = st.button(t("Clear Results", "Clear Results"), use_container_width=True)

            if do_clear:
                st.session_state.site_geo = {"status": "idle", "cands": [], "picked_idx": 0, "debug": {}}
                s.pop("lat", None); s.pop("lon", None)
                s.pop("competitors_debug", None); s.pop("traffic_debug", None)
                st.rerun()

            if do_search:
                query = (s.get("address") or "").strip()
                cands, dbg = geocode_candidates_multi_fuzzy(query, limit=6)
                st.session_state.site_geo = {"status": "ok" if cands else "fail", "cands": cands, "picked_idx": 0, "debug": dbg}
                st.rerun()

            geo = st.session_state.site_geo
            cands = geo.get("cands", []) or []

            if geo.get("status") == "idle" or not cands:
                st.info(t("请点击 Search/Locate 定位。", "Click Search/Locate to geocode."))
                base_lat, base_lon = 40.7590, -73.8290
                st.map(pd.DataFrame({"lat": [base_lat], "lon": [base_lon]}), zoom=12)
            else:
                labels = [c["display_name"] for c in cands]
                idx = int(geo.get("picked_idx", 0))
                idx = max(0, min(idx, len(labels) - 1))

                picked = st.selectbox(t("匹配到多个地址（请选择）", "Multiple matches (pick one)"), labels, index=idx)
                chosen = cands[labels.index(picked)]
                lat, lon = chosen["lat"], chosen["lon"]
                s["lat"], s["lon"] = float(lat), float(lon)

                st.caption(t(f"已定位坐标：{lat:.6f}, {lon:.6f}", f"Located at: {lat:.6f}, {lon:.6f}"))
                st.map(pd.DataFrame({"lat": [lat], "lon": [lon]}), zoom=14)

                e1, e2 = st.columns([1, 1])
                with e1:
                    if st.button(t("自动估算竞品&交通", "Auto-estimate competitors & traffic"), use_container_width=True):
                        bt = p.get("business_type", "Other")
                        rad = float(s.get("radius_miles", 1.0))

                        comp = estimate_competitors_overpass(lat, lon, rad, bt)
                        s["competitors_debug"] = comp
                        if comp.get("ok"):
                            s["competitors"] = int(comp["count"])

                        tp = estimate_traffic_proxy_overpass(lat, lon, rad)
                        s["traffic_debug"] = tp
                        if tp.get("ok"):
                            s["traffic"] = int(tp["traffic_est"])

                        st.rerun()

                with e2:
                    if st.button(t("清空估算结果", "Clear estimates"), use_container_width=True):
                        s.pop("competitors_debug", None)
                        s.pop("traffic_debug", None)
                        st.rerun()

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
        st.subheader(t("第 3 步：库存与现金", "Step 3: Inventory & Cash"))

        col1, col2 = st.columns([1, 1])
        with col1:
            inv["cash_target_days"] = st.slider(t("目标现金周转天数", "Cash target (days)"), 10, 120, int(inv["cash_target_days"]))
            inv["supplier_lead_time_days"] = st.slider(t("供应商交期（天）", "Supplier lead time (days)"), 1, 30, int(inv["supplier_lead_time_days"]))
        with col2:
            inv["seasonality"] = st.selectbox(t("季节因素", "Seasonality"), ["Winter", "Spring", "Summer", "Fall"],
                                             index=["Winter","Spring","Summer","Fall"].index(inv["seasonality"]))
            inv["notes"] = st.text_area(t("备注（可选）", "Notes (optional)"), inv["notes"])

        cA, cB = st.columns([1, 1])
        with cA:
            if st.button(t("加载示例数据", "Load sample data")):
                inv["df"] = pd.DataFrame({
                    "Item": ["Synthetic Oil", "Wiper Blades", "Brake Pads", "Tires", "Air Filter"],
                    "Stock": [120, 450, 30, 8, 200],
                    "Cost": [25, 8, 45, 120, 5],
                    "Monthly_Sales": [40, 5, 25, 6, 15]
                })
                st.rerun()
        with cB:
            uploaded = st.file_uploader(t("上传 CSV（Item,Stock,Cost,Monthly_Sales）", "Upload CSV (Item,Stock,Cost,Monthly_Sales)"),
                                        type=["csv"])
            if uploaded is not None:
                inv["df"] = pd.read_csv(uploaded)
                st.rerun()

        if inv["df"] is None:
            st.info(t("请先加载示例数据或上传 CSV。", "Load sample data or upload CSV."))
            return

        df = inv["df"]
        health = inventory_health(df)
        st.dataframe(health["df2"], use_container_width=True)

        st.metric(t("库存总价值", "Total Inventory Value"), f"${health['total_value']:,.0f}")
        st.metric(t("滞销库存价值", "Dead Stock Value"), f"${health['dead_value']:,.0f}")

        dead_n = len(health["dead_items"])
        stockout_n = len(health["stockout_items"])
        st.session_state.outputs["inventory_summary"] = (
            f"total_value=${health['total_value']:,.0f}; dead_value=${health['dead_value']:,.0f}; "
            f"dead_items={dead_n}; stockout_risk_items={stockout_n}"
        )

    # Step 4
    else:
        pr = st.session_state.pricing
        st.subheader(t("第 4 步：定价", "Step 4: Pricing"))

        col1, col2 = st.columns([1, 1])
        with col1:
            pr["strategy"] = st.selectbox(
                t("定价策略", "Strategy"),
                ["Competitive", "Value-based", "Premium", "Penetration"],
                index=["Competitive","Value-based","Premium","Penetration"].index(pr["strategy"])
            )
            pr["cost"] = st.number_input(t("单位成本（美元）", "Unit Cost (USD)"), min_value=0.0, value=float(pr["cost"]), step=1.0)
            pr["competitor_price"] = st.number_input(t("竞品价格（美元）", "Competitor Price (USD)"),
                                                    min_value=0.0, value=float(pr["competitor_price"]), step=1.0)
        with col2:
            pr["target_margin"] = st.slider(t("目标毛利率（%）", "Target Margin (%)"), 0, 80, int(pr["target_margin"]))
            pr["elasticity"] = st.selectbox(t("需求弹性", "Demand Elasticity"), ["Low", "Medium", "High"],
                                           index=["Low","Medium","High"].index(pr["elasticity"]))
            pr["notes"] = st.text_area(t("备注（可选）", "Notes (optional)"), pr["notes"])

        rec_price = pr["cost"] * (1 + pr["target_margin"] / 100.0)
        st.metric(t("推荐价格（简单计算）", "Recommended Price (simple)"), f"${rec_price:,.2f}")

# =========================================================
# Suite 2: Operations
# =========================================================
def render_operations():
    st.header(t("运营（跑起来）", "Operations"))
    st.markdown(f"<div class='card'>{t('这里偏日常运营：库存周检、补货、定价执行规则。', 'Day-to-day ops: inventory review, replenishment, pricing execution.')}</div>",
                unsafe_allow_html=True)

    tab_ops1, tab_ops2, tab_ops3 = st.tabs([t("库存周检", "Inventory Review"), t("定价执行", "Pricing"), t("运营问诊", "Ops Advisor")])

    with tab_ops1:
        inv = st.session_state.inventory
        cA, cB = st.columns([1, 1])
        with cA:
            if st.button(t("加载示例数据", "Load sample data"), key="ops_sample"):
                inv["df"] = pd.DataFrame({
                    "Item": ["Synthetic Oil", "Wiper Blades", "Brake Pads", "Tires", "Air Filter"],
                    "Stock": [120, 450, 30, 8, 200],
                    "Cost": [25, 8, 45, 120, 5],
                    "Monthly_Sales": [40, 5, 25, 6, 15]
                })
                st.rerun()
        with cB:
            uploaded = st.file_uploader(t("上传 CSV", "Upload CSV"), type=["csv"], key="ops_csv")
            if uploaded is not None:
                inv["df"] = pd.read_csv(uploaded)
                st.rerun()

        if inv["df"] is None:
            st.info(t("请先加载或上传库存数据。", "Load/upload inventory data first."))
        else:
            health = inventory_health(inv["df"])
            st.dataframe(health["df2"], use_container_width=True)

    with tab_ops2:
        pr = st.session_state.pricing
        col1, col2 = st.columns([1, 1])
        with col1:
            pr["cost"] = st.number_input(t("单位成本", "Unit Cost"), min_value=0.0, value=float(pr["cost"]), step=1.0)
            pr["competitor_price"] = st.number_input(t("竞品价格", "Competitor Price"), min_value=0.0, value=float(pr["competitor_price"]), step=1.0)
        with col2:
            pr["target_margin"] = st.slider(t("目标毛利率（%）", "Target Margin (%)"), 0, 80, int(pr["target_margin"]))
        rec_price = pr["cost"] * (1 + pr["target_margin"] / 100.0)
        st.metric(t("建议价（简单）", "Suggested Price (simple)"), f"${rec_price:,.2f}")

    with tab_ops3:
        q = st.text_area(t("描述你的运营问题", "Describe your ops problem"))
        if st.button(t("获取建议", "Get advice"), type="primary"):
            with st.spinner(t("分析中…", "Analyzing...")):
                out = ask_ai(q, mode="operations")
            st.write(out)

# =========================================================
# Suite 3: Finance
# =========================================================
def render_finance():
    st.header(t("财务分析", "Finance"))
    files = st.file_uploader(t("上传资料（可多选）", "Upload files (multi)"),
                             type=["csv", "xlsx", "xls", "txt", "md"], accept_multiple_files=True)
    question = st.text_area(t("你希望重点分析什么？", "What should we focus on?"))

    if st.button(t("开始分析", "Analyze"), type="primary"):
        doc_text = read_uploaded_to_text(files) if files else "[No files uploaded]"
        prompt = f"""
Return Markdown.
User question: {question if question.strip() else 'None'}
User documents (excerpts):
{doc_text}

Return:
1) Key findings (5 bullets)
2) Metrics you can compute (if any)
3) Risks (5 bullets)
4) Action plan (10 bullets with owners/metrics)
5) 3 follow-up questions
"""
        with st.spinner(t("分析中…", "Analyzing...")):
            out = ask_ai(prompt, mode="finance")
        st.write(out)

# =========================================================
# Router
# =========================================================
if st.session_state.active_suite == "open_store":
    render_open_store()
elif st.session_state.active_suite == "operations":
    render_operations()
else:
    render_finance()
