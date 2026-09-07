"""Financial regression tests for optional waste and holiday scenarios."""

import copy
import math
import unittest

from business_logic import calculate_open_store_feasibility
from test_business_logic import LAUNCH, PRICING, PROFILE, SITE


class SeasonalFinanceTests(unittest.TestCase):
    def setUp(self):
        self.launch = {
            "funding_available": 100000,
            "startup_cost_estimate": 10000,
            "monthly_fixed_cost_estimate": 2000,
            "expected_monthly_revenue": 10000,
            "expected_gross_margin": 60,
            "cash_target_months": 3,
        }
        self.pricing = {"cost": 40, "planned_price": 100, "competitor_price": 100}

    def calculate(self, **scenario):
        return calculate_open_store_feasibility(
            PROFILE, SITE, {**self.launch, **scenario}, self.pricing
        )

    def test_omitted_and_explicit_defaults_preserve_existing_results(self):
        original = calculate_open_store_feasibility(PROFILE, SITE, LAUNCH, PRICING)
        explicit = calculate_open_store_feasibility(
            PROFILE,
            SITE,
            {
                **LAUNCH,
                "perishable_enabled": False,
                "spoilage_rate_pct": 0,
                "holiday_sales_multiplier": 1,
                "holiday_cost_multiplier": 1,
                "holiday_months": 0,
            },
            PRICING,
        )
        self.assertEqual(original, explicit)
        self.assertEqual(original["overall_score"], 51)
        self.assertEqual(original["decision"], "NO-GO")
        self.assertEqual(original["margin_score"], 85)
        self.assertAlmostEqual(original["monthly_profit_after_fixed"], 5740)
        self.assertAlmostEqual(original["breakeven_revenue"], 26500 / 0.62)
        self.assertEqual(original["unit_cost"], 1.75)
        self.assertEqual(original["monthly_spoilage_extra_cost"], 0)

    def test_waste_replaces_lost_inventory_once_in_product_and_business_costs(self):
        result = self.calculate(perishable_enabled=True, spoilage_rate_pct=20)
        self.assertEqual(result["raw_unit_cost"], 40)
        self.assertEqual(result["effective_unit_cost"], 50)
        self.assertEqual(result["unit_cost"], 50)
        self.assertEqual(result["ordinary_cogs"], 5000)
        self.assertEqual(result["monthly_spoilage_extra_cost"], 1000)
        self.assertEqual(result["ordinary_adjusted_gross_margin_pct"], 50)
        self.assertEqual(result["expected_gross_margin_pct"], 50)
        self.assertEqual(result["raw_gross_margin_pct"], 60)
        self.assertEqual(result["monthly_profit_after_fixed"], 3000)
        self.assertEqual(result["implied_margin_pct"], 50)
        self.assertEqual(result["breakeven_revenue"], 4000)
        self.assertEqual(result["margin_score"], 70)
        self.assertTrue(any("exclude this waste" in text for text in result["input_warnings"]))

    def test_disabling_waste_ignores_saved_spoilage_amount(self):
        baseline = self.calculate()
        disabled = self.calculate(perishable_enabled=False, spoilage_rate_pct=80)
        for key in (
            "decision", "overall_score", "monthly_profit_after_fixed", "unit_cost",
            "expected_gross_margin_pct", "monthly_spoilage_extra_cost", "modeled_annual_profit",
        ):
            self.assertEqual(disabled[key], baseline[key], key)
        self.assertEqual(disabled["applied_spoilage_rate_pct"], 0)

    def test_zero_waste_does_not_change_ordinary_results(self):
        baseline = self.calculate()
        enabled = self.calculate(perishable_enabled=True, spoilage_rate_pct=0)
        for key in ("unit_cost", "monthly_profit_after_fixed", "overall_score", "decision"):
            self.assertEqual(enabled[key], baseline[key], key)

    def test_price_that_only_covers_raw_cost_is_blocking_after_waste(self):
        for price in (45, 50):
            with self.subTest(price=price):
                self.pricing["planned_price"] = price
                result = self.calculate(perishable_enabled=True, spoilage_rate_pct=20)
                self.assertEqual(result["decision"], "REVIEW INPUTS")
                self.assertFalse(result["decision_ready"])
                self.assertFalse(result["pricing_valid"])
                self.assertEqual(result["margin_score"], 0)
                self.assertTrue(any("effective unit cost after spoilage" in e for e in result["input_errors"]))

    def test_holiday_volume_cost_and_waste_are_not_double_counted(self):
        result = self.calculate(
            perishable_enabled=True,
            spoilage_rate_pct=20,
            holiday_sales_multiplier=2,
            holiday_cost_multiplier=1.5,
            holiday_months=2,
        )
        self.assertEqual(result["peak_revenue"], 20000)
        self.assertEqual(result["peak_cogs"], 15000)
        self.assertEqual(result["peak_gross_margin_pct"], 25)
        self.assertEqual(result["peak_profit_after_fixed"], 3000)
        self.assertEqual(result["modeled_annual_profit"], 36000)
        self.assertEqual(result["ordinary_cogs"], 5000)

    def test_more_holiday_sales_can_still_produce_losses(self):
        result = self.calculate(
            perishable_enabled=True,
            spoilage_rate_pct=20,
            holiday_sales_multiplier=2,
            holiday_cost_multiplier=3,
            holiday_months=2,
        )
        self.assertEqual(result["peak_revenue"], 20000)
        self.assertEqual(result["peak_profit_after_fixed"], -12000)
        self.assertEqual(result["modeled_annual_profit"], 6000)
        self.assertTrue(any("holiday scenario loses" in text for text in result["input_warnings"]))

    def test_holiday_scenario_never_improves_the_baseline_decision(self):
        self.launch["monthly_fixed_cost_estimate"] = 7000
        baseline = self.calculate()
        peak = self.calculate(holiday_sales_multiplier=5, holiday_cost_multiplier=0.1, holiday_months=12)
        self.assertLess(baseline["monthly_profit_after_fixed"], 0)
        self.assertGreater(peak["peak_profit_after_fixed"], 0)
        for key in (
            "decision", "overall_score", "margin_score", "cash_score", "funding_gap",
            "runway_months", "monthly_profit_after_fixed", "breakeven_revenue",
        ):
            self.assertEqual(peak[key], baseline[key], key)
        self.assertNotEqual(peak["decision"], "GO")

    def test_zero_and_twelve_holiday_months_use_the_correct_annual_blend(self):
        for months in (0, 1, 12):
            with self.subTest(months=months):
                result = self.calculate(holiday_sales_multiplier=2, holiday_months=months)
                self.assertEqual(result["modeled_annual_profit"], 4000 * (12 - months) + 10000 * months)

    def test_valid_limits_do_not_crash_even_when_spoilage_destroys_margin(self):
        for waste in (0, 80):
            for factor in (0.1, 5):
                with self.subTest(waste=waste, factor=factor):
                    result = self.calculate(
                        perishable_enabled=True,
                        spoilage_rate_pct=waste,
                        holiday_sales_multiplier=factor,
                        holiday_cost_multiplier=factor,
                        holiday_months=12,
                    )
                    self.assertFalse(any("must be a finite" in text for text in result["input_errors"]))
                    self.assertTrue(math.isfinite(result["effective_unit_cost"]))
                    self.assertTrue(math.isfinite(result["modeled_annual_profit"]))
                    if waste == 80:
                        self.assertLess(result["ordinary_adjusted_gross_margin_pct"], 0)
                        self.assertTrue(math.isinf(result["breakeven_revenue"]))
                        self.assertEqual(result["decision"], "REVIEW INPUTS")

    def test_invalid_scenario_values_block_instead_of_becoming_silent_defaults(self):
        invalid_values = {
            "spoilage_rate_pct": (-1, 80.1, float("nan"), float("inf"), float("-inf"), "abc", None, True),
            "holiday_sales_multiplier": (0, 0.09, 5.1, float("nan"), float("inf"), None, False),
            "holiday_cost_multiplier": (-1, 0.09, 5.1, float("nan"), float("inf"), None, False),
            "holiday_months": (-1, 13, 1.5, float("nan"), float("inf"), None, True),
            "perishable_enabled": ("false", "true", 0, 1, None),
        }
        for key, values in invalid_values.items():
            for value in values:
                with self.subTest(key=key, value=value):
                    result = self.calculate(**{key: value})
                    self.assertFalse(result["decision_ready"])
                    self.assertEqual(result["decision"], "REVIEW INPUTS")
                    self.assertTrue(result["input_errors"])
                    self.assertTrue(math.isfinite(result["modeled_annual_profit"]))

    def test_calculation_does_not_mutate_the_entered_raw_cost_or_margin(self):
        launch = {**self.launch, "perishable_enabled": True, "spoilage_rate_pct": 20}
        original_launch, original_pricing = copy.deepcopy(launch), copy.deepcopy(self.pricing)
        first = calculate_open_store_feasibility(PROFILE, SITE, launch, self.pricing)
        second = calculate_open_store_feasibility(PROFILE, SITE, launch, self.pricing)
        self.assertEqual(first, second)
        self.assertEqual(launch, original_launch)
        self.assertEqual(self.pricing, original_pricing)


if __name__ == "__main__":
    unittest.main()
