# Jenny Wilson Feedback Improvements

Implemented by **Yang Yu** on September 7, 2026, following flower-shop owner feedback about the Small Business Decision Toolkit.

## A warmer experience for independent owners

- Replaced the dark space-themed interface with a light cream, garden green, and terracotta visual system.
- Rewrote the opening message and AI guidance in warmer, everyday language while keeping financial warnings direct.
- Improved mobile layouts, keyboard focus visibility, cards, tables, buttons, metrics, and four-step progress styling.
- Changed the page icon and visible product attribution to match the welcoming toolkit experience.

## Step 1: concept and shop feeling

- Added **Flower Shop** and **Bakery** to the business-type choices, plus an editable description for Other.
- Added plain-language prompts for why customers would choose the shop and what customer evidence the owner has gathered.
- Added an optional local PNG/JPG inspiration-photo preview. The image is validated, resized, stripped of metadata, kept in the current session, and excluded from AI requests and reports.
- Added four curated mood palettes and an editable atmosphere brief.
- Added optional AI-written creative direction based on the owner's concept text and selected colors. It is explicitly labeled as written guidance rather than an AI-generated image.
- Invalidates earlier creative direction when the underlying concept changes.

## Step 2: neighborhood ecosystem

- Added an owner-triggered search for named nearby hotels, cafés, event venues, and offices using public OpenStreetMap data.
- Displays source links, retrieval time, estimated straight-line distance, a map, and a clear statement that listings are not confirmed partnerships.
- Requires coordinates verified for the current typed address, preventing a new address from using stale coordinates.
- Adds useful Google Maps category searches and practical partnership ideas when public map data is unavailable or incomplete.
- Does not contact any business or claim that a listed business is interested in partnering.

## Step 3: spoilage and seasonal reality

- Added an optional perishable-stock model using `effective cost = pre-waste cost / (1 - spoilage rate)`.
- Shows the added monthly waste cost and the effective representative-product cost.
- Blocks a selling price that falls below the effective cost after spoilage.
- Added busy-month sales-volume, wholesale-cost, and number-of-months controls for Valentine's Day, Mother's Day, and similar peaks.
- Shows ordinary-month and busy-month revenue, product costs, and profit side by side, plus a transparent annual scenario.
- Keeps the launch decision based on the ordinary month so an optimistic holiday scenario cannot hide an everyday loss.
- States that the simplified model holds fixed costs and spoilage constant and excludes taxes, financing, and extra seasonal labor or delivery costs.

## AI and report reliability

- AI prompts now include the customer promise, user-reported validation, mood brief, sourced neighborhood evidence, spoilage, and seasonal assumptions.
- Reports must preserve the deterministic launch verdict and cannot upgrade it based on storytelling or a holiday scenario.
- Failed top-level AI questions no longer appear as successful answers; the question stays available for retry.
- Report generation preserves entered values after a timeout, offers retry, and clears an old report when the owner changes the plan.

## Verification completed

- **57 automated tests passed** across business calculations, seasonal scenarios, image validation, map-response validation, full four-step UI state, report retries, Operations consent, Finance consent and parsed-data prompts.
- A flower-shop scenario was tested with USD 150,000 funding, USD 110,000 startup cost, USD 22,000 monthly fixed cost, USD 45,000 ordinary monthly revenue, 62% pre-waste gross margin, 15% spoilage, a USD 28 pre-waste unit cost, and a USD 75 selling price.
- The resulting ordinary-month profit was verified as **USD 2,882.35**, including waste. The effective representative unit cost was **USD 32.94**.
- A live public-map check around the Austin example location returned 10 sourced listings, including cafés and hotels. Automated tests never rely on live network access.
- The local application was visually reviewed in a desktop browser in English; bilingual UI paths were covered by automated tests.

Automated AI tests use a mocked provider response to verify prompts, success, timeout, retry, and privacy behavior. Live hosted AI availability is checked separately after deployment because provider credentials are not stored in the repository.
