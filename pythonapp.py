import streamlit as st
import pandas as pd
import numpy as np
import os
import time
import random
from datetime import datetime

# New SDK (kept internal; UI shows no vendor traces)
from google import genai


# =========================================================
# App Config
# =========================================================
st.set_page_config(
    page_title="Project B: SME BI Platform",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================================================
# Styling (dark tech feel)
# =========================================================
st.markdown("""
<style>
    .stApp {
        background-image: url("https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=2072&auto=format&fit=crop");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }
    .block-container { padding-top: 1.2rem; }
    .stTabs, .stMarkdown, .stMetric, .stRadio, .stSelectbox, .stTextInput, .stNumberInput, .stTextArea {
        background-color: rgba(20, 20, 20, 0.82);
        padding: 14px;
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.08);
        color: white !important;
    }
    h1, h2, h3, p, label, span, div {
        color: #ffffff !important;
        text-shadow: 0px 0px 5px rgba(0,0,0,0.75);
    }
    section[data-testid="stSidebar"] {
        background-color: rgba(0, 0, 0, 0.9);
    }
    .pill {
        display:inline-block;
        padding: 6px 10px;
        border-radius: 999px;
        border: 1px solid rgba(255,255,255,0.15);
        background: rgba(0,0,0,0.35);
        margin-right: 8px;
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)


# =========================================================
# Language: default EN
# =========================================================
if "lang" not in st.session_state:
    st.session_state.lang = "en"

def t(zh: str, en: str) -> str:
    return zh if st.session_state.lang == "zh" else en

def toggle_language():
    st.session_state.lang = "en" if st.session_state.lang == "zh" else "zh"


# =========================================================
# API Key from Secrets/Env (no UI traces)
# =========================================================
API_KEY = ""
try:
    API_KEY = st.secrets.get("GEMINI_API_KEY", "")
except Exception:
    API_KEY = ""
if not API_KEY:
    API_KEY = os.getenv("GEMINI_API_KEY", "")

client = genai.Client(api_key=API_KEY) if API_KEY else None


# =========================================================
# Robust AI call (neutral errors; detailed logs only in server)
# =========================================================
def ask_ai(prompt_content: str, model_name: str = "gemini-2.5-flash") -> str:
    if not API_KEY or not client:
        return "AI service is not configured."

    max_attempts = 4
    base_sleep = 1.2

    for attempt in range(1, max_attempts + 1):
        try:
            resp = client.models.generate_content(
                model=model_name,
                contents=prompt_content
            )
            text = getattr(resp, "text", None)
            return text if text else "No response returned."
        except Exception as e:
            msg = str(e)
            print(f"[AI_ERROR] attempt={attempt} err={msg}")

            # Rate limit / transient
            if ("429" in msg) or ("RESOURCE_EXHAUSTED" in msg) or ("rate" in msg.lower()):
                sleep_s = base_sleep * (2 ** (attempt - 1)) + random.random()
                time.sleep(sleep_s)
                continue

            return "AI service is temporarily unavailable. Please try again."

    return "AI service is temporarily unavailable. Please try again."


# =========================================================
# Session State init
# =========================================================
if "step" not in st.session_state:
    st.session_state.step = 1  # 1..4

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
        "cost": 100,
        "target_margin": 30,
        "competitor_price": 135,
        "elasticity": "Medium",
        "notes": ""
    }

if "outputs" not in st.session_state:
    st.session_state.outputs = {
        "step2": None,
        "step3": None,
        "step4": None,
        "report_md": ""
    }

if "username" not in st.session_state:
    st.session_state.username = ""
if "register_msg" not in st.session_state:
    st.session_state.register_msg = ""


# =========================================================
# Sidebar: username + language + status
# =========================================================
def on_username_submit():
    name = (st.session_state.username or "").strip()
    if name:
        st.session_state.register_msg = "Currently unavailable to register."
    else:
        st.session_state.register_msg = ""

with st.sidebar:
    st.button("🌐 Switch Language", on_click=toggle_language)
    st.markdown("---")

    st.image("https://cdn-icons-png.flaticon.com/512/2362/2362378.png", width=48)

    st.text_input(
        "Username",
        key="username",
        placeholder="Enter a username",
        on_change=on_username_submit
    )
    if st.session_state.register_msg:
        st.warning(st.session_state.register_msg)

    st.success("🟢 System Online")
    st.caption("v4.0 Decision Flow Edition")

    st.markdown("---")
    st.caption("Navigation")
    st.write(
        f"<span class='pill'>Step {st.session_state.step}/4</span>"
        f"<span class='pill'>{['Profile','Site','Inventory','Pricing'][st.session_state.step-1]}</span>",
        unsafe_allow_html=True
    )

    col_nav1, col_nav2 = st.columns(2)
    with col_nav1:
        if st.button("◀ Back", use_container_width=True):
            st.session_state.step = max(1, st.session_state.step - 1)
    with col_nav2:
        if st.button("Next ▶", use_container_width=True):
            st.session_state.step = min(4, st.session_state.step + 1)


# =========================================================
# Helpers: structured output + report builder
# =========================================================
def score_from_inputs_site(traffic: int, competitors: int, rent_level: str, parking: str) -> int:
    # Simple heuristic baseline (replace with real data later)
    score = 55
    # traffic
    if traffic >= 40000: score += 10
    elif traffic >= 25000: score += 6
    else: score += 2
    # competitors
    if competitors <= 6: score += 12
    elif competitors <= 12: score += 6
    else: score -= 6
    # rent
    if rent_level == "Low": score += 8
    elif rent_level == "Medium": score += 3
    else: score -= 6
    # parking
    if parking == "High": score += 6
    elif parking == "Medium": score += 2
    else: score -= 4

    return int(max(0, min(100, score)))

def inventory_health(df: pd.DataFrame) -> dict:
    # Assumes columns: Item, Stock, Cost, Monthly_Sales
    df = df.copy()
    df["Total_Value"] = df["Stock"] * df["Cost"]
    df["Months_Of_Cover"] = np.where(df["Monthly_Sales"] > 0, df["Stock"] / df["Monthly_Sales"], np.inf)
    dead = df[df["Monthly_Sales"] < df["Stock"] * 0.1]
    stockout = df[(df["Stock"] <= 10) & (df["Monthly_Sales"] >= 10)]
    total_value = float(df["Total_Value"].sum())
    dead_value = float(dead["Total_Value"].sum()) if len(dead) else 0.0

    return {
        "total_value": total_value,
        "dead_items": dead,
        "stockout_items": stockout,
        "dead_value": dead_value
    }

def build_report_md() -> str:
    p = st.session_state.profile
    s = st.session_state.site
    inv = st.session_state.inventory
    pr = st.session_state.pricing
    out = st.session_state.outputs

    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    md = []
    md.append(f"# Project B — Decision Report\n")
    md.append(f"- Generated: {now}\n")

    md.append("## 1) Business Profile\n")
    md.append(f"- Business type: {p['business_type']}\n")
    md.append(f"- Stage: {p['stage']}\n")
    md.append(f"- City: {p['city']}\n")
    md.append(f"- Budget: ${p['budget']:,.0f}\n")
    md.append(f"- Target customer: {p['target_customer']}\n")
    md.append(f"- Differentiator: {p['differentiator']}\n")
    if p["notes"].strip():
        md.append(f"- Notes: {p['notes'].strip()}\n")

    md.append("\n## 2) Site Check\n")
    md.append(f"- Address: {s['address']}\n")
    md.append(f"- Radius: {s['radius_miles']} miles\n")
    md.append(f"- Traffic: {s['traffic']}\n")
    md.append(f"- Competitors (reported/estimated): {s['competitors']}\n")
    md.append(f"- Parking: {s['parking']} | Rent: {s['rent_level']}\n")
    if out["step2"]:
        md.append("\n### Output\n")
        md.append(out["step2"].strip() + "\n")

    md.append("\n## 3) Inventory & Cash\n")
    if inv["df"] is not None:
        md.append(f"- Cash target: {inv['cash_target_days']} days\n")
        md.append(f"- Supplier lead time: {inv['supplier_lead_time_days']} days\n")
        md.append(f"- Seasonality: {inv['seasonality']}\n")
        if inv["notes"].strip():
            md.append(f"- Notes: {inv['notes'].strip()}\n")
    if out["step3"]:
        md.append("\n### Output\n")
        md.append(out["step3"].strip() + "\n")

    md.append("\n## 4) Pricing Action\n")
    md.append(f"- Strategy: {pr['strategy']}\n")
    md.append(f"- Cost: ${pr['cost']}\n")
    md.append(f"- Target margin: {pr['target_margin']}%\n")
    md.append(f"- Competitor price: ${pr['competitor_price']}\n")
    md.append(f"- Elasticity: {pr['elasticity']}\n")
    if pr["notes"].strip():
        md.append(f"- Notes: {pr['notes'].strip()}\n")
    if out["step4"]:
        md.append("\n### Output\n")
        md.append(out["step4"].strip() + "\n")

    return "\n".join(md)


# =========================================================
# Header
# =========================================================
st.title("Project B: SME BI Platform")
st.markdown("**Powered by AI Engine**")  # neutral

# Progress bar
st.progress(st.session_state.step / 4.0)
st.caption("Follow the guided flow to produce an actionable decision report.")


# =========================================================
# Step 1 — Business Profile
# =========================================================
def render_step1():
    st.header("Step 1 — Business Profile")
    st.write("Set the baseline context. Better inputs → better decisions.")

    col1, col2 = st.columns([1, 1])
    with col1:
        st.session_state.profile["business_type"] = st.selectbox(
            "Business Type",
            ["Auto Parts Store", "Convenience Store", "Coffee Shop", "Restaurant", "Beauty Salon", "Other"],
            index=["Auto Parts Store", "Convenience Store", "Coffee Shop", "Restaurant", "Beauty Salon", "Other"].index(
                st.session_state.profile["business_type"] if st.session_state.profile["business_type"] in
                ["Auto Parts Store","Convenience Store","Coffee Shop","Restaurant","Beauty Salon","Other"] else "Other"
            )
        )
        st.session_state.profile["stage"] = st.selectbox(
            "Stage",
            ["Planning", "Open Soon", "Operating", "Expansion"],
            index=["Planning","Open Soon","Operating","Expansion"].index(st.session_state.profile["stage"])
            if st.session_state.profile["stage"] in ["Planning","Open Soon","Operating","Expansion"] else 0
        )
        st.session_state.profile["city"] = st.text_input("City", st.session_state.profile["city"])

    with col2:
        st.session_state.profile["budget"] = st.number_input(
            "Initial Budget (USD)",
            min_value=0,
            value=int(st.session_state.profile["budget"]),
            step=1000
        )
        st.session_state.profile["target_customer"] = st.text_input(
            "Target Customer",
            st.session_state.profile["target_customer"]
        )
        st.session_state.profile["differentiator"] = st.text_input(
            "Differentiator",
            st.session_state.profile["differentiator"]
        )

    st.session_state.profile["notes"] = st.text_area(
        "Notes (optional)",
        st.session_state.profile["notes"],
        placeholder="Anything special: constraints, planned services, hours, staff, etc."
    )

    st.subheader("Checkpoint")
    st.write("✅ When ready, move to Step 2 for site evaluation.")
    c1, c2, c3 = st.columns([1, 1, 2])
    with c1:
        if st.button("Go to Step 2 ▶", type="primary", use_container_width=True):
            st.session_state.step = 2
    with c2:
        if st.button("Reset Profile", use_container_width=True):
            st.session_state.profile.update({
                "business_type": "Auto Parts Store",
                "stage": "Planning",
                "budget": 80000,
                "target_customer": "Local residents and small fleets",
                "differentiator": "Fast service + reliable stock",
                "city": "New York",
                "notes": ""
            })
    with c3:
        st.caption("Tip: Keep inputs simple. This version focuses on decision flow and reporting.")


# =========================================================
# Step 2 — Site Check
# =========================================================
def render_step2():
    st.header("Step 2 — Site Check")
    st.write("Evaluate commercial potential with clear output: conclusion, evidence, actions.")

    colA, colB = st.columns([1, 2])

    with colA:
        st.session_state.site["address"] = st.text_input("Address", st.session_state.site["address"])
        st.session_state.site["radius_miles"] = st.selectbox("Radius (miles)", [0.5, 1.0, 3.0], index=[0.5,1.0,3.0].index(st.session_state.site["radius_miles"]))
        st.session_state.site["traffic"] = st.slider("Traffic (estimated)", 1000, 50000, int(st.session_state.site["traffic"]), step=500)
        st.session_state.site["competitors"] = st.number_input("Competitors (reported/estimated)", min_value=0, value=int(st.session_state.site["competitors"]), step=1)

        st.session_state.site["parking"] = st.selectbox("Parking", ["Low", "Medium", "High"], index=["Low","Medium","High"].index(st.session_state.site["parking"]))
        st.session_state.site["rent_level"] = st.selectbox("Rent Level", ["Low", "Medium", "High"], index=["Low","Medium","High"].index(st.session_state.site["rent_level"]))
        st.session_state.site["foot_traffic_source"] = st.selectbox(
            "Foot Traffic Source",
            ["Mixed (Transit + Street)", "Street Dominant", "Transit Dominant", "Destination Only"],
            index=["Mixed (Transit + Street)","Street Dominant","Transit Dominant","Destination Only"].index(st.session_state.site["foot_traffic_source"])
        )

    with colB:
        st.subheader("Map Preview (demo)")
        # demo map point around Flushing-like coords
        base_lat, base_lon = 40.7590, -73.8290
        map_data = pd.DataFrame({
            "lat": [base_lat + np.random.randn()/2000],
            "lon": [base_lon + np.random.randn()/2000]
        })
        st.map(map_data, zoom=14)

        st.caption("This is a demo map marker. Replace with real geocoding + POI later.")

    # computed score + risk flags
    score = score_from_inputs_site(
        st.session_state.site["traffic"],
        st.session_state.site["competitors"],
        st.session_state.site["rent_level"],
        st.session_state.site["parking"]
    )

    risk_flags = []
    if st.session_state.site["competitors"] > 15:
        risk_flags.append("High competitive density")
    if st.session_state.site["rent_level"] == "High":
        risk_flags.append("High fixed cost (rent)")
    if st.session_state.site["parking"] == "Low":
        risk_flags.append("Low parking convenience")

    st.session_state.site["risk_flags"] = risk_flags

    st.subheader("Quick Readout")
    c1, c2, c3 = st.columns(3)
    c1.metric("Site Score", score)
    c2.metric("Competitors", st.session_state.site["competitors"])
    c3.metric("Traffic", st.session_state.site["traffic"])

    if risk_flags:
        st.warning("Risk flags: " + ", ".join(risk_flags))
    else:
        st.success("No major risk flags from current inputs.")

    st.divider()

    # AI generate structured output
    st.subheader("Decision Output")
    if st.button("Run Site Analysis", type="primary"):
        p = st.session_state.profile
        s = st.session_state.site
        prompt = f"""
You are an SME operations strategist.
Given the business profile and site inputs, produce a structured decision output with:
1) Conclusion (3 bullets)
2) Evidence (3-5 bullets, only use provided inputs, no external claims)
3) Next Actions (5 bullets, actionable, measurable)
Also provide a final Score (0-100) and Confidence (Low/Med/High).
Business:
- Type: {p['business_type']}
- Stage: {p['stage']}
- City: {p['city']}
- Budget: ${p['budget']}
- Target customer: {p['target_customer']}
- Differentiator: {p['differentiator']}
Site:
- Address: {s['address']}
- Radius: {s['radius_miles']} miles
- Traffic: {s['traffic']}
- Competitors: {s['competitors']}
- Parking: {s['parking']}
- Rent level: {s['rent_level']}
- Foot traffic source: {s['foot_traffic_source']}
- Risk flags: {', '.join(s['risk_flags']) if s['risk_flags'] else 'None'}
Return in plain text with clear headings.
"""
        with st.spinner("Analyzing..."):
            out = ask_ai(prompt)
        st.session_state.outputs["step2"] = out
        st.success("Analysis complete.")
        st.write(out)

    if st.session_state.outputs["step2"]:
        with st.expander("Last output", expanded=False):
            st.write(st.session_state.outputs["step2"])

    st.divider()
    cL, cR = st.columns([1, 1])
    with cL:
        if st.button("Go to Step 3 ▶", use_container_width=True):
            st.session_state.step = 3
    with cR:
        if st.button("Reset Site Inputs", use_container_width=True):
            st.session_state.site.update({
                "address": "39-01 Main St, Flushing, NY 11354",
                "radius_miles": 1.0,
                "traffic": 30000,
                "competitors": 12,
                "parking": "Medium",
                "rent_level": "High",
                "foot_traffic_source": "Mixed (Transit + Street)",
                "risk_flags": []
            })
            st.session_state.outputs["step2"] = None


# =========================================================
# Step 3 — Inventory & Cash
# =========================================================
def render_step3():
    st.header("Step 3 — Inventory & Cash")
    st.write("Diagnose inventory health, free cash, and reduce stockout risk.")

    col1, col2 = st.columns([1, 1])
    with col1:
        st.session_state.inventory["cash_target_days"] = st.slider("Cash target (days)", 10, 120, int(st.session_state.inventory["cash_target_days"]))
        st.session_state.inventory["supplier_lead_time_days"] = st.slider("Supplier lead time (days)", 1, 30, int(st.session_state.inventory["supplier_lead_time_days"]))
        st.session_state.inventory["seasonality"] = st.selectbox("Seasonality", ["Winter", "Spring", "Summer", "Fall"], index=["Winter","Spring","Summer","Fall"].index(st.session_state.inventory["seasonality"]))

    with col2:
        st.session_state.inventory["notes"] = st.text_area(
            "Notes (optional)",
            st.session_state.inventory["notes"],
            placeholder="Constraints: storage, cash pressure, supplier terms, minimum order, etc."
        )

    st.subheader("ERP Data")
    cA, cB = st.columns([1, 1])
    with cA:
        if st.button("Load sample ERP data"):
            data = {
                "Item": ["Synthetic Oil", "Wiper Blades", "Brake Pads", "Tires", "Air Filter"],
                "Stock": [120, 450, 30, 8, 200],
                "Cost": [25, 8, 45, 120, 5],
                "Monthly_Sales": [40, 5, 25, 6, 15]
            }
            df = pd.DataFrame(data)
            st.session_state.inventory["df"] = df
    with cB:
        uploaded = st.file_uploader("Upload CSV (Item,Stock,Cost,Monthly_Sales)", type=["csv"])
        if uploaded is not None:
            df = pd.read_csv(uploaded)
            st.session_state.inventory["df"] = df

    df = st.session_state.inventory["df"]
    if df is None:
        st.info("Load sample data or upload CSV to proceed.")
        return

    st.dataframe(df, use_container_width=True)

    # Heuristic health
    health = inventory_health(df)
    st.metric("Total Inventory Value", f"${health['total_value']:,.0f}")
    st.metric("Dead Stock Value", f"${health['dead_value']:,.0f}")

    if len(health["dead_items"]) > 0:
        st.warning(f"Dead stock items detected: {len(health['dead_items'])}")
        with st.expander("View dead stock details"):
            st.dataframe(health["dead_items"], use_container_width=True)
    else:
        st.success("No dead stock detected based on current heuristic.")

    if len(health["stockout_items"]) > 0:
        st.error(f"Stockout-risk items detected: {len(health['stockout_items'])}")
        with st.expander("View stockout-risk details"):
            st.dataframe(health["stockout_items"], use_container_width=True)

    st.divider()

    st.subheader("Decision Output")
    if st.button("Run Inventory Diagnostics", type="primary"):
        p = st.session_state.profile
        inv = st.session_state.inventory
        s = st.session_state.site
        prompt = f"""
