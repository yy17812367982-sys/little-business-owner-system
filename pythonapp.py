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
# MUST be first Streamlit call
# =========================================================
st.set_page_config(
    page_title="Project B: SME BI Platform",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# =========================================================
# Global constants / guardrails
# =========================================================
MAX_AI_INPUT_CHARS = 2500
OVERPASS_COOLDOWN_SECONDS = 10
MAX_TRAFFIC = 200000
MAX_COMPETITORS = 999
REQUIRED_INV_COLS = ["Item", "Stock", "Cost", "Monthly_Sales"]

# =========================================================
# UI: CSS (Menu clickable + Readability + Metrics)
# =========================================================
st.markdown(
    r"""
<style>
/* ---------- App background ---------- */
.stApp{
  background-image:url("https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=2072&auto=format&fit=crop");
  background-size:cover;
  background-position:center;
  background-attachment:fixed;
}
.stApp::before{
  content:""; position: fixed; inset: 0;
  background: rgba(0,0,0,0.55); pointer-events: none; z-index: 0;
}
div[data-testid="stAppViewContainer"]{ position: relative; z-index: 1; }

/* ---------- Typography ---------- */
div[data-testid="stAppViewContainer"] :where(h1,h2,h3,h4,p,label,small,li){
  color:#fff !important;
  text-shadow: 0 2px 12px rgba(0,0,0,0.85) !important;
}
.stMarkdown p{ color: rgba(255,255,255,0.86) !important; text-shadow:none !important; }

/* ---------- Sidebar ---------- */
section[data-testid="stSidebar"]{
  background: rgba(0,0,0,0.86) !important;
  backdrop-filter: blur(16px);
  border-right: 1px solid rgba(255,255,255,0.10);
  z-index: 99999 !important;
}

/* ---------- Header click handling ---------- */
header[data-testid="stHeader"]{
  background: transparent !important;
  pointer-events: none !important;
  z-index: 1000000 !important;
}
header[data-testid="stHeader"] > div{
  pointer-events: auto !important;
}

/* ---------- Collapsed control => big clickable MENU ---------- */
[data-testid="stSidebarCollapsedControl"]{
  position: fixed !important;
  top: 16px !important;
  left: 16px !important;
  z-index: 1000002 !important;

  width: 120px !important;
  height: 46px !important;
  background-color: rgba(0,0,0,0.65) !important;
  border: 1px solid rgba(255,255,255,0.32) !important;
  border-radius: 10px !important;

  display: block !important;
  pointer-events: auto !important;
  cursor: pointer !important;
}
[data-testid="stSidebarCollapsedControl"] button{
  position: absolute !important;
  inset: 0 !important;
  width: 100% !important;
  height: 100% !important;
  margin: 0 !important;
  padding: 0 !important;
  background: transparent !important;
  border: none !important;
  display:flex !important;
  align-items:center !important;
  justify-content:center !important;
  cursor:pointer !important;
}
[data-testid="stSidebarCollapsedControl"] button svg{ display:none !important; }
[data-testid="stSidebarCollapsedControl"] button::before{
  content: "☰ Menu";
  color: #fff !important;
  font-size: 16px !important;
  font-weight: 800 !important;
  letter-spacing: 0.4px;
}
[data-testid="stSidebarCollapsedControl"]:hover{
  background-color: rgba(0,0,0,0.82) !important;
  border-color: rgba(255,255,255,0.6) !important;
}

/* ---------- Inputs glass ---------- */
div[data-baseweb="input"], div[data-baseweb="base-input"], div[data-baseweb="select"], div[data-baseweb="textarea"],
div[data-baseweb="input"] > div, div[data-baseweb="base-input"] > div{
  background: rgba(0,0,0,0.33) !important;
  border: 1px solid rgba(255,255,255,0.14) !important;
  border-radius: 12px !important;
  backdrop-filter: blur(8px);
}
.stTextInput input, .stNumberInput input, .stTextArea textarea{
  background: transparent !important;
  color: rgba(255,255,255,0.96) !important;
}

/* dropdown menu */
div[data-baseweb="menu"], div[role="listbox"]{
  background:#fff !important;
  border-radius: 10px !important;
}
div[data-baseweb="menu"] *, div[role="listbox"] *{
  color:#111 !important;
  text-shadow:none !important;
}

/* ---------- Metric visibility ---------- */
div[data-testid="stMetricLabel"] *{
  color: rgba(255,255,255,0.92) !important;
  text-shadow: 0 2px 12px rgba(0,0,0,0.9) !important;
}
div[data-testid="stMetricValue"] *{
  color: rgba(255,255,255,0.99) !important;
  font-weight: 900 !important;
  text-shadow: 0 2px 18px rgba(0,0,0,0.98) !important;
}
div[data-testid="metric-container"]{
  background: rgba(0,0,0,0.42) !important;
  border: 1px solid rgba(255,255,255,0.14) !important;
  border-radius: 14px !important;
  padding: 12px 14px !important;
  backdrop-filter: blur(10px);
}

/* ---------- cards ---------- */
.card{
  background: rgba(0,0,0,0.32);
  border: 1px solid rgba(255,255,255,0.12);
  border-radius: 16px;
  padding: 14px 16px;
  margin: 8px 0;
  backdrop-filter: blur(10px);
}

/* scrollbar */
::-webkit-scrollbar{ width:6px; height:6px; }
::-webkit-scrollbar-thumb{ background: rgba(255,255,255,0.25); border-radius:10px; }
::-webkit-scrollbar-track{ background: transparent; }
</style>
""",
    unsafe_allow_html=True,
)

# =========================================================
# Language helper
# =========================================================
if "lang" not in st.session_state:
    st.session_state.lang = "en"


def t(zh: str, en: str) -> str:
    return zh if st.session_state.lang == "zh" else en


def toggle_language():
    st.session_state.lang = "en" if st.session_state.lang == "zh" else "zh"
    st.rerun()


# =========================================================
# AI client
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
- If asked "Who are you?" or "What model are you?":
  answer: "I'm Yangyu's AI assistant."
- Output structured, actionable; prefer bullet points, metrics, and next steps.
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
    if user_prompt and len(user_prompt) > MAX_AI_INPUT_CHARS:
        return t(
            f"你输入太长了（{len(user_prompt)} 字符）。请缩短到 {MAX_AI_INPUT_CHARS} 以内，或拆分几段。",
            f"Input too long ({len(user_prompt)} chars). Please keep within {MAX_AI_INPUT_CHARS} chars or split.",
        )
    if not API_KEY or not client:
        return t("AI 未配置（缺少 GEMINI_API_KEY）。", "AI is not configured (missing GEMINI_API_KEY).")

    mode_hint = {
        "general": "General Q&A. Be concise and practical.",
        "open_store": "Focus on store-opening decisions: site, checklist, risks, actions.",
        "operations": "Focus on operations: inventory, SOPs, pricing execution, weekly loops.",
        "finance": "Focus on cash flow, margins, scenario, controls, financial actions.",
    }.get(mode, "General Q&A.")

    prompt = f"{SYSTEM_POLICY}\n\nMode: {mode_hint}\n\nUser:\n{user_prompt}"
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
                    time.sleep(1.1 + random.random())
                    continue
                break

    return t(f"AI 暂时不可用：{last_err}", f"AI temporarily unavailable: {last_err}")


# =========================================================
# Geocoding / Overpass
# =========================================================
DEFAULT_NOMINATIM_EMAIL = os.getenv("NOMINATIM_CONTACT_EMAIL", "")
try:
    DEFAULT_NOMINATIM_EMAIL = st.secrets.get("NOMINATIM_CONTACT_EMAIL", DEFAULT_NOMINATIM_EMAIL)
except Exception:
    pass
NOMINATIM_CONTACT_EMAIL = (DEFAULT_NOMINATIM_EMAIL or "").strip()
NOMINATIM_UA = "ProjectB-SME-BI-Platform/1.0" + (
    f" (contact: {NOMINATIM_CONTACT_EMAIL})" if NOMINATIM_CONTACT_EMAIL else ""
)
MAPSCO_API_KEY = os.getenv("MAPSCO_API_KEY", "").strip()

OVERPASS_ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.nchc.org.tw/api/interpreter",
]


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

    # loose tokens
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

    time.sleep(0.5)

    providers = [
        {
            "name": "nominatim",
            "url": "https://nominatim.openstreetmap.org/search",
            "build_params": lambda qq: {
                "q": qq,
                "format": "json",
                "addressdetails": 1,
                "limit": int(limit),
                **({"email": NOMINATIM_CONTACT_EMAIL} if NOMINATIM_CONTACT_EMAIL else {}),
                "accept-language": "en",
            },
        }
    ]
    if MAPSCO_API_KEY:
        providers.append(
            {
                "name": "maps_co",
                "url": "https://geocode.maps.co/search",
                "build_params": lambda qq: {"q": qq, "api_key": MAPSCO_API_KEY},
            }
        )

    last_debug = {"ok": False, "err": "no attempt"}
    for qq in queries:
        for p in providers:
            try:
                params = p["build_params"](qq)
                data, dbg = _request_json(p["url"], params=params, headers=headers, timeout=12)

                out = []
                if p["name"] == "nominatim" and isinstance(data, list):
                    for d in data[:limit]:
                        if "lat" in d and "lon" in d:
                            out.append(
                                {
                                    "display_name": d.get("display_name", ""),
                                    "lat": float(d["lat"]),
                                    "lon": float(d["lon"]),
                                }
                            )
                elif isinstance(data, list):
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
                if "429" in str(e):
                    time.sleep(1.0 + random.random())
                continue

    return [], last_debug


