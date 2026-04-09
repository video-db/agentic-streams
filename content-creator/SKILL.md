---
name: content-creator
description: Turn any research topic into a polished video briefing with narration, dynamic visuals, and background music. Researches via parallel subagents, scripts a narrative arc, produces assets (AI video, Remotion data viz, browser capture, kinetic text), composes on a timeline, and self-reviews in a loop using VideoDB's scene indexing to verify visual-narration alignment.
---

# Content Creator

## Configuration

```
MAX_ITERATIONS: 5
SEGMENTS: 4-6
TARGET_DURATION: 60-120s
DEFAULT_RESOLUTION: 1280x720
DEFAULT_FORMAT: landscape
```

Adjust these before running. `MAX_ITERATIONS` controls how many review-and-fix cycles the agent runs before delivering.

## Parallel Execution

This skill supports parallel runs. Every run **must** generate a unique slug and namespace all local temp files under it.

### Slug Generation

At the very start of Phase 0 (before any file I/O), generate a slug:

```python
import uuid

SLUG = uuid.uuid4().hex[:8]
WORK_DIR = f"/tmp/vb_{SLUG}"
```

### What the slug isolates

| Resource | Path pattern |
|----------|-------------|
| Browser capture videos | `{WORK_DIR}/captures/` |
| Screenshots | `{WORK_DIR}/screenshots/` |
| Downloaded review frames | `{WORK_DIR}/frames/` |
| Any temp scripts | `{WORK_DIR}/scripts/` |

### Rules

1. **Never use bare `/tmp/` paths.** Always use `{WORK_DIR}/...` for every local file operation.
2. **Create `WORK_DIR` early.** Run `Path(WORK_DIR).mkdir(parents=True, exist_ok=True)` in Phase 0.
3. **Pass `WORK_DIR` to all functions.** Browser recording helpers, screenshot functions, and frame download code must all receive the slug-scoped directory — never rely on a hardcoded default.
4. **Clean up on completion.** After delivering the final stream URL, remove the work directory: `shutil.rmtree(WORK_DIR, ignore_errors=True)`.
5. **Log the slug.** Print the slug at the start so the user can identify the run: `print(f"Video briefing run: {SLUG}")`.

## Dependencies

