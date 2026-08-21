# Medical Explainer Video Agent

**Autonomous medical terminology and procedure explainer** -- give it a medical term or procedure, get a clear, accessible explainer video.

[![Watch Demo](https://img.shields.io/badge/▶_Watch-Demo_Video-blue?style=for-the-badge)](#)

---

## What It Does

This agent autonomously creates explainer videos for medical terms and procedures by:

1. **Researching** the term/procedure from trusted medical sources (Mayo Clinic, NIH, Cleveland Clinic, NHS)
2. **Finding** 2 YouTube explainer clips from medical education channels (Osmosis, Khan Academy, Nucleus Medical Media, etc.)
3. **Capturing** 2 medical illustrations/diagrams from trusted sources
4. **Capturing** 3 key fact screenshots from authoritative medical pages
5. **Writing** 10 voiceover scripts and generating TTS audio
6. **Assembling** everything into a polished 5-track timeline with background music

**Output:** A 3-4 minute video with title card, definition, explainer clips, medical illustrations, key facts/takeaways, and outro.

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

Just give the agent a medical term or procedure:

```
Create a medical explainer video about "angioplasty"
```

```
Make an explainer video for "Type 2 Diabetes"
```

```
Explain the MRI scan procedure as a video
```

The agent will autonomously:
- Research the term from trusted medical sources
- Find and process YouTube explainer videos
- Capture medical illustrations and key fact screenshots
- Write scripts and generate voiceovers
- Build and deliver the final video

**Output location:** `outputs/<term-slug>/output/output.json`

---

## File Structure

```
medical-explainer/
├── SKILL.md              # Main skill definition (agents read this)
├── AGENTS.md             # Detailed workflow instructions
├── README.md             # This file
│
├── assets/               # Shipped defaults
│   ├── medical-bg.jpg    # Clean medical/health background
│   └── medical-music.mp3 # Calm explainer background music
│
├── templates/
│   └── build_video.py    # Timeline builder (reads registry.json)
│
└── outputs/              # Agent-generated runs (one folder per term)
    └── <term-slug>/
        ├── data/         # Metadata (registry.json, scripts.json, research.md)
        ├── assets/       # Physical media (illustrations/, keyfacts/)
        ├── _build/       # Intermediate scratch files
        └── output/       # Final video URL
```

---

## Video Structure

Every medical explainer follows this deterministic structure:

```
[4s]  Title card: "<TERM>\nMEDICAL EXPLAINER"
[~12s] Intro voiceover — definition and why it matters (with illustration visual)

[~8s]  Hook 1 voiceover + [3s] source label + [~5s] muted preview + [25s] explainer clip 1
[~8s]  Hook 2 voiceover + [3s] source label + [~5s] muted preview + [25s] explainer clip 2

[~6s]  Illustration transition: "HOW IT WORKS"
[~15s] Illustration 1 narration + visual
[~15s] Illustration 2 narration + visual

[~6s]  Key facts transition: "KEY FACTS"
[~12s] Key fact 1 narration + screenshot
[~12s] Key fact 2 narration + screenshot
[~12s] Key fact 3 narration + screenshot

[5s]  Outro: "POWERED BY VIDEODB"
```

**Total:** ~3-4 minutes (varies based on TTS durations)

---

## Technical Details

### Timeline Architecture

5-track composition:
1. **bg_track** -- Background image (full duration, Fit.crop)
2. **visual_track** -- Content: images/videos (scale 0.75, Fit.contain, centered)
3. **text_track** -- Section labels (white text on teal box, auto-sized)
4. **audio_track** -- Voiceovers (full volume)
5. **music_track** -- Background music (12% volume, looped)

### Text Styling

- Font: Clear Sans, 80-96pt, white (#FFFFFF)
- Background: Teal box (#0d6e6e, 90% opacity), auto-sized to text length
- Border: White 2px
- Shadow: Black 3px offset
- Auto-wrapping: Lines longer than 35 chars wrap at word boundaries

### Asset Requirements

- **2 YouTube videos** -- Different medical education channels, 2-15 min length, English
- **2 medical illustrations** -- Diagrams or visual explanations from trusted sources
- **3 key fact screenshots** -- From authoritative medical pages (Mayo Clinic, NIH, etc.)
- **10 voiceover scripts** -- Intro, 2 hooks, illustration transition, 2 illustration narrations, key facts transition, 3 key fact narrations

---

## Quality Standards

Every output includes:
- 2 YouTube clips from trusted medical education channels (~25s each, self-contained)
- 2 medical illustrations/diagrams showing the anatomy or process
- 3 key fact screenshots from authoritative sources
- 10 professionally narrated voiceover segments
- Clean visuals with no popups or error pages
- Accurate metadata in registry.json

---

## Key Features

### Trusted Medical Sources
- Navigates directly to Mayo Clinic, NIH, Cleveland Clinic, NHS, WebMD
- Finds YouTube explainers from Osmosis, Khan Academy, Nucleus Medical Media
- Screenshots from peer-reviewed and authoritative sources only

### Patient-Friendly Language
- Scripts use clear, accessible language
- Medical jargon is defined when first used
- Designed for patients, students, and general audiences

### Deterministic Output
- Same structure every time
- Predictable timeline architecture
- Consistent quality standards

---

## Disclaimer

These videos are for **educational purposes only** and do not constitute medical advice. Always consult a qualified healthcare professional for medical decisions.

---

## Community & Support

- **Docs**: [docs.videodb.io](https://docs.videodb.io)
- **Issues**: [GitHub Issues](https://github.com/video-db/agentic-videos/issues)
- **Discord**: [Join community](https://discord.gg/py9P639jGz)
- **Console**: [Get API key](https://console.videodb.io)

---

<p align="center">Made with love by the <a href="https://videodb.io">VideoDB</a> team</p>

---
