"""Free, on-demand location evidence. No paid keys or AI requests."""
import hashlib
import json
import math
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

import pandas as pd
import requests
import streamlit as st

from owner_experience import distance_miles

TXDOT = "https://services.arcgis.com/KTcxiTD9dsQw4r7Z/ArcGIS/rest/services/TxDOT_5_Year_Statewide_AADT_Traffic_Counts/FeatureServer/0"
CENSUS_GEO = "https://geocoding.geo.census.gov/geocoder"
OVERPASS = "https://overpass-api.de/api/interpreter"
UA = {"User-Agent": "YangYu-SmallBusinessToolkit/1.2 (https://github.com/yy17812367982-sys/little-business-owner-system)"}
FILTERS = {
    "Flower Shop": '["shop"="florist"]',
    "Coffee Shop": '["amenity"="cafe"]',
    "Bakery": '["shop"="bakery"]',
    "Restaurant": '["amenity"="restaurant"]',
    "Convenience Store": '["shop"="convenience"]',
    "Small Retail Store": '["shop"="general"]',
    "Beauty Salon": '["shop"~"^(beauty|hairdresser)$"]',
    "Auto Parts Store": '["shop"="car_parts"]',
}
LABELS = {"competitor": ("Similar shops", "同类店铺"), "parking": ("Parking facilities", "停车设施"),
          "transit": ("Transit stops", "公交与轨道站点"), "partner": ("Potential partners", "潜在合作地点")}
_lock = threading.Lock()
_last_call = {}


def fetch_json(url, params=None, data=None):
    # Fixed endpoints only. Bound the response size and elapsed streaming time.
    deadline = time.monotonic() + 24
    method = requests.post if data is not None else requests.get
    kwargs = {"data": data} if data is not None else {"params": params}
    with method(url, **kwargs, headers=UA, timeout=(4, 16), stream=True) as response:
        response.raise_for_status()
        chunks, size = [], 0
        for chunk in response.iter_content(32768):
            size += len(chunk)
            if size > 2_000_000 or time.monotonic() > deadline:
                raise ValueError("response_limit")
            chunks.append(chunk)
        return json.loads(b"".join(chunks))


def throttle(service, seconds=1.1):
    with _lock:
        delay = seconds - (time.monotonic() - _last_call.get(service, 0))
        if delay > 0:
            time.sleep(delay)
        _last_call[service] = time.monotonic()


def validate_context(lat, lon, radius):
    if not all(math.isfinite(float(v)) for v in (lat, lon, radius)):
        raise ValueError("invalid_coordinates")
    if not (-90 <= lat <= 90 and -180 <= lon <= 180 and 0 < radius <= 3):
        raise ValueError("invalid_coordinates")


@st.cache_data(ttl=86400, max_entries=256, show_spinner=False)
def locate_address(address):
    if not isinstance(address, str) or not 3 <= len(address.strip()) <= 400:
        raise ValueError("invalid_address")
    # US address lookup is free. Nominatim provides a bounded fallback for place names.
    try:
        payload = fetch_json(CENSUS_GEO + "/locations/onelineaddress", {
            "address": address, "benchmark": "Public_AR_Current", "format": "json"})
        matches = payload.get("result", {}).get("addressMatches", [])
        if matches:
            return [{"name": x["matchedAddress"], "lat": float(x["coordinates"]["y"]),
                     "lon": float(x["coordinates"]["x"])} for x in matches[:5]]
    except (requests.RequestException, ValueError, KeyError, TypeError):
        pass
    throttle("nominatim")
    payload = fetch_json("https://nominatim.openstreetmap.org/search",
                         {"q": address, "format": "json", "limit": 5, "countrycodes": "us"})
    return [{"name": x["display_name"], "lat": float(x["lat"]), "lon": float(x["lon"])}
            for x in payload[:5]]


def category(tags, kind):
    shop, amenity = tags.get("shop"), tags.get("amenity")
    competitor = {
        "Flower Shop": shop == "florist", "Coffee Shop": amenity == "cafe",
        "Bakery": shop == "bakery", "Restaurant": amenity == "restaurant",
        "Convenience Store": shop == "convenience", "Small Retail Store": shop == "general",
        "Beauty Salon": shop in ("beauty", "hairdresser"), "Auto Parts Store": shop == "car_parts",
    }.get(kind, False)
    if competitor:
        return "competitor"
    if amenity == "parking":
        return "parking"
    if tags.get("highway") == "bus_stop" or tags.get("railway") in ("station", "tram_stop"):
        return "transit"
    if tags.get("tourism") in ("hotel", "guest_house") or amenity in ("events_venue", "conference_centre"):
        return "partner"
    return None