**Required:** [VideoDB](https://videodb.io) — handles all media generation (images, video, voice, music), timeline composition, indexing, search, and streaming. Install: `pip install videodb python-dotenv`. Get a free API key at [console.videodb.io](https://console.videodb.io). This skill never calls VideoDB APIs directly; it tells you *what* to produce and *why*.

**Optional tools (use if available, fall back gracefully if not):**
- **Remotion** — for code-rendered data visualizations (animated charts, counters, infographics). Fallback: kinetic text or AI-generated video.
- **Playwright** — Python library for browser recording and screenshots. Navigate to real tweets, articles, reports and record the navigation as video or capture screenshots. See [reference/browser-recording.md](reference/browser-recording.md) for the API patterns. Install: `pip install playwright && playwright install chromium`. Fallback: kinetic text quoting the source with attribution.

## The Vibe

You are the host and presenter of this briefing. You are not narrating over a slideshow — you are a journalist presenting your research. You show your sources, visualize your data, and walk the viewer through your findings. The final video should feel like a produced segment from a modern news or tech channel.

**Never a slideshow.** Every segment should have motion — whether it's an animated chart, a generated video clip, you navigating real websites, or text flying onto screen.

## Pipeline

```
0. Pre-flight       → verify tool availability before scripting
1. Research         → parallel subagents investigate the topic
2. Script           → structure findings into a video script
3. Asset Production → create visuals using the best approach per segment
4. Composition      → arrange everything on a timeline, generate stream
5. Self-Review      → index the draft, critique it, identify fixes
6. Iterate/Deliver  → fix issues and recompose, or deliver final URL
```

### Phase 0: Pre-flight Checks

Before research or scripting, verify which optional tools are available — and **install them if missing**. Do this early so the script can freely use any visual type without last-minute fallbacks.

**Playwright (for `browser_capture`):**

```bash
# Check and install in one shot
python -c "from playwright.sync_api import sync_playwright; print('Playwright OK')" 2>/dev/null \
  || (pip install playwright && playwright install chromium)
```

After running the above, verify it works:

```python
try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
```

If installation fails (e.g., permissions, disk space, unsupported platform), then fall back: do not assign `browser_capture` in Phase 2, use `image_scene` or `kinetic_text` instead. But always **try to install first** — `browser_capture` produces the most authentic footage (real GitHub issues, real news headlines, real tweets on screen).

**Remotion (for `data_viz`):**

```bash
# Check if npx is available (Node.js must be installed)
import shutil
REMOTION_AVAILABLE = shutil.which("npx") is not None
```

If Remotion is unavailable, fall back to `kinetic_text` for key stats or `image_scene` for chart approximations.

### Phase 1: Research

Launch 3-5 parallel subagents to investigate different angles of the topic simultaneously. Each subagent focuses on one research angle and returns structured findings.

See [reference/research.md](reference/research.md) for:
- How to decompose a topic into research angles
- Subagent prompt templates
- How to merge parallel results into a research brief

### Phase 2: Script

Convert the research brief into a video script — a sequence of segments, each with narration text, a visual type, visual direction, and optional data call-outs. The script defines the narrative arc: hook → context → insights → takeaway → close.

See [reference/scriptwriting.md](reference/scriptwriting.md) for:
- Narrative arc structure
- Visual types (`data_viz`, `motion_scene`, `kinetic_text`, `browser_capture`, `image_scene`)
- JSON schema for the script output
- Pacing and audience adaptation

### Phase 3: Asset Production

For each segment, pick the best approach to create its visual asset based on the `visual_type` declared in the script. Mix approaches across segments — never repeat the same approach consecutively.

See [reference/asset-production.md](reference/asset-production.md) for:
- 5 production approaches and when to use each
- AI images, AI video, Remotion, browser capture, kinetic text
- The "agent as host" mindset

Also generate per-segment narration audio and one background music track using the `videodb` skill.

### Phase 4: Composition

Arrange all assets on a multi-track timeline following editorial rules. Generate an instant playable stream URL — this is the v1 draft.

See [reference/composition.md](reference/composition.md) for:
- Structure rules (hook, breathing room, natural close)
- Track layering order
- Pacing rules (segment duration range, rhythm)
- Audio mixing (narration vs music vs SFX)

Present the stream URL to the user: `https://console.videodb.io/player?url={STREAM_URL}`

**Note:** For public sharing, convert console URLs to player URLs: `https://player.videodb.io/watch?v={STREAM_URL}`

### Phase 5: Self-Review (mandatory)

**Always runs at least once.** Upload the draft, index it (time-based scene extraction at 1-second intervals + spoken word indexing), and read back what's actually in the video. Build an intended timeline from your composition data and compare it second-by-second against the scene descriptions. Then critique the result — not just for bugs, but as a director making creative calls.

See [reference/self-review.md](reference/self-review.md) for:
- Scene indexing config (time-based, 1s interval, 2 frames)
- How to build the intended timeline and align it against scene descriptions
- Critique framework (narration, visual alignment, pacing, variety, flow)
- Director pass — creative authority to rearrange, swap, and recompose
- Fix strategy and iteration rules (respects `MAX_ITERATIONS`)

### Phase 6: Iterate or Deliver

Always run the first review. If issues remain and you haven't hit `MAX_ITERATIONS`:
1. Fix broken assets or swap visual types
2. Rearrange segments if the flow needs it — you're the director
3. Recompose the timeline
4. Generate a new stream URL
5. Go back to Phase 5

If clean or at iteration limit: deliver the final stream URL and player URL to the user. Print a segment breakdown with timestamps.

## Quick Reference

| Phase | Owner | Key Reference |
|-------|-------|---------------|
| Research | This skill | [research.md](reference/research.md) |
| Script | This skill | [scriptwriting.md](reference/scriptwriting.md) |
| Asset Production | This skill + videodb | [asset-production.md](reference/asset-production.md) |
| Composition | This skill + videodb | [composition.md](reference/composition.md) |
| Self-Review | This skill + videodb | [self-review.md](reference/self-review.md) |
| Media APIs | videodb skill | (read the videodb skill) |
