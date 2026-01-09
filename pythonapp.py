import streamlit as st
import pandas as pd
import numpy as np
import os
import time
import random

# ✅ 使用全新 SDK
from google import genai

# ==========================================
# 🌐 生产模式设置
# ==========================================
IS_DEV_MODE = False

# ==========================================
# 🔑 API 凭据加载 (通过 Secrets)
# ==========================================
API_KEY = ""
try:
    API_KEY = st.secrets.get("GEMINI_API_KEY", "")
except Exception:
    API_KEY = ""

client = genai.Client(api_key=API_KEY) if API_KEY else None

# ==========================================
# 🎨 页面配置 (Enterprise Look)
# ==========================================
st.set_page_config(
    page_title="Intelligence Platform",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 注入 CSS (增强科技感，隐藏额外标识)
st.markdown("""
<style>
    .stApp {
        background-image: url("https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=2072&auto=format&fit=crop");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }
    .stTabs, .stMarkdown, .stMetric, .stRadio, .stSelectbox, .stTextInput, .stNumberInput {
        background-color: rgba(20, 20, 20, 0.85);
        padding: 15px;
        border-radius: 10px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        color: white !important;
    }
    h1, h2, h3, p, label, span, div {
        color: #ffffff !important;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 🌍 核心修改：语言引擎 (默认英文)
# ==========================================
if "lang" not in st.session_state:
    st.session_state.lang = "en"  # <--- 默认设为英文

def t(en, zh):  # <--- 逻辑反转：第一个参数是英文
    return en if st.session_state.lang == "en" else zh

def toggle_language():
    st.session_state.lang = "zh" if st.session_state.lang == "en" else "en"

# ==========================================
# 🧠 核心修改：去标识化 AI 调用
# ==========================================
def ask_ai(prompt_content: str, model_name: str = "gemini-1.5-flash") -> str:
    """ 
    隐藏模型细节的通用 AI 接口
    """
    if not API_KEY or not client:
        return "System Configuration Error: API Access Denied."

    try:
        # 直接使用 Client 调用，外部感知不到底层模型
        resp = client.models.generate_content(
            model=model_name,
            contents=prompt_content
        )
        return resp.text if resp.text else "The AI engine returned an empty result."
    except Exception as e:
        return f"Service Temporary Unavailable: {str(e)}"

# ==========================================
# 📱 侧边栏
# ==========================================
with st.sidebar:
    st.button("🌐 Switch Language / 切换语言", on_click=toggle_language)
    st.markdown("---")
    st.write(f"**User:** Zhuo")
    st.write(f"**Tier:** Professional Edition")
    st.success("🟢 System Secure")

# ==========================================
# 🖥️ 主界面 (全英文优先)
# ==========================================
st.title(t("Business Intelligence Decision System", "全行业商业智能决策系统"))
st.markdown(t("**Powered by Enterprise-Grade Intelligence Engine**", "**由企业级智能引擎提供支持**"))

tab1, tab2, tab3 = st.tabs([
    t("📍 Site Selection", "📍 智能选址"),
    t("📦 Inventory AI", "📦 库存智脑"),
    t("💰 Dynamic Pricing", "💰 动态定价")
])

# --- TAB 1: 选址 ---
with tab1:
    st.subheader(t("Geospatial Business Intelligence", "地理空间商业智能"))
    
    col1, col2 = st.columns([1, 2])
    with col1:
        address = st.text_input(t("Target Address", "目标地址"), value="39-01 Main St, Flushing, NY 11354")
        traffic = st.slider(t("Daily Foot Traffic", "每日人流量"), 1000, 50000, 30000)

    with col2:
        st.write(t("🛰️ Positioning & Heatmap", "🛰️ 卫星定位与热力图"))
        map_data = pd.DataFrame({
            "lat": [40.7590 + np.random.randn() / 2000],
            "lon": [-73.8290 + np.random.randn() / 2000]
        })
        st.map(map_data, zoom=15)

    if st.button(t("🚀 Run AI Analysis", "🚀 启动 AI 地段分析"), type="primary"):
        # 修改 Spinner：完全去掉 Gemini 字样
        with st.spinner(t("AI is processing spatial data...", "AI 正在分析空间数据...")):
            prompt = f"Analyze the business potential for: {address}. Traffic: {traffic}. Provide: 1. Demographic profile 2. Competitive strategy 3. Score (0-100)."
            res = ask_ai(prompt)
            st.success(t("Analysis Complete", "分析完成"))
            st.markdown(res)

# --- TAB 2: 库存 ---
with tab2:
    st.subheader(t("Asset Health & Cash Flow", "资产健康与现金流诊断"))
    
    if st.button(t("📄 Load ERP Data", "📄 加载 ERP 数据")):
        data = {
            "Item": ["Synthetic Oil", "Wiper Blades", "Brake Pads", "Tires", "Air Filter"],
            "Stock": [120, 450, 30, 8, 200],
            "Cost": [25, 8, 45, 120, 5],
            "Monthly_Sales": [40, 5, 25, 6, 15]
        }
        st.session_state.df = pd.DataFrame(data)

    if "df" in st.session_state:
        df = st.session_state.df
        st.dataframe(df, use_container_width=True)
        
        if st.button(t("🧠 Run Optimization", "🧠 运行库存优化")):
            with st.spinner(t("AI is auditing financial data...", "AI 正在审计财务数据...")):
                advice = ask_ai(f"Audit this inventory data: {df.to_string()}. Find risks.")
                st.info(advice)
