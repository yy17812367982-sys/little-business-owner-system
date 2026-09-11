import os
import unittest
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

from visual_planner import money_scenario, storefront_markup
from test_business_logic import LAUNCH, PRICING, PROFILE, SITE


class VisualPlannerTests(unittest.TestCase):
    def test_storefront_renderer_uses_one_template_with_type_name_and_palette_parameters(self):
        flower = storefront_markup({"business_type": "Flower Shop", "shop_name": "Jenny <Room>",
                                    "mood_palette": "garden"})
        bakery = storefront_markup({"business_type": "Bakery", "shop_name": "Sunrise Bakery",
                                    "mood_palette": "sunshine"})
        self.assertIn('class="yy-storefront-building"', flower)
        self.assertIn('data-shop-type="Flower Shop"', flower)
        self.assertIn("Jenny &lt;Room&gt;", flower)
        self.assertIn("🌷", flower)
        self.assertIn('data-shop-type="Bakery"', bakery)
        self.assertIn("🥐", bakery)
        self.assertNotEqual(flower, bakery)

    def test_what_if_uses_existing_calculation_without_mutating_base_plan(self):
        launch = dict(LAUNCH)
        original = dict(launch)
        scenario = money_scenario(PROFILE, SITE, launch, PRICING, "sales_down")
        self.assertEqual(launch, original)
        self.assertEqual(scenario["expected_revenue"], LAUNCH["expected_monthly_revenue"] * .8)

    def test_shop_card_keeps_custom_text_and_survives_step_navigation(self):
        with patch.dict(os.environ, {"INTRO_VIDEO_SECONDS": "0"}):
            app = AppTest.from_file("pythonapp.py", default_timeout=30).run()
            app.text_input(key="open_target_customer").set_value("Local gift buyers").run()
            app.button(key="shop_card_Flower Shop").click().run()
            self.assertFalse(app.exception)
            self.assertEqual(app.selectbox(key="open_business_type").value, "Flower Shop")
            self.assertEqual(app.text_input(key="open_target_customer").value, "Local gift buyers")
            app.button(key="open_store_next_btn").click().run()
            app.button(key="open_store_back_btn").click().run()
            self.assertEqual(app.selectbox(key="open_business_type").value, "Flower Shop")
            self.assertEqual(app.text_input(key="open_target_customer").value, "Local gift buyers")

    def test_business_type_updates_default_name_and_palette_but_preserves_owner_name(self):
        with patch.dict(os.environ, {"INTRO_VIDEO_SECONDS": "0"}):
            app = AppTest.from_file("pythonapp.py", default_timeout=30).run()
            app.button(key="shop_card_Flower Shop").click().run()
            self.assertEqual(app.text_input(key="open_shop_name").value, "Jenny’s Flower Room")
            self.assertEqual(app.selectbox(key="open_storefront_palette").value, "garden")
            app.text_input(key="open_shop_name").set_value("Petal & Pine").run()
            app.button(key="shop_card_Bakery").click().run()
            self.assertEqual(app.selectbox(key="open_business_type").value, "Bakery")
            self.assertEqual(app.text_input(key="open_shop_name").value, "Petal & Pine")

    def test_preview_escapes_user_html(self):
        with patch.dict(os.environ, {"INTRO_VIDEO_SECONDS": "0"}):
            app = AppTest.from_file("pythonapp.py", default_timeout=30).run()
            app.text_input(key="open_differentiator").set_value("<script>alert(1)</script>").run()
            preview = next(item.value for item in app.markdown if "YOUR IDEA IS TAKING SHAPE" in item.value)
            self.assertIn("&lt;script&gt;", preview)
            self.assertNotIn("<script>", preview)

    def test_jenny_preset_name_palette_and_navigation_state_stay_live(self):
        with patch.dict(os.environ, {"INTRO_VIDEO_SECONDS": "0"}):
            app = AppTest.from_file("pythonapp.py", default_timeout=30).run()
            app.button(key="store_preset_jenny").click().run()
            self.assertEqual(app.selectbox(key="open_business_type").value, "Flower Shop")
            self.assertEqual(app.text_input(key="open_shop_name").value, "Jenny’s Flower Room")
            preview = next(item.value for item in app.markdown if "YOUR IDEA IS TAKING SHAPE" in item.value)
            self.assertIn('data-palette="garden"', preview)
            app.text_input(key="open_shop_name").set_value("Jenny’s New Room").run()
            preview = next(item.value for item in app.markdown if "YOUR IDEA IS TAKING SHAPE" in item.value)
            self.assertIn("Jenny’s New Room", preview)
            app.button(key="open_store_next_btn").click().run()
            app.button(key="open_store_back_btn").click().run()
            self.assertEqual(app.text_input(key="open_shop_name").value, "Jenny’s New Room")

    def test_budget_what_if_updates_simulation_without_polluting_base_plan(self):
        with patch.dict(os.environ, {"INTRO_VIDEO_SECONDS": "0"}):
            app = AppTest.from_file("pythonapp.py", default_timeout=30).run()
            app.button(key="open_store_next_btn").click().run()
            app.button(key="open_store_next_btn").click().run()
            base_sales = app.number_input(key="open_revenue_widget").value
            app.radio(key="open_money_what_if").set_value("sales_up").run()
            self.assertEqual(app.number_input(key="open_revenue_widget").value, base_sales)
            self.assertEqual(app.session_state["launch"]["expected_monthly_revenue"], base_sales)
            self.assertTrue(any("base inputs unchanged" in item.value for item in app.caption))

    def test_decision_begins_with_conclusion_reasons_and_next_action(self):
        with patch.dict(os.environ, {"INTRO_VIDEO_SECONDS": "0"}):
            app = AppTest.from_file("pythonapp.py", default_timeout=30).run()
            for _ in range(3):
                app.button(key="open_store_next_btn").click().run()
            lead_index = next(i for i, item in enumerate(app.markdown) if "SHOULD I OPEN?" in item.value)
            detail_index = next(i for i, item in enumerate(app.markdown) if "Scores &amp; detailed evidence" in item.value or "Scores & detailed evidence" in item.value)
            self.assertLess(lead_index, detail_index)
            lead = app.markdown[lead_index].value
            self.assertIn("Why?", lead)
            self.assertIn("What should I do next?", lead)
            self.assertNotIn("success probability", lead.lower())
