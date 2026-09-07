"""Shared warm, accessible visual language for Yang Yu's business toolkit."""

WARM_CSS = """
<style>
:root { --ink:#293b31; --muted:#62675d; --cream:#faf7f0; --paper:#fffcf7;
  --sage:#e9eee3; --green:#365c45; --clay:#9b563c; --line:#dddccf; }
html, body { overflow-x:hidden; }
.stApp { background:var(--cream); color:var(--ink); }
.block-container { max-width:1160px; padding-top:3.4rem; padding-bottom:3rem; }
[data-testid="stHeader"] { background:rgba(250,247,240,.95); }
[data-testid="stSidebar"] { background:#f0f0e6; border-right:1px solid var(--line); }
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h3 { font-size:1rem; }
h1, h2, h3 { color:var(--ink); letter-spacing:-.025em; }
h1 { font-family:Georgia,"Times New Roman",serif; font-weight:500; }
h2 { font-size:1.65rem; }
h3 { font-size:1.22rem; }
p, li { line-height:1.65; }
a { color:#355a44; text-underline-offset:3px; }
[data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] p,
[data-testid="stCaption"], [data-testid="stCaption"] p { color:var(--muted); }
.hero-card { position:relative; overflow:hidden; border:1px solid #dedfcf;
  border-radius:26px; background:#eef0e5; padding:32px 36px; margin-bottom:18px; }
.hero-eyebrow { color:#486548; font-size:.75rem; font-weight:700; letter-spacing:.15em;
  text-transform:uppercase; margin-bottom:12px; }
.hero-card h1 { font-size:clamp(2.1rem,4.5vw,3.4rem); line-height:1.12; max-width:720px;
  margin:0 0 14px; padding:0; }
.hero-card p { max-width:700px; margin:0; color:#4b5c4c; font-size:1.05rem; }
.hero-points { display:flex; flex-wrap:wrap; gap:9px; margin-top:23px; }
.hero-chip { background:#fffcf7; border:1px solid #d7ddcf; border-radius:99px;
  padding:6px 12px; color:#435643; font-size:.84rem; }
.card { border:1px solid var(--line); background:var(--paper); border-radius:17px;
  padding:17px 20px; margin:10px 0 18px; color:var(--ink); }
.trust-card { background:#edf2e9; border:1px solid #cedcca; border-radius:16px;
  padding:18px 20px; margin:12px 0 18px; color:#324d3b; line-height:1.65; }
.demo-badge { display:inline-block; border-radius:99px; padding:5px 11px;
  background:#f5ebd7; border:1px solid #e4d6bc; color:#725330;
  font-size:.8rem; font-weight:600; }
[data-testid="stExpander"] { background:var(--paper); border-radius:16px;
  border-color:var(--line); }
[data-testid="stForm"] { background:var(--paper); border-color:var(--line); border-radius:16px; }
[data-baseweb="input"], [data-baseweb="base-input"], [data-baseweb="textarea"],
[data-baseweb="select"] > div { border-radius:11px; }
[data-testid="stTextInput"] input, [data-testid="stTextArea"] textarea,
[data-testid="stNumberInput"] input { color:var(--ink); }
[data-testid="stButton"] button, [data-testid="stDownloadButton"] button,
[data-testid="stFormSubmitButton"] button { border-radius:12px; min-height:43px;
  padding:.5rem 1rem; transition:background-color .15s ease; }
[data-testid="stButton"] button[kind="secondary"],
[data-testid="stDownloadButton"] button,
[data-testid="stFormSubmitButton"] button[kind="secondary"] {
  background:var(--paper); border-color:#cbd3c4; color:var(--ink); }
[data-testid="stButton"] button[kind="primary"],
[data-testid="stFormSubmitButton"] button[kind="primary"] {
  background:var(--green); border-color:var(--green); color:white; }
[data-testid="stButton"] button[kind="primary"] p,
[data-testid="stFormSubmitButton"] button[kind="primary"] p { color:white; }
button:disabled { opacity:.5; cursor:not-allowed; }
button:focus-visible, input:focus-visible, textarea:focus-visible {
  outline:3px solid #8a6c3d !important; outline-offset:3px; }
[data-testid="stMetric"] { background:var(--paper); padding:16px 18px;
  border:1px solid var(--line); border-radius:16px; min-height:104px; }
[data-testid="stMetricLabel"] { color:#5a6558; }
[data-testid="stMetricValue"] { color:var(--ink); font-size:1.75rem; font-weight:600; }
[data-testid="stAlert"] { border-radius:13px; }
[data-testid="stMarkdownContainer"] table { width:100%; background:var(--paper); }
[data-testid="stMarkdownContainer"] th { background:var(--sage); color:var(--ink); }
[data-testid="stMarkdownContainer"] th, [data-testid="stMarkdownContainer"] td {
  padding:10px 13px; border:1px solid var(--line); }
[data-testid="stMarkdownContainer"] { overflow-wrap:anywhere; }
.open-step-wrap { display:grid; grid-template-columns:repeat(4,minmax(0,1fr));
  gap:10px; margin:17px 0 20px; }
.open-step-pill { display:flex; align-items:center; gap:9px; padding:12px 14px;
  border:1px solid var(--line); border-radius:13px; font-size:.89rem; }
.open-step-pill.current { background:#365c45; color:#fff; border-color:#365c45; font-weight:700; }
.open-step-pill.complete { background:#e7eedf; color:#385037; border-color:#cbd9c2; }
.open-step-pill.upcoming { background:#f4f1e8; color:#696d61; }
.open-step-badge { font-size:.9rem; }
.open-step-text { line-height:1.25; }
.toolkit-footer { text-align:center; font-size:.82rem; color:#656a60; line-height:1.7;
  padding:15px 10px 25px; }
@media(max-width:760px) {
  .block-container { padding:3.2rem 1rem 2rem; }
  .hero-card { padding:24px 21px; border-radius:20px; }
  .hero-card h1 { font-size:2.2rem; }
  .hero-card p { font-size:1rem; }
  .hero-chip { font-size:.76rem; padding:5px 9px; }
  .open-step-wrap { grid-template-columns:repeat(2,minmax(0,1fr)); gap:7px; }
  .open-step-pill { padding:10px; font-size:.83rem; }
  [data-testid="stHorizontalBlock"] { flex-wrap:wrap; gap:.8rem; }
  [data-testid="stHorizontalBlock"] > [data-testid="column"],
  [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {
    flex:1 1 100%; min-width:0; width:100%; }
  [data-testid="stDataFrame"] { overflow-x:auto; }
  [data-testid="stMetricValue"] { font-size:1.6rem; }
}
@media(prefers-reduced-motion:reduce) { * { transition:none !important; } }
</style>
"""
