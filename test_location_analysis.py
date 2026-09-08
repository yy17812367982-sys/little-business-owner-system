import copy
import os
import unittest
from unittest.mock import patch

import requests
from streamlit.testing.v1 import AppTest

from business_logic import calculate_open_store_feasibility
from location_analysis import (parse_places, collect_evidence, evidence_key,
                               report_location, road_traffic, community_data)
from test_business_logic import PROFILE, SITE, LAUNCH, PRICING


def element(oid=1, lat=30.25, lon=-97.75, tags=None):
    return {"type": "node", "id": oid, "lat": lat, "lon": lon,
            "tags": tags or {"shop": "florist", "name": "Example Flowers"}}


class LocationEvidenceTests(unittest.TestCase):
    def test_counts_exclude_wrong_categories_far_away_and_duplicates(self):
        nearby = element()
        result = parse_places({"elements": [nearby, nearby, element(2, lat=31),
            element(3, tags={"shop": "bakery"}), element(4, tags={"amenity": "parking", "access": "private"})]},
            30.25, -97.75, 1, "Flower Shop")
        self.assertEqual(len(result["places"]), 2)
        self.assertEqual(result["places"][1]["access"], "private")
        self.assertTrue(result["competitor_supported"])

    def test_partial_response_is_not_a_zero_count(self):
        with self.assertRaises(ValueError):
            parse_places({"elements": [], "remark": "timeout"}, 30.25, -97.75, 1, "Flower Shop")

    def test_unsupported_business_not_mislabeled_as_no_competition(self):
        result = parse_places({"elements": []}, 30.25, -97.75, 1, "Other")
        self.assertFalse(result["competitor_supported"])

    def test_sources_fail_independently(self):
        with patch("location_analysis.nearby_places", side_effect=requests.Timeout), \
             patch("location_analysis.community_data", return_value={"status": "key_required"}), \
             patch("location_analysis.road_traffic", return_value={"stations": []}):
            result = collect_evidence(30.25, -97.75, 1, "Flower Shop")
        self.assertEqual(result["map"]["status"], "unavailable")
        self.assertEqual(result["traffic"]["status"], "ok")
        self.assertEqual(result["community"]["status"], "key_required")

    def test_no_census_key_does_not_issue_unusable_request(self):
        with patch.dict(os.environ, {"CENSUS_API_KEY": ""}), patch("location_analysis.fetch_json") as request:
            community_data.clear()
            self.assertEqual(community_data(30.25, -97.75)["status"], "key_required")
            request.assert_not_called()

    def test_road_count_keeps_station_year_and_distance(self):
        data = {"features": [
            {"attributes": {"TRFC_STATN_ID": "TEST", "AADT_RPT_QTY": 20000, "LATEST_AADT_YR": 2025},
             "geometry": {"x": -97.75, "y": 30.25}},
            {"attributes": {"TRFC_STATN_ID": "FAR", "AADT_RPT_QTY": 90000, "LATEST_AADT_YR": 2025},
             "geometry": {"x": -90, "y": 35}}]}
        with patch("location_analysis.fetch_json", return_value=data):
            road_traffic.clear()
            result = road_traffic(30.25, -97.75, 1)
        self.assertEqual(len(result["stations"]), 1)
        self.assertEqual(result["stations"][0]["year"], 2025)
        self.assertEqual(result["stations"][0]["vehicles_per_day"], 20000)

    def test_missing_location_never_issues_go_or_fake_score(self):
        launch = {**LAUNCH, "funding_available": 500000}
        result = calculate_open_store_feasibility(PROFILE, {**SITE, "assessment_mode": "free"}, launch, PRICING)
        self.assertIsNone(result["overall_score"])
        self.assertIsNone(result["site_score"])
        self.assertTrue(result["location_pending"])
        self.assertEqual(result["decision"], "CAUTION")

    def test_new_address_radius_or_business_cannot_reuse_report_evidence(self):
        site = {"address": "Austin", "lat": 30.25, "lon": -97.75, "radius_miles": 1}
        site["location_evidence"] = {"key": evidence_key("Austin", 30.25, -97.75, 1, "Flower Shop"),
                                    "map": {"status": "ok", "places": []}}
        self.assertIn("public_evidence", report_location(site, "Flower Shop"))
        for field, value in [("address", "Dallas"), ("radius_miles", 3), ("lat", 31)]:
            changed = {**site, field: value}
            self.assertNotIn("public_evidence", report_location(changed, "Flower Shop"))
        self.assertNotIn("public_evidence", report_location(site, "Bakery"))


class FreeLocationUITests(unittest.TestCase):
    def test_lookup_is_explicit_and_address_edits_clear_results(self):
        result = {"map": {"status": "ok", "places": [
                      {"name": "Example Coffee", "category": "competitor", "lat": 30.251,
                       "lon": -97.751, "distance_miles": 0.1, "access": "unknown", "source": "https://example.test/1"},
                      {"name": "Example Parking", "category": "parking", "lat": 30.252,
                       "lon": -97.752, "distance_miles": 0.2, "access": "private", "source": "https://example.test/2"},
                  ], "competitor_supported": True},
                  "traffic": {"status": "ok", "stations": []}, "community": {"status": "key_required"}}
        matches = [{"name": "1011 S CONGRESS AVE, AUSTIN, TX", "lat": 30.25, "lon": -97.75}]
        with patch.dict(os.environ, {"INTRO_VIDEO_SECONDS": "0"}), \
             patch("location_analysis.locate_address", return_value=matches) as locate, \
             patch("location_analysis.collect_evidence", return_value=result) as collect:
            app = AppTest.from_file("pythonapp.py", default_timeout=30).run()
            app.button(key="open_store_next_btn").click().run()
            locate.assert_not_called()
            collect.assert_not_called()
            app.button(key="free_location_search").click().run()
            self.assertFalse(app.exception)
            self.assertIn("location_evidence", app.session_state["site"])
            collect.assert_called_once()
            legend = next(item.value for item in app.markdown if "Mapped coffee shops" in item.value)
            self.assertIn("Same business type recorded on OpenStreetMap", legend)
            self.assertEqual(app.selectbox(key="location_map_category").value, "competitor")
            app.text_input(key="free_location_address").set_value("A different address").run()
            self.assertFalse(app.exception)
            self.assertNotIn("location_evidence", app.session_state["site"])
            self.assertNotIn("located_address", app.session_state["site"])
            app.button(key="open_store_next_btn").click().run()
            app.button(key="open_store_next_btn").click().run()
            self.assertFalse(app.exception)
            self.assertTrue(any("no overall score" in w.value.lower() for w in app.warning))
