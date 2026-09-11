"""Visual planning components backed by the app's existing plan and calculations."""
from copy import deepcopy
import html

import streamlit as st

from business_logic import calculate_open_store_feasibility


SHOP_ICONS = {
    "Flower Shop": "🌷", "Coffee Shop": "☕", "Bakery": "🥐",
    "Restaurant": "🍽️", "Convenience Store": "🛒", "Small Retail Store": "🛍️",
    "Beauty Salon": "✂️", "Auto Parts Store": "🔧", "Other": "🏡",
}

PALETTE_TOKENS = {
    "garden": {"name_en": "Garden mornings", "name_zh": "花园清晨",
               "wall": "#e8eadc", "accent": "#4e6553", "awning": "#bd806e", "light": "#fff9ef"},
    "blush": {"name_en": "Soft blush", "name_zh": "柔和玫瑰",
              "wall": "#f3ddd5", "accent": "#615047", "awning": "#b57672", "light": "#fff8f3"},
    "sunshine": {"name_en": "Sunny neighborhood", "name_zh": "暖阳街角",
                 "wall": "#f3dfad", "accent": "#695444", "awning": "#8da68b", "light": "#fff8e6"},
    "clay": {"name_en": "Coffee & clay", "name_zh": "咖啡与陶土",
             "wall": "#dfc2aa", "accent": "#4d4339", "awning": "#986a50", "light": "#fbf2e7"},
}

DECORATION_PACKS = {
    "Flower Shop": {"window": ("🌿", "🌷", "🌼"), "street": ("🪴", "🌸"), "label": "BOTANICAL DETAILS"},
    "Coffee Shop": {"window": ("☕", "🫘", "🥤"), "street": ("🪑", "🌿"), "label": "COFFEE DETAILS"},
    "Bakery": {"window": ("🥖", "🥐", "🍞"), "street": ("🧺", "🌿"), "label": "BAKERY DETAILS"},
}

STORE_PRESETS = {
    "jenny": {
        "label": "Jenny’s Flower Room", "business_type": "Flower Shop",
        "shop_name": "Jenny’s Flower Room", "mood_palette": "garden",
        "target_customer": "Neighbors marking meaningful everyday moments",
        "differentiator": "Personal bouquets with a warm neighborhood feel",
    },
    "corner_bean": {
        "label": "Corner Bean Café", "business_type": "Coffee Shop",
        "shop_name": "Corner Bean Café", "mood_palette": "clay",
        "target_customer": "Neighbors and commuters looking for a familiar stop",
        "differentiator": "A calm corner for well-made coffee and quick breakfasts",
    },
    "sunrise": {
        "label": "Sunrise Bakery", "business_type": "Bakery",
        "shop_name": "Sunrise Bakery", "mood_palette": "sunshine",
        "target_customer": "Local families and early-morning regulars",
        "differentiator": "Fresh everyday bakes in a bright, welcoming shop",
    },
}

BUSINESS_TYPE_DEFAULTS = {
    "Flower Shop": {"shop_name": "Jenny’s Flower Room", "mood_palette": "garden"},
    "Coffee Shop": {"shop_name": "Corner Bean Café", "mood_palette": "clay"},
    "Bakery": {"shop_name": "Sunrise Bakery", "mood_palette": "sunshine"},
    "Restaurant": {"shop_name": "My Neighborhood Restaurant", "mood_palette": "clay"},
    "Convenience Store": {"shop_name": "My Corner Store", "mood_palette": "sunshine"},
    "Small Retail Store": {"shop_name": "My Little Shop", "mood_palette": "garden"},
    "Beauty Salon": {"shop_name": "My Neighborhood Salon", "mood_palette": "blush"},
    "Auto Parts Store": {"shop_name": "My Auto Parts Shop", "mood_palette": "clay"},
    "Other": {"shop_name": "", "mood_palette": "garden"},
}


