"""Warm, owner-friendly visual summaries for Operations and Finance."""

from __future__ import annotations

from html import escape
from math import isfinite

import pandas as pd
import streamlit as st


def _money(value: float) -> str:
    return f"USD {value:,.0f}"


def build_operations_focus(health: dict, lang: str = "en") -> dict:
    """Choose one defensible next action from computed inventory health."""
    candidates = [
        ("perishable", health.get("perishable_items")),
        ("stockout", health.get("stockout_items")),
        ("overstock", health.get("overstock_items")),
    ]
    kind = "healthy"
    chosen = None
    for candidate_kind, frame in candidates:
        if isinstance(frame, pd.DataFrame) and not frame.empty:
            kind = candidate_kind
            sort_col = "Total_Value" if "Total_Value" in frame.columns else frame.columns[0]
            chosen = frame.sort_values(sort_col, ascending=False).iloc[0]
            break

    if chosen is None:
        frame = health.get("df2")
        if isinstance(frame, pd.DataFrame) and not frame.empty:
            chosen = frame.sort_values("Total_Value", ascending=False).iloc[0]

    if chosen is None:
        return {
            "kind": "empty",
            "item": "",
            "title": "先放入一份库存数据" if lang == "zh" else "Start with a simple inventory picture",
            "copy": "系统会从损耗、缺货和积压中，只挑出今天最值得处理的一件事。" if lang == "zh" else "The toolkit will choose one useful move from waste, stockout and overstock risks.",
            "action": "",
            "savings": 0.0,
        }

    item = str(chosen.get("Item", "Item"))
    stock = max(float(chosen.get("Stock", 0) or 0), 0.0)
    cost = max(float(chosen.get("Cost", 0) or 0), 0.0)
    total_value = max(float(chosen.get("Total_Value", stock * cost) or 0), 0.0)
    savings = min(total_value, max(cost * min(stock, max(stock * 0.35, 1)), 0.0))

    if kind == "perishable":
        title = f"今天先处理 {item}" if lang == "zh" else f"Give {item} a plan today"
        copy = (
            f"它的现有库存可能超过保鲜期内能卖出的数量。先做套餐、当日特选或小批量折扣，最多可优先保护约 {_money(savings)} 的库存。"
            if lang == "zh" else
            f"Current stock may outlast its shelf life. A same-day feature, bundle, or small promotion can prioritize about {_money(savings)} of inventory."
        )
        action = "加入今天的保鲜行动" if lang == "zh" else "Add a freshness action for today"
    elif kind == "stockout":
        title = f"先确认 {item} 的补货" if lang == "zh" else f"Confirm the {item} reorder first"
        copy = (
            "库存覆盖已经进入风险区。先核对供应商交期和现有订单，再决定补货量。"
            if lang == "zh" else
            "Inventory cover is already in the risk zone. Check supplier timing and open orders before confirming quantity."
        )
        action = "加入今天的补货检查" if lang == "zh" else "Add a reorder check for today"
        savings = 0.0
    elif kind == "overstock":
        title = f"暂停 {item} 的自动补货" if lang == "zh" else f"Pause automatic reorders for {item}"
        copy = (
            f"这项库存占用约 {_money(total_value)}。先暂停补货，再考虑组合销售、退货或折扣。"
            if lang == "zh" else
            f"This item ties up about {_money(total_value)}. Pause replenishment before trying bundles, returns, or a targeted discount."
        )
        action = "加入今天的去库存行动" if lang == "zh" else "Add an overstock action for today"
        savings = 0.0
    else:
        title = "今天没有明显的库存警报" if lang == "zh" else "No obvious inventory alarm today"
        copy = (
            f"{item} 是当前库存价值较高的项目，保持正常检查即可。"
            if lang == "zh" else
            f"{item} is one of the larger inventory positions; a normal check is enough for now."
        )
        action = "标记今天已检查" if lang == "zh" else "Mark today’s check complete"
        savings = 0.0

    return {
        "kind": kind,
        "item": item,
        "title": title,
        "copy": copy,
        "action": action,
        "savings": round(savings, 2),
    }