def _miles_to_meters(mi: float) -> float:
    return float(mi) * 1609.344


def _clamp(x, lo, hi):
    return max(lo, min(hi, x))


def _business_to_competitor_osm_filters(business_type: str):
    bt = (business_type or "").lower()
    if "auto" in bt:
        return ['["shop"="car_parts"]', '["shop"="tyres"]', '["shop"="car_repair"]', '["amenity"="fuel"]']
    if "convenience" in bt:
        return ['["shop"="convenience"]', '["shop"="supermarket"]', '["shop"="grocery"]']
    if "coffee" in bt:
        return ['["amenity"="cafe"]', '["shop"="coffee"]', '["amenity"="fast_food"]']
    if "restaurant" in bt:
        return ['["amenity"="restaurant"]', '["amenity"="fast_food"]', '["amenity"="cafe"]']
    if "beauty" in bt or "salon" in bt:
        return ['["shop"="beauty"]', '["shop"="hairdresser"]', '["amenity"="spa"]']
    return ['["shop"]', '["amenity"="restaurant"]', '["amenity"="cafe"]']


def _overpass_post(query: str, timeout: int = 35):
    headers = {"User-Agent": NOMINATIM_UA}
    body = query.encode("utf-8")
    last_dbg = {"ok": False, "err": "no attempt"}

    for ep in OVERPASS_ENDPOINTS:
        time.sleep(0.2 + random.random() * 0.2)
        try:
            resp = requests.post(ep, data=body, headers=headers, timeout=timeout)
            if resp.status_code != 200:
                last_dbg = {"ok": False, "endpoint": ep, "status": resp.status_code, "text_head": resp.text[:260]}
                if resp.status_code in (429, 502, 503, 504):
                    continue
                return None, last_dbg
            return resp.json(), {"ok": True, "endpoint": ep, "status": resp.status_code}
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
        return {"ok": False, "count": None, "debug": dbg}
    elements = data.get("elements", []) or []
    seen = set((e.get("type"), e.get("id")) for e in elements if e.get("type") and e.get("id"))
    return {"ok": True, "count": len(seen), "debug": dbg}


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
        return {"ok": False, "traffic_est": None, "debug": dbg}

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
    for e in elements:
        tags = e.get("tags", {}) or {}
        hw = tags.get("highway")
        if hw:
            score += weights.get(hw, 0.8)

    traffic_est = int(_clamp(1000 + score * 120, 1000, MAX_TRAFFIC))
    return {"ok": True, "traffic_est": traffic_est, "debug": dbg}