def storefront_identity(profile, lang="en"):
    """Return a bounded visual identity; only curated values enter CSS."""
    kind = str(profile.get("business_type") or "Other")
    custom_kind = str(profile.get("custom_business_type") or "").strip()
    display_kind = custom_kind if kind == "Other" and custom_kind else kind
    default_name = "你的小店" if lang == "zh" else "Your Little Shop"
    name = str(profile.get("shop_name") or custom_kind or default_name).strip()[:80]
    palette_key = str(profile.get("mood_palette") or "")
    if palette_key not in PALETTE_TOKENS:
        palette_key = "garden" if kind == "Flower Shop" else "sunshine" if kind == "Bakery" else "clay"
    pack = DECORATION_PACKS.get(kind, {
        "window": (SHOP_ICONS.get(kind, "🏡"), "✦", "▦"), "street": ("🪴", "◫"),
        "label": "SHOP DETAILS",
    })
    return {"kind": kind, "display_kind": display_kind, "name": name,
            "palette_key": palette_key, "palette": PALETTE_TOKENS[palette_key], "pack": pack}


def storefront_markup(profile, lang="en"):
    """Build one reusable 2.5D storefront from shop type, name and palette."""
    identity = storefront_identity(profile, lang)
    palette = identity["palette"]
    pack = identity["pack"]
    esc_name = html.escape(identity["name"])
    esc_kind = html.escape(identity["display_kind"])
    window_items = "".join(f'<span aria-hidden="true">{item}</span>' for item in pack["window"])
    street_items = "".join(f'<span aria-hidden="true">{item}</span>' for item in pack["street"])
    eyebrow = "你的小店正在成形" if lang == "zh" else "YOUR IDEA IS TAKING SHAPE"
    illustrative = "示意图 · 不代表已验证需求" if lang == "zh" else "ILLUSTRATIVE · NOT VERIFIED DEMAND"
    palette_name = palette["name_zh" if lang == "zh" else "name_en"]
    return f"""
<div class="yy-storefront-card" data-shop-type="{html.escape(identity['kind'], quote=True)}" data-palette="{identity['palette_key']}"
 style="--sf-wall:{palette['wall']};--sf-accent:{palette['accent']};--sf-awning:{palette['awning']};--sf-light:{palette['light']}">
  <div class="yy-storefront-head"><div><span>{eyebrow}</span><b>{esc_kind}</b></div>
    <small>{html.escape(palette_name)}</small></div>
  <div class="yy-storefront-scene" role="img" aria-label="{html.escape(illustrative + ': ' + identity['name'], quote=True)}">
    <div class="yy-storefront-sky"><i></i><i></i><i></i></div>
    <div class="yy-storefront-building">
      <div class="yy-storefront-side"></div><div class="yy-storefront-roof"></div>
      <div class="yy-storefront-face">
        <div class="yy-storefront-sign">{esc_name}</div>
        <div class="yy-storefront-awning"><i></i><i></i><i></i><i></i><i></i></div>
        <div class="yy-storefront-window"><div class="yy-storefront-decor">{window_items}</div><div class="yy-storefront-shelf"></div></div>
        <div class="yy-storefront-door"><span>{SHOP_ICONS.get(identity['kind'], '◆')}</span></div>
      </div>
    </div>
    <div class="yy-storefront-pavement"><div>{street_items}</div><span>{html.escape(pack['label'])}</span></div>
  </div>
  <div class="yy-storefront-foot"><span>{illustrative}</span><b>{esc_name}</b></div>
</div>"""


def _sync_profile_widgets(profile, fields):
    for field, value in fields.items():
        profile[field] = value
    widget_keys = {
        "business_type": "open_business_type", "shop_name": "open_shop_name",
        "mood_palette": "open_storefront_palette", "target_customer": "open_target_customer",
        "differentiator": "open_differentiator", "custom_business_type": "open_custom_business_type",
    }
    for field, key in widget_keys.items():
        if field in fields:
            st.session_state[key] = fields[field]


def apply_store_preset(profile, preset_key):
    """Apply concept-only sample text; never introduce financial or traction data."""
    if preset_key == "own":
        _sync_profile_widgets(profile, {
            "business_type": "Other", "custom_business_type": "", "shop_name": "",
            "target_customer": "", "differentiator": "", "mood_palette": "garden",
        })
        st.session_state.open_shop_name_customized = False
        st.session_state.open_storefront_palette_customized = False
        return
    preset = STORE_PRESETS[preset_key]
    _sync_profile_widgets(profile, {key: value for key, value in preset.items() if key != "label"})
    st.session_state.open_shop_name_customized = False
    st.session_state.open_storefront_palette_customized = False


