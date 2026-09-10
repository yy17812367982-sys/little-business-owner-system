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
[data-testid="stExpandSidebarButton"] { width:auto !important; min-width:92px;
  min-height:42px; margin:9px 0 0 10px; padding:8px 13px !important;
  border:1px solid #294b37 !important; border-radius:12px !important;
  background:#365c45 !important; color:#fff !important;
  box-shadow:0 4px 14px rgba(41,75,55,.18); }
[data-testid="stExpandSidebarButton"]::after { content:"Menu"; margin-left:7px;
  color:#fff; font-size:.88rem; font-weight:700; letter-spacing:.01em; }
[data-testid="stExpandSidebarButton"] svg { fill:#fff !important; color:#fff !important; }
[data-testid="stExpandSidebarButton"]:hover { background:#294b37 !important;
  border-color:#294b37 !important; }
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
.yy-identity-strip { display:flex; align-items:center; gap:11px; margin:-7px 0 18px;
  padding:10px 13px; border:1px solid #ddd8ca; border-radius:14px; background:#fffaf2; }
.yy-identity-strip>span { display:grid; place-items:center; width:38px; height:38px; border-radius:11px;
  background:#edf1e8; font-size:1.25rem; }
.yy-identity-strip>div { display:flex; min-width:0; flex-direction:column; }
.yy-identity-strip small { color:#687168; font-size:.69rem; font-weight:800; letter-spacing:.08em; text-transform:uppercase; }
.yy-identity-strip b { overflow:hidden; text-overflow:ellipsis; white-space:nowrap; font-family:Georgia,"Times New Roman",serif; }
.yy-identity-strip>i { width:32px; height:8px; margin-left:auto; border-radius:99px; }
.yy-storefront-card { overflow:hidden; border:1px solid #d9d4c6; border-radius:24px; background:#fffdf8;
  box-shadow:0 18px 45px rgba(75,59,38,.12); }
.yy-storefront-head { display:flex; align-items:center; justify-content:space-between; gap:12px; padding:14px 17px; }
.yy-storefront-head>div { display:flex; min-width:0; flex-direction:column; }
.yy-storefront-head span { color:#56705c; font-size:.67rem; font-weight:800; letter-spacing:.12em; }
.yy-storefront-head b { overflow:hidden; text-overflow:ellipsis; white-space:nowrap; font-size:.88rem; }
.yy-storefront-head small { flex:0 0 auto; padding:5px 9px; border-radius:99px; background:#f0eee5; color:#62685f; }
.yy-storefront-scene { position:relative; min-height:335px; overflow:hidden;
  background:linear-gradient(160deg,var(--sf-light) 0 58%,#d7c7ae 58% 100%); perspective:900px; }
.yy-storefront-sky { position:absolute; inset:22px 20px auto auto; display:flex; gap:9px; opacity:.55; }
.yy-storefront-sky i { display:block; width:31px; height:9px; border-radius:99px; background:#fff; box-shadow:18px 3px 0 #fff; }
.yy-storefront-building { position:absolute; left:13%; bottom:42px; width:70%; height:238px;
  transform:rotateY(-7deg) rotateX(1deg); transform-style:preserve-3d; filter:drop-shadow(18px 18px 16px rgba(59,50,38,.18)); }
.yy-storefront-face { position:absolute; inset:0; z-index:2; border:2px solid color-mix(in srgb,var(--sf-accent) 45%,#fff);
  border-radius:5px 5px 2px 2px; background:var(--sf-wall); }
.yy-storefront-side { position:absolute; z-index:1; top:16px; right:-53px; width:56px; height:222px;
  background:color-mix(in srgb,var(--sf-wall) 72%,#6f685d); transform:skewY(-29deg); transform-origin:left top; }
.yy-storefront-roof { position:absolute; z-index:4; left:-7px; top:-14px; width:calc(100% + 34px); height:19px;
  border-radius:4px; background:var(--sf-accent); transform:skewX(24deg); }
.yy-storefront-sign { position:absolute; z-index:4; left:12%; right:10%; top:20px; overflow:hidden; padding:11px 10px;
  border:1px solid rgba(255,255,255,.28); border-radius:5px; background:var(--sf-accent); color:#fff;
  box-shadow:0 5px 0 rgba(58,49,39,.13); font-family:Georgia,"Times New Roman",serif; font-size:clamp(.88rem,2vw,1.25rem);
  letter-spacing:.02em; text-align:center; text-overflow:ellipsis; white-space:nowrap; }
.yy-storefront-awning { position:absolute; z-index:4; top:77px; left:7%; right:6%; display:grid; grid-template-columns:repeat(5,1fr);
  height:34px; transform:skewX(-6deg); filter:drop-shadow(0 7px 3px rgba(64,50,37,.17)); }
.yy-storefront-awning i { background:var(--sf-awning); }
.yy-storefront-awning i:nth-child(even) { background:var(--sf-light); }
.yy-storefront-awning i:first-child { border-radius:2px 0 0 8px; }
.yy-storefront-awning i:last-child { border-radius:0 2px 8px 0; }
.yy-storefront-window { position:absolute; left:8%; right:35%; bottom:20px; height:113px; overflow:hidden;
  border:6px solid var(--sf-accent); border-bottom-width:12px; background:linear-gradient(145deg,#b9d6d1 0 44%,#e8f2ed 44% 55%,#99bbb8 55%);
  box-shadow:inset 18px 0 24px rgba(255,255,255,.3); }
.yy-storefront-decor { position:absolute; inset:auto 8px 20px; display:flex; align-items:end; justify-content:space-around; font-size:1.45rem; }
.yy-storefront-shelf { position:absolute; left:6px; right:6px; bottom:13px; height:5px; background:#765b43; }
.yy-storefront-door { position:absolute; right:8%; bottom:0; display:grid; place-items:center; width:21%; height:130px;
  border:7px solid var(--sf-accent); border-bottom:0; background:linear-gradient(150deg,#9ebfbd,#deebe7); }
.yy-storefront-door:after { content:""; position:absolute; right:8px; width:5px; height:5px; border-radius:50%; background:var(--sf-accent); }
.yy-storefront-door span { font-size:1.25rem; }
.yy-storefront-pavement { position:absolute; left:4%; right:3%; bottom:18px; display:flex; align-items:end; justify-content:space-between;
  min-height:44px; transform:skewX(-18deg); border-radius:4px; background:rgba(255,252,247,.55); }
.yy-storefront-pavement>div { display:flex; gap:8px; padding-left:12px; transform:skewX(18deg); font-size:1.4rem; }
.yy-storefront-pavement>span { padding:0 12px 7px; transform:skewX(18deg); color:#625f56; font-size:.56rem; font-weight:800; letter-spacing:.1em; }
.yy-storefront-foot { display:flex; justify-content:space-between; gap:12px; padding:12px 16px; color:#6a6d64; font-size:.64rem; letter-spacing:.06em; }
.yy-storefront-foot b { overflow:hidden; color:var(--sf-accent); text-overflow:ellipsis; white-space:nowrap; }
.yy-storefront-promise { display:flex; flex-direction:column; gap:4px; margin:11px 0; padding:12px 15px; border-left:4px solid #bd806e;
  border-radius:4px 12px 12px 4px; background:#fffaf2; }
.yy-storefront-promise span { color:#686d64; font-size:.78rem; }
.yy-storefront-promise b { font-family:Georgia,"Times New Roman",serif; font-size:.96rem; }
.yy-explore-callout { margin:14px 0 10px; padding:22px 24px; border:1px solid #cbd9c6; border-radius:21px;
  background:linear-gradient(145deg,#edf3e9,#fffaf2); box-shadow:0 10px 26px rgba(54,92,69,.09); }
.yy-explore-callout>span { color:#456c53; font-size:.68rem; font-weight:800; letter-spacing:.12em; }
.yy-explore-callout h3 { margin:7px 0 5px; font-family:Georgia,"Times New Roman",serif; font-size:1.45rem; }
.yy-explore-callout p { margin:0; color:#5f695f; }
.yy-explore-callout>div { display:flex; flex-wrap:wrap; gap:7px; margin-top:14px; }
.yy-explore-callout>div b { padding:6px 9px; border:1px solid #d6ddcf; border-radius:99px; background:#fffdf8; color:#4a604f; font-size:.72rem; }
.yy-plan-money-story { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:13px; margin:14px 0 20px; }
.yy-plan-money-story section { padding:21px; border:1px solid #ddd6c7; border-radius:21px; background:#fffaf2; }
.yy-plan-money-story section>span { color:#456c53; font-size:.69rem; font-weight:800; letter-spacing:.12em; }
.yy-plan-money-story h3 { min-height:2.5em; margin:7px 0 16px; font-family:Georgia,"Times New Roman",serif; font-size:1.2rem; }
.yy-opening-equation { display:grid; grid-template-columns:minmax(88px,1fr) auto minmax(88px,1fr) auto minmax(88px,1fr); align-items:stretch; gap:7px; }
.yy-opening-equation>div,.yy-month-flow>div { padding:11px; border-radius:12px; background:#eef1e8; }
.yy-opening-equation>div,.yy-month-flow>div,.yy-opening-equation small,.yy-opening-equation b,
.yy-month-flow small,.yy-month-flow b { overflow-wrap:normal; word-break:normal; }
.yy-opening-equation>i { align-self:center; font-style:normal; color:#77786f; }
.yy-opening-equation small,.yy-opening-equation b,.yy-month-flow small,.yy-month-flow b { display:block; }
.yy-opening-equation small,.yy-month-flow small { color:#697068; font-size:.65rem; }
.yy-opening-equation b,.yy-month-flow b { margin-top:4px; font-size:.82rem; }
.yy-opening-equation .negative,.yy-month-flow .negative { background:#f5dfd7; }
.yy-month-flow { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:7px; }
.yy-month-flow .positive { background:#dfecdd; }
.yy-plan-money-story section>p { margin:11px 0 0; color:#5f675e; font-size:.78rem; }
.yy-decision-lead { margin:12px 0 22px; padding:26px; border:1px solid #d5d9c9; border-left:8px solid #557761;
  border-radius:22px; background:#f1f3e9; box-shadow:0 13px 32px rgba(54,72,58,.1); }
.yy-decision-lead.caution { border-left-color:#bf8739; background:#fff5df; }
.yy-decision-lead.stop { border-left-color:#a75b4a; background:#fae9e3; }
.yy-decision-lead h2 { margin:6px 0 7px; font-family:Georgia,"Times New Roman",serif; font-size:clamp(2rem,5vw,3.1rem); }
.yy-decision-lead h2 { clear:both; overflow-wrap:normal; word-break:normal; }
.yy-decision-lead>p { margin:0 0 19px; color:#4f5c53; font-size:1rem; }
.yy-decision-shop { display:flex; align-items:center; gap:9px; width:max-content; max-width:100%; margin:0 0 16px; padding:7px 10px;
  border:1px solid rgba(70,88,73,.15); border-radius:12px; background:rgba(255,255,255,.55); }
.yy-decision-shop>span { font-size:1.25rem; }
.yy-decision-shop>div { display:flex; flex-direction:column; }
.yy-decision-shop small { color:#687168; font-size:.62rem; }
.yy-decision-shop b { max-width:190px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; font-size:.78rem; }
.yy-decision-grid { display:grid; grid-template-columns:1.15fr .85fr; gap:12px; clear:both; }
.yy-decision-grid>div { padding:15px 17px; border:1px solid rgba(70,88,73,.13); border-radius:14px; background:rgba(255,255,255,.63); }
.yy-decision-grid ul { margin:9px 0 0; padding-left:19px; }
.yy-decision-grid li { margin:4px 0; line-height:1.45; }
.yy-decision-grid p { margin:9px 0 0; line-height:1.5; }
.yy-section-kicker { display:block; margin-bottom:7px; color:#456c53; font-size:.73rem;
  font-weight:800; letter-spacing:.12em; text-transform:uppercase; }
.yy-live-pill { display:inline-flex; align-items:center; flex:0 0 auto; padding:7px 11px;
  border-radius:99px; background:#e7eee4; color:#405e48; font-size:.78rem; font-weight:700; }
.yy-ops-story,.yy-finance-story { margin:12px 0 22px; padding:24px; border:1px solid #ddd7c8;
  border-radius:24px; background:#fffaf2; box-shadow:0 13px 34px rgba(81,60,36,.09); }
.yy-ops-story-head,.yy-finance-head { display:flex; align-items:flex-start; justify-content:space-between;
  gap:20px; margin-bottom:18px; }
.yy-ops-story h2,.yy-finance-story h2 { max-width:730px; margin:0; font-family:Georgia,"Times New Roman",serif;
  font-size:clamp(1.65rem,3vw,2.35rem); line-height:1.12; font-weight:600; }
.yy-day-line { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:8px; margin:18px 0; }
.yy-day-part { position:relative; overflow:hidden; min-height:68px; padding:11px 12px;
  border-radius:14px; background:#e8eee4; }
.yy-day-part.busy { background:#f4dfc3; }
.yy-day-part b,.yy-day-part small { display:block; }
.yy-day-part b { margin-bottom:4px; font-size:.84rem; }
.yy-day-part small { color:#667064; font-size:.72rem; }
.yy-ops-body { display:grid; grid-template-columns:minmax(0,1.45fr) minmax(260px,.78fr); gap:14px; }
.yy-shop-picture { overflow:hidden; border-radius:20px; background:linear-gradient(150deg,#f1dfc8,#e5ecdc); }
.yy-shop-sign { margin:15px auto 0; width:max-content; max-width:calc(100% - 30px); padding:9px 20px;
  border-radius:6px 6px 2px 2px; background:#365c45; color:#fff; font-family:Georgia,"Times New Roman",serif;
  font-size:1.08rem; }
.yy-shop-shelf { display:grid; gap:8px; margin:13px 15px 0; padding:14px; border-radius:15px 15px 0 0;
  background:#fffaf3; }
.yy-stock-row { display:grid; grid-template-columns:minmax(95px,1fr) minmax(70px,1.25fr) 54px;
  align-items:center; gap:9px; }
.yy-stock-row span:first-child { min-width:0; }
.yy-stock-row b,.yy-stock-row small { display:block; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.yy-stock-row b { font-size:.82rem; }
.yy-stock-row small { color:#72776f; font-size:.65rem; }
.yy-stock-track { height:10px; overflow:hidden; border-radius:99px; background:#e8ece5; }
.yy-stock-track i { display:block; height:100%; border-radius:inherit; background:#5b8268; }
.yy-stock-track i.risk { background:#bf6d58; }
.yy-stock-row strong { text-align:right; font-size:.72rem; }
.yy-shop-floor { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:8px; padding:15px;
  background:#dcc5a7; }
.yy-shop-floor span { min-width:0; padding:10px; border-radius:12px; background:rgba(255,252,247,.82); }
.yy-shop-floor b,.yy-shop-floor small { display:block; }
.yy-shop-floor b { margin-top:4px; font-size:.8rem; }
.yy-shop-floor small { color:#686c63; font-size:.67rem; }
.yy-next-move { padding:20px; border-radius:20px; background:#365c45; color:#fff; }
.yy-next-move.done { background:#6e9480; }
.yy-next-move>span { font-size:.72rem; font-weight:800; letter-spacing:.08em; text-transform:uppercase; opacity:.8; }
.yy-next-move h3 { margin:14px 0 10px; color:#fff; font-family:Georgia,"Times New Roman",serif;
  font-size:1.45rem; line-height:1.15; }
.yy-next-move p { margin:0; color:#f1f5ef; font-size:.9rem; line-height:1.55; }
.yy-finance-story { background:#fffdf8; }
.yy-revenue-source { margin:18px 0 14px; padding:19px 21px; border-radius:17px; background:#365c45; color:#fff; }
.yy-revenue-source small,.yy-revenue-source b { display:block; }
.yy-revenue-source small { margin-bottom:4px; opacity:.78; }
.yy-revenue-source b { font-family:Georgia,"Times New Roman",serif; font-size:2rem; }
.yy-money-flow { display:grid; gap:9px; }
.yy-money-row { display:grid; grid-template-columns:145px 1fr 92px; align-items:center; gap:10px; }
.yy-money-row>span { color:#636b63; font-size:.82rem; }
.yy-money-row>i { height:23px; overflow:hidden; border-radius:7px; background:#edf0e9; }
.yy-money-row>i>b { display:block; min-width:4px; height:100%; border-radius:inherit; background:#e2b67d; }
.yy-money-row>i>b.team { background:#7ca6a1; }
.yy-money-row>i>b.rent { background:#c89339; }
.yy-money-row>i>b.waste { background:#bf6d58; }
.yy-money-row>i>b.other { background:#a9b1a6; }
.yy-money-row>strong { text-align:right; font-size:.8rem; }
.yy-money-result { display:flex; align-items:center; justify-content:space-between; gap:18px; margin-top:17px;
  padding:16px 18px; border-radius:15px; background:#e8eee4; }
.yy-money-result.negative { background:#f5dfd7; }
.yy-money-result>span { font-family:Georgia,"Times New Roman",serif; font-size:1.05rem; font-weight:600; }
.yy-money-result>b { flex:0 0 auto; font-family:Georgia,"Times New Roman",serif; font-size:1.45rem; }
.yy-linked-note { display:block; margin-top:5px; color:#456c53; font-family:Inter,system-ui,sans-serif;
  font-size:.72rem; font-weight:700; }
.yy-cash-cushion { display:flex; justify-content:space-between; gap:14px; margin-top:12px; color:#626a61; font-size:.78rem; }
.yy-cash-cushion strong { color:#365c45; }
.yy-finance-controls { margin-bottom:8px; padding:18px 20px 5px; border:1px solid #dddccf;
  border-radius:18px; background:#fffaf2; }
.toolkit-footer { text-align:center; font-size:.82rem; color:#656a60; line-height:1.7;
  padding:15px 10px 25px; }
@media(max-width:760px) {
  .block-container { padding:3.2rem 1rem 2rem; }
  [data-testid="stExpandSidebarButton"] { min-width:82px; min-height:40px;
    margin-left:8px; padding:7px 11px !important; }
  [data-testid="stExpandSidebarButton"]::after { font-size:.8rem; }
  .hero-card { padding:24px 21px; border-radius:20px; }
  .hero-card h1 { font-size:2.2rem; }
  .hero-card p { font-size:1rem; }
  .hero-chip { font-size:.76rem; padding:5px 9px; }
  .open-step-wrap { grid-template-columns:repeat(2,minmax(0,1fr)); gap:7px; }
  .open-step-pill { padding:10px; font-size:.83rem; }
  .yy-storefront-scene { min-height:285px; }
  .yy-storefront-building { left:8%; width:76%; height:205px; }
  .yy-storefront-side { height:189px; }
  .yy-storefront-window { right:34%; height:96px; }
  .yy-storefront-door { height:111px; }
  .yy-plan-money-story,.yy-decision-grid { grid-template-columns:1fr; }
  .yy-opening-equation { grid-template-columns:1fr; }
  .yy-opening-equation>i { display:none; }
  .yy-plan-money-story h3 { min-height:0; }
  .yy-decision-lead { padding:21px; }
  .yy-decision-shop { float:none; width:max-content; max-width:100%; margin:0 0 17px; }
  .yy-ops-story,.yy-finance-story { padding:18px; border-radius:20px; }
  .yy-ops-story-head,.yy-finance-head { flex-direction:column; gap:10px; }
  .yy-day-line { grid-template-columns:repeat(2,minmax(0,1fr)); }
  .yy-ops-body { grid-template-columns:1fr; }
  .yy-shop-floor { grid-template-columns:1fr; }
  .yy-money-row { grid-template-columns:105px 1fr 78px; }
  .yy-money-result,.yy-cash-cushion { align-items:flex-start; flex-direction:column; gap:7px; }
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
