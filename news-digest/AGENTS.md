# News Digest Video — Agent Instructions

Detailed workflow for agents building news digest videos. Read `SKILL.md` first for the overview.

## CRITICAL RULE: No Hallucinated Data

**You MUST use browser-use for ALL internet research.** This means:
- Every YouTube URL must come from navigating to youtube.com and searching
- Every tweet screenshot must come from navigating to Twitter/X
- Every article must come from navigating to the actual news site
- Research facts must come from reading real web pages, not LLM memory

**If browser-use is not available or not working, STOP immediately and tell the user.** Do NOT proceed by generating URLs from memory or creating placeholder images. The entire value of this video is real, sourced content.

## Prerequisites

- VideoDB SDK installed: `pip install videodb python-dotenv`
- `VIDEO_DB_API_KEY` set in environment or `.env` file
- **Browser use skill installed and working** — this is your only way to access the internet
- Read `~/.claude/skills/browser-use/SKILL.md` before starting
- **Note:** Chrome `--profile` flag requires Google Chrome (not Chromium). If you need authenticated sessions, install Chrome first.

## CRITICAL: Close Popups/Ads Before Screenshots

**Before taking ANY screenshot or starting ANY scroll recording, you MUST close all popups, overlays, and ads.**

Common overlays to close:
- Cookie consent banners
- Newsletter signup popups
- Donation prompts (especially Guardian, Wikipedia)
- "Support us" overlays
- Privacy policy notices
- Mobile app download prompts

**How to close overlays:**

1. **Wait for page to fully load:** `sleep 2` after navigation
2. **Identify overlay elements:** `browser-use state` to see clickable elements
3. **Close via clicking:** `browser-use click <close-button-index>`
4. **Or hide via JavaScript:**
   ```bash
   browser-use eval "document.querySelectorAll('[class*=\"modal\"], [class*=\"popup\"], [class*=\"overlay\"]').forEach(el => el.remove())"
   ```

**Example workflow:**
```bash
# Navigate to article
browser-use open "https://www.theguardian.com/us-news/2026/..."

# Wait for popups to appear
sleep 2

# Remove overlays
browser-use eval "document.querySelectorAll('[class*=\"Support\"], [id*=\"banner\"]').forEach(el => el.remove())"

# Now screenshot/scroll
browser-use screenshot article_screenshot.png
```

**Quality check:** Before saving, visually verify no overlays are visible in the captured image/video.

## Step-by-Step Workflow

### Step 1: Research Topic (BROWSER-USE REQUIRED)

**Goal:** Build enough context to write accurate voiceover scripts later.

**You MUST use browser-use to do real web research.** Do NOT write this from LLM memory.

**CRITICAL: Do NOT use search engines (Google, DuckDuckGo, Bing).** They show CAPTCHAs in headless mode.

**Instead, navigate directly to news site search pages:**

1. **BBC search:** `browser-use open "https://www.bbc.com/search?q=<topic>"`
2. **AP News hub or search:** `browser-use open "https://apnews.com/hub/<topic-slug>"` or `"https://apnews.com/search?q=<topic>"`
3. **NBC News search:** `browser-use open "https://www.nbcnews.com/search/?q=<topic>"`
4. **The Guardian:** `browser-use open "https://www.theguardian.com/us-news"` (then search or browse)

**Navigate to articles:**
- Use `browser-use state` to see clickable element indices
- Use `browser-use click <index>` to navigate to articles
- **Do NOT hardcode BBC article URLs** — they often land on generic pages. Always navigate through BBC search results.

**Extract article text:**
```bash
# Get clean text (first 5000 chars)
browser-use eval "document.querySelector('article')?.innerText?.substring(0, 5000)"

# For longer articles, paginate
browser-use eval "document.querySelector('article')?.innerText?.substring(5000, 10000)"
browser-use eval "document.querySelector('article')?.innerText?.substring(10000, 15000)"
```

**Visit 2-3 trusted sources** and extract key facts.