def parse_places(payload, lat, lon, radius, kind):
    if not isinstance(payload, dict) or payload.get("remark") or not isinstance(payload.get("elements"), list):
        raise ValueError("incomplete_map_response")
    records, seen = [], set()
    for item in payload["elements"]:
        tags = item.get("tags", {})
        cat = category(tags, kind)
        typ, oid = item.get("type"), item.get("id")
        point = item if typ == "node" else item.get("center", {})
        if not cat or typ not in ("node", "way", "relation") or type(oid) is not int:
            continue
        try:
            y, x = float(point["lat"]), float(point["lon"])
            validate_context(y, x, radius)
        except (KeyError, TypeError, ValueError):
            continue
        distance = distance_miles(lat, lon, y, x)
        name = str(tags.get("name") or tags.get("ref") or "Unnamed mapped feature")[:180]
        identity = (typ, oid)
        named_identity = (cat, name.casefold(), round(y, 4), round(x, 4))
        if distance > radius or identity in seen or (name != "Unnamed mapped feature" and named_identity in seen):
            continue
        seen.update((identity, named_identity))
        records.append({"name": name, "category": cat, "lat": y, "lon": x,
                        "distance_miles": round(distance, 3),
                        "access": str(tags.get("access", "unknown")),
                        "source": f"https://www.openstreetmap.org/{typ}/{oid}"})
    return {"places": sorted(records, key=lambda x: x["distance_miles"]),
            "limited": len(payload["elements"]) >= 500,
            "data_time": payload.get("osm3s", {}).get("timestamp_osm_base", ""),
            "competitor_supported": kind in FILTERS}


