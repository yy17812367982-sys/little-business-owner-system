"""Pure business rules for the small-business decision application.

Keeping these calculations outside Streamlit makes them independently testable
and prevents the UI and AI report from using different financial logic.
"""

from __future__ import annotations

from typing import Any, Dict, List
import math


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    return number if math.isfinite(number) else default


def score_from_inputs_site(
    traffic: int,
    competitors: int,
    rent_level: str,
    parking: str,
) -> int:
    """Return the transparent 0-100 location score used by the app."""
    score = 55.0
    if traffic >= 40000:
        score += 10
    elif traffic >= 25000:
        score += 6
    else:
        score += 2

    if competitors <= 6:
        score += 12
    elif competitors <= 12:
        score += 6
    else:
        score -= 6

    if rent_level == "Low":
        score += 8
    elif rent_level == "Medium":
        score += 3
    else:
        score -= 6

    if parking == "High":
        score += 6
    elif parking == "Medium":
        score += 2
    else:
        score -= 4

    return int(max(0, min(100, score)))


def validate_pricing(pricing: Dict[str, Any]) -> Dict[str, Any]:
    """Validate one representative product before it affects a decision."""
    cost = _as_float(pricing.get("cost"))
    planned_price = _as_float(pricing.get("planned_price"))
    competitor_price = _as_float(pricing.get("competitor_price"))
    errors: List[str] = []
    warnings: List[str] = []

    if cost <= 0:
        errors.append("Unit cost must be greater than USD 0.")
    if planned_price <= 0:
        errors.append("Planned price must be greater than USD 0.")
    if cost > 0 and planned_price > 0 and planned_price <= cost:
        errors.append(
            f"Planned price (USD {planned_price:,.2f}) must be higher than "
            f"unit cost (USD {cost:,.2f})."
        )

    implied_margin = (
        (planned_price - cost) / planned_price
        if planned_price > 0
        else 0.0
    )
    implied_markup = (
        (planned_price - cost) / cost
        if cost > 0
        else 0.0
    )

    if not errors and implied_margin < 0.10:
        warnings.append(
            f"Representative product margin is only {implied_margin:.1%}; "
            "review cost and price assumptions."
        )
    if competitor_price > 0 and planned_price > 0:
        price_ratio = planned_price / competitor_price
        if price_ratio < 0.50 or price_ratio > 1.50:
            warnings.append(
                "Planned price differs from the competitor price by more than 50%; "
                "confirm both amounts and units."
            )

    return {
        "valid": not errors,
        "errors": errors,
        "warnings": warnings,
        "cost": cost,
        "planned_price": planned_price,
        "competitor_price": competitor_price,
        "implied_margin": implied_margin,
        "implied_markup": implied_markup,
    }


