# Proof-First Financial News Video Agent

Build daily financial news videos backed by:
- article proof
- official-source proof
- chart proof
- optional YouTube/news clips
- narrated summary video output

This repo is designed so an agentic coding tool can reproduce the workflow with minimal manual work.

---

## What this project does

For a chosen date, the agent can:
1. collect financial news and official sources
2. extract and store article text
3. capture screenshots
4. build market-reaction charts
5. search YouTube/news clips with VideoDB
6. index clips and select evidence segments
7. assemble a narrated video timeline
8. optionally add subtitles as a final pass

The emphasis is **proof-first**, not hype-first.

---

## Who this is for

This repo is for people building:
- autonomous news-video agents
- market recap video pipelines
- proof-backed financial content workflows
- reusable agent skills for research + video assembly

---

## Recommended repo structure

```text
.
├── README.md
├── AGENTS.md
├── .env.example
├── 2026-04-01/
│   ├── research/
│   ├── screenshots/
│   ├── video_build/
│   ├── clips/
│   ├── final/
│   ├── clip_registry.json
│   ├── audio_registry.json
│   ├── render_registry.json
│   └── make_video.py
├── assets/
│   └── 2026-04-01/
├── reports/
├── skills/
│   └── financial-news-video-agent/
│       └── SKILL.md
└── docs/
    └── SETUP.md
```

---

## Requirements

## 1. VideoDB
Used for:
- uploading clips and rendered streams
- indexing spoken words
- searching transcript moments
- assembling the final video
- subtitle passes

## 2. Python + uv
Use `uv` to run scripts.

## 3. Optional browser screenshot support
For article screenshots, this repo uses Playwright CLI where available.

---

## Installation

See full setup instructions in:
- `docs/SETUP.md`

Quick version:

### Python runtime
Install `uv`:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Node runtime
Needed for Playwright-based screenshots.

### Playwright browser
```bash
npx playwright install chromium
```

---

## Configuration

Create `.env`:

```env
VIDEO_DB_API_KEY=your_key_here
```

Optional future additions:
```env
POLYGON_API_KEY=
ALPHA_VANTAGE_API_KEY=
```

Do not commit `.env`.

---

## Skills used

This project can work well with the following skills in an agentic tool:

### Core
- `videodb`
- `url-to-markdown`
- `uv`

### Helpful extras
- browser/screenshot automation
- yahoo/market data fetchers
- SEC filing fetchers

---

## Local skill entrypoint

A reusable local skill is documented here:
- `skills/financial-news-video-agent/SKILL.md`

Use that skill when you want the agent to:
- create a date-based financial brief
- gather proof assets
- build a narrated video
- reuse cached clips/audio instead of recomputing everything

---

## Day-based workflow

### Step 1: create date workspace
Example:
```text
2026-04-01/
```

### Step 2: gather sources
Store in:
```text
2026-04-01/research/
```

### Step 3: capture screenshots
Store in:
```text
2026-04-01/screenshots/
```

### Step 4: generate charts
Store in:
```text
assets/2026-04-01/
```

### Step 5: search and cache clips
Store metadata in:
- `2026-04-01/clip_registry.json`
- `2026-04-01/clip_search_notes.md`

### Step 6: reuse or generate narration audio
Store metadata in:
- `2026-04-01/audio_registry.json`

### Step 7: assemble video
Main script example:
- `2026-04-01/make_video.py`

### Step 8: subtitle only at the end
Create subtitles as a final post-process pass after the draft is approved.

---

## Fast iteration rule

Do **not** rebuild everything if one story changes.

If one section changes:
- reuse previously uploaded assets
- reuse previously indexed clips
- reuse narration audio if text is unchanged
- only replace the affected section
- rebuild the final composition last

More guidance is in:
- `AGENTS.md`

---

## Example commands

### Run the daily video builder
```bash
uv run 2026-04-01/make_video.py
```

### Basic subtitle pass
```bash
uv run --with videodb --with python-dotenv python subtitle_pass.py
```

---

## What to share publicly

If publishing this for others, include:
1. this `README.md`
2. `docs/SETUP.md`
3. `skills/financial-news-video-agent/SKILL.md`
4. `.env.example`
5. one example date folder
6. one example generated report and storyboard

Included example in this repo:
- `examples/2026-04-01/`
- `examples/2026-04-01/reports/2026-04-01-midday-financial-news-brief.md`
- `examples/2026-04-01/reports/2026-04-01-video-storyboard.md`
- `examples/2026-04-01/README.md`

That gives others both:
- a reproducible setup
- a concrete example

---

## Suggested public positioning

You can describe this repo as:

> A proof-first financial news video agent that turns daily market news, charts, screenshots, and selected news clips into coherent evidence-backed recap videos.

---

## Next recommended improvement

Before wider sharing, consider splitting the current pipeline into reusable modules:
- source collection
- screenshot capture
- clip search and registry
- narration registry
- scene renderer
- final assembler
- subtitle pass

That will make it easier for others to adapt to their own agentic stack.

---

## Included example

A concrete example day is included for reference:

- workspace: `examples/2026-04-01/`
- charts: `examples/2026-04-01/charts/`
- report: `examples/2026-04-01/reports/2026-04-01-midday-financial-news-brief.md`
- storyboard: `examples/2026-04-01/reports/2026-04-01-video-storyboard.md`
- example guide: `examples/2026-04-01/README.md`

The example folder is self-contained and includes:
- research markdown
- screenshots
- chart svgs
- built slide assets
- scripts
- `video_result.json`
