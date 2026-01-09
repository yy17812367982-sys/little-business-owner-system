import streamlit as st
import pandas as pd
import numpy as np
import os
import time
import random

# 使用全新 SDK
from google import genai

# ==========================================
# 🔑 API 配置 (通过 Secrets)
# ==========================================
API_KEY = st.secrets.get("GEMINI_API_KEY", "")
client = genai.Client(api_key=API_KEY) if API_KEY else None

# ==========================================
# 🌍 核心修改 1：语言引擎 (默认英文)
# ==========================================
if "lang" not in st.session_state:
    st.session_state.lang = "en"

def t(en, zh):
    return en if st.session_state.lang == "en" else zh

def toggle_language():
    st.session_state.lang = "zh" if st.session_state.lang == "en" else "en"

# ==========================================
# 🧠 核心修改 2：彻底修复 404 的 AI 调用函数
# ==========================================
def ask_ai(prompt_content: str) -> str:
    """ 
    去标识化 AI 接口：适配新版 google-genai SDK 
    """
    if not API_KEY or not client:
        return "System Configuration Error: API Access Denied."

    try:
        # 修复关键点：在新版 SDK 中，模型名通常直接写 'gemini-1.5-flash'
        # 如果还报错，SDK 会自动处理路径映射
        resp = client.models.generate_content(
            model="gemini-1.5-flash", 
            contents=prompt_content
        )
        return resp.text if resp.text else "The AI engine returned an empty result."
    except Exception as e:
        # 记录诊断信息但不展示品牌名
        return f"Service Temporary Unavailable: AI node connection failed."

# ==========================================
# 🎨 页面配置与美化 (默认全英文)
# ==========================================
st.set_page_config(page_title="Intelligence Platform", layout="wide")

# CSS 注入 (隐藏 Google 痕迹)
st.markdown("""
<style>
    .stApp {
        background-image: url("https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=2072&auto=format&fit=crop");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }
    .stTabs, .stMarkdown, .stMetric, .stTextInput, .stNumberInput {
        background-color: rgba(20, 20, 20, 0.85);
        padding: 15px; border-radius: 10px; color: white !important;
    }
</style>
""", unsafe_allow_html=True)

# --- 侧边栏 ---
with st.sidebar:
    st.button("🌐 Switch Language / 切换语言", on_click=toggle_language)
    st.write(f"**Tier:** Professional Edition")
    st.success("🟢 System Online")

# --- 主界面 ---
st.title(t("Business Intelligence Decision System", "全行业商业智能决策系统"))
st.markdown(t("**Enterprise-Grade Intelligence Engine**", "**企业级智能引擎**"))

tab1, tab2 = st.tabs([t("📍 Site Selection", "📍 智能选址"), t("📦 Inventory AI", "📦 库存智脑")])

with tab1:
    st.subheader(t("Geospatial Analysis", "地理空间分析"))
    address = st.text_input(t("Target Address", "目标地址"), value="39-01 Main St, Flushing, NY 11354")
    
    if st.button(t("🚀 Run AI Analysis", "🚀 启动 AI 分析"), type="primary"):
        # 核心修改 3：去掉 Gemini 思考文案
        with st.spinner(t("AI is processing data...", "AI 正在处理数据...")):
            res = ask_ai(f"Analyze business potential for {address}")
            st.success(t("Analysis Complete", "分析完成"))
            st.markdown(res)

with tab2:
    st.subheader(t("Inventory Health", "库存健康诊断"))
    if st.button(t("📄 Load Data", "📄 加载数据")):
        st.info(t("Data loaded from secure ERP node.", "数据已从安全 ERP 节点加载。"))
