# News Digest Video Agent

**Autonomous multi-source news video creator** — give it a topic, get a professional 3-4 minute broadcast-style video.

[![Watch Demo](https://img.shields.io/badge/▶_Watch-Demo_Video-blue?style=for-the-badge)](https://player.videodb.io/watch?v=https://play.videodb.io/v1/43570285-1d6e-4548-86e6-294201d2418f.m3u8)

---

## What It Does

This skill autonomously creates professional news digest videos from any topic by:

1. **Researching** the topic via real web sources (BBC, AP News, NBC, Guardian)
2. **Finding** 3 YouTube news clips from diverse sources (Al Jazeera, BBC, CNN, etc.)
3. **Capturing** 3 tweet screenshots showing different perspectives
4. **Recording** 2 article scroll videos with key screenshots
5. **Writing** 11 voiceover scripts and generating TTS audio
6. **Assembling** everything into a polished 5-track timeline with background music

**Output:** A 3-4 minute video with title card, intro, news clips, social media reactions, deep analysis, and outro.

---

## Quick Start

### Prerequisites

1. **VideoDB SDK:**
   ```bash
   pip install videodb python-dotenv
   ```

2. **API Key** (get free at [console.videodb.io](https://console.videodb.io)):
   ```bash
   export VIDEO_DB_API_KEY=your_key_here
   ```

3. **Browser-use skill** (for web research):
   ```bash
   mkdir -p ~/.claude/skills/browser-use
   curl -o ~/.claude/skills/browser-use/SKILL.md \
     https://raw.githubusercontent.com/browser-use/browser-use/main/skills/browser-use/SKILL.md
   ```

### Usage

Just give the agent a news topic:

```
Create a news digest video about the Iran-US conflict
```

```
Make a news digest covering the recent tech regulation summit
```

The agent will autonomously:
- Research the topic from trusted sources
- Find and process YouTube videos
- Capture tweets and article assets
- Write scripts and generate voiceovers
- Build and deliver the final video

**Output location:** `outputs/<topic-slug>/output/output.json`

---

## File Structure

```
news-digest/
├── SKILL.md              # Main skill definition (agents read this)
├── AGENTS.md             # Detailed workflow instructions
├── README.md             # This file
│
├── assets/               # Shipped defaults
│   ├── news-bg.jpg       # Professional dark news background
│   └── news-music.mp3    # Background music (125s, 15% volume)
│
├── templates/
│   └── build_video.py    # Timeline builder (reads registry.json)
│
└── outputs/              # Agent-generated runs (one folder per topic)
    └── <topic-slug>/
        ├── data/         # Metadata (registry.json, scripts.json, research.md)
        ├── assets/       # Physical media (tweets/, articles/)
        ├── _build/       # Intermediate scratch files
        └── output/       # Final video URL
```

---

## Video Structure

Every news digest follows this deterministic structure:

```
[4s]  Title card: "<TOPIC>\nNEWS DIGEST"
[~10s] Intro voiceover (with first tweet visual)

[~8s]  Hook 1 voiceover + [3s] news source label + [~5s] muted preview + [25s] news clip 1
[~8s]  Hook 2 voiceover + [3s] news source label + [~5s] muted preview + [25s] news clip 2
[~8s]  Hook 3 voiceover + [3s] news source label + [~5s] muted preview + [25s] news clip 3

[~8s]  Tweet transition: "SOCIAL MEDIA\nREACTIONS"
[~12s] Tweet 1 narration + visual
[~12s] Tweet 2 narration + visual
[~12s] Tweet 3 narration + visual

[~6s]  Article transition: "DEEP ANALYSIS"
[~17s] Article 1 narration (scroll video + key screenshot)
[~17s] Article 2 narration (scroll video + key screenshot)

[5s]  Outro: "POWERED BY VIDEODB"
```

**Total:** ~3-4 minutes (varies based on TTS durations)

---

## Technical Details

### Timeline Architecture

5-track composition:
1. **bg_track** — Background image (full duration, Fit.crop)
2. **visual_track** — Content: images/videos (scale 0.75, Fit.contain, centered)
3. **text_track** — Section labels (white text on blue box, auto-sized)
4. **audio_track** — Voiceovers (full volume)
5. **music_track** — Background music (15% volume, looped)

### Text Styling

"Option C" design:
- Font: Clear Sans, 80-96pt, white (#FFFFFF)
- Background: Blue box (#1a3a5c, 90% opacity), auto-sized to text length
- Border: White 2px
- Shadow: Black 3px offset
- **Auto-wrapping:** Lines longer than 35 chars wrap at word boundaries

### Asset Requirements

- **3 YouTube videos** — Different news sources, 2-15 min length, English
- **3 tweet screenshots** — Different perspectives (leader, critic, supporter)
- **2 article assets** — One economic/impact, one historical/context
- **11 voiceover scripts** — Intro, 3 hooks, tweet transition, 3 tweet narrations, article transition, 2 article summaries

---

## Quality Standards

Every output includes:
- 3 YouTube clips from different news sources (~25s each, self-contained)
- 3 tweet screenshots from notable accounts showing diverse perspectives
- 2 articles from trusted sources with scroll videos and key screenshots
- 11 professionally narrated voiceover segments
- Clean visuals with no popups or error pages
- Accurate metadata in registry.json

---

## Key Features

### Real Web Research
- Navigates directly to trusted news sources (BBC, AP News, NBC, Guardian)
- Finds YouTube videos from major news channels
- Captures tweets from public X.com profiles
- Verifies article content before capturing assets

### Deterministic Output
- Same structure every time
- Predictable timeline architecture
- Consistent quality standards

### Professional Quality
- Broadcast-style text overlays with auto-sizing
- Clean typography and smooth transitions
- Background music at optimal volume
- Natural voiceover pacing

---

## Example Output

**Iran War 2026** — Multi-source analysis with Al Jazeera, BBC, CNN clips:  
[▶ Watch Video](https://player.videodb.io/watch?v=https://play.videodb.io/v1/43570285-1d6e-4548-86e6-294201d2418f.m3u8)

For complete registry structure and asset organization, see agent-generated runs in `outputs/` folder.

---

## Community & Support

- **Docs**: [docs.videodb.io](https://docs.videodb.io)
- **Issues**: [GitHub Issues](https://github.com/video-db/agentic-video-creator/issues)
- **Discord**: [Join community](https://discord.gg/py9P639jGz)
- **Console**: [Get API key](https://console.videodb.io)

---

<p align="center">Made with ❤️ by the <a href="https://videodb.io">VideoDB</a> team</p>

---