You are the CFO/COO for an SME.
Using ONLY the provided data, produce a structured output with:
1) Conclusion (3 bullets)
2) Evidence (3-5 bullets)
3) Next Actions (6 bullets; each action includes a metric or target)
Also provide:
- Cash recovery estimate range (rough)
- Priority list: Top 3 items to act on first
Business: {p['business_type']} | Stage: {p['stage']} | City: {p['city']}
Site context: traffic={s['traffic']}, competitors={s['competitors']}, rent={s['rent_level']}
Inventory constraints:
- Cash target days: {inv['cash_target_days']}
- Lead time days: {inv['supplier_lead_time_days']}
- Seasonality: {inv['seasonality']}
Notes: {inv['notes'] if inv['notes'].strip() else 'None'}
Inventory table:
{df.to_string(index=False)}
Return plain text with clear headings.
"""
        with st.spinner("Analyzing..."):
            out = ask_ai(prompt)
        st.session_state.outputs["step3"] = out
        st.success("Analysis complete.")
        st.write(out)

    if st.session_state.outputs["step3"]:
        with st.expander("Last output", expanded=False):
            st.write(st.session_state.outputs["step3"])

    st.divider()
    cL, cR = st.columns([1, 1])
    with cL:
        if st.button("Go to Step 4 ▶", use_container_width=True):
            st.session_state.step = 4
    with cR:
        if st.button("Reset Inventory", use_container_width=True):
            st.session_state.inventory.update({
                "df": None,
                "cash_target_days": 45,
                "supplier_lead_time_days": 7,
                "seasonality": "Winter",
                "notes": ""
            })
            st.session_state.outputs["step3"] = None


# =========================================================
# Step 4 — Pricing Action + Report
# =========================================================
def render_step4():
    st.header("Step 4 — Pricing Action")
    st.write("Produce a pricing plan that is measurable and immediately executable.")

    pr = st.session_state.pricing
    col1, col2 = st.columns([1, 1])
    with col1:
        pr["strategy"] = st.selectbox("Strategy", ["Competitive", "Value-based", "Premium", "Penetration"], index=["Competitive","Value-based","Premium","Penetration"].index(pr["strategy"]))
        pr["cost"] = st.number_input("Unit Cost (USD)", min_value=0.0, value=float(pr["cost"]), step=1.0)
        pr["competitor_price"] = st.number_input("Competitor Price (USD)", min_value=0.0, value=float(pr["competitor_price"]), step=1.0)
    with col2:
        pr["target_margin"] = st.slider("Target Margin (%)", 0, 80, int(pr["target_margin"]))
        pr["elasticity"] = st.selectbox("Demand Elasticity", ["Low", "Medium", "High"], index=["Low","Medium","High"].index(pr["elasticity"]))
        pr["notes"] = st.text_area("Notes (optional)", pr["notes"], placeholder="Any constraints: minimum advertised price, promotions, bundles, etc.")

    rec_price = pr["cost"] * (1 + pr["target_margin"] / 100.0)
    st.metric("Recommended Price (simple)", f"${rec_price:,.2f}")

    st.divider()

    st.subheader("Decision Output")
    if st.button("Run Pricing Plan", type="primary"):
        p = st.session_state.profile
        s = st.session_state.site
        inv = st.session_state.inventory
        prompt = f"""
