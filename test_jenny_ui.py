"""End-to-end Streamlit state regressions, with a mocked AI provider.

These tests exercise real application widgets, callbacks and finance parsing.
They never call a live AI provider and do not claim to evaluate model quality.
"""

import io
import os
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from streamlit.testing.v1 import AppTest

from business_logic import calculate_open_store_feasibility


APP_PATH = Path(__file__).with_name("pythonapp.py")
FLOWER_FIELDS = {
    "open_funding_widget": 150000.0,
    "open_startup_cost_widget": 110000.0,
    "open_fixed_cost_widget": 22000.0,
    "open_revenue_widget": 45000.0,
    "open_unit_cost_widget": 28.0,
    "open_planned_price_widget": 75.0,
    "open_competitor_price_widget": 65.0,
}
CUSTOMER_REASON = "Personal apology bouquets, same-day delivery, and anniversary reminders."
CUSTOMER_EVIDENCE = "Twelve neighbors asked for a trial bouquet; no paid orders yet."
MOCK_REPORT = "# Flower shop plan\n\nReview the ordinary month before signing a lease."
EVIDENCE_BOUNDARY = (
    "**Evidence boundary:** The decision, scores, and financial figures above are based on your entered data "
    "and the toolkit's calculations. Any other target or benchmark suggested by the AI is a planning idea—"
    "not verified market evidence—and must be set or checked by the owner before use."
)
EXPECTED_OPEN_STORE_REPORT = f"{MOCK_REPORT}\n\n---\n\n{EVIDENCE_BOUNDARY}"


