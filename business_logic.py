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


def _seasonal_inputs(launch: Dict[str, Any]) -> Dict[str, Any]:
    """Validate optional scenario inputs without silently accepting NaN or infinity.

    Invalid values receive a safe calculation default AND a blocking error; the
    fallback must never turn an invalid scenario into a launch recommendation.
    """
    errors: List[str] = []
    enabled = launch.get("perishable_enabled", False)
    if not isinstance(enabled, bool):
        errors.append("Perishable inventory must be enabled or disabled.")
        enabled = False

    normalized: Dict[str, Any] = {"perishable_enabled": enabled}
    fields = (
        ("spoilage_rate_pct", "Spoilage rate", 0.0, 0.0, 80.0),
        ("holiday_sales_multiplier", "Holiday sales multiplier", 1.0, 0.1, 5.0),
        ("holiday_cost_multiplier", "Holiday wholesale cost multiplier", 1.0, 0.1, 5.0),
        ("holiday_months", "Holiday months", 0.0, 0.0, 12.0),
    )
    for key, label, default, minimum, maximum in fields:
        value = launch.get(key, default)
        try:
            number = float(value)
        except (ValueError, TypeError, OverflowError):
            number = math.nan
        if (
            isinstance(value, bool)
            or not math.isfinite(number)
            or not minimum <= number <= maximum
            or (key == "holiday_months" and not number.is_integer())
        ):
            whole = "a whole number " if key == "holiday_months" else "a finite number "
            errors.append(f"{label} must be {whole}between {minimum:g} and {maximum:g}.")
            number = default
        normalized[key] = int(number) if key == "holiday_months" else number
    normalized["errors"] = errors
    return normalized


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
    raw_gm = _as_float(launch.get("expected_gross_margin")) / 100.0
    target_months = max(1.0, _as_float(launch.get("cash_target_months"), 3.0))
    seasonal = _seasonal_inputs(launch)
    waste_fraction = seasonal["spoilage_rate_pct"] / 100.0 if seasonal["perishable_enabled"] else 0.0
    retained_fraction = 1.0 - waste_fraction
    raw_unit_cost = _as_float(pricing.get("cost"))
    effective_unit_cost = raw_unit_cost / retained_fraction
    # The entered margin excludes inventory waste. Sales are fulfilled sales,
    # so enough inventory must be purchased to replace the unsold fraction.
    # Preserve ordinary results exactly when the optional waste feature is off.
    expected_gm = 1.0 - (1.0 - raw_gm) / retained_fraction if waste_fraction else raw_gm

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
    if not 0 < raw_gm < 1:
        input_errors.append("Expected gross margin must be between 0% and 100%.")
    input_errors.extend(seasonal["errors"])

    pricing_check = validate_pricing({**pricing, "cost": effective_unit_cost})
    if waste_fraction:
        pricing_check["errors"] = [
            message.replace("unit cost (", "effective unit cost after spoilage (")
            for message in pricing_check["errors"]
        ]
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
    raw_cogs = expected_revenue * (1.0 - raw_gm)
    ordinary_cogs = raw_cogs / retained_fraction
    monthly_spoilage_extra_cost = ordinary_cogs - raw_cogs
    peak_revenue = expected_revenue * seasonal["holiday_sales_multiplier"]
    peak_cogs = ordinary_cogs * seasonal["holiday_sales_multiplier"] * seasonal["holiday_cost_multiplier"]
    peak_gross_margin = (peak_revenue - peak_cogs) / peak_revenue if peak_revenue > 0 else 0.0
    peak_profit_after_fixed = peak_revenue - peak_cogs - monthly_fixed_cost
    modeled_annual_profit = (
        monthly_profit_after_fixed * (12 - seasonal["holiday_months"])
        + peak_profit_after_fixed * seasonal["holiday_months"]
    )
    if waste_fraction:
        input_warnings.append(
            f"Spoilage adds USD {monthly_spoilage_extra_cost:,.0f} to ordinary monthly inventory costs; "
            "the entered product cost and business gross margin must exclude this waste "
            "to avoid counting it twice."
        )
    if seasonal["holiday_months"] > 0 and peak_profit_after_fixed < 0:
        input_warnings.append(
            f"The holiday scenario loses USD {abs(peak_profit_after_fixed):,.0f} per peak month; "
            "higher sales do not guarantee profit when wholesale costs also rise."
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
        "raw_unit_cost": raw_unit_cost,
        "effective_unit_cost": effective_unit_cost,
        "raw_gross_margin_pct": raw_gm * 100,
        "ordinary_adjusted_gross_margin_pct": expected_gm * 100,
        "ordinary_cogs": ordinary_cogs,
        "monthly_spoilage_extra_cost": monthly_spoilage_extra_cost,
        "peak_revenue": peak_revenue,
        "peak_cogs": peak_cogs,
        "peak_gross_margin_pct": peak_gross_margin * 100,
        "peak_profit_after_fixed": peak_profit_after_fixed,
        "modeled_annual_profit": modeled_annual_profit,
        "perishable_enabled": seasonal["perishable_enabled"],
        "spoilage_rate_pct": seasonal["spoilage_rate_pct"],
        "applied_spoilage_rate_pct": waste_fraction * 100,
        "holiday_sales_multiplier": seasonal["holiday_sales_multiplier"],
        "holiday_cost_multiplier": seasonal["holiday_cost_multiplier"],
        "holiday_months": seasonal["holiday_months"],
        "scenario_assumptions": [
            "Launch decisions and scores use the ordinary month, never holiday profits.",
            "When perishable inventory is enabled, all costs of goods represented by the entered "
            "gross margin and the representative product cost are assumed perishable. "
            "Enter both before spoilage; do not include the same waste twice.",
            "Spoilage is the fraction of purchased inventory lost: effective unit cost equals "
            "raw unit cost / (1 - waste rate), and ordinary costs of goods equal "
            "ordinary revenue * (1 - entered gross margin) / (1 - waste rate).",
            "The holiday sales multiplier is an unverified sales-volume scenario at unchanged "
            "selling prices. It increases both revenue and inventory needs. The holiday wholesale "
            "cost multiplier then changes costs of goods per unit; spoilage is applied only once.",
            "Monthly fixed costs and spoilage rates stay constant in ordinary and holiday months. "
            "Any extra holiday staffing, delivery, or rent must be allowed for separately.",
            "Modeled annual operating profit equals ordinary monthly profit * (12 - holiday months) "
            "+ holiday monthly profit * holiday months. It excludes startup spending, financing "
            "and taxes, and is not a cash-flow forecast.",
        ],
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