@st.cache_data(ttl=86400, max_entries=128, show_spinner=False)
def nearby_places(lat, lon, radius, kind):
    validate_context(lat, lon, radius)
    filters = [FILTERS[kind]] if kind in FILTERS else []
    filters += ['["amenity"="parking"]', '["highway"="bus_stop"]',
                '["railway"~"^(station|tram_stop)$"]', '["tourism"~"^(hotel|guest_house)$"]',
                '["amenity"~"^(events_venue|conference_centre)$"]']
    body = "".join(f"nwr{tag}(around:{int(radius*1609.344)},{lat:.6f},{lon:.6f});" for tag in filters)
    throttle("overpass", 2)
    payload = fetch_json(OVERPASS, data={"data": "[out:json][timeout:12][maxsize:16777216];(" + body + ");out center 500;"})
    result = parse_places(payload, lat, lon, radius, kind)
    result["retrieved_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    return result


@st.cache_data(ttl=86400, max_entries=128, show_spinner=False)
def community_data(lat, lon):
    validate_context(lat, lon, 1)
    census_key = os.getenv("CENSUS_API_KEY", "")
    if not census_key:
        return {"status": "key_required"}
    # Match the geography vintage to the ACS data year, never infer a radius population.
    geo = fetch_json(CENSUS_GEO + "/geographies/coordinates", {
        "x": lon, "y": lat, "benchmark": "Public_AR_Current",
        "vintage": "ACS2024_Current", "layers": "Census Tracts", "format": "json"})
    tracts = geo.get("result", {}).get("geographies", {}).get("Census Tracts", [])
    if not tracts:
        raise ValueError("no_tract")
    tract = tracts[0]
    params = {"get": "NAME,B01003_001E,B19013_001E,B19013_001M",
              "for": "tract:" + tract["TRACT"],
              "in": "state:" + tract["STATE"] + " county:" + tract["COUNTY"]}
    rows = fetch_json("https://api.census.gov/data/2024/acs/acs5", {**params, "key": census_key})
    if not isinstance(rows, list) or len(rows) < 2:
        raise ValueError("no_community_data")
    row = dict(zip(rows[0], rows[1]))
    def value(key):
        try:
            n = int(row[key])
            return n if n >= 0 else None
        except (TypeError, ValueError, KeyError):
            return None
    return {"area": row["NAME"], "population": value("B01003_001E"),
            "income": value("B19013_001E"), "income_moe": value("B19013_001M"),
            "period": "2020–2024 ACS 5-year",
            "source": "https://api.census.gov/data/2024/acs/acs5?" + requests.compat.urlencode(params),
            "retrieved_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}


@st.cache_data(ttl=86400, max_entries=128, show_spinner=False)
def road_traffic(lat, lon, radius):
    validate_context(lat, lon, radius)
    # This source only covers Texas. Query nearby station records, not storefront visitors.
    payload = fetch_json(TXDOT + "/query", {
        "f": "json", "geometry": f"{lon},{lat}", "geometryType": "esriGeometryPoint",
        "inSR": 4326, "spatialRel": "esriSpatialRelIntersects", "distance": radius,
        "units": "esriSRUnit_StatuteMile", "outFields": "TRFC_STATN_ID,LATEST_AADT_YR,AADT_RPT_QTY",
        "outSR": 4326, "returnGeometry": "true", "resultRecordCount": 200})
    if "error" in payload or payload.get("exceededTransferLimit"):
        raise ValueError("incomplete_traffic_response")
    stations = []
    for item in payload.get("features", []):
        attr, point = item.get("attributes", {}), item.get("geometry", {})
        try:
            y, x = float(point["y"]), float(point["x"])
            count, year = int(attr["AADT_RPT_QTY"]), int(attr["LATEST_AADT_YR"])
            distance = distance_miles(lat, lon, y, x)
        except (KeyError, TypeError, ValueError):
            continue
        if count < 0 or distance > radius:
            continue
        stations.append({"station": str(attr["TRFC_STATN_ID"]), "vehicles_per_day": count,
                         "year": year, "distance_miles": round(distance, 3), "lat": y, "lon": x})
    return {"stations": sorted(stations, key=lambda x: x["distance_miles"])[:5],
            "source": TXDOT, "retrieved_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}


def evidence_key(address, lat, lon, radius, kind):
    return hashlib.sha256(json.dumps([address.strip().casefold(), lat, lon, radius, kind]).encode()).hexdigest()


def report_location(site, kind):
    """Keep report evidence small and reject stale lookups."""
    result = {k: v for k, v in site.items() if k != "location_evidence"}
    saved = site.get("location_evidence", {})
    key = evidence_key(site.get("address", ""), site.get("lat"), site.get("lon"),
                       site.get("radius_miles", 1.0), kind)
    if not saved or saved.get("key") != key:
        return result
    mapped = saved.get("map", {})
    places = mapped.get("places", [])
    result["public_evidence"] = {
        "map_status": mapped.get("status", "unavailable"),
        "mapped_counts": {cat: sum(x["category"] == cat for x in places) for cat in LABELS}
            if mapped.get("status") == "ok" else None,
        "competitor_supported": mapped.get("competitor_supported", False),
        "partial": mapped.get("limited", False),
        "retrieved_at": mapped.get("retrieved_at"),
        "places": places[:12],
        "community": saved.get("community"),
        "road_traffic": saved.get("traffic"),
    }
    return result


def collect_evidence(lat, lon, radius, kind):
    validate_context(lat, lon, radius)
    tasks = {"map": (nearby_places, (lat, lon, radius, kind)),
             "community": (community_data, (lat, lon)),
             "traffic": (road_traffic, (lat, lon, radius))}
    result = {}
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = {key: pool.submit(fn, *args) for key, (fn, args) in tasks.items()}
        for key, future in futures.items():
            try:
                result[key] = {"status": "ok", **future.result()}
            except (requests.RequestException, ValueError, KeyError, TypeError, IndexError):
                result[key] = {"status": "unavailable"}
    return result


def render_location_analysis(profile, site, launch, lang):
    zh = lang == "zh"
    def tr(en, cn):
        return cn if zh else en
    st.subheader(tr("Explore this neighborhood", "看看这个位置怎么样"))
    st.caption(tr("Free public data for US locations; road counts cover Texas. No paid AI is used.",
                  "查询美国免费公开数据；道路车流目前覆盖得州。不调用付费 AI。"))
    old_address = site.get("address", "")
    address = st.text_input(tr("Address or Trade Area", "地址或商圈"), value=old_address,
                            key="free_location_address")
    radius = st.select_slider(tr("Search radius (miles)", "查询半径（英里）"),
                              options=[0.5, 1.0, 3.0], value=site.get("radius_miles", 1.0))
    kind = profile.get("business_type", "Other")
    site.update(address=address, radius_miles=radius, assessment_mode="free",
                traffic=None, competitors=None, rent_level="Unknown", parking="Unknown",
                foot_traffic_source="Unknown", risk_flags=[])
    if address != old_address:
        site.pop("located_address", None)
        site.pop("location_evidence", None)
        st.session_state.pop("free_location_matches", None)
        st.session_state.pop("free_location_match", None)
    st.caption(tr("The address/coordinates are sent to public Census, OpenStreetMap and TxDOT services when you search.",
                  "点击查询时，地址或坐标将发送给 Census、OpenStreetMap 和得州交通局公开服务。"))
    search = st.button(tr("🔎 Explore this address", "🔎 分析这个地址"), type="primary",
                       key="free_location_search", disabled=len(address.strip()) < 3)
    if search:
        site.pop("location_evidence", None)
        with st.spinner(tr("Finding your address…", "正在定位地址…")):
            try:
                matches = locate_address(address.strip())
            except (requests.RequestException, ValueError, KeyError, TypeError):
                matches = []
            st.session_state.free_location_matches = matches
        if not matches:
            site.pop("located_address", None)
            st.warning(tr("Address unavailable. Try a complete US street address, then retry.",
                          "暂时无法定位。请填写完整美国街道地址后重试。"))
    matches = st.session_state.get("free_location_matches", [])
    if matches:
        chosen = st.selectbox(tr("Confirm the mapped address", "确认地图匹配的地址"),
                              matches, format_func=lambda item: item["name"], key="free_location_match")
        site.update(lat=chosen["lat"], lon=chosen["lon"], located_address=address)
        st.caption(tr("Matched: ", "匹配地址：") + chosen["name"])
    verified = site.get("located_address") == address and bool(address.strip())
    key = evidence_key(address, site.get("lat"), site.get("lon"), radius, kind)
    saved = site.get("location_evidence", {})
    if saved and saved.get("key") != key:
        site.pop("location_evidence", None)
        saved = {}
    # Exact single matches run immediately; ambiguous addresses require selection before lookup.
    analyze = search and len(matches) == 1
    if verified:
        analyze = st.button(tr("Load / refresh neighborhood data", "查询 / 更新周边数据"),
                            key="free_location_load") or analyze
    if analyze and verified:
        with st.spinner(tr("Checking maps, community statistics and road counts…",
                           "正在查询地图、社区统计和道路车流…")):
            result = collect_evidence(site["lat"], site["lon"], radius, kind)
        saved = {"key": key, **result}
        site["location_evidence"] = saved
    if not saved:
        st.info(tr("Choose an address to build your location snapshot. Missing data will stay unknown.",
                   "输入地址开始生成选址参考。缺失的数据会保留为未知。"))
    else:
        render_snapshot(saved, site, zh)
    with st.expander(tr("Add the landlord's quote (optional)", "填写房东报价（可选）")):
        rent = st.number_input(tr("Monthly rent quoted (USD)", "房东报的月租（美元）"),
                               min_value=0.0, value=float(site.get("monthly_rent_quote") or 0), step=100.0)
        site["monthly_rent_quote"] = rent or None
        revenue = float(launch.get("expected_monthly_revenue") or 0)
        if rent and revenue:
            st.write(tr(f"Rent is {rent/revenue:.1%} of your assumed monthly sales.",
                        f"月租占你假设的月销售额的 {rent/revenue:.1%}。"))
        st.caption(tr("Include this rent in your monthly fixed-cost total on Budget. It is not added twice automatically.",
                      "请把租金计入预算页每月固定费用总额。系统不会自动再加一次。"))
    st.caption(tr("Actual storefront footfall and lease terms remain unverified. A location or overall score is not issued from incomplete public data.",
                  "真实门前人流和租约条款仍待核实。公开数据不完整时，不给出选址或综合分数。"))


def render_snapshot(saved, site, zh):
    def tr(en, cn):
        return cn if zh else en
    mapped = saved.get("map", {})
    rows = mapped.get("places", []) if mapped.get("status") == "ok" else []
    columns = st.columns(4)
    for col, (category_name, labels) in zip(columns, LABELS.items()):
        available = mapped.get("status") == "ok" and (category_name != "competitor" or mapped.get("competitor_supported"))
        col.metric(labels[1 if zh else 0], str(sum(x["category"] == category_name for x in rows)) if available else "—")
    st.caption(tr("Counts are mapped features found, not a complete business census. Stops may include both sides of a road; parking may be private.",
                  "数量为地图找到的设施，不代表完整商户清单。站点可能包含道路两侧，停车场可能不对外开放。"))
    if mapped.get("status") != "ok":
        st.warning(tr("Map data is temporarily unavailable. Retry the lookup; no zero counts have been assumed.",
                      "地图数据暂时不可用。可以重试；不会把查询失败当作零家店。"))
    elif not mapped.get("competitor_supported"):
        st.info(tr("Choose a specific supported shop type to search competitors. General retail only matches stores tagged as general shops.",
                   "请选择支持的具体店型查询竞品。小型零售仅匹配标记为综合商店的地点。"))
    if mapped.get("limited"):
        st.warning(tr("A busy area reached the result limit. These are partial counts; try a smaller radius.",
                      "区域结果达到上限，当前数量不完整。请缩小查询半径。"))
    import pydeck as pdk
    colors = {"competitor": [189, 128, 110], "parking": [83, 130, 180],
              "transit": [207, 162, 60], "partner": [54, 92, 69]}
    points = [{**x, "color": colors[x["category"]]} for x in rows]
    points.append({"lat": site["lat"], "lon": site["lon"], "name": tr("Your selected location", "你的选址"),
                   "category": "Selected location", "color": [50, 45, 40]})
    st.pydeck_chart(pdk.Deck(
        layers=[pdk.Layer("ScatterplotLayer", data=points, get_position="[lon, lat]",
                          get_fill_color="color", get_radius=30, radius_min_pixels=5, pickable=True)],
        initial_view_state=pdk.ViewState(latitude=site["lat"], longitude=site["lon"], zoom=13),
        map_style="https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
        tooltip={"text": "{name}\n{category}"}), height=360)
    st.caption(tr("Terracotta: similar shops · Blue: parking · Gold: transit · Green: partners · Dark: your location",
                  "陶红：同类店铺 · 蓝色：停车 · 金色：交通站点 · 绿色：合作地点 · 深色：你的选址"))
    if rows:
        with st.expander(tr("View names, distances and sources", "查看名称、距离和来源")):
            st.dataframe(pd.DataFrame(rows)[["name", "category", "distance_miles", "access", "source"]],
                         hide_index=True, use_container_width=True)
    if mapped.get("status") == "ok":
        st.caption("© OpenStreetMap contributors · " + mapped.get("retrieved_at", "") +
                   " · Map data: " + mapped.get("data_time", ""))
        st.markdown("[OpenStreetMap / ODbL](https://www.openstreetmap.org/copyright)")
    community, traffic = saved.get("community", {}), saved.get("traffic", {})
    left, right = st.columns(2)
    with left:
        st.subheader(tr("Community background", "社区背景"))
        if community.get("status") == "ok":
            population, income = community.get("population"), community.get("income")
            st.metric(tr("Residents in census tract", "普查区居民"), f"{population:,}" if population is not None else "—")
            st.metric(tr("Median household income", "家庭收入中位数"), f"USD {income:,}" if income is not None else "—")
            st.caption(community["area"] + " · " + community["period"])
            if community.get("income_moe") is not None:
                st.caption(tr("Income margin of error: ", "收入误差范围：") + f"± USD {community['income_moe']:,}")
            st.caption(tr("Census tract, not your search circle. Historical estimates, not current shoppers.",
                          "这是普查区而非查询圆圈的数据；属于历史统计估计，不代表当前顾客。"))
            st.markdown("[US Census ACS](" + community["source"] + ")")
            st.caption(community["retrieved_at"])
        else:
            message = tr("Community statistics are not connected yet. Other location results are available.",
                         "社区统计暂未接通，其他选址结果仍可使用。") if community.get("status") == "key_required" else tr(
                         "Community data is unavailable for this lookup.", "本次查询暂无社区数据。")
            st.info(message)
    with right:
        st.subheader(tr("Nearby road traffic", "附近道路车流"))
        stations = traffic.get("stations", [])
        if traffic.get("status") == "ok" and stations:
            nearest = stations[0]
            st.metric(tr("Vehicles / day at nearest mapped station", "最近已找到测点的日均车辆"), f"{nearest['vehicles_per_day']:,}")
            st.caption(f"{nearest['year']} · {nearest['distance_miles']:.2f} mi · Station {nearest['station']}")
            st.caption(tr("Road AADT, not pedestrians or shop visits. Nearby roads can serve very different traffic.",
                          "这是道路年平均日车流，不是行人或进店人数。邻近道路的实际用途可能不同。"))
            st.dataframe(pd.DataFrame(stations)[["station", "year", "vehicles_per_day", "distance_miles"]],
                         hide_index=True, use_container_width=True)
            st.markdown("[TxDOT traffic counts](" + TXDOT + ")")
            st.caption(traffic["retrieved_at"])
        else:
            st.info(tr("No usable nearby Texas road count returned. Storefront footfall remains unknown.",
                       "未返回可用的附近得州道路车流。店门口人流仍为未知。"))
