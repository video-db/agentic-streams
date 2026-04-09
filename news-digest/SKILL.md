---
name: news-digest-video-agent
description: Create professional multi-source news digest videos. Given a topic, autonomously finds YouTube news clips, tweets, and articles, then assembles a narrated video with voiceovers, background music, and broadcast-style text overlays using VideoDB.
---

# News Digest Video Agent Skill

Use this skill when the user wants to:
- Create a news digest video on any topic
- Turn a breaking news story into a multi-perspective video summary
- Combine YouTube clips, tweets, and articles into a professional broadcast-style video

## Setup (run once)

Before using this skill, ensure these dependencies are installed:

### 1. VideoDB skill & SDK
```bash
# Install VideoDB skill (provides video upload, indexing, search, TTS, timeline editing)
npx skills add video-db/skills

# Install Python SDK
pip install videodb python-dotenv
```

Set your API key (get one free at https://console.videodb.io):
```bash
export VIDEO_DB_API_KEY=your_key_here
```

### 2. Browser use skill
```bash
# Install browser-use skill (provides screenshot, scroll recording, web page capture)
mkdir -p ~/.claude/skills/browser-use
curl -o ~/.claude/skills/browser-use/SKILL.md \
  https://raw.githubusercontent.com/browser-use/browser-use/main/skills/browser-use/SKILL.md
```

Follow the browser-use SKILL.md instructions for any additional setup (e.g., playwright install).

### 3. Verify setup
```python
from dotenv import load_dotenv
load_dotenv(".env")
import videodb
conn = videodb.connect()
print("VideoDB connected:", conn)
```

## Required tools / capabilities

**Strictly required:**
- **VideoDB skill** — video upload, indexing, search, TTS, timeline editing
- **Browser use skill** — ALL internet research, searching, screenshots, scroll recordings
- **File read/write** — manage registry, scripts, and output files
- **Bash / Python** — run the build script

## CRITICAL: No Hallucinated Data

**Every URL, every fact, every piece of content MUST come from actual browser navigation.**

- You MUST use browser-use to visit real websites and find real URLs
- You MUST NOT generate YouTube URLs from memory — go to youtube.com and search
- You MUST NOT create fake tweet images — go to Twitter/X and screenshot real tweets
- You MUST NOT write research from LLM knowledge alone — browse real articles first
- If browser-use is not working, STOP and tell the user. Do NOT proceed with made-up data.

**Browser-use is your internet.** It handles both discovery (searching Google, YouTube, Twitter) AND capture (screenshots, scroll recordings). There is no other search tool.

## Video Structure (fixed, deterministic)

Every news digest follows the same structure:

```
Title card (4s) → Intro voiceover
→ News clip 1 (hook + clip) → News clip 2 (hook + clip) → News clip 3 (hook + clip)
→ Tweet transition → Tweet 1 → Tweet 2 → Tweet 3
→ Article transition → Article 1 → Article 2
→ Outro (5s)

Total: ~3-4 minutes (varies based on generated voiceover lengths)
```

**Note:** Only the title card (4s) and outro (5s) have fixed durations. Everything else is dynamically sized based on the actual voiceover durations returned by VideoDB TTS. The `build_video.py` template reads exact durations from `registry.json` — nothing is hardcoded.

## Inputs

The only required input is:
- **topic** — e.g., "iran war", "claude source code leak", "us tariffs china"

Optional:
- Custom background image (default: shipped `assets/news-bg.jpg`)
- Custom background music (default: shipped `assets/news-music.mp3`)

## Workflow

### Step 1: Research the topic (USE BROWSER-USE)
Use browser-use to actually browse the internet and gather real information:

1. Open Google → search `<topic> news coverage 2024/2025/2026`
2. Visit 2-3 top results from trusted news sites
3. Read the actual article content
4. Extract key facts: what happened, who's involved, timeline, impact

**Do NOT write research from LLM memory.** Every fact in `research.md` must trace back to a real URL you visited.

Save to `outputs/<topic-slug>/data/research.md` — include source URLs for every claim.

### Step 2: Find 3 YouTube news videos (USE BROWSER-USE)
Use browser-use to navigate to YouTube and find real videos:

1. Open `youtube.com` → search `<topic> BBC News`
2. Click on a real result → copy the URL from the browser
3. Repeat for 2 more channels

**Preferred YouTube channels to search:**
- Al Jazeera English
- BBC News
- CNN
- Reuters
- CNBC
- DW News
- Sky News
- PBS NewsHour

**Search strategy:** Go to youtube.com and search for each channel + topic. Do NOT construct URLs from memory.

**Criteria:**
- 3 different news sources for diverse perspectives
- Recent and relevant to the topic
- 2-15 minutes long, English language
- Each should present a distinct "take" or angle
- **Every URL must come from actually visiting youtube.com** — not from LLM knowledge

Save URLs to `outputs/<topic-slug>/data/videos.json`

### Step 3: Process YouTube videos with VideoDB
For each of the 3 videos:
1. Upload to VideoDB: `coll.upload(url=youtube_url)`
2. Index spoken words: `video.index_spoken_words(force=True)`
3. Semantic search for the best ~25 second clip: `video.search(query)`
4. Select a clip that is self-contained, ends at a natural sentence, and shows the channel's perspective

Update `registry.json` with video IDs, clip start times, and durations.

### Step 4: Capture 3 tweet screenshots (USE BROWSER-USE)
Use browser-use to visit X.com profiles of key figures and find real tweets:

1. Visit public profiles directly: `x.com/<handle>` (works without login in headless mode)
2. Find 3 tweets from notable people with different perspectives
3. Screenshot each tweet via the embed endpoint: `platform.twitter.com/embed/Tweet.html?id=<ID>`

**Note:** X.com **search** (`x.com/search?q=...`) requires login and won't work. Stick to visiting profiles directly. See `AGENTS.md` Step 4 for the full workflow.

**Do NOT create fake/placeholder tweet images.** Every screenshot must be of a real tweet from a real browser session.

Save to `outputs/<topic-slug>/assets/tweets/tweet_1.png`, `tweet_2.png`, `tweet_3.png`
Upload each to VideoDB and update `data/registry.json`.

### Step 5: Capture 2 article assets (USE BROWSER-USE)
Use browser-use to find and capture real articles:

1. Open Google → search `<topic> site:apnews.com` (or other preferred sites)
2. Visit the actual article in the browser
3. Screenshot the key section (chart, data, key quote)
4. Record a scroll video (~8-13 seconds) by scrolling through the article

**Preferred article sources (search these first):**
- AP News (apnews.com)
- Council on Foreign Relations (cfr.org)
- Reuters (reuters.com)
- BBC News (bbc.com/news)
- The Guardian (theguardian.com)
- NPR (npr.org)

**Do NOT create fake scroll videos with ffmpeg from static images.** The scroll must be a real browser recording of a real article.

**Criteria:**
- Article 1: economic/domestic impact angle
- Article 2: historical context / geopolitical analysis angle

Save to `outputs/<topic-slug>/assets/articles/`
Update `data/registry.json`.

### Step 6: Write scripts & generate voiceovers
Write **11 voiceover scripts** based on research and collected sources:

| Script | Guideline | Content |
|--------|-----------|---------|
| intro | 2-3 sentences | Quick hook — what happened, why it matters |
| hook_1 | 1-2 sentences | Introduce news source 1, what they report |
| hook_2 | 1-2 sentences | Introduce news source 2, what they report |
| hook_3 | 1-2 sentences | Introduce news source 3, what they report |
| tweet_transition | 1-2 sentences | Bridge to social media reactions |
| tweet_1 | 2-3 sentences | Narrate tweet 1 content and context |
| tweet_2 | 2-3 sentences | Narrate tweet 2 content and context |
| tweet_3 | 2-3 sentences | Narrate tweet 3 content and context |
| article_transition | 1 sentence | Bridge to deep analysis section |
| article_1 | 3-4 sentences | Summarize article 1 key findings |
| article_2 | 3-4 sentences | Summarize article 2 key findings |

**Tone:** Professional broadcast news narrator. Concise, factual, no speculation.

**Duration note:** Do NOT target specific second counts. Write natural scripts following the sentence guidelines above. Generate via TTS, then record the **exact duration** returned by `audio.length` into `registry.json`. The build template handles all timing dynamically.

Generate each using VideoDB TTS: `coll.generate_voice(text=script, voice_name="Default")`

Save scripts to `data/scripts.json`. Update `data/registry.json` with audio IDs and **exact durations** (from `audio.length`).

### Step 7: Build the video
Run the build template:
```bash
python templates/build_video.py outputs/<topic-slug>/data/registry.json
```

This assembles the 5-track timeline and generates the final stream URL.
Output saved to `outputs/<topic-slug>/output/output.json`.

## Per-run folder structure

All runs go inside `outputs/` within the skill directory. **Never** create run folders at the skill root. **Never** place loose files at the topic folder root — everything goes in a subfolder.

```
agentic-video-creator/news-digest/
├── SKILL.md
├── AGENTS.md
├── README.md
├── assets/                             # Shipped defaults (bg, music)
├── templates/
└── outputs/                            # ALL runs go here
    └── <topic-slug>/                   # e.g., "epstein-files"
        │
        ├── assets/                     # Physical files (viewable media)
        │   ├── tweets/                 #   Tweet screenshot PNGs
        │   │   ├── tweet_1.png
        │   │   ├── tweet_2.png
        │   │   └── tweet_3.png
        │   └── articles/               #   Article scroll videos + screenshots
        │       ├── article_1_scroll.mp4
        │       ├── article_1_screenshot.png
        │       ├── article_2_scroll.mp4
        │       └── article_2_screenshot.png
        │
        ├── data/                       # Digital metadata (IDs, scripts, research)
        │   ├── research.md             #   Topic research brief
        │   ├── scripts.json            #   All 11 voiceover scripts
        │   ├── registry.json           #   All VideoDB asset IDs + durations
        │   └── videos.json             #   YouTube URLs + clip metadata
        │
        ├── _build/                     # Intermediate/working files (agent scratch)
        │   └── ...                     #   Upload results, processing logs, etc.
        │
        └── output/                     # Final deliverables
            └── output.json             #   Stream URL, player URL, duration
```

**Rules:**
- `assets/` = physical media files you can open and preview
- `data/` = metadata, IDs, scripts — everything VideoDB and the build template need
- `_build/` = intermediate files created during processing (prefixed with `_` to signal "ignore")
- `output/` = the final video URL and metadata
- **Zero files at the topic root** — everything in a subfolder

## Shipped assets

Default background and music are in `assets/`:
- `assets/news-bg.jpg` — Professional dark news background
- `assets/news-music.mp3` — News-style background music (125s, looped at 15% volume)

Users can replace these with their own files. Upload to VideoDB and update registry.

## Deliverables

A successful run produces:
- `output/output.json` with playable stream URL
- All physical media preserved in `assets/`
- Full `data/registry.json` for reproducibility

## Reference

See `outputs/` folder for complete agent-generated examples with full registry structure and asset organization.

**Example output:** [Iran War 2026 Video](https://player.videodb.io/watch?v=https://play.videodb.io/v1/43570285-1d6e-4548-86e6-294201d2418f.m3u8)

## Reference docs

- `README.md` — Overview, setup, and usage guide
- `AGENTS.md` — Detailed agent workflow, error handling, quality criteria
- `templates/build_video.py` — Timeline builder (reads registry.json)