You are a pricing strategist for an SME.
Using ONLY provided inputs, produce:
1) Conclusion (3 bullets)
2) Evidence (3-5 bullets)
3) Pricing Plan (6 bullets: price range, promo triggers, bundle ideas, guardrails, weekly review metric)
4) Risk controls (3 bullets)
Provide final: Suggested price range (min/target/max) and Confidence (Low/Med/High).
Business: {p['business_type']} | Stage: {p['stage']} | Budget: ${p['budget']}
Site: traffic={s['traffic']}, competitors={s['competitors']}, rent={s['rent_level']}
Inventory context: seasonality={inv['seasonality']}, cash_target_days={inv['cash_target_days']}, lead_time={inv['supplier_lead_time_days']}
Pricing inputs:
- Strategy: {pr['strategy']}
- Unit cost: {pr['cost']}
- Competitor price: {pr['competitor_price']}
- Target margin: {pr['target_margin']}%
- Elasticity: {pr['elasticity']}
Notes: {pr['notes'] if pr['notes'].strip() else 'None'}
Return plain text with clear headings.
"""
        with st.spinner("Analyzing..."):
            out = ask_ai(prompt)
        st.session_state.outputs["step4"] = out
        st.success("Analysis complete.")
        st.write(out)

    if st.session_state.outputs["step4"]:
        with st.expander("Last output", expanded=False):
            st.write(st.session_state.outputs["step4"])

    st.divider()

    # Report generation
    st.header("Deliverable — Decision Report")
    st.write("Generate a single report you can share internally or keep as record.")

    colA, colB = st.columns([1, 1])
    with colA:
        if st.button("Generate Report (Markdown)", type="primary", use_container_width=True):
            md = build_report_md()
            st.session_state.outputs["report_md"] = md
            st.success("Report generated.")
    with colB:
        if st.button("Clear Report", use_container_width=True):
            st.session_state.outputs["report_md"] = ""

    if st.session_state.outputs["report_md"]:
        st.text_area("Report Preview", st.session_state.outputs["report_md"], height=420)
        st.download_button(
            label="Download report.md",
            data=st.session_state.outputs["report_md"],
            file_name="decision_report.md",
            mime="text/markdown"
        )

    st.divider()
    st.caption("Next iteration: connect real geocoding/POI counts, real competitor pulls, and a persistent user workspace.")


# =========================================================
# Router
# =========================================================
if st.session_state.step == 1:
    render_step1()
elif st.session_state.step == 2:
    render_step2()
elif st.session_state.step == 3:
    render_step3()
else:
    render_step4()

