# Example: 2026-04-01 Financial Market Analysis

This is a self-contained example of a proof-first financial news video workflow for **2026-04-01**.

## What this example contains

### Inputs
- `research/` — cleaned source text and official source extracts
- `screenshots/` — captured source-page screenshots
- `charts/` — reusable chart SVGs

### Outputs
- `reports/` — written brief and storyboard
- `video_build/` — rendered slide assets and build metadata

### Scripts
- `scripts/make_video.py` — assembles the proof-first video
- `scripts/capture_screenshot.js` — captures page screenshots with Playwright

## Key files to inspect first

1. `reports/2026-04-01-midday-financial-news-brief.md`
2. `reports/2026-04-01-video-storyboard.md`
3. `video_build/video_result.json`
4. `scripts/make_video.py`

## Output

Primary output stream for this example day:
- `https://play.videodb.io/v1/f37914dd-5239-4c10-aa2e-006f9095ac7c.m3u8`

Player:
- `https://player.videodb.io/watch?v=https://play.videodb.io/v1/f37914dd-5239-4c10-aa2e-006f9095ac7c.m3u8`

## Why this structure

This example is intentionally self-contained so that a user or agent can:
- understand one full run in one folder
- copy the folder as a template for another date
- edit only the parts that changed without searching the whole repo

## Suggested reuse pattern

When creating a new day:
- copy this folder structure
- replace `research/`, `screenshots/`, and `charts/`
- regenerate the final build

## Notes

This example includes:
- screenshot proof
- chart proof
- VideoDB-selected clip proof
- final timeline build metadata

It may also contain some intermediate build artifacts that are useful for debugging or iteration.
