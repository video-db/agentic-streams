---
name: financial-news-video-agent
description: Create proof-first financial news recap videos using article proof, screenshots, charts, and selected VideoDB clips. Use when asked to build a daily market-news video, a proof-backed financial recap, or a news-to-video workflow.
---

# Financial News Video Agent Skill

Use this skill when the user wants to:
- make a daily financial news summary video
- turn market news into a proof-backed recap
- combine charts, screenshots, and video clips into a coherent financial brief
- reuse cached clips and audio instead of recomputing the whole pipeline

## Required tools / capabilities
- file read/write/edit
- bash
- Python via `uv run`
- VideoDB access
- URL/article extraction
- optional screenshot/browser support

## Inputs to gather
Before running, gather:
- target date
- market focus (US equities, macro, sectors, etc.)
- target length
- whether the user wants draft or final mode
- whether subtitles are needed

## Standard workflow

### 1. Create date folder
Use:
```text
YYYY-MM-DD/
```

### 2. Collect proof sources
Store in:
```text
YYYY-MM-DD/research/
```

Collect:
- official releases
- reputable articles
- transcripts where available

### 3. Capture screenshots
Store in:
```text
YYYY-MM-DD/screenshots/
```

Create video-friendly crops from full screenshots.
Do not place raw tall screenshots directly into the final timeline.

### 4. Build charts
Store in:
```text
assets/YYYY-MM-DD/
```

At minimum include:
- market overview
- stock-specific chart for each chosen story

### 5. Search clips with VideoDB
For each chosen story:
- search YouTube/news clips
- upload only the selected source
- index spoken words
- search transcript for the best quote or segment
- save result in `clip_registry.json`

### 6. Reuse cached clip/audio assets
Before generating new assets:
- check `clip_registry.json`
- check `audio_registry.json`
- reuse existing VideoDB ids whenever possible

### 7. Assemble the draft video
Include:
- title/opening
- screenshot proof
- chart proof
- actual clip proof when available
- closing summary

### 8. Subtitle only at the end
Subtitles should be a final pass after draft approval.

## Caching policy
Do not rebuild the whole project when one story changes.

If one story changes:
- update only that story's screenshots/crops
- update only that story's selected clip
- update only that story's narration audio if needed
- rebuild the final timeline last

## Suggested per-day files
- `YYYY-MM-DD/README.md`
- `YYYY-MM-DD/research/`
- `YYYY-MM-DD/screenshots/`
- `YYYY-MM-DD/charts/`
- `YYYY-MM-DD/reports/`
- `YYYY-MM-DD/video_build/`
- `YYYY-MM-DD/scripts/`
- `YYYY-MM-DD/clip_registry.json`
- `YYYY-MM-DD/audio_registry.json`
- `YYYY-MM-DD/render_registry.json`
- `YYYY-MM-DD/clip_search_notes.md`

## Deliverables
A good run should produce:
- per-day self-contained example folder
- report markdown
- storyboard markdown
- charts
- screenshots
- final or draft video stream URL
- optional subtitled stream URL

## Public example convention
When preparing examples for others, prefer a self-contained layout:

```text
examples/
  YYYY-MM-DD/
    README.md
    research/
    screenshots/
    charts/
    reports/
    scripts/
    video_build/
```

## Reference docs in this repo
- `README.md`
- `docs/SETUP.md`
- `AGENTS.md`