def apply_business_type(profile, kind=None):
    """Change visual defaults without overwriting a name or palette the owner edited."""
    new_kind = kind or st.session_state.get("open_business_type", "Other")
    current_name = str(st.session_state.get("open_shop_name", profile.get("shop_name", "")) or "")
    current_palette = str(st.session_state.get("open_storefront_palette", profile.get("mood_palette", "")) or "")
    known_names = {item["shop_name"] for item in BUSINESS_TYPE_DEFAULTS.values()}
    known_palettes = {item["mood_palette"] for item in BUSINESS_TYPE_DEFAULTS.values()}
    defaults = BUSINESS_TYPE_DEFAULTS.get(new_kind, BUSINESS_TYPE_DEFAULTS["Other"])
    profile["business_type"] = new_kind
    st.session_state.open_business_type = new_kind
    if not st.session_state.get("open_shop_name_customized") or current_name in known_names:
        profile["shop_name"] = defaults["shop_name"]
        st.session_state.open_shop_name = defaults["shop_name"]
        st.session_state.open_shop_name_customized = False
    if not st.session_state.get("open_storefront_palette_customized") or current_palette in known_palettes:
        profile["mood_palette"] = defaults["mood_palette"]
        st.session_state.open_storefront_palette = defaults["mood_palette"]
        st.session_state.open_storefront_palette_customized = False


def mark_shop_name_customized():
    st.session_state.open_shop_name_customized = True


def mark_storefront_palette_customized():
    st.session_state.open_storefront_palette_customized = True


def render_store_presets(profile, lang):
    zh = lang == "zh"
    st.markdown("#### " + ("从一个示意概念开始" if zh else "Start from an illustrative concept"))
    st.caption("这些示例只提供店名、店型和视觉方向，不包含经营表现、客流或财务假设。" if zh else
               "These examples set only concept text and visual identity—never performance, traction or financial assumptions.")
    columns = st.columns(4)
    options = [("jenny", "Jenny’s Flower Room"), ("corner_bean", "Corner Bean Café"),
               ("sunrise", "Sunrise Bakery"), ("own", "Start with my own idea")]
    for column, (key, label) in zip(columns, options):
        translated = "从我的想法开始" if zh and key == "own" else label
        column.button(translated, key=f"store_preset_{key}", use_container_width=True,
                      on_click=apply_store_preset, args=(profile, key))


def render_shop_cards(profile, lang):
    zh = lang == "zh"
    st.caption("选择店型，店面装饰会立即改变。" if zh else "Choose a shop type and the storefront details change instantly.")
    columns = st.columns(3)
    for column, (kind, label) in zip(columns, [
        ("Flower Shop", "花店" if zh else "Flower shop"),
        ("Coffee Shop", "咖啡店" if zh else "Coffee shop"),
        ("Bakery", "烘焙店" if zh else "Bakery"),
    ]):
        def choose(value=kind):
            apply_business_type(st.session_state.profile, value)
        column.button(f"{SHOP_ICONS[kind]}  {label}", key=f"shop_card_{kind}",
                      type="primary" if profile.get("business_type") == kind else "secondary",
                      on_click=choose, use_container_width=True)


def render_idea_preview(profile, lang):
    customer = profile.get("target_customer") or ("你想服务谁？" if lang == "zh" else "Who would love this place?")
    promise = profile.get("differentiator") or ("写一句你的特色，预览会同步更新。" if lang == "zh" else
                                                "Add your special touch and the preview will follow.")
    st.markdown(
        storefront_markup(profile, lang)
        + f'<div class="yy-storefront-promise"><span>{html.escape(str(customer))}</span>'
        f'<b>{html.escape(str(promise))}</b></div>', unsafe_allow_html=True,
    )
    st.caption("这是视觉构想，不是经过验证的市场需求或成功预测。" if lang == "zh" else
               "This is a visual concept—not verified market demand or a prediction of success.")


def money_scenario(profile, site, launch, pricing, scenario_key):
    """Run a what-if through existing calculations without mutating the base plan."""
    scenario_launch = deepcopy(launch)
    if scenario_key == "sales_down":
        scenario_launch["expected_monthly_revenue"] = float(launch["expected_monthly_revenue"]) * 0.80
    elif scenario_key == "sales_up":
        scenario_launch["expected_monthly_revenue"] = float(launch["expected_monthly_revenue"]) * 1.15
    elif scenario_key == "opening_down":
        scenario_launch["startup_cost_estimate"] = float(launch["startup_cost_estimate"]) * 0.90
    return calculate_open_store_feasibility(deepcopy(profile), deepcopy(site), scenario_launch, deepcopy(pricing))