# =========================================================
# State init
# =========================================================
if "active_suite" not in st.session_state:
    st.session_state.active_suite = "open_store"

if "open_step" not in st.session_state:
    st.session_state.open_step = 1

if "last_overpass_ts" not in st.session_state:
    st.session_state.last_overpass_ts = 0.0

if "profile" not in st.session_state:
    st.session_state.profile = {
        "business_type": "Auto Parts Store",
        "stage": "Planning",
        "budget": 80000,
        "target_customer": "Local residents and small fleets",
        "differentiator": "Fast service + reliable stock",
        "city": "New York",
        "notes": "",
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
        "risk_flags": [],
    }

if "inventory" not in st.session_state:
    st.session_state.inventory = {
        "df": None,
        "cash_target_days": 45,
        "supplier_lead_time_days": 7,
        "seasonality": "Winter",
        "notes": "",
    }

if "pricing" not in st.session_state:
    st.session_state.pricing = {
        "strategy": "Competitive",
        "cost": 100.0,
        "target_margin": 30,
        "competitor_price": 135.0,
        "elasticity": "Medium",
        "notes": "",
    }

if "outputs" not in st.session_state:
    st.session_state.outputs = {
        "open_store_report_md": "",
        "inventory_summary": "",
        "ops_report_md": "",
        "finance_report_md": "",
    }

if "site_geo" not in st.session_state:
    st.session_state.site_geo = {"status": "idle", "cands": [], "picked_idx": 0, "debug": {}}

# suite 切换后自动收起 sidebar 的触发旗标（JS 尝试）
if "collapse_sidebar_once" not in st.session_state:
    st.session_state.collapse_sidebar_once = False


# =========================================================
# Validations / scoring
# =========================================================
def score_from_inputs_site(traffic: int, competitors: int, rent_level: str, parking: str) -> int:
    score = 55
    if traffic >= 80000:
        score += 14
    elif traffic >= 40000:
        score += 10
    elif traffic >= 25000:
        score += 6
    else:
        score += 2

    if competitors <= 6:
        score += 12
    elif competitors <= 12:
        score += 6
    elif competitors <= 25:
        score += 0
    else:
        score -= 6

    if rent_level == "Low":
        score += 8
    elif rent_level == "Medium":
        score += 3
    else:
        score -= 6

    if parking == "High":
        score += 6
    elif parking == "Medium":
        score += 2
    else:
        score -= 4

    return int(max(0, min(100, score)))


def validate_site_inputs(traffic: int, competitors: int, radius: float):
    warns = []
    if traffic < 1000 or traffic > MAX_TRAFFIC:
        warns.append(
            t(
                f"Traffic 建议范围 1000~{MAX_TRAFFIC}（你填的是 {traffic}）。",
                f"Traffic recommended range: 1000~{MAX_TRAFFIC} (you entered {traffic}).",
            )
        )
    if competitors < 0 or competitors > MAX_COMPETITORS:
        warns.append(
            t(
                f"Competitors 建议范围 0~{MAX_COMPETITORS}（你填的是 {competitors}）。",
                f"Competitors recommended range: 0~{MAX_COMPETITORS} (you entered {competitors}).",
            )
        )
    if radius >= 3.0 and competitors > 50:
        warns.append(
            t("半径=3 miles 且竞品很高：口径可能过宽，建议先用 0.5 或 1 mile。",
              "Radius=3 miles with high competitors: likely too broad; try 0.5 or 1 mile first.")
        )
    return warns


