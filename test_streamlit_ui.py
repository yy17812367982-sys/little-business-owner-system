import unittest

from streamlit.testing.v1 import AppTest


class DanielFollowUpUITests(unittest.TestCase):
    def setUp(self):
        self.app = AppTest.from_file("pythonapp.py", default_timeout=30).run()
        self.assertFalse(self.app.exception)

    def _go_to_budget_page(self):
        self.app.button(key="open_store_next_btn").click().run()
        self.app.button(key="open_store_next_btn").click().run()
        self.assertFalse(self.app.exception)

    def test_next_is_disabled_when_pricing_has_a_blocking_error(self):
        self._go_to_budget_page()
        self.app.number_input(key="open_unit_cost_widget").set_value(100.0).run()

        self.assertTrue(self.app.button(key="open_store_next_btn").disabled)
        self.assertTrue(any("must be higher" in error.value for error in self.app.error))
        self.assertTrue(
            any("Fix the input errors" in caption.value for caption in self.app.caption)
        )

    def test_scoring_explanation_reports_no_errors_for_valid_inputs(self):
        self._go_to_budget_page()
        self.app.button(key="open_store_next_btn").click().run()

        self.assertTrue(
            any(
                "There are currently no blocking input errors" in caption.value
                for caption in self.app.caption
            )
        )

    def test_operations_ai_actions_require_explicit_consent(self):
        self.app.radio[0].set_value("Operations").run()
        self.app.button(key="ops_load_cafe_sample").click().run()

        ai_labels = {"Run Operations Diagnosis", "Generate Operations Report"}
        ai_buttons = [button for button in self.app.button if button.label in ai_labels]
        self.assertEqual(len(ai_buttons), 2)
        self.assertTrue(all(button.disabled for button in ai_buttons))

        self.app.checkbox(key="operations_ai_consent").check().run()
        ai_buttons = [button for button in self.app.button if button.label in ai_labels]
        self.assertTrue(all(not button.disabled for button in ai_buttons))


if __name__ == "__main__":
    unittest.main()
