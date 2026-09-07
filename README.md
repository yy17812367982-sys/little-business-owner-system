# Small Business Decision Support System

An AI-powered decision support platform designed to help small business owners make more informed operational and financial decisions.

## Key Features

- Financial performance analysis
- Business health assessment
- AI-powered recommendations
- Revenue and cost analysis
- Market location insights
- Interactive reporting dashboard
- Warm, bilingual four-step store-planning experience
- Local inspiration-photo preview, curated mood palettes, and AI-written creative direction
- Public-map discovery for nearby hotels, cafés, venues, and office partners
- Perishable-stock waste and holiday peak scenarios
- Evidence-based launch reports that preserve the ordinary-month decision

## Technology Stack

- Python
- Streamlit
- Pandas
- Plotly
- Google Gen AI SDK

## Testing

Run the business rules, owner-experience, UI, and AI reliability checks with:

```bash
python -m unittest discover -v
```

External AI calls are mocked in automated tests. Nearby-place tests use mocked map responses; a live OpenStreetMap read can be performed separately when network access is available.

## Live Demo

https://yu-yang-small-business-owner-system.streamlit.app/