def validate_inventory_df(df: pd.DataFrame):
    missing = [c for c in REQUIRED_INV_COLS if c not in df.columns]
    if missing:
        return False, t(f"库存CSV缺少列：{missing}。必须包含：{REQUIRED_INV_COLS}",
                        f"Inventory CSV missing columns: {missing}. Required: {REQUIRED_INV_COLS}")
    # numeric sanity
    for c in ["Stock", "Cost", "Monthly_Sales"]:
        if not np.issubdtype(df[c].dtype, np.number):
            return False, t(f"列 {c} 必须是数字。", f"Column {c} must be numeric.")
    if (df["Stock"] < 0).any() or (df["Cost"] < 0).any() or (df["Monthly_Sales"] < 0).any():
        return False, t("Stock/Cost/Monthly_Sales 不应为负数。", "Stock/Cost/Monthly_Sales should not be negative.")
    return True, ""


def inventory_health(df: pd.DataFrame) -> dict:
    df2 = df.copy()
    df2["Total_Value"] = df2["Stock"] * df2["Cost"]
    df2["Months_Of_Cover"] = np.where(df2["Monthly_Sales"] > 0, df2["Stock"] / df2["Monthly_Sales"], np.inf)

    months = df2["Months_Of_Cover"].replace([np.inf, -np.inf], np.nan)
    dead = df2[(df2["Monthly_Sales"] < df2["Stock"] * 0.1) & (months.fillna(999) > 6)]
    stockout = df2[(df2["Stock"] <= 10) & (df2["Monthly_Sales"] >= 10)]

    total_value = float(df2["Total_Value"].sum())
    dead_value = float(dead["Total_Value"].sum()) if len(dead) else 0.0
    df2["Months_Of_Cover"] = df2["Months_Of_Cover"].replace([np.inf, -np.inf], 999)

    return {
        "df2": df2,
        "total_value": total_value,
        "dead_items": dead,
        "stockout_items": stockout,
        "dead_value": dead_value,
    }


def validate_pricing(cost: float, competitor_price: float, margin: float):
    if cost <= 0:
        return False, t("单位成本必须 > 0。", "Unit cost must be > 0.")
    if competitor_price <= 0:
        return False, t("竞品价格必须 > 0。", "Competitor price must be > 0.")
    if margin < 0 or margin > 200:
        return False, t("目标毛利率建议 0~200%。", "Target margin recommended 0~200%.")
    return True, ""


# =========================================================
# Auto-collapse sidebar (best-effort JS)
# =========================================================
def collapse_sidebar_best_effort():
    # 只触发一次，避免无限 rerun
    if st.session_state.collapse_sidebar_once:
        st.session_state.collapse_sidebar_once = False
        st.markdown(
            """
            <script>
              // Try to close sidebar by clicking main container (works on many builds/mobile)
              setTimeout(() => {
                const main = window.parent.document.querySelector('div[data-testid="stAppViewContainer"]');
                if (main) { main.click(); }
              }, 80);
            </script>
            """,
            unsafe_allow_html=True,
        )


# =========================================================
# Sidebar
# =========================================================
with st.sidebar:
    st.button(t("🌐 切换语言", "🌐 Switch Language"), on_click=toggle_language, key="sb_lang_btn")
    st.markdown("---")

    st.markdown("### " + t("功能集合", "Suites"))
    suite_label = st.radio(
        "",
        options=[
            t("开店（决策流）", "Open a Store"),
            t("运营（跑起来）", "Operations"),
            t("财务（分析）", "Finance"),
        ],
        index={"open_store": 0, "operations": 1, "finance": 2}.get(st.session_state.active_suite, 0),
        key="sb_suite_radio",
    )

    mapping = {
        t("开店（决策流）", "Open a Store"): "open_store",
        t("运营（跑起来）", "Operations"): "operations",
        t("财务（分析）", "Finance"): "finance",
    }
    new_suite = mapping[suite_label]
    if new_suite != st.session_state.active_suite:
        st.session_state.active_suite = new_suite
        st.session_state.collapse_sidebar_once = True  # suite 变更后尝试自动收起
        st.rerun()

    st.markdown("---")
    st.caption("v5.5 Full merged build")


# =========================================================
# Main
# =========================================================
st.title("Project B: SME BI Platform")
collapse_sidebar_best_effort()

# =========================================================
# TOP AI (small entry)
# =========================================================
with st.expander(t("问 AI（快捷入口）", "Ask AI (Quick Entry)"), expanded=False):
    mode = st.session_state.active_suite
    q = st.text_input(t("输入问题", "Your question"), key="top_ai_q", placeholder=t("例如：这家店开还是不开？", "E.g., should I open or not?"))
    colq1, colq2 = st.columns([1, 1])
    with colq1:
        st.session_state.ai_quality = st.selectbox(
            t("质量", "Quality"),
            options=["pro", "fast"],
            index=0 if st.session_state.ai_quality == "pro" else 1,
            key="top_ai_quality",
        )
    with colq2:
        go = st.button(t("发送", "Send"), key="top_ai_send", use_container_width=True)

    if go and q.strip():
        with st.spinner(t("分析中…", "Analyzing...")):
            ans = ask_ai(q.strip(), mode=mode)
        st.markdown("<div class='card'>"+ans.replace("\n","<br>")+"</div>", unsafe_allow_html=True)