Write a concise brief (10-20 lines) to `outputs/<topic-slug>/data/research.md`. Include:
- What happened (key events in chronological order)
- Who is involved (countries, leaders, organizations)
- Why it matters (impact, stakes)
- Current status
- **Source URLs for every claim** (the actual pages you visited)

This file is your reference for all script writing later. Every fact must trace to a real URL.

---

### Step 2: Find 3 YouTube News Videos (BROWSER-USE REQUIRED)

**Goal:** Find 3 real videos from different trusted sources showing diverse perspectives.

**You MUST use browser-use to navigate to YouTube and search.** Do NOT construct YouTube URLs from memory.

**How to find videos:**

YouTube works fine in headless mode (no CAPTCHA). Use direct YouTube search:

```bash
browser-use open "https://www.youtube.com/results?search_query=<topic>+BBC+News+2026"
```

**Extract video URLs:**
```bash
browser-use eval "Array.from(document.querySelectorAll('a#video-title')).slice(0, 5).map(a => ({title: a.title, href: a.href}))"
```

This returns an array of `{title, href}` objects with real YouTube URLs.

**Preferred channels to search:**
- Al Jazeera English, BBC News, CNN, Reuters, CNBC, DW News, Sky News, PBS NewsHour

**If a channel has no results:** Try the next channel. Keep going until you have 3 real URLs.

**Selection criteria:**
- 3 different news organizations (never 2 from the same source)
- Each presents a distinct perspective or angle
- Video is 2-15 minutes long (enough content to find a good 25s clip)
- English language
- Recent and directly about the topic
- **The URL must come from YouTube search results you actually saw in the browser**

Save to `outputs/<topic-slug>/data/videos.json`:
```json
{
  "video_1": { "url": "https://youtube.com/watch?v=...", "source": "Al Jazeera", "title": "..." },
  "video_2": { "url": "https://youtube.com/watch?v=...", "source": "BBC News", "title": "..." },
  "video_3": { "url": "https://youtube.com/watch?v=...", "source": "CNN", "title": "..." }
}
```

---

### Step 3: Process YouTube Videos with VideoDB

**Goal:** Upload, index, and find the best ~25 second clip from each video.

For each video:

```python
from dotenv import load_dotenv
load_dotenv(".env")
import videodb
from videodb import SearchType

conn = videodb.connect()
coll = conn.get_collection()

# Upload
video = coll.upload(url="https://youtube.com/watch?v=...")

# Index transcript
video.index_spoken_words(force=True)

# Search for best segment — KEEP QUERIES SHORT (3-5 words)
# Long queries often return "No results found"
# Good: "climate summit agreement", "tech regulation policy"
# Bad: "climate summit leaders powerful nations agreement emissions targets"
results = video.search("climate summit agreement", search_type=SearchType.semantic)
shots = results.get_shots()

# Pick the best shot, trim to ~25 seconds
shot = shots[0]
clip_start = float(shot.start)
clip_duration = min(float(shot.end) - float(shot.start), 25.0)
```

**Clip selection criteria:**
- ~25 seconds (20-30s acceptable)
- Starts and ends at natural sentence boundaries
- Self-contained (makes sense without surrounding context)
- Shows the source's unique perspective/angle
- No dead air, no ads, no off-topic segments

**Error handling:**
- If YouTube upload fails with "Download failed": try an alternate URL from the same source. Some YouTube videos have download restrictions. Try 2-3 different videos per channel before giving up on that channel.
- If a channel's videos consistently fail: swap to another preferred channel (e.g., if CNN fails, try CNBC or DW News)
- **If semantic search returns "No results found":** Your query is too long or specific. Retry with a shorter, more generic query (3-5 words). Example: change "climate summit leaders powerful nations emissions targets" → "climate summit agreement"
- If clip is too short (<15s): widen the selection or try a different search query
- **CRITICAL:** Do NOT skip news clips entirely. The 3 YouTube clips are the core of the video. Keep trying different URLs until you have 3 working clips.

Update `registry.json` with the video_id, clip_start, clip_duration, and label.

---

### Step 4: Capture 3 Tweet Screenshots

**Goal:** Find and screenshot 3 high-profile tweets showing different reactions.