class JennyFeedbackUITests(unittest.TestCase):
    def setUp(self):
        # Explicitly override secrets/env so a developer's real key cannot be used.
        self.addCleanup(patch.stopall)
        self.api_environment = patch.dict(os.environ, {"GEMINI_API_KEY": "mock-provider-only"})
        self.api_environment.start()
        self.provider = Mock(return_value=SimpleNamespace(text=MOCK_REPORT))
        patch(
            "google.genai.Client",
            return_value=SimpleNamespace(models=SimpleNamespace(generate_content=self.provider)),
        ).start()
        self.network_guard = patch(
            "requests.sessions.Session.request",
            side_effect=AssertionError("Automated UI tests must not call live services."),
        ).start()
        self.app = AppTest.from_file(str(APP_PATH), default_timeout=30)
        self.app.run()
        self.assert_no_exception()

    def assert_no_exception(self):
        self.assertFalse(self.app.exception, [error.value for error in self.app.exception])

    def button(self, label):
        matches = [button for button in self.app.button if button.label == label]
        self.assertEqual(len(matches), 1, f"Expected one button labelled {label!r}")
        return matches[0]

    def set_text(self, key, value):
        for collection in (self.app.text_input, self.app.text_area):
            for element in collection:
                if element.key == key:
                    element.set_value(value)
                    return
        self.fail(f"Missing editable text field {key!r}")

    def next(self):
        button = self.app.button(key="open_store_next_btn")
        self.assertFalse(button.disabled)
        button.click().run()
        self.assert_no_exception()

    def back(self):
        self.app.button(key="open_store_back_btn").click().run()
        self.assert_no_exception()

    def enter_flower_concept(self):
        self.app.selectbox(key="open_business_type").set_value("Flower Shop").run()
        self.set_text("open_target_customer", "Austin neighbors buying thoughtful gifts and wedding flowers.")
        self.set_text("open_differentiator", "Personal storytelling bouquets and unusual seasonal flowers.")
        self.set_text("open_customer_reason", CUSTOMER_REASON)
        self.set_text("open_customer_evidence", CUSTOMER_EVIDENCE)
        self.app.run()
        self.assert_no_exception()

    def flower_budget(self):
        self.enter_flower_concept()
        self.next()
        self.next()
        for key, value in FLOWER_FIELDS.items():
            self.app.number_input(key=key).set_value(value)
        self.app.slider(key="open_gross_margin_widget").set_value(62)
        self.app.run()
        self.app.checkbox(key="open_perishable_widget").check().run()
        self.app.slider(key="open_spoilage_widget").set_value(15.0)
        self.app.slider(key="open_peak_sales_widget").set_value(2.0)
        self.app.slider(key="open_peak_cost_widget").set_value(1.4)
        self.app.slider(key="open_peak_months_widget").set_value(2)
        self.app.run()
        self.assert_no_exception()

    def ready_report(self):
        self.flower_budget()
        self.next()
        self.app.checkbox(key="open_store_inputs_reviewed_checkbox").check().run()
        self.assertFalse(self.button("Generate Launch Decision Report").disabled)

    def test_flower_inputs_and_waste_calculation_survive_four_steps_and_back(self):
        self.flower_budget()
        state = self.app.session_state
        metrics = calculate_open_store_feasibility(
            state["profile"], state["site"], state["launch"], state["pricing"]
        )
        self.assertAlmostEqual(metrics["monthly_profit_after_fixed"], 2882.35294117647)
        self.assertAlmostEqual(metrics["effective_unit_cost"], 32.94117647058824)
        self.assertAlmostEqual(metrics["peak_profit_after_fixed"], 11670.58823529412)
        self.assertAlmostEqual(metrics["modeled_annual_profit"], 52164.70588235295)
        self.assertTrue(any("2,882" in metric.value for metric in self.app.metric))
        self.next()
        self.assertEqual(state["open_step"], 4)
        self.assertTrue(self.button("Generate Launch Decision Report").disabled)
        self.back()
        for key, expected in FLOWER_FIELDS.items():
            self.assertEqual(self.app.number_input(key=key).value, expected, key)
        self.assertEqual(self.app.slider(key="open_spoilage_widget").value, 15.0)
        self.assertEqual(self.app.slider(key="open_peak_cost_widget").value, 1.4)
        self.back()
        self.back()
        self.assertEqual(self.app.selectbox(key="open_business_type").value, "Flower Shop")
        self.assertEqual(state["profile"]["customer_reason"], CUSTOMER_REASON)
        self.assertEqual(state["profile"]["customer_evidence"], CUSTOMER_EVIDENCE)
        self.assertFalse(any("current fields are an Austin coffee-shop" in caption.value for caption in self.app.caption))
        self.provider.assert_not_called()
        self.network_guard.assert_not_called()

    def test_after_waste_below_cost_price_blocks_next_then_recovers(self):
        self.flower_budget()
        self.app.number_input(key="open_planned_price_widget").set_value(30.0).run()
        self.assertTrue(self.app.button(key="open_store_next_btn").disabled)
        self.assertTrue(any("effective unit cost after spoilage" in error.value for error in self.app.error))
        self.app.number_input(key="open_planned_price_widget").set_value(75.0).run()
        self.assertFalse(self.app.button(key="open_store_next_btn").disabled)
        self.next()
        self.assertEqual(self.app.session_state["open_step"], 4)

    def test_report_success_includes_flower_context_and_changes_invalidate_it(self):
        self.ready_report()
        self.button("Generate Launch Decision Report").click().run()
        self.assert_no_exception()
        self.assertEqual(self.app.session_state["outputs"]["open_store_report_md"], EXPECTED_OPEN_STORE_REPORT)
        self.assertTrue(any(EVIDENCE_BOUNDARY in markdown.value for markdown in self.app.markdown))
        self.assertEqual(self.provider.call_count, 1)
        sent_prompt = self.provider.call_args.kwargs["contents"]
        self.assertIn(CUSTOMER_REASON, sent_prompt)
        self.assertIn(CUSTOMER_EVIDENCE, sent_prompt)
        self.assertIn("Flower Shop", sent_prompt)
        self.assertIn("scenario_assumptions", sent_prompt)
        self.assertIn("monthly_spoilage_extra_cost", sent_prompt)
        self.assertIn("never upgrade the verdict", sent_prompt)
        self.assertIn("Never describe it as a local average", sent_prompt)
        self.assertIn('write "owner to set" instead of choosing a number', sent_prompt)
        self.assertIn("Do not infer neighborhood affluence", sent_prompt)
        self.back()
        self.app.number_input(key="open_planned_price_widget").set_value(80.0).run()
        self.assertEqual(self.app.session_state["outputs"]["open_store_report_md"], "")
        self.next()
        self.assertFalse(any(EVIDENCE_BOUNDARY in markdown.value for markdown in self.app.markdown))
        self.assertEqual(self.provider.call_count, 1)

    def test_report_timeout_shows_retry_preserves_values_then_succeeds(self):
        self.ready_report()
        self.provider.side_effect = TimeoutError("simulated timeout")
        self.button("Generate Launch Decision Report").click().run()
        self.assert_no_exception()
        self.assertEqual(self.provider.call_count, 3)
        self.assertEqual(self.app.session_state["outputs"]["open_store_report_md"], "")
        self.assertTrue(self.app.error)
        self.assertFalse(self.button("Retry Launch Decision Report").disabled)
        self.assertEqual(self.app.session_state["pricing"]["planned_price"], 75.0)
        self.provider.side_effect = None
        self.button("Retry Launch Decision Report").click().run()
        self.assert_no_exception()
        self.assertEqual(self.app.session_state["outputs"]["open_store_report_md"], EXPECTED_OPEN_STORE_REPORT)
        self.assertEqual(self.app.session_state["open_store_report_error"], "")

    def test_top_ai_success_and_missing_configuration_are_distinct(self):
        question = "I lose 15 out of every 100 flowers. How should I price my bouquets?"
        self.app.text_input(key="top_ask_ai").set_value(question)
        self.button("Send").click().run()
        self.assert_no_exception()
        self.assertEqual(self.app.session_state["top_last_status"], "ready")
        self.assertEqual(self.app.session_state["chat_history"][-1]["role"], "ai")
        self.assertIn(question, self.provider.call_args.kwargs["contents"])
        self.assertTrue(any("Answer ready" in success.value for success in self.app.success))

        self.api_environment.stop()
        patch.dict(os.environ, {"GEMINI_API_KEY": ""}).start()
        self.app.run()
        failed_question = "What about fragile tulips?"
        self.app.text_input(key="top_ask_ai").set_value(failed_question)
        self.button("Send").click().run()
        self.assert_no_exception()
        self.assertEqual(self.app.session_state["top_last_status"], "error")
        self.assertEqual(self.app.session_state["chat_history"][-1]["role"], "user")
        self.assertEqual(self.app.text_input(key="top_ask_ai").value, failed_question)
        self.assertTrue(any("not configured" in error.value for error in self.app.error))
        self.assertFalse(any("Answer ready" in success.value for success in self.app.success))
        self.assertEqual(self.provider.call_count, 1)

    def test_operations_consent_gates_data_and_ai_report(self):
        self.app.radio[0].set_value("Operations").run()
        self.app.button(key="ops_load_cafe_sample").click().run()
        self.assertTrue(self.button("Run Operations Diagnosis").disabled)
        self.assertTrue(self.button("Generate Operations Report").disabled)
        self.provider.assert_not_called()
        self.app.checkbox(key="operations_ai_consent").check().run()
        self.assertFalse(self.button("Run Operations Diagnosis").disabled)
        self.assertFalse(self.button("Generate Operations Report").disabled)
        self.button("Run Operations Diagnosis").click().run()
        self.assert_no_exception()
        self.assertEqual(self.provider.call_count, 1)
        self.assertIn("Milk Gallons", self.provider.call_args.kwargs["contents"])
        self.app.checkbox(key="operations_ai_consent").uncheck().run()
        self.assertTrue(self.button("Generate Operations Report").disabled)

    def test_finance_csv_requires_consent_and_supplies_real_computed_data_to_ai(self):
        self.app.radio[0].set_value("Finance").run()
        self.assertTrue(self.button("Analyze").disabled)
        uploaded = io.BytesIO(b"Month,Revenue,COGS,Rent\nJanuary,12345,4000,2000\n")
        uploaded.name = "mock-flower-shop-finances.csv"
        uploaded.size = len(uploaded.getvalue())
        # AppTest 1.40 has no upload setter; substitute only the upload widget.
        # The production CSV parsing, consent, prompt and AI output paths run.
        with patch("streamlit.file_uploader", return_value=[uploaded]):
            self.app.run()
            self.assertTrue(self.button("Analyze").disabled)
            self.provider.assert_not_called()
            consent = next(c for c in self.app.checkbox if "consent to sending parsed content" in c.label)
            consent.check().run()
            self.assertFalse(self.button("Analyze").disabled)
            self.assertFalse(self.button("Generate Finance Report").disabled)
            self.button("Analyze").click().run()
            self.assert_no_exception()
            self.assertEqual(self.provider.call_count, 1)
            self.assertIn("12,345", self.provider.call_args.kwargs["contents"])
            self.assertIn("8,345", self.provider.call_args.kwargs["contents"])
            self.assertEqual(self.app.session_state["outputs"]["finance_ai_output"], MOCK_REPORT)


if __name__ == "__main__":
    unittest.main()