# =========================================================
# Suite: Open Store
# =========================================================
def ai_report_open_store() -> str:
    p = st.session_state.profile
    s = st.session_state.site
    inv = st.session_state.inventory
    pr = st.session_state.pricing

    inv_snapshot = st.session_state.outputs.get("inventory_summary", "No inventory summary available.")
    inv_df = inv.get("df", None)

    site_score = score_from_inputs_site(int(s["traffic"]), int(s["competitors"]), s["rent_level"], s["parking"])
    rec_price = pr["cost"] * (1 + pr["target_margin"] / 100.0)

    prompt = f"""
Return Markdown.

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


def render_open_store():
    st.header(t("开店（决策流）", "Open a Store (Decision Flow)"))

    step_titles = [
        t("业务画像", "Profile"),
        t("选址检查", "Site Check"),
        t("库存与现金", "Inventory & Cash"),
        t("定价 & 总结", "Pricing & Summary"),
    ]
    st.write(f"{t('步骤', 'Step')} {st.session_state.open_step}/4 — {step_titles[st.session_state.open_step-1]}")
    st.progress(st.session_state.open_step / 4.0)

    nav1, nav2, nav3 = st.columns([1, 1, 2])
    with nav1:
        if st.button(t("◀ 上一步", "◀ Back"), use_container_width=True, key="os_back_btn"):
            st.session_state.open_step = max(1, st.session_state.open_step - 1)
            st.rerun()
    with nav2:
        if st.button(t("下一步 ▶", "Next ▶"), use_container_width=True, key="os_next_btn"):
            st.session_state.open_step = min(4, st.session_state.open_step + 1)
            st.rerun()
    with nav3:
        st.caption(t("提示：此集合专注开店决策。运营/财务在其它集合更细。",
                     "Tip: This suite focuses on launch decisions. Ops/Finance are more detailed elsewhere."))

    # Step 1: Profile
    if st.session_state.open_step == 1:
        p = st.session_state.profile
        st.subheader(t("第 1 步：业务画像", "Step 1: Business Profile"))
        c1, c2 = st.columns(2)
        with c1:
            p["business_type"] = st.selectbox(
                t("业态类型", "Business Type"),
                ["Auto Parts Store", "Convenience Store", "Coffee Shop", "Restaurant", "Beauty Salon", "Other"],
                index=["Auto Parts Store", "Convenience Store", "Coffee Shop", "Restaurant", "Beauty Salon", "Other"].index(
                    p["business_type"] if p["business_type"] in ["Auto Parts Store", "Convenience Store", "Coffee Shop", "Restaurant", "Beauty Salon", "Other"] else "Other"
                ),
                key="os_bt",
            )
            p["stage"] = st.selectbox(
                t("阶段", "Stage"),
                ["Planning", "Open Soon", "Operating", "Expansion"],
                index=["Planning", "Open Soon", "Operating", "Expansion"].index(p["stage"]) if p["stage"] in ["Planning", "Open Soon", "Operating", "Expansion"] else 0,
                key="os_stage",
            )
            p["city"] = st.text_input(t("城市", "City"), p["city"], key="os_city")
        with c2:
            p["budget"] = st.number_input(t("初始预算（美元）", "Initial Budget (USD)"), min_value=0, value=int(p["budget"]), step=1000, key="os_budget")
            p["target_customer"] = st.text_input(t("目标客户", "Target Customer"), p["target_customer"], key="os_cust")
            p["differentiator"] = st.text_input(t("差异化", "Differentiator"), p["differentiator"], key="os_diff")
        p["notes"] = st.text_area(t("备注（可选）", "Notes (optional)"), p["notes"], key="os_notes")

    # Step 2: Site
    elif st.session_state.open_step == 2:
        s = st.session_state.site
        p = st.session_state.profile

        st.subheader(t("第 2 步：选址检查", "Step 2: Site Check"))
        colA, colB = st.columns([1, 2])

        with colA:
            s["address"] = st.text_input(t("地址（支持模糊）", "Address (fuzzy supported)"), s["address"], key="os_addr")
            s["radius_miles"] = st.selectbox(t("半径（英里）", "Radius (miles)"), [0.5, 1.0, 3.0],
                                             index=[0.5, 1.0, 3.0].index(s["radius_miles"]), key="os_radius")
            s["traffic"] = st.slider(t("人流/车流（估计）", "Traffic (estimated)"), 1000, MAX_TRAFFIC, int(s["traffic"]), step=500, key="os_traffic")
            s["competitors"] = st.number_input(t("竞品数量（估计）", "Competitors (estimated)"), 0, MAX_COMPETITORS, int(s["competitors"]), 1, key="os_comp")
            s["parking"] = st.selectbox(t("停车便利", "Parking"), ["Low", "Medium", "High"], index=["Low", "Medium", "High"].index(s["parking"]), key="os_parking")
            s["rent_level"] = st.selectbox(t("租金水平", "Rent Level"), ["Low", "Medium", "High"], index=["Low", "Medium", "High"].index(s["rent_level"]), key="os_rent")

        with colB:
            st.subheader(t("地图预览", "Map Preview"))
            b1, b2 = st.columns(2)
            with b1:
                do_search = st.button("🔎 " + t("Search / Locate", "Search / Locate"), use_container_width=True, key="os_search_btn")
            with b2:
                do_clear = st.button(t("Clear", "Clear"), use_container_width=True, key="os_clear_geo_btn")

            if do_clear:
                st.session_state.site_geo = {"status": "idle", "cands": [], "picked_idx": 0, "debug": {}}
                s.pop("lat", None)
                s.pop("lon", None)
                st.rerun()

            if do_search:
                cands, dbg = geocode_candidates_multi_fuzzy(s["address"], limit=6)
                st.session_state.site_geo = {"status": "ok" if cands else "fail", "cands": cands, "picked_idx": 0, "debug": dbg}

            geo = st.session_state.site_geo
            cands = geo.get("cands", []) or []

            if not cands:
                st.info(t("暂无结果或未搜索。", "No results yet or search failed."))
                st.map(pd.DataFrame({"lat": [40.7590], "lon": [-73.8290]}), zoom=12)
            else:
                labels = [c["display_name"] for c in cands]
                pick = st.selectbox(t("请选择匹配地址", "Pick a match"), labels, index=0, key="os_pick_addr")
                chosen = cands[labels.index(pick)]
                s["lat"], s["lon"] = float(chosen["lat"]), float(chosen["lon"])
                st.map(pd.DataFrame({"lat": [s["lat"]], "lon": [s["lon"]]}), zoom=14)

                can_run = (time.time() - float(st.session_state.last_overpass_ts)) >= OVERPASS_COOLDOWN_SECONDS
                btn = st.button(t("自动估算竞品&交通", "Auto-estimate competitors & traffic"),
                                use_container_width=True, key="os_overpass_btn", disabled=not can_run)
                if btn:
                    st.session_state.last_overpass_ts = time.time()
                    comp = estimate_competitors_overpass(s["lat"], s["lon"], float(s["radius_miles"]), p["business_type"])
                    traf = estimate_traffic_proxy_overpass(s["lat"], s["lon"], float(s["radius_miles"]))
                    if comp.get("ok"):
                        s["competitors"] = int(min(MAX_COMPETITORS, comp["count"]))
                    if traf.get("ok"):
                        s["traffic"] = int(_clamp(traf["traffic_est"], 1000, MAX_TRAFFIC))
                    st.rerun()

                if not can_run:
                    wait_s = int(OVERPASS_COOLDOWN_SECONDS - (time.time() - float(st.session_state.last_overpass_ts)))
                    st.caption(t(f"⏳ 冷却 {max(wait_s,0)} 秒", f"⏳ Cooling down {max(wait_s,0)}s"))

        for w in validate_site_inputs(int(s["traffic"]), int(s["competitors"]), float(s["radius_miles"])):
            st.warning(w)

        score = score_from_inputs_site(int(s["traffic"]), int(s["competitors"]), s["rent_level"], s["parking"])
        rf = []
        if int(s["competitors"]) > 25:
            rf.append(t("竞品密度偏高", "High competitive density"))
        if s["rent_level"] == "High":
            rf.append(t("租金偏高", "High rent"))
        if s["parking"] == "Low":
            rf.append(t("停车不便", "Low parking"))
        s["risk_flags"] = rf

        m1, m2, m3 = st.columns(3)
        m1.metric(t("选址评分", "Site Score"), score)
        m2.metric(t("竞品数", "Competitors"), int(s["competitors"]))
        m3.metric(t("流量", "Traffic"), int(s["traffic"]))

        if rf:
            st.warning(t("风险提示：", "Risk flags: ") + "，".join(rf))
        else:
            st.success(t("未发现明显风险标记。", "No major risk flags."))

    # Step 3: Inventory & Cash
    elif st.session_state.open_step == 3:
        inv = st.session_state.inventory
        st.subheader(t("第 3 步：库存与现金", "Step 3: Inventory & Cash"))

        c1, c2 = st.columns([1, 1])
        with c1:
            inv["cash_target_days"] = st.number_input(
                t("现金安全垫（天）", "Cash buffer (days)"),
                min_value=7,
                max_value=365,
                value=int(inv["cash_target_days"]),
                step=1,
                key="os_cash_days",
            )
            inv["supplier_lead_time_days"] = st.number_input(
                t("供货周期（天）", "Supplier lead time (days)"),
                min_value=1,
                max_value=120,
                value=int(inv["supplier_lead_time_days"]),
                step=1,
                key="os_lead_days",
            )
            inv["seasonality"] = st.selectbox(
                t("季节性", "Seasonality"),
                ["None", "Spring", "Summer", "Fall", "Winter"],
                index=["None", "Spring", "Summer", "Fall", "Winter"].index(inv["seasonality"]) if inv["seasonality"] in ["None", "Spring", "Summer", "Fall", "Winter"] else 0,
                key="os_season",
            )
        with c2:
            inv["notes"] = st.text_area(t("库存/现金备注", "Inventory/Cash notes"), inv["notes"], key="os_inv_notes")

        st.markdown("#### " + t("上传库存 CSV（可选）", "Upload inventory CSV (optional)"))
        up = st.file_uploader("CSV", type=["csv"], key="os_inv_upload")
        if up is not None:
            try:
                df = pd.read_csv(up)
                ok, msg = validate_inventory_df(df)
                if not ok:
                    st.error(msg)
                else:
                    inv["df"] = df
                    st.success(t("库存表已载入。", "Inventory loaded."))
            except Exception as e:
                st.error(t(f"读取失败：{e}", f"Failed to read: {e}"))

        if isinstance(inv.get("df"), pd.DataFrame):
            health = inventory_health(inv["df"])
            df2 = health["df2"]

            st.markdown("#### " + t("库存概览", "Inventory snapshot"))
            total_value = health["total_value"]
            dead_value = health["dead_value"]
            dead_ratio = (dead_value / total_value) if total_value > 0 else 0.0

            m1, m2, m3 = st.columns(3)
            m1.metric(t("库存总价值", "Total Inventory Value"), f"${total_value:,.0f}")
            m2.metric(t("疑似滞销金额", "Dead stock value"), f"${dead_value:,.0f}")
            m3.metric(t("滞销占比", "Dead stock ratio"), f"{dead_ratio*100:.1f}%")

            st.session_state.outputs["inventory_summary"] = (
                f"TotalValue=${total_value:,.0f}; DeadValue=${dead_value:,.0f} ({dead_ratio*100:.1f}%); "
                f"StockoutItems={len(health['stockout_items'])}"
            )

            with st.expander(t("查看明细（前 50 行）", "Details (first 50 rows)"), expanded=False):
                st.dataframe(df2.head(50), use_container_width=True)

            if len(health["dead_items"]) > 0:
                st.warning(t("发现疑似滞销：建议做降价/捆绑/退换/清仓策略。", "Dead stock detected: consider discount/bundle/return/clearance."))
            if len(health["stockout_items"]) > 0:
                st.warning(t("发现可能缺货：建议提高安全库存/缩短补货周期。", "Potential stockouts: consider higher safety stock or faster replenishment."))
        else:
            st.info(t("未上传库存也可以继续。", "You can proceed without inventory upload."))

    # Step 4: Pricing & Summary
    elif st.session_state.open_step == 4:
        pr = st.session_state.pricing
        st.subheader(t("第 4 步：定价 & 总结", "Step 4: Pricing & Summary"))

        c1, c2 = st.columns(2)
        with c1:
            pr["strategy"] = st.selectbox(t("定价策略", "Pricing strategy"),
                                          ["Competitive", "Premium", "Penetration", "Value-Based"],
                                          index=["Competitive", "Premium", "Penetration", "Value-Based"].index(pr["strategy"]) if pr["strategy"] in ["Competitive", "Premium", "Penetration", "Value-Based"] else 0,
                                          key="os_price_strategy")
            pr["cost"] = st.number_input(t("单位成本（USD）", "Unit cost (USD)"), min_value=0.01, value=float(pr["cost"]), step=1.0, key="os_cost")
            pr["target_margin"] = st.slider(t("目标毛利率（%）", "Target margin (%)"), 0, 200, int(pr["target_margin"]), key="os_margin")
        with c2:
            pr["competitor_price"] = st.number_input(t("竞品价格（USD）", "Competitor price (USD)"), min_value=0.01, value=float(pr["competitor_price"]), step=1.0, key="os_comp_price")
            pr["elasticity"] = st.selectbox(t("价格弹性", "Elasticity"), ["Low", "Medium", "High"],
                                            index=["Low", "Medium", "High"].index(pr["elasticity"]) if pr["elasticity"] in ["Low","Medium","High"] else 1,
                                            key="os_elasticity")
            pr["notes"] = st.text_area(t("定价备注", "Pricing notes"), pr["notes"], key="os_price_notes")

        ok, msg = validate_pricing(float(pr["cost"]), float(pr["competitor_price"]), float(pr["target_margin"]))
        if not ok:
            st.error(msg)
            return

        rec_price = float(pr["cost"]) * (1.0 + float(pr["target_margin"]) / 100.0)
        st.metric(t("建议价格（简单）", "Recommended Price (simple)"), f"${rec_price:,.2f}")

        st.divider()
        if st.button(t("生成最终开店报告", "Run Final Analysis (Open a Store)"), key="os_final_btn", use_container_width=True):
            with st.spinner(t("生成中…", "Generating...")):
                md = ai_report_open_store()
            st.session_state.outputs["open_store_report_md"] = md
            st.success(t("已生成报告。", "Report generated."))

        md = st.session_state.outputs.get("open_store_report_md", "")
        if md:
            st.markdown(md)


# =========================================================
# Suite: Operations
# =========================================================
def ai_report_operations() -> str:
    inv = st.session_state.inventory
    inv_df = inv.get("df")
    inv_table = inv_df.head(80).to_string(index=False) if isinstance(inv_df, pd.DataFrame) else "Not provided"
    inv_snapshot = st.session_state.outputs.get("inventory_summary", "No inventory summary available.")

    prompt = f"""