def render_money_story(profile, site, launch, pricing, metrics, lang):
    zh = lang == "zh"
    funding = float(launch["funding_available"])
    startup = float(metrics["startup_cost"])
    cash_left = funding - startup
    gap = float(metrics["funding_gap"])
    result = float(metrics["monthly_profit_after_fixed"])
    st.markdown(f"""
<div class="yy-plan-money-story">
  <section><span>{'OPENING DAY · 开业日' if zh else 'OPENING DAY'}</span><h3>{'开门之后，手头还剩多少？' if zh else 'What remains after the doors open?'}</h3>
    <div class="yy-opening-equation"><div><small>{'可用现金' if zh else 'Cash available'}</small><b>USD {funding:,.0f}</b></div><i>−</i>
    <div><small>{'开店成本' if zh else 'Opening cost'}</small><b>USD {startup:,.0f}</b></div><i>=</i>
    <div class="{'negative' if cash_left < 0 else ''}"><small>{'开业后现金' if zh else 'Cash left after opening'}</small><b>USD {cash_left:,.0f}</b></div></div>
    <p>{('目标现金储备仍差 USD ' if zh else 'Gap to the target cash reserve: USD ') + f'{gap:,.0f}'}</p></section>
  <section><span>{'AN ORDINARY MONTH · 普通月份' if zh else 'AN ORDINARY MONTH'}</span><h3>{'一个普通月的钱会怎么走？' if zh else 'How does the money move in a normal month?'}</h3>
    <div class="yy-month-flow"><div><small>{'销售额' if zh else 'Sales'}</small><b>USD {metrics['expected_revenue']:,.0f}</b></div>
    <div><small>{'商品成本' if zh else 'Product costs'}</small><b>− USD {metrics['ordinary_cogs']:,.0f}</b></div>
    <div><small>{'固定费用' if zh else 'Fixed costs'}</small><b>− USD {metrics['monthly_fixed_cost']:,.0f}</b></div>
    <div class="{'negative' if result < 0 else 'positive'}"><small>{'月度结果' if zh else 'Monthly result'}</small><b>USD {result:,.0f}</b></div></div></section>
</div>""", unsafe_allow_html=True)

    st.markdown("### " + ("What if? · 如果情况有变化" if zh else "What if?"))
    st.caption("以下仅为模拟，绝不会改写上方基础计划。" if zh else
               "These scenarios are simulations only. Your base plan stays unchanged.")
    labels = {
        "sales_down": "Sales -20%" if not zh else "销售额 -20%",
        "sales_up": "Sales +15%" if not zh else "销售额 +15%",
        "opening_down": "Opening cost -10%" if not zh else "开店成本 -10%",
    }
    selected = st.radio("Scenario" if not zh else "选择情景", list(labels), horizontal=True,
                        format_func=lambda key: labels[key], key="open_money_what_if", label_visibility="collapsed")
    scenario = money_scenario(profile, site, launch, pricing, selected)
    left, right, third = st.columns(3)
    left.metric("Monthly sales" if not zh else "月销售额", f"USD {scenario['expected_revenue']:,.0f}")
    right.metric("Opening cost" if not zh else "开店成本", f"USD {scenario['startup_cost']:,.0f}")
    third.metric("Monthly result" if not zh else "月度结果", f"USD {scenario['monthly_profit_after_fixed']:,.0f}")
    st.caption(("模拟结果 · 基础输入未改变" if zh else "Simulated result · base inputs unchanged") +
               (" · 包含当前损耗设置" if zh else " · includes current waste settings"))


def render_money_picture(launch, metrics, lang):
    """Compatibility wrapper for older imports; new UI uses render_money_story."""
    del launch
    st.caption(("月度结果：" if lang == "zh" else "Monthly result: ") +
               f"USD {metrics['monthly_profit_after_fixed']:,.0f}")


