# Free location research for prospective shop owners

Project owner: Yang Yu

## What changed

Owners enter a US address, choose a search radius and request a neighborhood snapshot. The location page replaces estimated traffic and competition sliders with evidence from free public services.

- Census address lookup with a rate-limited OpenStreetMap fallback; ambiguous addresses can be selected before neighborhood lookup.
- OpenStreetMap queries for mapped competitors, parking, transit and potential partner locations, with a colored map and source links.
- Nearby TxDOT annual average daily vehicle counts with station ID, year and distance. These are explicitly not storefront footfall or customer counts.
- Optional landlord rent quote and comparison with assumed sales; rent must be included in the existing fixed-cost total, not added twice.
- Independent data-source failures, bounded requests, daily caches, timestamps and partial-result notices.
- Address, radius and business-type changes invalidate old evidence. Report context is bounded and excludes stale results.
- Incomplete location evidence produces no site, competition or overall score. Financial calculations remain available with a provisional financial-only decision.

## Community statistics setup

The ACS community connector is implemented but not active without CENSUS_API_KEY in the deployment environment. Live testing found that Census redirects requests without a key to its missing-key page. Obtain a free Census API key and set this environment variable to enable tract population and median household income with period and margin of error. Never commit the key. The key is not included in public source links.

Until configured, the page explicitly says community statistics are not connected. Other sources continue to work. No paid map or AI requests are made by this feature.

## Validation

- Automated tests cover source failures, partial responses, distance filtering, unsupported shop categories, source year retention, stale evidence, explicit lookup and provisional decisions.
- Live public-address test: 1011 S Congress Ave, Austin, TX 78704 resolved successfully; OpenStreetMap returned facilities and TxDOT returned nearby station data.
- At test time the closest returned station was 227U749, approximately 0.114 miles away, with 2025 AADT of 25,360 vehicles. This is a road observation, not a business forecast.
- Public-map coverage is incomplete. General retail uses the general-shop map category and does not encompass every retailer. Parking counts do not guarantee availability or public access.

Sources: https://www.openstreetmap.org/copyright ; https://www.txdot.gov/data-maps/traffic-count-maps.html ; https://www.census.gov/data/developers.html