def render_operations_story(health: dict, focus: dict, lang: str = "en", plan_applied: bool = False) -> None:
    """Render one unified shop-day picture from computed inventory results."""
    df = health["df2"].copy()
    urgent = len(health.get("stockout_items", []))
    perishable = len(health.get("perishable_items", []))
    overstock = len(health.get("overstock_items", []))
    total_attention = urgent + perishable + overstock

    cards = []
    ranked = df.assign(
        _priority=(df["Perishable_Risk"].ne("").astype(int) * 3)
        + (df["Status"].eq("Critical Stockout Risk").astype(int) * 2)
        + (df["Status"].isin(["Overstock", "Dead / Overstock", "No Sales / Review"]).astype(int))
    ).sort_values(["_priority", "Total_Value"], ascending=[False, False]).head(3)
    for _, row in ranked.iterrows():
        cover = float(row.get("Months_Of_Cover", 0) or 0)
        if not isfinite(cover):
            cover = 12.0
        fill = max(8, min(100, cover / 4 * 100))
        is_risk = bool(row.get("Perishable_Risk")) or str(row.get("Status")) == "Critical Stockout Risk"
        status = str(row.get("Perishable_Risk") or row.get("Status") or "Review")
        cards.append(
            "<div class='yy-stock-row'>"
            f"<span><b>{escape(str(row.get('Item', 'Item')))}</b><small>{escape(status)}</small></span>"
            f"<span class='yy-stock-track'><i class='{'risk' if is_risk else ''}' style='width:{fill:.0f}%'></i></span>"
            f"<strong>{cover:.1f} mo</strong></div>"
        )

    focus_label = "已加入今天的计划" if lang == "zh" and plan_applied else (
        "Added to today’s plan" if plan_applied else ("今天最值得做" if lang == "zh" else "Best next move")
    )
    day_labels = (
        [("开店前", "收货与准备"), ("上午", "平稳营业"), ("下午", "订单高峰"), ("关店前", "清点与整理")]
        if lang == "zh" else
        [("Before open", "Deliveries & prep"), ("Morning", "Steady service"), ("Afternoon", "Order rush"), ("Before close", "Count & refresh")]
    )
    timeline = "".join(
        f"<span class='yy-day-part {'busy' if idx == 2 else ''}'><b>{escape(a)}</b><small>{escape(b)}</small></span>"
        for idx, (a, b) in enumerate(day_labels)
    )
    summary = (
        f"{total_attention} 个项目需要关注" if lang == "zh" else f"{total_attention} items deserve attention"
    )
    st.markdown(
        f"""
        <section class="yy-ops-story">
          <div class="yy-ops-story-head">
            <div><span class="yy-section-kicker">{'今天的小店' if lang == 'zh' else 'TODAY AT YOUR SHOP'}</span>
            <h2>{'看着店面安排今天，而不是盯着表格。' if lang == 'zh' else 'Run the day by looking at the shop—not a spreadsheet.'}</h2></div>
            <span class="yy-live-pill">{escape(summary)}</span>
          </div>
          <div class="yy-day-line">{timeline}</div>
          <div class="yy-ops-body">
            <div class="yy-shop-picture">
              <div class="yy-shop-sign">{'库存小屋' if lang == 'zh' else 'Your stock room'}</div>
              <div class="yy-shop-shelf">{''.join(cards)}</div>
              <div class="yy-shop-floor">
                <span>🌿 <b>{'库存' if lang == 'zh' else 'Stock'}</b><small>{perishable} {'项损耗风险' if lang == 'zh' else 'waste risks'}</small></span>
                <span>🧺 <b>{'补货' if lang == 'zh' else 'Reorders'}</b><small>{urgent} {'项紧急' if lang == 'zh' else 'urgent'}</small></span>
                <span>🤝 <b>{'现金' if lang == 'zh' else 'Cash'}</b><small>{_money(health.get('slow_value', 0))} {'被积压占用' if lang == 'zh' else 'tied up'}</small></span>
              </div>
            </div>
            <aside class="yy-next-move {'done' if plan_applied else ''}">
              <span>{escape(focus_label)}</span>
              <h3>{escape(focus['title'])}</h3>
              <p>{escape(focus['copy'])}</p>
            </aside>
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def calculate_finance_snapshot(
    average_sale: float,
    orders_per_day: int,
    monthly_rent: float,
    *,
    payroll: float,
    other_fixed: float,
    product_cost_rate: float,
    waste_rate: float,
    available_cash: float,
    operations_savings: float = 0.0,
) -> dict:
    """Calculate the owner-facing money flow without hiding assumptions."""
    average_sale = max(float(average_sale), 0.0)
    orders_per_day = max(int(orders_per_day), 0)
    monthly_rent = max(float(monthly_rent), 0.0)
    payroll = max(float(payroll), 0.0)
    other_fixed = max(float(other_fixed), 0.0)
    product_cost_rate = min(max(float(product_cost_rate), 0.0), 1.0)
    waste_rate = min(max(float(waste_rate), 0.0), 1.0)
    available_cash = max(float(available_cash), 0.0)
    operations_savings = max(float(operations_savings), 0.0)

    revenue = average_sale * orders_per_day * 26
    product_cost = revenue * product_cost_rate
    gross_waste = revenue * product_cost_rate * waste_rate
    applied_operations_savings = min(operations_savings, gross_waste)
    waste = gross_waste - applied_operations_savings
    total_cost = product_cost + payroll + monthly_rent + other_fixed + waste
    monthly_result = revenue - total_cost
    fixed_cost = payroll + monthly_rent + other_fixed
    reserve_months = available_cash / fixed_cost if fixed_cost else float("inf")
    return {
        "revenue": revenue,
        "product_cost": product_cost,
        "payroll": payroll,
        "rent": monthly_rent,
        "other_fixed": other_fixed,
        "waste": waste,
        "total_cost": total_cost,
        "monthly_result": monthly_result,
        "reserve_months": reserve_months,
        "operations_savings": operations_savings,
        "applied_operations_savings": applied_operations_savings,
    }


def render_finance_story(snapshot: dict, lang: str = "en") -> None:
    """Render an immediately readable money-flow picture."""
    expenses = [
        ("商品和材料" if lang == "zh" else "Products & materials", snapshot["product_cost"], "materials"),
        ("团队" if lang == "zh" else "Team", snapshot["payroll"], "team"),
        ("房租" if lang == "zh" else "Rent", snapshot["rent"], "rent"),
        ("损耗" if lang == "zh" else "Spoilage", snapshot["waste"], "waste"),
        ("其他固定费用" if lang == "zh" else "Other fixed bills", snapshot["other_fixed"], "other"),
    ]
    scale = max((value for _, value, _ in expenses), default=1.0) or 1.0
    flows = "".join(
        "<div class='yy-money-row'>"
        f"<span>{escape(label)}</span><i><b class='{kind}' style='width:{max(3, value / scale * 100):.1f}%'></b></i>"
        f"<strong>{_money(value)}</strong></div>"
        for label, value, kind in expenses
    )
    result = snapshot["monthly_result"]
    reserve = snapshot["reserve_months"]
    reserve_text = "∞" if not isfinite(reserve) else f"{reserve:.1f}"
    human_summary = (
        (f"按这个节奏，每月大约能留下 {_money(result)}。" if result >= 0 else f"按这个节奏，每月大约还差 {_money(abs(result))}。")
        if lang == "zh" else
        (f"At this pace, the shop keeps about {_money(result)} each month." if result >= 0 else f"At this pace, the shop falls short by about {_money(abs(result))} each month.")
    )
    linked = ""
    if snapshot.get("applied_operations_savings", 0) > 0:
        linked = (
            f"<small class='yy-linked-note'>✓ {'今天的运营行动已减少约' if lang == 'zh' else 'Today’s operations action reduces about'} {_money(snapshot['applied_operations_savings'])} {'的情景损耗' if lang == 'zh' else 'of modeled spoilage'}.</small>"
        )
    elif snapshot.get("operations_savings", 0) > 0:
        linked = (
            "<small class='yy-linked-note'>✓ "
            + ("运营行动已经保存；在 Open a Store 填写损耗假设后，Finance 才会把它计入试算。" if lang == "zh" else
               "The operations action is saved. Add a spoilage assumption in Open a Store before Finance includes it in the estimate.")
            + "</small>"
        )
    st.markdown(
        f"""
        <section class="yy-finance-story">
          <div class="yy-finance-head"><div><span class="yy-section-kicker">{'钱从哪里来，又去了哪里' if lang == 'zh' else 'SEE WHERE THE MONEY GOES'}</span>
          <h2>{'不是财务迷宫，而是一张钱的流向图。' if lang == 'zh' else 'Not a finance maze—just a clear money flow.'}</h2></div>
          <span class="yy-live-pill">{'可盈利情景' if result >= 0 and lang == 'zh' else ('Healthy scenario' if result >= 0 else ('需要调整' if lang == 'zh' else 'Needs adjustment'))}</span></div>
          <div class="yy-revenue-source"><small>{'每月进账' if lang == 'zh' else 'Money coming in each month'}</small><b>{_money(snapshot['revenue'])}</b></div>
          <div class="yy-money-flow">{flows}</div>
          <div class="yy-money-result {'negative' if result < 0 else ''}"><span>{human_summary}{linked}</span><b>{_money(result)}</b></div>
          <div class="yy-cash-cushion"><span>{'现有现金可覆盖固定费用' if lang == 'zh' else 'Cash reserve covers fixed costs for'}</span><strong>{reserve_text} {'个月' if lang == 'zh' else 'months'}</strong></div>
        </section>
        """,
        unsafe_allow_html=True,
    )