def decision_reasons(metrics, lang):
    zh = lang == "zh"
    reasons = []
    if metrics["funding_gap"] > 0:
        reasons.append((f"目标现金储备仍差 USD {metrics['funding_gap']:,.0f}" if zh else
                        f"The target cash reserve has a USD {metrics['funding_gap']:,.0f} gap"))
    else:
        reasons.append(("资金覆盖开店成本和目标固定费用储备" if zh else
                        "Available cash covers opening cost and the target fixed-cost reserve"))
    if metrics["monthly_profit_after_fixed"] < 0:
        reasons.append((f"普通月份预计亏损 USD {abs(metrics['monthly_profit_after_fixed']):,.0f}" if zh else
                        f"An ordinary month is estimated to lose USD {abs(metrics['monthly_profit_after_fixed']):,.0f}"))
    else:
        reasons.append((f"普通月份预计结余 USD {metrics['monthly_profit_after_fixed']:,.0f}" if zh else
                        f"An ordinary month is estimated to leave USD {metrics['monthly_profit_after_fixed']:,.0f}"))
    if metrics.get("site_score_provisional"):
        reasons.append(("选址仅有公开地图和租金形成的临时证据，仍需线下核实" if zh else
                        "Location evidence is provisional public-map and rent evidence; verify it in person"))
    elif metrics.get("location_pending"):
        reasons.append(("选址证据尚未探索，不能判断真实需求" if zh else
                        "Location evidence is still unexplored; demand has not been verified"))
    return reasons[:3]


def decision_next_action(metrics, lang):
    zh = lang == "zh"
    if not metrics.get("decision_ready"):
        return "返回预算页修正输入错误。" if zh else "Return to Budget and correct the blocking input errors."
    if metrics["monthly_profit_after_fixed"] < 0:
        return ("先测试能否提高普通月销售或降低商品与固定成本，再承担租约。" if zh else
                "Test a path to higher ordinary-month sales or lower product and fixed costs before taking on a lease.")
    if metrics["funding_gap"] > 0:
        return ("先缩小开店成本、谈免租期或补足资金缺口。" if zh else
                "Reduce opening cost, negotiate a rent-free period, or close the funding gap first.")
    if metrics.get("location_pending"):
        return ("线下核实客流、租约和附近竞争，再决定是否签约。" if zh else
                "Verify storefront footfall, lease terms and nearby competition in person before signing.")
    return "完成开业前检查清单，再决定是否投入。" if zh else "Complete the pre-launch checklist before committing funds."


def render_decision_lead(metrics, decision_message, display_decision, profile, lang):
    identity = storefront_identity(profile, lang)
    reasons = decision_reasons(metrics, lang)
    reason_html = "".join(f"<li>{html.escape(reason)}</li>" for reason in reasons)
    next_action = decision_next_action(metrics, lang)
    decision_class = "go" if metrics["decision"] == "GO" else "caution" if metrics["decision"] == "CAUTION" else "stop"
    st.markdown(f"""
<div class="yy-decision-lead {decision_class}">
  <div class="yy-decision-shop"><span>{SHOP_ICONS.get(identity['kind'], '🏡')}</span><div><small>{html.escape(identity['display_kind'])}</small><b>{html.escape(identity['name'])}</b></div></div>
  <span class="yy-section-kicker">{'SHOULD I OPEN? · 是否开店？' if lang == 'zh' else 'SHOULD I OPEN?'}</span>
  <h2>{html.escape(str(display_decision))}</h2><p>{html.escape(str(decision_message))}</p>
  <div class="yy-decision-grid"><div><b>{'为什么？' if lang == 'zh' else 'Why?'}</b><ul>{reason_html}</ul></div>
  <div><b>{'下一步做什么？' if lang == 'zh' else 'What should I do next?'}</b><p>{html.escape(next_action)}</p></div></div>
</div>""", unsafe_allow_html=True)


def render_store_identity_strip(profile, step, lang):
    identity = storefront_identity(profile, lang)
    verbs_en = ("Imagine it", "Place it", "Make the money work", "Decide")
    verbs_zh = ("想象它", "找到它的位置", "让钱算得通", "做决定")
    verb = verbs_zh[step - 1] if lang == "zh" else verbs_en[step - 1]
    st.markdown(
        f'<div class="yy-identity-strip"><span>{SHOP_ICONS.get(identity["kind"], "🏡")}</span>'
        f'<div><small>{html.escape(verb)} · {step}/4</small><b>{html.escape(identity["name"])}</b></div>'
        f'<i style="background:{identity["palette"]["awning"]}"></i></div>', unsafe_allow_html=True,
    )
