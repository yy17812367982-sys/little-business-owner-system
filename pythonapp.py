import streamlit as st
import pandas as pd

# =========================
# Page config
# =========================
st.set_page_config(
    page_title="Project B: SME BI Platform",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================
# CSS + JS injection
# =========================
st.markdown(
    r"""
<style>
html, body {
  height: 100%;
  overflow: hidden;
}

div[data-testid="stAppViewContainer"]{
  height: 100vh;
  overflow-y: auto;
  overflow-x: hidden;
  -webkit-overflow-scrolling: touch;
}

.stApp{
  min-height: 100vh;
  overflow: hidden;
}

.block-container{
  padding-top: 1rem;
  padding-bottom: 0.5rem;
}
footer { display:none; }

/* Card */
.card{
  background: rgba(0,0,0,0.30);
  border: 1px solid rgba(255,255,255,0.12);
  border-radius: 16px;
  padding: 14px;
  margin: 8px 0;
}

/* Menu button */
.fab-menu{
  position: fixed;
  left: 12px;
  top: 12px;
  z-index: 10000;
  width: 44px;
  height: 44px;
  border-radius: 14px;
  border: 1px solid rgba(255,255,255,0.18);
  background: rgba(0,0,0,0.45);
  color: #fff;
  font-size: 22px;
  line-height: 44px;
  text-align: center;
  cursor: pointer;
  user-select: none;
  backdrop-filter: blur(10px);
}

/* Desktop: sidebar always visible */
@media (min-width: 901px){
  section[data-testid="stSidebar"]{
    transform: translateX(0) !important;
    visibility: visible !important;
  }
}

/* Mobile: sidebar hidden by default */
@media (max-width: 900px){
  section[data-testid="stSidebar"]{
    transform: translateX(-105%) !important;
    visibility: hidden !important;
  }
  body.sidebar-open section[data-testid="stSidebar"]{
    transform: translateX(0) !important;
    visibility: visible !important;
  }
}
</style>

<div class="fab-menu" onclick="window.toggleSidebar()" title="Menu">☰</div>

<script>
window.toggleSidebar = function(){
  const doc = window.parent.document;
  doc.body.classList.toggle("sidebar-open");
};
</script>
""",
    unsafe_allow_html=True
)

# =========================
# Sidebar
# =========================
with st.sidebar:
    st.markdown("## Suites")
    suite = st.radio(
        "",
        ["Open a Store", "Operations", "Finance"],
        index=0
    )

# =========================
# Main content
# =========================
st.title("Project B: SME BI Platform")

def scroll_top():
    st.markdown("<script>window.parent.scrollTo(0,0)</script>", unsafe_allow_html=True)

def scroll_bottom():
    st.markdown("<script>window.parent.scrollTo(0,document.body.scrollHeight)</script>", unsafe_allow_html=True)

c1, c2, c3 = st.columns([1,1,6])
with c1:
    if st.button("⬆ Top"):
        scroll_top()
with c2:
    if st.button("⬇ Bottom"):
        scroll_bottom()

st.markdown("---")

if suite == "Open a Store":
    st.header("Open a Store")
    st.markdown("<div class='card'>Step 1: Business profile</div>", unsafe_allow_html=True)
    st.text_input("Business type")
    st.text_input("City")

elif suite == "Operations":
    st.header("Operations")
    st.markdown("<div class='card'>Weekly inventory review</div>", unsafe_allow_html=True)

elif suite == "Finance":
    st.header("Finance")
    st.markdown("<div class='card'>Upload your finance data</div>", unsafe_allow_html=True)
    st.file_uploader("Upload CSV", type=["csv"])

st.caption("v-stable-sidebar-1.0")
