# A simpler, more visual shop planner

Project owner: Yang Yu

## Changes

- Added clickable flower-shop, coffee-shop and bakery choices, retaining all other business types.
- Added a live shop preview that reflects the selected type, target customer and differentiator.
- Moved supporting concept questions and inspiration tools into optional sections.
- Collapsed location assumptions so the address and map are easier to find.
- Reduced the initial budget controls to funding, opening cost, monthly fixed costs and monthly sales.
- Added live funding and monthly-result charts using the report's existing calculations, including waste.
- Retained expandable pricing, margin, waste and seasonality controls and all existing blocking validation.
- Kept example-data reminders visible; selecting a shop does not invent new industry-specific numbers.

## Verification

- Existing automated suite passed after integration, including AI success/failure mocks, report generation, consent, pricing validation and data persistence.
- Browser check: flower-shop selection and custom text update the preview.
- Browser check: changing funding from USD 80,000 to USD 150,000 updates the funding gap.
- Mobile check at 390 x 844: two charts rendered and document width remained 390 pixels.

The AI checks use mocked responses. This update does not change the AI service or establish a new live-provider availability result.
