"""Visual planning feedback using the same inputs and calculations as the report."""
import html
import math

import pandas as pd
import streamlit as st

SHOP_ICONS = {"Flower Shop": "🌷", "Coffee Shop": "☕", "Bakery": "🥐",
              "Restaurant": "🍽️", "Convenience Store": "🛒", "Small Retail Store": "🛍️",
              "Beauty Salon": "✂️", "Auto Parts Store": "🔧", "Other": "🏡"}


def render_shop_cards(profile, lang):
    zh = lang == "zh"
    st.caption("点一个店型，开始想象你的店。" if zh else "Pick a shop to start picturing your idea.")
    columns = st.columns(3)
    for column, (kind, label) in zip(columns, [
        ("Flower Shop", "花店" if zh else "Flower shop"),
        ("Coffee Shop", "咖啡店" if zh else "Coffee shop"),
        ("Bakery", "烘焙店" if zh else "Bakery"),
    ]):
        def choose(value=kind):
            st.session_state.open_business_type = value
            st.session_state.profile["business_type"] = value
        column.button(f"{SHOP_ICONS[kind]}  {label}", key=f"shop_card_{kind}",
                      type="primary" if profile.get("business_type") == kind else "secondary",
                      on_click=choose, use_container_width=True)


def render_idea_preview(profile, lang):
    zh = lang == "zh"
    kind = profile.get("business_type", "Other")
    title = profile.get("custom_business_type") if kind == "Other" else kind
    title = title or ("我的小店" if zh else "Your little shop")
    customer = profile.get("target_customer") or ("你想服务谁？" if zh else "Who would love this place?")
    promise = profile.get("differentiator") or ("写一句你的特色，预览就会更新。" if zh else "Add your special touch and watch this take shape.")
    st.markdown(f"""
<div style="border:1px solid #d5ddcb;border-radius:24px;padding:28px;background:#f0f0e6;margin:12px 0">
<div style="font-size:48px" aria-hidden="true">{SHOP_ICONS.get(kind, "🏡")}</div>
<p style="color:#365c45">{'你的小店正在成形' if zh else 'YOUR IDEA IS TAKING SHAPE'}</p>
<h3>{html.escape(str(title))}</h3>
<p>{html.escape(str(customer))}</p>
<hr style="border:0;border-top:1px solid #cbd5c5">
<p>{html.escape(str(promise))}</p>
</div>""", unsafe_allow_html=True)
    st.caption("这是你的构想预览，不代表已验证的市场需求。" if zh else
               "A picture of your idea, not evidence of market demand.")


def render_money_picture(launch, metrics, lang):
    zh = lang == "zh"
    st.subheader("看看钱会怎么走" if zh else "See where your money goes")
    st.caption("图表使用当前输入和损耗调整；修改数字后会更新。" if zh else
               "These charts use your current inputs, including waste. Change a number to update the picture.")
    funding = float(launch["funding_available"])
    required = metrics["startup_cost"] + metrics["monthly_fixed_cost"] * int(launch["cash_target_months"])
    revenue = float(launch["expected_monthly_revenue"])
    profit = metrics["monthly_profit_after_fixed"]
    columns = st.columns(2)
    with columns[0]:
        st.markdown("**启动资金够不够？**" if zh else "**Enough to open and keep going?**")
        st.bar_chart(pd.DataFrame({
            "USD": [funding, required],
        }, index=["手头资金" if zh else "Cash available",
                  "开店 + 目标储备" if zh else "Opening + target reserve"]),
            color="#365c45", horizontal=True, height=220)
        st.caption(("目标储备按固定费用计算：" if zh else "Reserve based on fixed costs: ") +
                   f"{int(launch['cash_target_months'])} " + ("个月。" if zh else "months."))
    with columns[1]:
        st.markdown("**普通月份会剩多少？**" if zh else "**What is left in an ordinary month?**")
        st.bar_chart(pd.DataFrame({
            "USD": [revenue, revenue - profit, profit],
        }, index=["销售收入" if zh else "Sales",
                  "商品 + 固定费用" if zh else "Product + fixed costs",
                  "月度结果" if zh else "Monthly result"]),
            color="#bd806e", horizontal=True, height=220)
        st.caption("负数表示亏损。未计税费和融资等额外费用。" if zh else
                   "A negative result means a loss. Taxes, financing and other extra costs are excluded.")
    gap = metrics["funding_gap"]
    breakeven = metrics["breakeven_revenue"]
    if gap > 0:
        st.info((f"距离目标资金还差 USD {gap:,.0f}。试着降低开店成本，看看图怎么变。" if zh else
                 f"USD {gap:,.0f} short of your funding target. Try a lower opening cost and see what changes."))
    if math.isfinite(breakeven):
        st.caption((f"按当前利润假设，每月销售约 USD {breakeven:,.0f} 才能打平。" if zh else
                    f"At your current margin, about USD {breakeven:,.0f} in monthly sales covers costs."))

