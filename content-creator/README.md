# Content Creator — Self-Reviewing Video Agent

**Autonomous video briefing agent that reviews its own output using VideoDB's See + Understand capabilities** — research any topic, produce a broadcast-quality video, then verify visual-narration alignment frame by frame before delivering.

[![Watch Demo](https://img.shields.io/badge/▶_Watch-Demo_Video-blue?style=for-the-badge)](https://player.videodb.io/watch?v=https://play.videodb.io/v1/a43d5463-a39d-4aac-994f-abdfb5b3bf2d.m3u8)

---

## What Makes This Different

Most video agents produce a video and hand it over. This one **watches its own rough cut**.

After composing the first draft, the agent uploads the rendered stream back into VideoDB and uses two core capabilities to inspect it:

**See** — Extract scenes at 1-second intervals with frame images. The agent downloads and looks at actual frames from the rendered video, checking whether each second shows the intended visual (a chart, a browser capture, kinetic text, an AI-generated clip).

**Understand** — Index scenes with AI-powered descriptions and index spoken words for a full transcript. The agent reads back what the AI sees at every timestamp and what was actually spoken, then compares both against the original script.

**Act** — Build a mismatch report, fix broken assets, swap visual types, adjust timing, recompose the timeline, and generate a new stream. Repeat up to `MAX_ITERATIONS` times until the output passes review.

```
Research → Script → Produce Assets → Compose Timeline → See the Draft → Understand What's There → Fix & Recompose
                                                         ↑_______________________________________________|
                                                                    self-review loop
```

This is the same See + Understand pipeline you'd use for video search, monitoring, or content moderation — applied to quality assurance on the agent's own output.

---

## The Self-Review Loop

The agent treats its own video exactly like any other video in VideoDB:

### 1. Upload the draft stream
```python
review_video = coll.upload(url=stream_url)
```

### 2. Index spoken words (what was said)
```python
review_video.index_spoken_words()
transcript = review_video.get_transcript()
```

### 3. Extract scenes with frames (what's on screen)
```python
scene_collection = review_video.extract_scenes(
    extraction_type=SceneExtractionType.time_based,
    extraction_config={"time": 1, "select_frames": ["first", "last"]},
)
```

### 4. Index scenes with AI descriptions
```python
scene_index_id = review_video.index_scenes(
    extraction_type=SceneExtractionType.time_based,
    extraction_config={"time": 1, "select_frames": ["first", "last"]},
    prompt="Describe the visual content: type, what it shows, visible text, motion vs static.",
)
scene_records = review_video.get_scene_index(scene_index_id)
```

### 5. Compare intended vs actual
The agent builds a timeline of what *should* be at each second (from the script and composition data) and aligns it against what *actually* appears (from scene descriptions and frame images). Mismatches get flagged:

| Intended | Actual | Verdict |
|----------|--------|---------|
| `browser_capture` — Reddit top posts | Error/block page | **Mismatch** — regenerate as AI image |
| `kinetic_text` — "73% stat" | Large bold "73%" on screen | Match |
| `motion_scene` — drone shot | Static photo, no motion | **Mismatch** — swap visual type |

### 6. Fix and recompose
Regenerate only what's broken. Recompose the timeline. Generate a new stream. Review again.

---

## How It Works (Full Pipeline)

```
Phase 0: Pre-flight    → Verify tools (Playwright, VideoDB SDK)
Phase 1: Research      → Parallel subagents investigate different angles
Phase 2: Script        → Narrative arc: hook → context → insights → takeaway → close
Phase 3: Asset Production → AI video, AI images, browser captures, kinetic text, voiceover, music
Phase 4: Composition   → Multi-track timeline with narration, visuals, callouts, music
Phase 5: Self-Review   → Upload draft → See (frames) → Understand (descriptions + transcript) → Critique
Phase 6: Iterate       → Fix issues → Recompose → Review again → Deliver
```

### Visual variety across segments
The agent mixes 5 production approaches and never repeats the same type consecutively:

| Approach | Use Case |
|----------|----------|
| **AI-Generated Video** | Hooks, transitions, atmospheric b-roll |
| **AI-Generated Images** | Abstract concepts, mood backgrounds |
| **Browser Capture** | Citing sources, showing real web content |
| **Kinetic Text** | Key stats, quotes, punchy declarations |
| **Data Viz (Remotion)** | Animated charts, counters, comparisons |

---

## Quick Start

### Prerequisites

1. **VideoDB API Key** (get free at [console.videodb.io](https://console.videodb.io)):
   ```bash
   export VIDEO_DB_API_KEY=your_key_here
   ```

2. **VideoDB SDK:**
   ```bash
   pip install videodb python-dotenv
   ```

3. **Playwright** (optional, for browser captures):
   ```bash
   pip install playwright && playwright install chromium
   ```

### Usage

Give the agent a topic:

```
Create a video briefing about "r/ClaudeAI top posts this week"
```

```
Make a video report on "the state of AI coding assistants in 2026"
```

The agent autonomously researches, scripts, produces, composes, reviews, and delivers a playable stream URL.

---

## File Structure

```
content-creator/
├── README.md                         # This file
├── SKILL.md                          # Main skill definition (agents read this)
└── reference/
    ├── research.md                   # How to decompose topics and run parallel research
    ├── scriptwriting.md              # Narrative arc, visual types, script schema
    ├── asset-production.md           # 5 production approaches and when to use each
    ├── browser-recording.md          # Playwright patterns for web capture
    ├── composition.md                # Timeline architecture, pacing, audio mixing
    └── self-review.md                # The See + Understand review loop
```

---

## Example Output

**r/ClaudeAI Weekly Recap** — Top posts, memes, drama, and builds from the Claude subreddit:
[▶ Watch Video](https://player.videodb.io/watch?v=https://play.videodb.io/v1/a43d5463-a39d-4aac-994f-abdfb5b3bf2d.m3u8)

```
00:00 - 00:16  Hook (motion_scene) — "11,400 upvotes for teaching Claude to talk like a caveman"
00:16 - 00:29  Context (image) — Reddit-style feed showing top posts
00:29 - 00:49  The Memes (kinetic_text) — "14 limit tracker posts today, 6 in the last hour"
00:49 - 01:12  The Drama (image) — Claude Code 512K line source leak
01:12 - 01:40  The Builds (image) — Windows 98 rebuild, job search system, wholesome friendship post
01:40 - 01:55  Takeaway (kinetic_text) — "Roast it at noon. Build with it by five. Love letter by midnight."
01:55 - 01:59  Outro
```

---

## Why VideoDB

This agent demonstrates VideoDB as infrastructure for the full video lifecycle — not just assembly, but **understanding**:

| Capability | How It's Used |
|------------|---------------|
| **Generate** (images, video, voice, music) | Produce all visual and audio assets from text prompts |
| **Compose** (multi-track timeline) | Arrange visuals, narration, callouts, and music on layered tracks |
| **See** (scene extraction + frames) | Extract frame images from the rendered draft at every second |
| **Understand** (scene indexing + spoken word indexing) | Get AI descriptions of what's on screen and transcribe what was said |
| **Stream** (instant playback) | Deliver a playable HLS URL immediately after composition |

The self-review loop closes the gap between "I told the system to put a chart at t=30" and "there's actually a chart at t=30." That gap is where most automated video pipelines silently fail.

---

## Community & Support

- **Docs**: [docs.videodb.io](https://docs.videodb.io)
- **Issues**: [GitHub Issues](https://github.com/video-db/agentic-videos/issues)
- **Discord**: [Join community](https://discord.gg/py9P639jGz)
- **Console**: [Get API key](https://console.videodb.io)

---

<p align="center">Made with ❤️ by the <a href="https://videodb.io">VideoDB</a> team</p>
