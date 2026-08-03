import copy
import unittest

from business_logic import calculate_open_store_feasibility, validate_pricing


PROFILE = {"budget": 80000}
SITE = {
    "traffic": 28000,
    "competitors": 12,
    "rent_level": "High",
    "parking": "Medium",
}
LAUNCH = {
    "funding_available": 80000,
    "startup_cost_estimate": 62000,
    "monthly_fixed_cost_estimate": 26500,
    "expected_monthly_revenue": 52000,
    "expected_gross_margin": 62,
    "cash_target_months": 3,
}
PRICING = {
    "cost": 1.75,
    "planned_price": 5.25,
    "competitor_price": 5.50,
}


class PricingValidationTests(unittest.TestCase):
    def test_valid_default_pricing(self):
        result = validate_pricing(PRICING)
        self.assertTrue(result["valid"])
        self.assertAlmostEqual(result["implied_margin"], 2 / 3, places=4)

    def test_price_below_cost_is_blocking(self):
        result = validate_pricing({"cost": 100, "planned_price": 5.25, "competitor_price": 135})
        self.assertFalse(result["valid"])
        self.assertTrue(any("must be higher" in error for error in result["errors"]))


class FeasibilityTests(unittest.TestCase):
    def test_default_scenario_is_internally_consistent(self):
        result = calculate_open_store_feasibility(PROFILE, SITE, LAUNCH, PRICING)
        self.assertTrue(result["decision_ready"])
        self.assertNotEqual(result["decision"], "REVIEW INPUTS")
        self.assertGreater(result["margin_score"], 0)
        self.assertAlmostEqual(sum(result["score_weights"].values()), 1.0)

    def test_invalid_pricing_blocks_decision_and_report(self):
        bad_pricing = copy.deepcopy(PRICING)
        bad_pricing.update({"cost": 100, "planned_price": 5.25, "competitor_price": 135})
        result = calculate_open_store_feasibility(PROFILE, SITE, LAUNCH, bad_pricing)
        self.assertFalse(result["decision_ready"])
        self.assertEqual(result["decision"], "REVIEW INPUTS")
        self.assertEqual(result["margin_score"], 0)
        self.assertLess(result["implied_margin_pct"], 0)

    def test_margin_mismatch_is_visible_and_caps_score(self):
        launch = copy.deepcopy(LAUNCH)
        launch["expected_gross_margin"] = 80
        pricing = copy.deepcopy(PRICING)
        pricing["cost"] = 4.50
        result = calculate_open_store_feasibility(PROFILE, SITE, launch, pricing)
        self.assertTrue(result["input_warnings"])
        self.assertLessEqual(result["margin_score"], 55)


if __name__ == "__main__":
    unittest.main()
