import unittest

import pandas as pd

from operations_finance_visuals import build_operations_focus, calculate_finance_snapshot


class OperationsFinanceVisualTests(unittest.TestCase):
    def test_perishable_item_becomes_the_single_next_move(self):
        df = pd.DataFrame([
            {"Item": "Tulips", "Stock": 72, "Cost": 2.0, "Total_Value": 144.0},
            {"Item": "Vases", "Stock": 20, "Cost": 8.0, "Total_Value": 160.0},
        ])
        health = {
            "df2": df,
            "perishable_items": df.iloc[[0]],
            "stockout_items": df.iloc[0:0],
            "overstock_items": df.iloc[[1]],
        }

        focus = build_operations_focus(health)

        self.assertEqual(focus["kind"], "perishable")
        self.assertEqual(focus["item"], "Tulips")
        self.assertGreater(focus["savings"], 0)
        self.assertIn("today", focus["title"].lower())

    def test_operations_savings_flow_into_finance_without_changing_revenue(self):
        baseline = calculate_finance_snapshot(
            68, 18, 4800,
            payroll=7000,
            other_fixed=2500,
            product_cost_rate=.28,
            waste_rate=.08,
            available_cash=25000,
        )
        linked = calculate_finance_snapshot(
            68, 18, 4800,
            payroll=7000,
            other_fixed=2500,
            product_cost_rate=.28,
            waste_rate=.08,
            available_cash=25000,
            operations_savings=96,
        )

        self.assertEqual(baseline["revenue"], linked["revenue"])
        self.assertAlmostEqual(baseline["waste"] - linked["waste"], 96)
        self.assertAlmostEqual(linked["monthly_result"] - baseline["monthly_result"], 96)

    def test_negative_month_is_reported_as_a_real_negative_result(self):
        snapshot = calculate_finance_snapshot(
            20, 5, 9000,
            payroll=8000,
            other_fixed=3000,
            product_cost_rate=.40,
            waste_rate=.10,
            available_cash=12000,
        )

        self.assertLess(snapshot["monthly_result"], 0)
        self.assertAlmostEqual(snapshot["reserve_months"], 0.6)


if __name__ == "__main__":
    unittest.main()
