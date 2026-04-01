# Agent Instructions

## Goal

Build proof-first daily financial news videos quickly, with minimal recomputation when one section changes.

---

## Fast Iteration Strategy

### Core rule
Do **not** rebuild the full video from scratch when only one story changes.

Instead, treat the pipeline as a set of reusable stages with cached artifacts.

---

## Recommended Pipeline

## 1. Research cache
Store each day's inputs under a date folder.

Example:
- `2026-04-01/research/`
- `2026-04-01/screenshots/`
- `2026-04-01/video_build/`
- `2026-04-01/clips/`
- `2026-04-01/final/`

Save and reuse:
- cleaned articles
- official source text
- screenshots
- chart images
- search results / chosen URLs

Never re-fetch a source unless:
- the source changed
- the earlier fetch failed
- the user asks for a refresh

---

## 2. Clip registry
Maintain a JSON registry for all external video clips used in a daily brief.

Suggested file:
- `YYYY-MM-DD/clip_registry.json`

For each clip, save:
- story key
- source URL
- uploaded VideoDB video id
- transcript indexed? yes/no
- chosen search query
- selected start/end
- why this clip was chosen
- alternate clip candidates

Example fields:
```json
{
  "lly": {
    "source_url": "https://www.youtube.com/watch?v=...",
    "video_id": "m-z-...",
    "search_query": "obesity pill led to around 12% weight loss",
    "start": 36.45,
    "duration": 24.0,
    "status": "approved"
  }
}
```

If the story script changes but the clip is still valid, reuse the same clip.

---

## 3. Pre-rendered scene assets
Each logical scene should have its own file.

Examples:
- title card
- ADP screenshot slide
- Intel screenshot slide
- Lilly screenshot slide
- Nike screenshot slide
- each chart slide

These are cheap to regenerate individually.

If one story changes, regenerate only the affected scene files.

---

## 4. Separate narration from visuals
For image/card scenes, keep narration as separate reusable audio assets.

Suggested registry:
- `YYYY-MM-DD/audio_registry.json`

Map:
- scene filename
- narration text hash
- generated audio id
- duration

If narration text is unchanged, reuse the audio asset.
If only one line changes, regenerate only that line's audio.

---

## 5. Prefer section-level timelines
Build the final video from reusable sections instead of one monolithic script.

Suggested sections:
- opening
- macro
- stock story 1
- stock story 2
- stock story 3
- closing

Each section should have a deterministic asset list and timing.

When one section changes:
- update that section's scene list
- keep all other section timings and assets if possible
- rebuild only the final composition step

---

## 6. Reuse uploaded VideoDB assets
Do not repeatedly upload the same:
- screenshot images
- charts
- clip sources
- final stream used for subtitle pass

Before uploading, check the registry for an existing asset id.

Only upload again if:
- the local file changed
- the URL changed
- the asset was deleted or invalid

---

## 7. Save clip-search work
Video search can be expensive and noisy.

For each candidate video:
- store search queries tried
- best matching shot text
- accepted start/end
- rejected reasons for bad clips

Suggested file:
- `YYYY-MM-DD/clip_search_notes.md`

This prevents repeating the same search work every run.

---

## 8. Two output modes
Always support two modes:

### Draft mode
Fastest possible iteration.
- no subtitle pass
- no extra polish
- reuse existing audio
- reuse existing clips
- rebuild final composition only

### Final mode
Slower, delivery-quality pass.
- optional subtitles
- final chosen clips only
- final screenshots/crops
- final render metadata saved

Use draft mode during editing.
Use final mode only when story order and assets are stable.

---

## 9. Subtitle strategy
Subtitles should be a final post-process step.

Do **not** subtitle every intermediate draft.

Workflow:
1. assemble final draft stream
2. upload final stream once
3. index spoken words once
4. add subtitles once
5. save resulting subtitled stream URL in registry

Suggested file:
- `YYYY-MM-DD/final/render_registry.json`

---

## 10. Minimal rebuild policy
When something changes, use this rule:

### If article crop changes
Rebuild only the affected screenshot scene.

### If chart changes
Rebuild only that chart scene.

### If selected video clip changes
Re-run only:
- clip search for that story
- that story's timeline segment
- final composition

### If narration changes for one story
Regenerate only that story's audio.

### If only scene ordering changes
Do not regenerate assets; only rebuild the final timeline.

---

## Recommended Files Per Day

- `YYYY-MM-DD/research/`
- `YYYY-MM-DD/screenshots/`
- `YYYY-MM-DD/video_build/`
- `YYYY-MM-DD/clips/`
- `YYYY-MM-DD/clip_registry.json`
- `YYYY-MM-DD/audio_registry.json`
- `YYYY-MM-DD/render_registry.json`
- `YYYY-MM-DD/clip_search_notes.md`
- `YYYY-MM-DD/final/`

---

## Execution Guidance for Agents

1. First look for existing registries before fetching/uploading/generating.
2. Reuse VideoDB asset ids whenever possible.
3. Prefer updating a single section over rebuilding the whole pipeline.
4. Treat clip search, screenshot crop generation, narration generation, and final composition as separate caches.
5. Only run full final render after the user approves story selection and proof assets.

---

## Practical Recommendation for This Repo

Next implementation step should be to split `2026-04-01/make_video.py` into:
- source collection
- asset cache / registry manager
- clip search / selection
- scene renderer
- final timeline assembler
- subtitle pass

This will make edits much faster and cheaper.