**CRITICAL UPDATE:** X.com **public profiles work perfectly** in headless mode without login. Only the **search feature** requires login.

**What works:**
- ✅ Profile pages: `x.com/ZelenskyyUa`, `x.com/elonmusk`, etc. (full access, no login)
- ✅ Embed endpoint: `platform.twitter.com/embed/Tweet.html?id=<ID>` (for clean screenshots)
- ❌ Search pages: `x.com/search?q=...` (requires login, doesn't work in headless mode)

**Recommended workflow (fastest):**

#### Step A: Identify relevant X handles from research

From your research step, identify 3-5 key figures related to your topic. Examples:
- Government officials/leaders (presidents, foreign ministers, press secretaries)
- Key organizations (official accounts like @WhiteHouse, @UN, @NATO)
- Prominent journalists covering the story
- Affected parties or their representatives

#### Step B: Visit X.com profiles directly

```bash
browser-use open "https://x.com/ZelenskyyUa"
```

The profile loads fully without login. You can see all recent tweets.

#### Step C: Extract tweet IDs from the profile

```bash
browser-use eval "Array.from(document.querySelectorAll('a[href*=\"/status/\"]')).slice(0, 10).map(a => ({text: a.closest('article')?.innerText?.substring(0, 200) || 'No preview', href: a.href}))"
```

This returns the 10 most recent tweets with preview text and full URLs.

Pick 3 tweets that show different perspectives on your topic.

#### Step D: Screenshot via Twitter embed endpoint

For each tweet ID (extract from URL like `x.com/user/status/1234567890`):

```bash
browser-use open "https://platform.twitter.com/embed/Tweet.html?id=1234567890"
sleep 1  # wait for embed to load
browser-use screenshot /tmp/tweet_raw.png
```

**Crop with PIL** to remove excess whitespace:

```python
from PIL import Image
img = Image.open("/tmp/tweet_raw.png")
cropped = img.crop((0, 0, 560, 480))  # Adjust as needed
cropped.save("outputs/<topic-slug>/assets/tweets/tweet_1.png")
```

#### Fallback: NBC News articles (if profile approach fails)

If you can't find relevant handles or profiles are private, fall back to extracting tweet links from NBC News articles:

```bash
browser-use open "https://www.nbcnews.com/search/?q=<topic>"
# Click into articles and extract x.com links
browser-use eval "Array.from(document.querySelectorAll('a')).filter(a => a.href.includes('x.com/') && a.href.includes('/status/')).map(a => a.href)"
```

**Note:** Most NBC articles don't embed tweet links (hit rate ~10%), so this is less reliable than visiting profiles directly.

**Find 3 tweets from different perspectives:**
- A key political leader or official directly involved
- A critic or analyst offering an opposing view
- A supporter/defender offering a contrasting take

**Quality criteria:**
- From verified/notable accounts
- Directly about the topic (not tangential)
- Different viewpoints (avoid 3 tweets saying the same thing)
- Clean screenshot (no browser chrome, no other tweets visible)
- **CLOSE ALL POPUPS before screenshotting** (see popup section above)

Save as:
```
outputs/<topic-slug>/assets/tweets/tweet_1.png
outputs/<topic-slug>/assets/tweets/tweet_2.png
outputs/<topic-slug>/assets/tweets/tweet_3.png
```

Upload each to VideoDB:
```python
img = coll.upload(file_path="outputs/<topic-slug>/assets/tweets/tweet_1.png")
# Record img.id in data/registry.json
```

---

### Step 5: Capture 2 Article Assets

**Goal:** Find 2 trusted articles and capture scroll videos + key screenshots.

**CRITICAL:** Do NOT use search engines (Google, DuckDuckGo, Bing). They show CAPTCHAs.

**Navigate directly to news site search pages:**

```bash
# AP News
browser-use open "https://apnews.com/search?q=<topic>"

# BBC News  
browser-use open "https://www.bbc.com/search?q=<topic>"

# The Guardian
browser-use open "https://www.theguardian.com/us-news"  # or /world

# NBC News
browser-use open "https://www.nbcnews.com/search/?q=<topic>"

# Reuters
browser-use open "https://www.reuters.com/site-search/?query=<topic>"

# NPR
browser-use open "https://www.npr.org/search?query=<topic>"
```

**Article selection:**
- Article 1: Economic/domestic impact angle (how does this affect markets, people, daily life?)
- Article 2: Historical/geopolitical context (how did we get here? what's the broader picture?)

For each article, **use the browser-use skill**:

#### 1. Record scroll video (~10 seconds):

**CRITICAL: `browser-use` Python doesn't support async screen recording.** Use frame capture + ffmpeg instead:

```bash
# Navigate and wait for page load
browser-use open "https://apnews.com/article/..."
sleep 2

# CLOSE ALL POPUPS FIRST (see popup section above)
browser-use eval "document.querySelectorAll('[class*=\"modal\"], [class*=\"banner\"]').forEach(el => el.remove())"

# VERIFY PAGE CONTENT IS RELEVANT
# Before capturing, check that the article actually loaded (not "404" or "article not found")
browser-use eval "document.body.innerText.substring(0, 500)"
# Review output: Does it match your topic? Is it article content or an error page?
# If you see "not found", "404", or generic news listings → navigate to a different article

# Scroll to top
browser-use eval "window.scrollTo(0, 0)"

# Capture 10 frames while scrolling
for i in $(seq 0 9); do
    browser-use screenshot "/tmp/scroll_frame_${i}.png"
    browser-use scroll down --amount 300
    sleep 0.3
done

# Stitch into video with ffmpeg
ffmpeg -y -framerate 1 -i /tmp/scroll_frame_%d.png \
  -vf "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2" \
  -c:v libx264 -pix_fmt yuv420p -r 30 \
  outputs/<topic-slug>/assets/articles/article_1_scroll.mp4
```

This creates a 10-second video (10 frames at 1fps, encoded at 30fps).

#### 2. Capture key screenshot:

Navigate to the most impactful section (chart, key quote, headline), **close all popups**, then screenshot:

```bash
browser-use screenshot outputs/<topic-slug>/assets/articles/article_1_screenshot.png
```

Save to:
```
outputs/<topic-slug>/assets/articles/article_1_scroll.mp4
outputs/<topic-slug>/assets/articles/article_1_screenshot.png
outputs/<topic-slug>/assets/articles/article_2_scroll.mp4
outputs/<topic-slug>/assets/articles/article_2_screenshot.png
```

Upload all 4 files to VideoDB and update `registry.json`.

---

### Step 6: Write Scripts & Generate Voiceovers

**Goal:** Write 11 voiceover scripts and generate TTS audio for each.

Use `research.md` and your collected sources as context.

**Script writing guidelines:**
- Professional broadcast news tone
- Concise and factual — no speculation, no opinion
- Intro: 2-3 sentences, sets up the whole story as a quick hook
- Hooks: 1-2 sentences, introduce what the news source reports
- Tweet narrations: Read the tweet content with brief context
- Article summaries: Key findings in 3-4 sentences
- Transitions: Short bridge sentences connecting sections

**Generate each voiceover:**
```python
voice = coll.generate_voice(text=script, voice_name="Default")
# IMPORTANT: voice.length returns a STRING, not a float
# Cast to float before using in calculations or formatting
audio_id = voice.id
exact_duration = float(voice.length)  # This is the ground truth
```

Save all scripts to `outputs/<topic-slug>/data/scripts.json`:
```json
{
  "intro": "[Date]. [Major event description]. [Key parties involved]. [What's at stake].",
  "hook_1": "[Source name] reports that [their key perspective]...",
  ...
}
```

Update `registry.json` voiceovers section with:
- `id` — VideoDB audio asset ID
- `duration` — exact duration from `float(voice.length)` (NOT estimated, cast to float)
- `script` — the text used

**Example:**
```json
"intro": {
  "id": "a-z-019d...",
  "duration": 16.431020,
  "script": "February 2026. Major event description..."
}
```

---

### Step 7: Build the Video

**Goal:** Assemble the final video using the build template.

```bash
python templates/build_video.py outputs/<topic-slug>/data/registry.json
```

This reads `data/registry.json`, builds a 5-track timeline, and generates the stream.

Output is saved to `outputs/<topic-slug>/output/output.json`:
```json
{
  "stream_url": "https://play.videodb.io/v1/...",
  "player_url": "https://console.videodb.io/player?url=...",
  "duration_seconds": 211.9,
  "duration_formatted": "3:31"
}
```

**Note:** The code outputs console URLs. Convert to player URLs (`https://player.videodb.io/watch?v=...`) manually when sharing publicly.

**If the build fails:**
- `Clip duration greater than audio length` → Your `registry.json` duration is wrong. Re-check `voice.length` for that audio ID.
- `Invalid request` → Check that all asset IDs in registry.json are valid and uploaded.

---

## Registry Schema

`registry.json` is the single source of truth. Every asset ID, every duration, everything the build script needs.

```json
{
  "topic": "string — the topic name",
  "created": "YYYY-MM-DD",
  "background": {
    "image_id": "img-z-... — VideoDB image ID for background",
    "music_id": "a-z-... — VideoDB audio ID for background music",
    "music_duration": 125.257 
  },
  "videos": {
    "video_1": {
      "label": "AL JAZEERA — displayed as text overlay",
      "source_url": "YouTube URL",
      "video_id": "m-z-... — VideoDB video ID",
      "clip_start": 10.6,
      "clip_duration": 25.8
    },
    "video_2": { "..." : "same structure" },
    "video_3": { "..." : "same structure" }
  },
  "tweets": {
    "tweet_1": { "image_id": "img-z-..." },
    "tweet_2": { "image_id": "img-z-..." },
    "tweet_3": { "image_id": "img-z-..." }
  },
  "articles": {
    "article_1": {
      "scroll_id": "m-z-... — VideoDB video ID of scroll recording",
      "scroll_duration": 8.0,
      "screenshot_id": "img-z-... — VideoDB image ID of key screenshot"
    },
    "article_2": { "..." : "same structure" }
  },
  "voiceovers": {
    "intro": { "id": "a-z-...", "duration": 10.213, "script": "..." },
    "hook_1": { "id": "a-z-...", "duration": 8.855, "script": "..." },
    "hook_2": { "id": "a-z-...", "duration": 7.889, "script": "..." },
    "hook_3": { "id": "a-z-...", "duration": 7.758, "script": "..." },
    "tweet_transition": { "id": "a-z-...", "duration": 8.907, "script": "..." },
    "tweet_1": { "id": "a-z-...", "duration": 13.557, "script": "..." },
    "tweet_2": { "id": "a-z-...", "duration": 15.360, "script": "..." },
    "tweet_3": { "id": "a-z-...", "duration": 11.363, "script": "..." },
    "article_transition": { "id": "a-z-...", "duration": 6.817, "script": "..." },
    "article_1": { "id": "a-z-...", "duration": 16.326, "script": "..." },
    "article_2": { "id": "a-z-...", "duration": 19.591, "script": "..." }
  }
}
```

---

## Background Assets

Default background image and music are shipped in `assets/`:
- `assets/news-bg.jpg` — dark professional news background
- `assets/news-music.mp3` — news-style music (125.3s)

**First-time setup:** Upload both to VideoDB and record their IDs.

```python
bg_img = coll.upload(file_path="assets/news-bg.jpg")
bg_music = coll.upload(file_path="assets/news-music.mp3")
```

These IDs can be reused across multiple runs (same VideoDB collection). Store them at the top of each `registry.json`.

---

## Quality Checklist

Before delivering the final video:

- [ ] 3 YouTube clips from 3 different sources
- [ ] Each clip is ~25s, self-contained, ends naturally
- [ ] 3 tweet screenshots are clean and from notable accounts
- [ ] 3 tweets show different perspectives
- [ ] 2 articles from trusted sources, different angles
- [ ] Scroll videos are smooth, 8-13 seconds
- [ ] All 11 voiceover scripts are factual and concise
- [ ] All durations in registry.json match actual `voice.length` values
- [ ] Build completes without errors
- [ ] Video plays correctly at the output URL