Return Markdown.

# Operations Report
## Current Snapshot
- Inventory snapshot: {inv_snapshot}
- Cash buffer days: {inv['cash_target_days']}
- Lead time days: {inv['supplier_lead_time_days']}
- Seasonality: {inv['seasonality']}

## SOP建议（可落地）
- Receiving / Replenishment / Pricing execution / Weekly review

## KPI（至少8项）
- 每项要有口径和目标建议

## Next 14 days action plan（12条）
- 每条包含 Owner + Metric/Target

Inventory table:
{inv_table}
"""
    return ask_ai(prompt, mode="operations")


def render_operations():
    st.header(t("运营（跑起来）", "Operations"))
    st.caption(t("这里更关注：库存周转、补货规则、执行SOP、每周复盘。",
                 "Focus: inventory turns, replenishment rules, SOP execution, weekly review."))

    inv = st.session_state.inventory

    c1, c2 = st.columns([1, 1])
    with c1:
        st.number_input(t("现金安全垫（天）", "Cash buffer (days)"), 7, 365, int(inv["cash_target_days"]), 1, key="ops_cash_days")
        inv["cash_target_days"] = int(st.session_state.ops_cash_days)
    with c2:
        st.number_input(t("供货周期（天）", "Lead time (days)"), 1, 120, int(inv["supplier_lead_time_days"]), 1, key="ops_lead_days")
        inv["supplier_lead_time_days"] = int(st.session_state.ops_lead_days)

    st.markdown("#### " + t("库存数据", "Inventory data"))
    if isinstance(inv.get("df"), pd.DataFrame):
        st.dataframe(inv["df"].head(50), use_container_width=True)
    else:
        st.info(t("你还没在“开店-第3步”上传库存表。没有也能生成运营建议，但会更泛。",
                  "No inventory uploaded yet. We can still generate, but it will be more generic."))

    if st.button(t("生成运营报告", "Generate Operations Report"), key="ops_run_btn", use_container_width=True):
        with st.spinner(t("生成中…", "Generating...")):
            md = ai_report_operations()
        st.session_state.outputs["ops_report_md"] = md
        st.success(t("已生成。", "Done."))

    md = st.session_state.outputs.get("ops_report_md", "")
    if md:
        st.markdown(md)


# =========================================================
# Suite: Finance
# =========================================================
def read_uploaded_to_text(files) -> str:
    chunks = []
    for f in files:
        name = f.name.lower()
        try:
            if name.endswith(".csv"):
                df = pd.read_csv(f)
                chunks.append(f"## {f.name}\n{df.head(60).to_string(index=False)}\n")
            elif name.endswith(".xlsx") or name.endswith(".xls"):
                df = pd.read_excel(f)
                chunks.append(f"## {f.name}\n{df.head(60).to_string(index=False)}\n")
            elif name.endswith(".txt") or name.endswith(".md"):
                text = f.read().decode("utf-8", errors="ignore")
                chunks.append(f"## {f.name}\n{text[:9000]}\n")
            else:
                chunks.append(f"## {f.name}\n[Unsupported type in this version]\n")
        except Exception as e:
            chunks.append(f"## {f.name}\n[Parse failed: {e}]\n")
    return "\n".join(chunks)


def ai_report_finance(doc_text: str, focus: str, style: str, question: str) -> str:
    prompt = f"""
