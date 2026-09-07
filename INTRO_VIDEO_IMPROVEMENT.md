# Warm Storefront Intro Video

Implemented by Yang Yu in response to the request for a warmer first impression.

## What changed

- Added a four-second illustrated storefront opening screen before the homepage.
- The shop window warms and lights up, the hanging sign turns to `OPEN`, and the brand message appears in stages.
- The film uses the same cream, garden green, terracotta, and soft gold palette as the redesigned toolkit.
- The final frame identifies the product and displays `BY YANG YU`.

## Playback and accessibility

- The video starts automatically and muted when a new browser session opens.
- The small MP4 is delivered with the opening screen to avoid a separate cloud-media buffering delay.
- The opening fills the viewport while the homepage initializes safely underneath it, then fades away automatically.
- Portrait phones receive a dedicated 9:16 edit with the message above the storefront, plus a full-frame fit so the composition remains legible instead of being cropped to one corner.
- Session state prevents the opening from replaying during form edits, step changes, or suite navigation.
- The MP4 has no audio track, and playback is capped so visitors cannot be trapped on the opening screen.
- No forced Streamlit rerun occurs after playback, preventing the Cloud startup race that displayed `Bad message format: Tried to use SessionInfo before it was initialized`.
- The Cloud runtime now uses Streamlit 1.52.2 instead of 1.40.2. The older frontend predates Streamlit's upstream SessionInfo reconnect-race fix and could continue showing the dialog even after application-level reruns were removed.

## Verification

- Duration: 4 seconds
- Resolution: 1280 × 720
- Encoding: H.264 video in an MP4 container
- Decode verification completed without errors
