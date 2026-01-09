import streamlit as st
import pandas as pd
import numpy as np
import google.generativeai as genai
import time
import os
import random

# ==========================================
# 🌐 智能网络适配器 (Smart Network Adapter)
# ==========================================
# [上线必读] 部署到 Streamlit Cloud 时，请将下方设置为 False
IS_DEV_MODE = False  

if IS_DEV_MODE:
    # 这里填你本地梯子的端口 (如 7890, 10809)
    PROXY_PORT = "7890" 
    os.environ["HTTP_PROXY"] = f"http://127.0.0.1:{PROXY_PORT}"
    os.environ["HTTPS_PROXY"] = f"http://127.0.0.1:{PROXY_PORT}"
    print(f"🔧 开发模式：强制启用本地代理 {PROXY_PORT}")
else:
    print("🚀 生产模式：使用云端直连网络")

# ==========================================
# 🔑 API 配置区
# ==========================================
# 在本地测试时，填入你的 Key。
# 上线后，建议在 Streamlit 后台 Secrets 里配置，或者暂时先硬编码在这里（演示用）
API_KEY = "AIzaSyDgAIkeGpS2RU1Y1JwvHqXJj5JzFKA4Maw"  # <--- 确保这里有你的 Key

if API_KEY:
    genai.configure(api_key=API_KEY)

# ==========================================
# 🎨 页面配置与美化
# ==========================================
st.set_page_config(
    page_title="Project B: SME Intelligence Platform",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 注入 CSS (深色科技风)
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
        text-shadow: 0px 0px 5px rgba(0,0,0,0.8);
    }
    section[data-testid="stSidebar"] {
        background-color: rgba(0, 0, 0, 0.9);
    }
</style>
""", unsafe_allow_html=True)

# 状态管理
if 'lang' not in st.session_state: st.session_state.lang = 'zh'
def t(zh, en): return zh if st.session_state.lang == 'zh' else en
def toggle_language(): st.session_state.lang = 'en' if st.session_state.lang == 'zh' else 'zh'

# ==========================================
# 🧠 AI 调用函数
# ==========================================
def ask_gemini(prompt_content):
    """通用 AI 调用接口"""
    try:
        if not API_KEY:
            time.sleep(2)
            return "⚠️ API Key Missing. Please configure key."
        
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(prompt_content)
        return response.text
    except Exception as e:
        return f"AI Service Error: {str(e)}"

# ==========================================
# 📱 侧边栏
# ==========================================
with st.sidebar:
    st.button("🌐 Switch Language / 切换语言", on_click=toggle_language)
    st.markdown("---")
    st.image("https://cdn-icons-png.flaticon.com/512/2362/2362378.png", width=50)
    st.write(f"**User:** Zhuo (Owner)")
    st.write("**Status:** NIW Premium")
    st.success("🟢 System Online")
    st.caption("v3.2 Cloud Edition")

# ==========================================
# 🖥️ 主界面
# ==========================================
st.title(t("Project B: 全行业商业智能决策系统", "Project B: SME BI Platform"))
st.markdown("**Powered by Google Gemini AI**")

tab1, tab2, tab3 = st.tabs([
    t("📍 智能选址 (Map AI)", "📍 Site Selection"), 
    t("📦 库存智脑 (Inventory AI)", "📦 Inventory Brain"), 
    t("💰 动态定价 (Pricing)", "💰 Dynamic Pricing")
])

# --- TAB 1: 选址 (带地图) ---
with tab1:
    st.subheader(t("选址与地图智能分析", "Location & Geospatial Intelligence"))
    
    col_map1, col_map2 = st.columns([1, 2])
    with col_map1:
        address = st.text_input(t("输入地址", "Address"), value="39-01 Main St, Flushing, NY 11354")
        traffic = st.slider(t("人流量", "Traffic"), 1000, 50000, 30000)
        
    with col_map2:
        st.write(t("🛰️ 卫星定位与热力图", "Satellite Positioning"))
        # 模拟地图坐标 (演示用)
        map_data = pd.DataFrame({'lat': [40.7590 + np.random.randn()/2000], 'lon': [-73.8290 + np.random.randn()/2000]})
        st.map(map_data, zoom=15)

    if st.button(t("🚀 AI 分析该地段", "🚀 Analyze Location"), type="primary"):
        prompt = f"分析地址【{address}】的商业潜力，已知人流量{traffic}，请给出：1.区域画像 2.竞争策略 3.评分(0-100)。"
        with st.spinner("Gemini is analyzing map data..."):
            res = ask_gemini(prompt)
            st.success("Analysis Complete")
            st.write(res)

# --- TAB 2: 库存 (带数据表格) ---
with tab2:
    st.subheader(t("库存健康度与资金诊断", "Inventory Health & Cash Flow"))
    
    if st.button(t("📄 加载 ERP 数据 (模拟)", "📄 Load ERP Data")):
        # 模拟数据
        data = {
            'Item': ['Synthetic Oil', 'Wiper Blades', 'Brake Pads', 'Tires', 'Air Filter'],
            'Stock': [120, 450, 30, 8, 200],
            'Cost': [25, 8, 45, 120, 5],
            'Monthly_Sales': [40, 5, 25, 6, 15] # Wiper is dead stock
        }
        df = pd.DataFrame(data)
        df['Total_Value'] = df['Stock'] * df['Cost']
        df['Status'] = np.where(df['Monthly_Sales'] < df['Stock']*0.1, '⚠️ Dead Stock', '✅ Healthy')
        st.session_state.df = df
    
    if 'df' in st.session_state:
        df = st.session_state.df
        st.dataframe(df, use_container_width=True)
        
        st.metric("Total Inventory Value", f"${df['Total_Value'].sum():,.0f}")
        
        if st.button(t("🧠 启动 CFO 诊断", "🧠 Run CFO Diagnostics")):
            prompt = f"作为CFO，分析这份库存数据：\n{df.to_string()}\n找出滞销品(Dead Stock)并给出回笼资金的建议。"
            with st.spinner("Analyzing cash flow..."):
                advice = ask_gemini(prompt)
                st.info(advice)

# --- TAB 3: 定价 (简单版) ---
with tab3:
    st.subheader(t("智能定价引擎", "Dynamic Pricing Engine"))
    cost = st.number_input("Cost ($)", 100)
    margin = st.slider("Target Margin (%)", 10, 80, 30)
    st.metric("Recommended Price", f"${cost * (1 + margin/100):.2f}")