def calculate_open_store_feasibility(
    profile: Dict[str, Any],
    site: Dict[str, Any],
    launch: Dict[str, Any],
    pricing: Dict[str, Any],
) -> Dict[str, Any]:
    """Calculate the single source of truth for scores and launch decisions."""
    budget = _as_float(profile.get("budget"))
    funding_available = _as_float(launch.get("funding_available"), budget)
    startup_cost = _as_float(launch.get("startup_cost_estimate"))
    monthly_fixed_cost = _as_float(launch.get("monthly_fixed_cost_estimate"))
    expected_revenue = _as_float(launch.get("expected_monthly_revenue"))
    expected_gm = _as_float(launch.get("expected_gross_margin")) / 100.0
    target_months = max(1.0, _as_float(launch.get("cash_target_months"), 3.0))

    input_errors: List[str] = []
    input_warnings: List[str] = []
    if funding_available <= 0:
        input_errors.append("Available launch funding must be greater than USD 0.")
    if startup_cost < 0:
        input_errors.append("Startup cost cannot be negative.")
    if monthly_fixed_cost <= 0:
        input_errors.append("Monthly fixed cost must be greater than USD 0.")
    if expected_revenue <= 0:
        input_errors.append("Expected monthly revenue must be greater than USD 0.")
    if not 0 < expected_gm < 1:
        input_errors.append("Expected gross margin must be between 0% and 100%.")

    pricing_check = validate_pricing(pricing)
    input_errors.extend(pricing_check["errors"])
    input_warnings.extend(pricing_check["warnings"])

    remaining_cash = funding_available - startup_cost
    runway_months = (
        remaining_cash / monthly_fixed_cost
        if monthly_fixed_cost > 0
        else math.inf
    )
    target_cash_need = monthly_fixed_cost * target_months
    funding_gap = max(0.0, startup_cost + target_cash_need - funding_available)
    contribution_profit = expected_revenue * expected_gm
    monthly_profit_after_fixed = contribution_profit - monthly_fixed_cost
    breakeven_revenue = (
        monthly_fixed_cost / expected_gm
        if expected_gm > 0
        else math.inf
    )

    site_score = score_from_inputs_site(
        int(_as_float(site.get("traffic"))),
        int(_as_float(site.get("competitors"))),
        str(site.get("rent_level", "Medium")),
        str(site.get("parking", "Medium")),
    )

    cash_score = 100
    if runway_months < 1:
        cash_score = 20
    elif runway_months < 2:
        cash_score = 45
    elif runway_months < target_months:
        cash_score = 65
    else:
        cash_score = 85
    if funding_gap > 0:
        cash_score = max(15, cash_score - 20)

    product_margin = pricing_check["implied_margin"]
    margin_gap = abs(expected_gm - product_margin)
    if not pricing_check["valid"]:
        margin_score = 0
    else:
        conservative_margin = min(expected_gm, product_margin)
        if monthly_profit_after_fixed > 0 and conservative_margin >= 0.55:
            margin_score = 85
        elif monthly_profit_after_fixed > 0 and conservative_margin >= 0.35:
            margin_score = 70
        elif monthly_profit_after_fixed > 0 and conservative_margin >= 0.20:
            margin_score = 55
        else:
            margin_score = 35

        if margin_gap > 0.15:
            margin_score = min(margin_score, 55)
            input_warnings.append(
                "Expected business gross margin and representative product margin "
                f"differ by {margin_gap:.1%}; reconcile the assumptions."
            )

    competitors = int(_as_float(site.get("competitors")))
    competition_score = 80
    if competitors > 20:
        competition_score = 35
    elif competitors > 12:
        competition_score = 55
    elif competitors > 6:
        competition_score = 70

    score_weights = {
        "site": 0.35,
        "cash": 0.35,
        "margin": 0.20,
        "competition": 0.10,
    }
    overall_score = int(round(
        site_score * score_weights["site"]
        + cash_score * score_weights["cash"]
        + margin_score * score_weights["margin"]
        + competition_score * score_weights["competition"]
    ))

    decision_ready = not input_errors
    if not decision_ready:
        decision = "REVIEW INPUTS"
    elif overall_score >= 75 and funding_gap <= 0 and monthly_profit_after_fixed >= 0:
        decision = "GO"
    elif overall_score >= 55:
        decision = "CAUTION"
    else:
        decision = "NO-GO"

    risks: List[str] = []
    risks.extend(f"Input error: {message}" for message in input_errors)
    risks.extend(f"Assumption warning: {message}" for message in input_warnings)
    if funding_gap > 0:
        risks.append(f"Funding gap of USD {funding_gap:,.0f} against target cash runway")
    if runway_months < target_months:
        risks.append(
            f"Cash runway is {runway_months:.1f} months, below the target of "
            f"{target_months:g} months"
        )
    if monthly_profit_after_fixed < 0:
        risks.append(
            "Expected monthly gross profit does not cover fixed costs; "
            f"estimated shortfall is USD {abs(monthly_profit_after_fixed):,.0f}/month"
        )
    if site.get("rent_level") == "High":
        risks.append("Rent level is marked High, increasing break-even pressure")
    if competitors > 12:
        risks.append(
            f"Competitive density is high with {competitors} competitors in the selected radius"
        )

    competitor_price = pricing_check["competitor_price"]
    planned_price = pricing_check["planned_price"]
    price_vs_competitor = (
        (planned_price - competitor_price) / competitor_price
        if competitor_price > 0
        else 0.0
    )
    if price_vs_competitor > 0.10:
        risks.append(
            f"Planned price is {price_vs_competitor:.1%} above competitor price"
        )

    return {
        "startup_cost": startup_cost,
        "monthly_fixed_cost": monthly_fixed_cost,
        "remaining_cash": remaining_cash,
        "runway_months": runway_months,
        "target_cash_need": target_cash_need,
        "funding_gap": funding_gap,
        "expected_revenue": expected_revenue,
        "expected_gross_margin_pct": expected_gm * 100,
        "contribution_profit": contribution_profit,
        "monthly_profit_after_fixed": monthly_profit_after_fixed,
        "breakeven_revenue": breakeven_revenue,
        "site_score": site_score,
        "cash_score": cash_score,
        "margin_score": margin_score,
        "competition_score": competition_score,
        "overall_score": overall_score,
        "decision": decision,
        "decision_ready": decision_ready,
        "recommended_price": planned_price,
        "unit_cost": pricing_check["cost"],
        "competitor_price": competitor_price,
        "implied_margin_pct": product_margin * 100,
        "implied_markup_pct": pricing_check["implied_markup"] * 100,
        "price_vs_competitor_pct": price_vs_competitor * 100,
        "margin_assumption_gap_pct": margin_gap * 100,
        "input_errors": input_errors,
        "input_warnings": input_warnings,
        "pricing_valid": pricing_check["valid"],
        "score_weights": score_weights,
        "risks": risks,
    }