Return Markdown.

# Finance Analysis Report
## 1) Executive Summary (5 bullets)
## 2) What the data suggests
- Only compute from provided excerpts
## 3) Risks & Controls (8 bullets)
## 4) Action Plan (12 bullets)
- Each bullet: Owner + Metric/Target
## 5) Follow-up Questions (5)

Focus={focus}
Style={style}
UserQuestion={question if question.strip() else "None"}

Documents:
{doc_text}
"""
    return ask_ai(prompt, mode="finance")


def render_finance():
    st.header(t("财务（分析）", "Finance"))
    st.caption(t("这里更关注：现金流、安全边际、毛利与费用结构、场景测算、控制点。",
                 "Focus: cash flow, runway, margin/expense, scenarios, controls."))

    focus = st.selectbox(
        t("分析重点", "Focus"),
        ["Cash Flow / Runway", "Margin & Pricing", "Cost Control", "Scenario Planning", "Debt / Financing"],
        key="fin_focus",
    )
    style = st.selectbox(t("输出风格", "Style"), ["Concise", "Detailed", "Board-ready"], key="fin_style")
    question = st.text_input(t("你最关心的问题（可选）", "Your main question (optional)"), key="fin_q")

    files = st.file_uploader(t("上传财务材料（CSV/XLSX/TXT/MD）", "Upload documents (CSV/XLSX/TXT/MD)"),
                             type=["csv", "xlsx", "xls", "txt", "md"], accept_multiple_files=True, key="fin_up")

    doc_text = ""
    if files:
        doc_text = read_uploaded_to_text(files)
        st.success(t("已读取部分内容用于分析（仅展示前几行/节选）。", "Loaded excerpts for analysis."))

    if st.button(t("生成财务报告", "Generate Finance Report"), key="fin_run_btn", use_container_width=True):
        if not doc_text.strip():
            st.warning(t("你没上传材料，我可以给泛化建议，但你最好先上传一份损益表/流水/成本清单。",
                         "No docs uploaded. I can generate generic advice, but uploading P&L/cashflow/cost list is better."))
        with st.spinner(t("生成中…", "Generating...")):
            md = ai_report_finance(doc_text or "[No documents provided]", focus, style, question or "")
        st.session_state.outputs["finance_report_md"] = md
        st.success(t("已生成。", "Done."))

    md = st.session_state.outputs.get("finance_report_md", "")
    if md:
        st.markdown(md)


# =========================================================
# Router
# =========================================================
suite = st.session_state.active_suite
if suite == "open_store":
    render_open_store()
elif suite == "operations":
    render_operations()
else:
    render_finance()
