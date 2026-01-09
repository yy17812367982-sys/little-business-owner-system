import streamlit as st
import pandas as pd
import numpy as np
import os
import time
import random
from datetime import datetime
from google import genai


# =========================================================
# Page config + style
# =========================================================
st.set_page_config(
    page_title="Project B: SME BI Platform",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .stApp {
        background-image: url("https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=2072&auto=format&fit=crop");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }
    .block-container { padding-top: 1.1rem; }
    .stMarkdown, .stMetric, .stRadio, .stSelectbox, .stTextInput, .stNumberInput, .stTextArea, .stFileUploader {
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
    section[data-testid="stSidebar"] { background-color: rgba(0, 0, 0, 0.9); }
    .pill {
        display:inline-block;
        padding: 6px 10px;
        border-radius: 999px;
        border: 1px solid rgba(255,255,255,0.15);
        background: rgba(0,0,0,0.35);
        margin-right: 8px;
        font-size: 0.9rem;
    }
    .card {
        background: rgba(0,0,0,0.30);
        border: 1px solid rgba(255,255,255,0.10);
        border-radius: 14px;
        padding: 14px 16px;
        margin: 8px 0;
    }
</style>
""", unsafe_allow_html=True)


# =========================================================
# Language (default EN, switchable)
# =========================================================
if "lang" not in st.session_state:
    st.session_state.lang = "en"

def t(zh: str, en: str) -> str:
    return zh if st.session_state.lang == "zh" else en

def toggle_language():
    st.session_state.lang = "en" if st.session_state.lang == "zh" else "zh"
    st.rerun()


# =========================================================
# API Key + client (no UI traces)
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
# AI wrapper: "Yangyu's AI" persona + no vendor traces
# =========================================================
SYSTEM_POLICY = """
You are "Yangyu's AI" — an AI assistant branded for an SME decision platform.
Rules:
- NEVER mention any underlying model/provider/vendor or internal API names.
- If asked "Who are you?", "What model are you?", "Are you Gemini?" or similar:
  answer: "I'm Yangyu's AI assistant." (and optionally explain you are an AI helper inside this platform).
- Keep outputs structured and actionable; prefer bullet points, metrics, and next steps.
- If user requests sensitive/illegal help, refuse briefly and offer safe alternatives.
"""

def ask_ai(user_prompt: str, mode: str = "general") -> str:
    if not API_KEY or not client:
        return t("AI 服务未配置。", "AI service is not configured.")

    # Mode-specific steering (kept generic)
    mode_hint = {
        "general": "General Q&A. Be concise and practical.",
        "open_store": "Focus on store-opening decisions: location, setup, launch checklist, risks, and actions.",
        "operations": "Focus on operations: inventory, staffing, SOPs, pricing execution, weekly review loops.",
        "finance": "Focus on financial analysis: cash flow, margins, runway, costs, scenario and controls.",
    }.get(mode, "General Q&A.")

    prompt = f"{SYSTEM_POLICY}\n\nContext:\n- Mode: {mode_hint}\n\nUser:\n{user_prompt}"

    max_attempts = 4
    base_sleep = 1.2
    for attempt in range(1, max_attempts + 1):
        try:
            resp = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            text = getattr(resp, "text", None)
            return text if text else t("AI 返回为空。", "No response returned.")
        except Exception as e:
            msg = str(e)
            print(f"[AI_ERROR] attempt={attempt} err={msg}")

            if ("429" in msg) or ("RESOURCE_EXHAUSTED" in msg) or ("rate" in msg.lower()):
                time.sleep(base_sleep * (2 ** (attempt - 1)) + random.random())
                continue

            return t("AI 暂时不可用，请稍后重试。", "AI service is temporarily unavailable. Please try again.")
    return t("AI 暂时不可用，请稍后重试。", "AI service is temporarily unavailable. Please try again.")


# =========================================================
# State init
# =========================================================
if "active_suite" not in st.session_state:
    st.session_state.active_suite = "open_store"  # open_store / operations / finance

# Sidebar username behavior
if "username" not in st.session_state:
    st.session_state.username = ""
if "register_msg" not in st.session_state:
    st.session_state.register_msg = ""

def on_username_submit():
    name = (st.session_state.username or "").strip()
    st.session_state.register_msg = t("目前不可注册。", "Currently unavailable to register.") if name else ""

# Open-store wizard step
if "open_step" not in st.session_state:
    st.session_state.open_step = 1  # 1..4

# Data buckets
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
        "ops_ai_output": None,
        "finance_ai_output": None
    }

# Top Ask-AI chat
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []  # list[{"role":"user/ai","text":...}]


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

def build_open_store_report_md() -> str:
    p = st.session_state.profile
    s = st.session_state.site
    inv = st.session_state.inventory
    pr = st.session_state.pricing
    out = st.session_state.outputs

    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    md = []
    md.append("# Open a Store — Decision Report\n")
    md.append(f"- Generated: {now}\n")

    md.append("## Business Profile\n")
    md.append(f"- Type: {p['business_type']}\n")
    md.append(f"- Stage: {p['stage']}\n")
    md.append(f"- City: {p['city']}\n")
    md.append(f"- Budget: ${p['budget']:,.0f}\n")
    md.append(f"- Target customer: {p['target_customer']}\n")
    md.append(f"- Differentiator: {p['differentiator']}\n")
    if p["notes"].strip():
        md.append(f"- Notes: {p['notes'].strip()}\n")

    md.append("\n## Site\n")
    md.append(f"- Address: {s['address']}\n")
    md.append(f"- Radius: {s['radius_miles']} miles\n")
    md.append(f"- Traffic: {s['traffic']}\n")
    md.append(f"- Competitors: {s['competitors']}\n")
    md.append(f"- Parking: {s['parking']} | Rent: {s['rent_level']}\n")
    if s["risk_flags"]:
        md.append(f"- Risk flags: {', '.join(s['risk_flags'])}\n")

    md.append("\n## Inventory & Cash\n")
    if inv["df"] is None:
        md.append("- Inventory data: Not provided\n")
    else:
        md.append(f"- Cash target: {inv['cash_target_days']} days\n")
        md.append(f"- Lead time: {inv['supplier_lead_time_days']} days\n")
        md.append(f"- Seasonality: {inv['seasonality']}\n")
        if inv["notes"].strip():
            md.append(f"- Notes: {inv['notes'].strip()}\n")
        if out["inventory_summary"]:
            md.append(f"- Snapshot: {out['inventory_summary']}\n")

    md.append("\n## Pricing\n")
    md.append(f"- Strategy: {pr['strategy']}\n")
    md.append(f"- Cost: ${pr['cost']}\n")
    md.append(f"- Target margin: {pr['target_margin']}%\n")
    md.append(f"- Competitor price: ${pr['competitor_price']}\n")
    md.append(f"- Elasticity: {pr['elasticity']}\n")
    if pr["notes"].strip():
        md.append(f"- Notes: {pr['notes'].strip()}\n")

    md.append("\n## Final Output\n")
    md.append(out["final_open_store"].strip() + "\n" if out["final_open_store"] else "Not generated.\n")

    return "\n".join(md)

def read_uploaded_to_text(files) -> str:
    """
    Convert user uploaded documents into plain text summary for AI prompt.
    Supports: CSV/XLSX/TXT/MD (simple). PDFs not handled here (keep minimal, safe).
    """
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
                # cap size
                chunks.append(f"## {f.name}\n{text[:8000]}\n")
            else:
                chunks.append(f"## {f.name}\n[Unsupported file type for text extraction in this version]\n")
        except Exception as e:
            chunks.append(f"## {f.name}\n[Failed to parse: {e}]\n")
    return "\n".join(chunks)


# =========================================================
# Sidebar (suite switching + username + language)
# =========================================================
with st.sidebar:
    st.button(t("🌐 切换语言", "🌐 Switch Language"), on_click=toggle_language)
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
    st.caption(t("功能集合", "Suites"))
    suite = st.radio(
        "",
        options=["open_store", "operations", "finance"],
        format_func=lambda x: {
            "open_store": t("开店", "Open a Store"),
            "operations": t("运营", "Operations"),
            "finance": t("财务分析", "Financial Analysis")
        }[x],
        index=["open_store","operations","finance"].index(st.session_state.active_suite)
    )
    if suite != st.session_state.active_suite:
        st.session_state.active_suite = suite
        st.rerun()

    st.success(t("🟢 系统在线", "🟢 System Online"))
    st.caption("v5.0 Suites Edition")


# =========================================================
# Header + Top Ask AI (landing feature)
# =========================================================
st.title("Project B: SME BI Platform")
ai_label = t("Yangyu 的 AI", "Yangyu's AI")
st.markdown(f"<div class='card'><b>{ai_label}:</b><br>{m['text']}</div>", unsafe_allow_html=True)


with st.expander(t("问 AI（入口）", "Ask AI (Top Entry)"), expanded=True):
    colA, colB = st.columns([3, 1])
    with colA:
        user_q = st.text_input(
            t("你想问什么？", "Ask anything..."),
            key="top_ask_ai",
            placeholder=t("例如：这个地址适合开店吗？我该怎么降库存？", "E.g., Is this site viable? How do I reduce dead stock?")
        )
    with colB:
        send = st.button(t("发送", "Send"), type="primary", use_container_width=True)

    if send and user_q.strip():
        st.session_state.chat_history.append({"role": "user", "text": user_q.strip()})
        mode = st.session_state.active_suite
        ans = ask_ai(user_q.strip(), mode=mode)
        st.session_state.chat_history.append({"role": "ai", "text": ans})
        st.rerun()

    if st.session_state.chat_history:
        st.markdown("---")
        for m in st.session_state.chat_history[-8:]:
            if m["role"] == "user":
                st.markdown(f"<div class='card'><b>{t('你', 'You')}:</b><br>{m['text']}</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div class='card'><b>{t('Yangyu 的 AI', \"Yangyu's AI\")}:</b><br>{m['text']}</div>", unsafe_allow_html=True)
        colc1, colc2 = st.columns([1, 4])
        with colc1:
            if st.button(t("清空对话", "Clear Chat")):
                st.session_state.chat_history = []
                st.rerun()


# =========================================================
# Suite 1: Open a Store (wizard inside)
# =========================================================
def render_open_store():
    st.header(t("开店（决策流）", "Open a Store (Decision Flow)"))

    step_titles = [
        t("业务画像", "Profile"),
        t("选址检查", "Site Check"),
        t("库存与现金", "Inventory & Cash"),
        t("定价 & 总结", "Pricing & Summary")
    ]
    st.write(
        f"<span class='pill'>{t('步骤', 'Step')} {st.session_state.open_step}/4</span>"
        f"<span class='pill'>{step_titles[st.session_state.open_step-1]}</span>",
        unsafe_allow_html=True
    )
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
        st.caption(t("提示：这部分专注“开店决策”。运营和财务在其他集合里更细。", "Tip: This suite focuses on launch decisions. Operations & finance are in other suites."))

    # ---- Step 1
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
            p["stage"] = st.selectbox(t("阶段", "Stage"), ["Planning", "Open Soon", "Operating", "Expansion"],
                                      index=["Planning","Open Soon","Operating","Expansion"].index(p["stage"]) if p["stage"] in ["Planning","Open Soon","Operating","Expansion"] else 0)
            p["city"] = st.text_input(t("城市", "City"), p["city"])
        with col2:
            p["budget"] = st.number_input(t("初始预算（美元）", "Initial Budget (USD)"), min_value=0, value=int(p["budget"]), step=1000)
            p["target_customer"] = st.text_input(t("目标客户", "Target Customer"), p["target_customer"])
            p["differentiator"] = st.text_input(t("差异化", "Differentiator"), p["differentiator"])

        p["notes"] = st.text_area(t("备注（可选）", "Notes (optional)"), p["notes"],
                                  placeholder=t("例如：营业时间、人员配置、服务范围、限制条件等", "Constraints, hours, staffing, services, etc."))

    # ---- Step 2
    elif st.session_state.open_step == 2:
        s = st.session_state.site
        st.subheader(t("第 2 步：选址检查", "Step 2: Site Check"))
        colA, colB = st.columns([1, 2])
        with colA:
            s["address"] = st.text_input(t("地址", "Address"), s["address"])
            s["radius_miles"] = st.selectbox(t("半径（英里）", "Radius (miles)"), [0.5, 1.0, 3.0],
                                             index=[0.5, 1.0, 3.0].index(s["radius_miles"]))
            s["traffic"] = st.slider(t("人流/车流（估计）", "Traffic (estimated)"), 1000, 50000, int(s["traffic"]), step=500)
            s["competitors"] = st.number_input(t("竞品数量（估计）", "Competitors (estimated)"), min_value=0, value=int(s["competitors"]), step=1)
            s["parking"] = st.selectbox(t("停车便利", "Parking"), ["Low", "Medium", "High"], index=["Low","Medium","High"].index(s["parking"]))
            s["rent_level"] = st.selectbox(t("租金水平", "Rent Level"), ["Low", "Medium", "High"], index=["Low","Medium","High"].index(s["rent_level"]))
            s["foot_traffic_source"] = st.selectbox(t("客流来源", "Foot Traffic Source"),
                                                    ["Mixed (Transit + Street)", "Street Dominant", "Transit Dominant", "Destination Only"],
                                                    index=["Mixed (Transit + Street)","Street Dominant","Transit Dominant","Destination Only"].index(s["foot_traffic_source"]))
        with colB:
            st.subheader(t("地图预览（演示）", "Map Preview (demo)"))
            base_lat, base_lon = 40.7590, -73.8290
            map_data = pd.DataFrame({"lat": [base_lat + np.random.randn()/2000], "lon": [base_lon + np.random.randn()/2000]})
            st.map(map_data, zoom=14)
            st.caption(t("当前是演示点位：后续可接真实地理编码与 POI 统计。", "Demo marker only. Replace with real geocoding + POI counts later."))

        score = score_from_inputs_site(s["traffic"], s["competitors"], s["rent_level"], s["parking"])
        risk_flags = []
        if s["competitors"] > 15: risk_flags.append(t("竞品密度偏高", "High competitive density"))
        if s["rent_level"] == "High": risk_flags.append(t("固定成本偏高（租金）", "High fixed cost (rent)"))
        if s["parking"] == "Low": risk_flags.append(t("停车不便可能影响转化", "Low parking convenience"))
        s["risk_flags"] = risk_flags

        c1, c2, c3 = st.columns(3)
        c1.metric(t("选址评分", "Site Score"), score)
        c2.metric(t("竞品数", "Competitors"), s["competitors"])
        c3.metric(t("流量", "Traffic"), s["traffic"])
        if risk_flags:
            st.warning(t("风险提示：", "Risk flags: ") + "，".join(risk_flags))
        else:
            st.success(t("当前输入下未发现明显风险标记。", "No major risk flags from current inputs."))

    # ---- Step 3 (data + metrics only)
    elif st.session_state.open_step == 3:
        inv = st.session_state.inventory
        st.subheader(t("第 3 步：库存与现金（不跑 AI）", "Step 3: Inventory & Cash (no AI here)"))

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
            uploaded = st.file_uploader(t("上传 CSV（Item,Stock,Cost,Monthly_Sales）", "Upload CSV (Item,Stock,Cost,Monthly_Sales)"), type=["csv"])
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

    # ---- Step 4 (pricing + final AI + report)
    else:
        pr = st.session_state.pricing
        st.subheader(t("第 4 步：定价 & 一键总分析", "Step 4: Pricing & One-click Final Analysis"))

        col1, col2 = st.columns([1, 1])
        with col1:
            pr["strategy"] = st.selectbox(t("定价策略", "Strategy"),
                                         ["Competitive", "Value-based", "Premium", "Penetration"],
                                         index=["Competitive","Value-based","Premium","Penetration"].index(pr["strategy"]))
            pr["cost"] = st.number_input(t("单位成本（美元）", "Unit Cost (USD)"), min_value=0.0, value=float(pr["cost"]), step=1.0)
            pr["competitor_price"] = st.number_input(t("竞品价格（美元）", "Competitor Price (USD)"), min_value=0.0, value=float(pr["competitor_price"]), step=1.0)

        with col2:
            pr["target_margin"] = st.slider(t("目标毛利率（%）", "Target Margin (%)"), 0, 80, int(pr["target_margin"]))
            pr["elasticity"] = st.selectbox(t("需求弹性", "Demand Elasticity"),
                                           ["Low", "Medium", "High"],
                                           index=["Low","Medium","High"].index(pr["elasticity"]))
            pr["notes"] = st.text_area(t("备注（可选）", "Notes (optional)"), pr["notes"],
                                      placeholder=t("例如：促销限制、捆绑策略、最低标价等", "Constraints: promos, bundles, MAP, etc."))

        rec_price = pr["cost"] * (1 + pr["target_margin"] / 100.0)
        st.metric(t("推荐价格（简单计算）", "Recommended Price (simple)"), f"${rec_price:,.2f}")

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
        st.subheader(t("可交付物：报告", "Deliverable: Report"))

        colA, colB = st.columns([1, 1])
        with colA:
            if st.button(t("生成报告（Markdown）", "Generate Report (Markdown)"), use_container_width=True):
                st.session_state.outputs["open_store_report_md"] = build_open_store_report_md()
                st.rerun()
        with colB:
            if st.button(t("清空报告", "Clear Report"), use_container_width=True):
                st.session_state.outputs["open_store_report_md"] = ""
                st.rerun()

        if st.session_state.outputs["open_store_report_md"]:
            st.text_area(t("报告预览", "Report Preview"), st.session_state.outputs["open_store_report_md"], height=420)
            st.download_button(
                label=t("下载 report.md", "Download report.md"),
                data=st.session_state.outputs["open_store_report_md"],
                file_name="open_store_report.md",
                mime="text/markdown"
            )


# =========================================================
# Suite 2: Operations (daily running)
# =========================================================
def render_operations():
    st.header(t("运营（帮助企业跑起来）", "Operations (Run the business)"))

    st.markdown(f"<div class='card'>{t('这里更偏“日常运营”：库存周报、补货策略、促销触发、SOP 检查表等。', 'This suite focuses on day-to-day operations: weekly inventory review, replenishment rules, promo triggers, SOP checklists.')}</div>", unsafe_allow_html=True)

    tab_ops1, tab_ops2, tab_ops3 = st.tabs([
        t("库存周检", "Inventory Weekly Review"),
        t("定价执行", "Pricing Execution"),
        t("运营问诊", "Ops Advisor")
    ])

    # Inventory Weekly Review
    with tab_ops1:
        inv = st.session_state.inventory
        st.subheader(t("库存周检（数据+指标）", "Inventory Weekly Review (Data + Metrics)"))

        colA, colB = st.columns([1, 1])
        with colA:
            if st.button(t("加载示例数据", "Load sample data")):
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

    # Pricing Execution
    with tab_ops2:
        pr = st.session_state.pricing
        st.subheader(t("定价执行（从策略到动作）", "Pricing Execution (From strategy to actions)"))

        col1, col2 = st.columns([1, 1])
        with col1:
            pr["strategy"] = st.selectbox(t("定价策略", "Strategy"), ["Competitive", "Value-based", "Premium", "Penetration"],
                                         index=["Competitive","Value-based","Premium","Penetration"].index(pr["strategy"]),
                                         key="ops_strategy")
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

    # Ops Advisor (AI)
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


# =========================================================
# Suite 3: Financial Analysis (upload docs + AI guidance)
# =========================================================
def render_finance():
    st.header(t("财务分析（上传资料 → AI 指导）", "Financial Analysis (Upload docs → AI guidance)"))

    st.markdown(f"<div class='card'>{t('上传你自己的财务资料（CSV/XLSX/TXT），AI 会做结构化分析：现金流、利润率、成本项、风险点、下一步动作。', 'Upload your own finance materials (CSV/XLSX/TXT). AI will produce a structured analysis: cash flow, margins, costs, risks, next actions.')}</div>", unsafe_allow_html=True)

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


# =========================================================
# Router by suite
# =========================================================
if st.session_state.active_suite == "open_store":
    render_open_store()
elif st.session_state.active_suite == "operations":
    render_operations()
else:
    render_finance()
