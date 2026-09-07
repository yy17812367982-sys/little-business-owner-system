"""Regression tests for Jenny's creative concept and neighborhood features."""

import io
import json
import unittest
from unittest.mock import Mock, patch
from urllib.parse import parse_qs, urlparse

import requests
from PIL import Image
from streamlit.testing.v1 import AppTest

import owner_experience as owner


class MoodBoardTests(unittest.TestCase):
    def test_valid_image_is_small_metadata_free_preview(self):
        image = Image.new("RGB", (1600, 1000), "pink")
        output = io.BytesIO()
        image.save(output, format="PNG")
        preview = owner.validate_mood_image(output.getvalue())
        self.assertEqual(preview.size, (1000, 625))
        self.assertFalse(preview.info)

    def test_fake_image_and_oversized_upload_are_rejected(self):
        for value in (b"not a real image", b"", b"x" * (owner.MAX_IMAGE_BYTES + 1)):
            with self.subTest(size=len(value)):
                with self.assertRaises(ValueError):
                    owner.validate_mood_image(value)

    def test_gif_is_not_accepted_even_if_filename_claims_png(self):
        output = io.BytesIO()
        Image.new("RGB", (10, 10)).save(output, format="GIF")
        with self.assertRaisesRegex(ValueError, "image_format"):
            owner.validate_mood_image(output.getvalue())

    def test_excessive_dimensions_are_rejected_before_full_decode(self):
        output = io.BytesIO()
        Image.new("1", (4001, 3000)).save(output, format="PNG")
        with self.assertRaisesRegex(ValueError, "image_dimensions"):
            owner.validate_mood_image(output.getvalue())

    def test_dynamic_palette_title_is_escaped(self):
        markup = owner.palette_html("garden", '<script>alert("hello")</script>')
        self.assertNotIn("<script>", markup)
        self.assertIn("&lt;script&gt;", markup)
        self.assertIn("#F7F1E8", markup)

    def test_changed_concept_invalidates_previous_ai_direction(self):
        profile = {"business_type": "Flower Shop", "mood_board_brief": "Warm wood"}
        fingerprint, _ = owner.sync_mood_direction(profile, "en")
        profile.update(mood_board_direction="Previous idea", mood_board_fingerprint=fingerprint)
        self.assertFalse(owner.sync_mood_direction(profile, "en")[1])
        profile["target_customer"] = "Wedding couples"
        self.assertTrue(owner.sync_mood_direction(profile, "en")[1])
        self.assertNotIn("mood_board_direction", profile)

    def test_prompt_contains_selected_context_but_no_image_or_private_data(self):
        profile = {"business_type": "Flower Shop", "mood_palette": "garden", "mood_board_brief": "Pink tulips", "raw_image": b"secret_bytes", "bank_account": "123private"}
        prompt = owner.mood_prompt(profile, "zh")
        self.assertIn("Pink tulips", prompt)
        self.assertIn("Chinese", prompt)
        self.assertNotIn("secret_bytes", prompt)
        self.assertNotIn("123private", prompt)
        self.assertIn("not an image", prompt)


class PartnerEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.site = {"address": "101 Main St", "located_address": "101 Main St", "lat": 30.0, "lon": -97.0, "radius_miles": 1.0}
        self.payload = {"elements": [
            {"type": "node", "id": 123, "lat": 30.001, "lon": -97.001, "tags": {"name": "Rose Café", "amenity": "cafe"}},
            {"type": "way", "id": 456, "center": {"lat": 30.002, "lon": -97.002}, "tags": {"name": "River Hotel", "tourism": "hotel"}},
            {"type": "node", "id": 789, "lat": 40, "lon": -90, "tags": {"name": "Faraway venue", "amenity": "events_venue"}},
        ], "osm3s": {"timestamp_osm_base": "2026-09-07T00:00:00Z"}}

    def test_changed_or_unlocated_address_cannot_use_old_coordinates(self):
        self.assertEqual(owner.verified_site_coordinates(self.site), (30.0, -97.0))
        self.site["address"] = "999 Different Street"
        self.assertIsNone(owner.verified_site_coordinates(self.site))
        self.site.pop("located_address")
        self.assertIsNone(owner.verified_site_coordinates(self.site))

    def test_invalid_coordinates_are_rejected(self):
        for latitude in (float("nan"), float("inf"), 100):
            self.site["lat"] = latitude
            self.assertIsNone(owner.verified_site_coordinates(self.site))

    def test_maps_search_url_encodes_address_and_category_safely(self):
        address = "12 Main St & 3rd, Austin #5"
        link = owner.maps_search_link(address, "events")
        self.assertEqual(urlparse(link).netloc, "www.google.com")
        query = parse_qs(urlparse(link).query)["query"][0]
        self.assertIn(address, query)
        self.assertIn("wedding planners", query)

    def test_only_actual_named_in_radius_places_appear(self):
        self.payload["elements"].extend([
            self.payload["elements"][0],
            {"type": "node", "id": 800, "lat": 30.001, "lon": -97, "tags": {"amenity": "cafe"}},
            {"type": "node", "id": 801, "lat": 30.001, "lon": -97, "tags": {"name": "Unrelated shop", "shop": "clothes"}},
        ])
        records = owner.parse_partner_elements(self.payload, 30, -97, 1.0, list(owner.PARTNER_CATEGORIES))
        self.assertEqual([place["name"] for place in records], ["Rose Café", "River Hotel"])
        self.assertEqual(records[1]["source"], "https://www.openstreetmap.org/way/456")
        self.assertGreater(records[1]["distance_miles"], 0)

    def test_category_filter_is_respected(self):
        records = owner.parse_partner_elements(self.payload, 30, -97, 1.0, ["hotels"])
        self.assertEqual([place["name"] for place in records], ["River Hotel"])

    def test_overpass_partial_error_is_not_presented_as_complete_data(self):
        self.payload["remark"] = "runtime error: Query timed out"
        with self.assertRaisesRegex(ValueError, "incomplete_map_response"):
            owner.parse_partner_elements(self.payload, 30, -97, 1.0, ["hotels"])

    def test_changed_radius_invalidates_map_evidence(self):
        profile = {}
        fingerprint, _ = owner.sync_partner_evidence(profile, self.site, ["hotels"])
        profile["partner_ecosystem"] = {"fingerprint": fingerprint, "places": [{"name": "Old result"}]}
        self.site["radius_miles"] = 3.0
        self.assertTrue(owner.sync_partner_evidence(profile, self.site, ["hotels"])[1])
        self.assertNotIn("partner_ecosystem", profile)

    def _response(self, body):
        response = Mock()
        response.__enter__ = Mock(return_value=response)
        response.__exit__ = Mock(return_value=False)
        response.iter_content.return_value = [body]
        return response

    def test_network_lookup_has_timeout_cap_source_and_timestamp(self):
        response = self._response(json.dumps(self.payload).encode())
        with patch.object(owner.requests, "post", return_value=response) as post:
            result = owner.query_nearby_partners(30, -97, 1.0, ("hotels", "cafes"))
        self.assertEqual(len(result["places"]), 2)
        self.assertIn("UTC", result["retrieved_at"])
        self.assertEqual(result["map_data_timestamp"], "2026-09-07T00:00:00Z")
        self.assertEqual(post.call_args.kwargs["timeout"], (4, 12))
        self.assertIn("out center 120", post.call_args.kwargs["data"]["data"])

    def test_network_failure_is_visible_to_caller(self):
        with patch.object(owner.requests, "post", side_effect=requests.Timeout):
            with self.assertRaises(requests.Timeout):
                owner.query_nearby_partners(30, -97, 1.0, ("hotels",))

    def test_oversized_map_response_is_rejected(self):
        response = self._response(b"x" * (owner.MAX_RESPONSE_BYTES + 1))
        with patch.object(owner.requests, "post", return_value=response):
            with self.assertRaisesRegex(ValueError, "map_response_limit"):
                owner.query_nearby_partners(30, -97, 1.0, ("hotels",))

    def test_invalid_queries_never_reach_network(self):
        for coords in ((float("nan"), -97, 1, ("hotels",)), (30, -97, 100, ("hotels",)), (30, -97, 1, ('hotels];out;',))):
            with patch.object(owner.requests, "post") as post:
                with self.assertRaises(ValueError):
                    owner.query_nearby_partners(*coords)
                post.assert_not_called()


