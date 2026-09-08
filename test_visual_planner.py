import os
import unittest
from unittest.mock import patch

from streamlit.testing.v1 import AppTest


class VisualPlannerTests(unittest.TestCase):
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

    def test_preview_escapes_user_html(self):
        with patch.dict(os.environ, {"INTRO_VIDEO_SECONDS": "0"}):
            app = AppTest.from_file("pythonapp.py", default_timeout=30).run()
            app.text_input(key="open_differentiator").set_value("<script>alert(1)</script>").run()
            preview = next(item.value for item in app.markdown if "YOUR IDEA IS TAKING SHAPE" in item.value)
            self.assertIn("&lt;script&gt;", preview)
            self.assertNotIn("<script>", preview)