MOOD_APP = '''
import streamlit as st
from owner_experience import render_mood_board
if "profile" not in st.session_state:
    st.session_state.profile = {"business_type": "Flower Shop"}
def test_ai(prompt, **kwargs):
    st.session_state.ai_prompt = prompt
    st.session_state.ai_kwargs = kwargs
    if st.session_state.get("fail_ai"):
        raise RuntimeError("test failure")
    return "Try warm wooden shelves and soft garden colors."
render_mood_board(st.session_state.profile, st.session_state.get("lang", "en"), test_ai)
'''


PARTNER_APP = '''
import streamlit as st
from owner_experience import render_partner_ecosystem
if "profile" not in st.session_state:
    st.session_state.profile = {"business_type": "Flower Shop"}
if "site" not in st.session_state:
    st.session_state.site = {"address": "101 Main St", "lat": 30.0, "lon": -97.0, "radius_miles": 1.0}
render_partner_ecosystem(st.session_state.profile, st.session_state.site, "en", None)
'''


class OwnerExperienceUITests(unittest.TestCase):
    def test_mood_ai_success_and_changed_input_stale_result(self):
        app = AppTest.from_string(MOOD_APP).run()
        self.assertFalse(app.exception)
        app.text_area(key="owner_mood_brief").set_value("A peaceful garden").run()
        app.button(key="owner_mood_generate").click().run()
        self.assertFalse(app.exception)
        self.assertIn("warm wooden", app.session_state["profile"]["mood_board_direction"])
        self.assertTrue(app.session_state["ai_kwargs"]["raise_on_failure"])
        app.text_area(key="owner_mood_brief").set_value("Bright pop art").run()
        self.assertNotIn("mood_board_direction", app.session_state["profile"])

    def test_mood_ai_failure_keeps_brief_and_allows_retry(self):
        app = AppTest.from_string(MOOD_APP).run()
        app.text_area(key="owner_mood_brief").set_value("Warm and cozy").run()
        app.session_state["fail_ai"] = True
        app.button(key="owner_mood_generate").click().run()
        self.assertFalse(app.exception)
        self.assertEqual(app.session_state["profile"]["mood_board_brief"], "Warm and cozy")
        self.assertTrue(any("could not respond" in item.value for item in app.warning))
        self.assertFalse(app.button(key="owner_mood_generate").disabled)

    def test_chinese_mood_ui(self):
        app = AppTest.from_string(MOOD_APP)
        app.session_state["lang"] = "zh"
        app.run()
        self.assertFalse(app.exception)
        self.assertEqual(app.button(key="owner_mood_generate").label, "帮我描绘小店的感觉")

    def test_partner_search_does_not_call_network_until_clicked(self):
        with patch.object(owner, "cached_nearby_partners") as query:
            app = AppTest.from_string(PARTNER_APP).run()
            self.assertFalse(app.exception)
            self.assertTrue(app.button(key="owner_partner_find").disabled)
            app.session_state["site"]["located_address"] = "101 Main St"
            app.run()
            self.assertFalse(app.button(key="owner_partner_find").disabled)
            query.assert_not_called()

    def test_partner_failure_has_fallback_and_retry(self):
        with patch.object(owner, "cached_nearby_partners", side_effect=requests.Timeout):
            app = AppTest.from_string(PARTNER_APP).run()
            app.session_state["site"]["located_address"] = "101 Main St"
            app.run()
            app.button(key="owner_partner_find").click().run()
        self.assertFalse(app.exception)
        self.assertTrue(any("unavailable" in item.value for item in app.warning))
        self.assertFalse(app.button(key="owner_partner_find").disabled)
        self.assertEqual(len(app.get("link_button")), 4)

    def test_partner_success_maps_real_evidence_and_retains_source(self):
        result = {"places": [{"name": "Test Café", "category": "cafes", "lat": 30.001, "lon": -97.001, "distance_miles": 0.1, "source": "https://www.openstreetmap.org/node/123"}], "retrieved_at": "2026-09-07 10:00 UTC", "source": "OpenStreetMap", "limited": False}
        with patch.object(owner, "cached_nearby_partners", return_value=result):
            app = AppTest.from_string(PARTNER_APP).run()
            app.session_state["site"]["located_address"] = "101 Main St"
            app.run()
            app.button(key="owner_partner_find").click().run()
        self.assertFalse(app.exception)
        self.assertEqual(len(app.dataframe), 1)
        self.assertEqual(app.session_state["profile"]["partner_ecosystem"]["places"][0]["name"], "Test Café")


if __name__ == "__main__":
    unittest.main()
