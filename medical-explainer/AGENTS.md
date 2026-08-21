# Medical Explainer Video -- Agent Instructions

Detailed workflow for agents building medical explainer videos. Read `SKILL.md` first for the overview.

## CRITICAL RULE: No Hallucinated Data

**You MUST use browser-use for ALL internet research.** This means:
- Every YouTube URL must come from navigating to youtube.com and searching
- Every illustration must come from screenshotting a real medical page
- Every key fact screenshot must come from navigating to actual medical sites
- Research facts must come from reading real web pages, not LLM memory

**If browser-use is not available or not working, STOP immediately and tell the user.** Do NOT proceed by generating URLs from memory or creating placeholder images. The entire value of this video is real, sourced, accurate medical content.

## CRITICAL RULE: Medical Accuracy

**All content must come from authoritative medical sources.** This is a medical education tool -- accuracy is paramount.

- Never use unverified sources, personal blogs, or social media as medical references
- Always cross-reference key claims across at least 2 authoritative sources
- Include source attribution in research.md for every medical fact
- The video is for educational purposes only -- scripts must NOT give medical advice (e.g., "consult your doctor" instead of "you should take X medication")

## Prerequisites

- VideoDB SDK installed: `pip install videodb python-dotenv`
- `VIDEO_DB_API_KEY` set in environment or `.env` file
- **Browser use skill installed and working** -- this is your only way to access the internet
- Read `~/.claude/skills/browser-use/SKILL.md` before starting
- **Note:** Chrome `--profile` flag requires Google Chrome (not Chromium). If you need authenticated sessions, install Chrome first.

## CRITICAL: Close Popups/Ads Before Screenshots

**Before taking ANY screenshot, you MUST close all popups, overlays, and ads.**

Common overlays to close:
- Cookie consent banners
- Newsletter signup popups
- Donation prompts
- Privacy policy notices
- Mobile app download prompts
- "Accept cookies" banners (especially common on medical sites)

**How to close overlays:**

1. **Wait for page to fully load:** `sleep 2` after navigation
2. **Identify overlay elements:** `browser-use state` to see clickable elements
3. **Close via clicking:** `browser-use click <close-button-index>`
4. **Or hide via JavaScript:**
   ```bash
   browser-use eval "document.querySelectorAll('[class*=\"modal\"], [class*=\"popup\"], [class*=\"overlay\"], [class*=\"consent\"], [class*=\"cookie\"]').forEach(el => el.remove())"
   ```

**Quality check:** Before saving, visually verify no overlays are visible in the captured image.

## Step-by-Step Workflow

### Step 1: Research Medical Term (BROWSER-USE REQUIRED)

**Goal:** Build authoritative medical context to write accurate voiceover scripts later.

**You MUST use browser-use to do real web research.** Do NOT write this from LLM memory.

**CRITICAL: Do NOT use search engines (Google, DuckDuckGo, Bing).** They show CAPTCHAs in headless mode.

**Instead, navigate directly to medical site search pages:**

1. **Mayo Clinic:** `browser-use open "https://www.mayoclinic.org/search/search-results?q=<term>"`
2. **NIH MedlinePlus:** `browser-use open "https://medlineplus.gov/search?query=<term>"`
3. **Cleveland Clinic:** `browser-use open "https://my.clevelandclinic.org/search?q=<term>"`
4. **NHS:** `browser-use open "https://www.nhs.uk/search/results?q=<term>"`
5. **Johns Hopkins:** `browser-use open "https://www.hopkinsmedicine.org/search?q=<term>"`

**Navigate to articles:**
- Use `browser-use state` to see clickable element indices
- Use `browser-use click <index>` to navigate to articles
- Always verify the page is about your specific term (not a generic landing page)

**Extract article text:**
```bash
# Get clean text (first 5000 chars)
browser-use eval "document.querySelector('article, main, [role=\"main\"]')?.innerText?.substring(0, 5000)"

# For longer articles, paginate
browser-use eval "document.querySelector('article, main, [role=\"main\"]')?.innerText?.substring(5000, 10000)"
```

**Visit 2-3 trusted medical sources** and extract:
- **Definition:** What is it? (in plain language)
- **Mechanism:** How does it work? What happens in the body?
- **Who is affected:** Risk factors, demographics, prevalence
- **Procedure details** (if applicable): Preparation, what happens during, recovery
- **Key statistics:** Success rates, prevalence, survival rates
- **Warning signs:** When to see a doctor, red flags
- **Common misconceptions:** Things people often get wrong

Write to `outputs/<term-slug>/data/research.md`. Include source URLs for every claim.

---

### Step 2: Find 2 YouTube Explainer Videos (BROWSER-USE REQUIRED)

**Goal:** Find 2 high-quality educational videos from different trusted medical channels.

**You MUST use browser-use to navigate to YouTube and search.** Do NOT construct YouTube URLs from memory.

**How to find videos:**

YouTube works fine in headless mode (no CAPTCHA). Use direct YouTube search:

```bash
browser-use open "https://www.youtube.com/results?search_query=<term>+medical+explanation+Osmosis"
```

**Extract video URLs:**
```bash
browser-use eval "Array.from(document.querySelectorAll('a#video-title')).slice(0, 5).map(a => ({title: a.title, href: a.href}))"
```

**Preferred channels to search (in order of preference):**
- Osmosis (animated medical explainers -- excellent for patient education)
- Khan Academy Medicine (clear, methodical explanations)
- Nucleus Medical Media (high-quality 3D medical animations)
- Armando Hasudungan (illustrated medical lectures)
- Ninja Nerd (detailed medical education)
- Mayo Clinic (official, authoritative)
- Cleveland Clinic (official, authoritative)

**Selection criteria:**
- 2 different channels (never 2 from the same source)
- Each presents a different aspect: one overview, one detailed mechanism/procedure
- Video is 2-15 minutes long (enough content to find a good 25s clip)
- English language, clear audio
- Educational focus -- not patient testimonials, news, or vlogs
- **The URL must come from YouTube search results you actually saw in the browser**

Save to `outputs/<term-slug>/data/videos.json`:
```json
{
  "video_1": { "url": "https://youtube.com/watch?v=...", "source": "Osmosis", "title": "..." },
  "video_2": { "url": "https://youtube.com/watch?v=...", "source": "Khan Academy", "title": "..." }
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

# Search for best segment -- KEEP QUERIES SHORT (3-5 words)
# Good: "how stent is placed", "insulin resistance mechanism"
# Bad: "the doctor performs angioplasty by inserting a balloon catheter into the artery"
results = video.search("stent placement artery", search_type=SearchType.semantic)
shots = results.get_shots()

# Pick the best shot, trim to ~25 seconds
shot = shots[0]
clip_start = float(shot.start)
clip_duration = min(float(shot.end) - float(shot.start), 25.0)
```

**Clip selection criteria:**
- ~25 seconds (20-30s acceptable)
- Contains a clear explanation of a key concept
- Self-contained (makes sense without surrounding context)
- Has visual aids (animations, diagrams) if possible
- No dead air, no ads, no off-topic segments
- Video 1: General overview or definition
- Video 2: Detailed mechanism, procedure steps, or how it works

**Error handling:**
- If YouTube upload fails: try an alternate URL from the same source
- If semantic search returns no results: retry with shorter query (3-5 words)
- If clip is too short (<15s): widen the selection or try a different search query
- **CRITICAL:** Do NOT skip explainer clips entirely. Keep trying different URLs until you have 2 working clips.

Update `registry.json` with the video_id, clip_start, clip_duration, and label.

---

### Step 4: Capture 2 Medical Illustrations (BROWSER-USE REQUIRED)

**Goal:** Find and screenshot 2 clear medical diagrams showing the anatomy or process.

**Navigate directly to medical sites with visual content:**

```bash
# Mayo Clinic procedure/condition page
browser-use open "https://www.mayoclinic.org/search/search-results?q=<term>"

# Cleveland Clinic
browser-use open "https://my.clevelandclinic.org/search?q=<term>"

# NIH MedlinePlus
browser-use open "https://medlineplus.gov/search?query=<term>"
```

**Finding illustrations:**
1. Navigate to the condition/procedure page
2. Look for diagrams, anatomical illustrations, or process flowcharts
3. Scroll to the illustration section
4. Close all popups
5. Screenshot the illustration

```bash
# Navigate to the page
browser-use open "https://www.mayoclinic.org/tests-procedures/..."
sleep 2

# Remove overlays
browser-use eval "document.querySelectorAll('[class*=\"modal\"], [class*=\"cookie\"], [class*=\"consent\"]').forEach(el => el.remove())"

# Scroll to illustration if needed
browser-use eval "document.querySelector('img[alt*=\"<term>\"]')?.scrollIntoView()"
sleep 1

# Screenshot
browser-use screenshot outputs/<term-slug>/assets/illustrations/illustration_1.png
```

**Illustration selection:**
- Illustration 1: Anatomy overview or condition visualization (what does it look like?)
- Illustration 2: Process or mechanism (how does the procedure/condition work?)

**Quality criteria:**
- Clear, labeled diagrams (not stock photos of doctors)
- Shows relevant anatomy, process flow, or mechanism
- High enough resolution to read labels
- No watermarks or copyright-restricted content
- **CLOSE ALL POPUPS before screenshotting**

**If no good illustration exists on medical sites:** Fall back to screenshotting a clear frame from one of the YouTube explainer videos (especially Osmosis or Nucleus Medical Media which have excellent animations).

Save as:
```
outputs/<term-slug>/assets/illustrations/illustration_1.png
outputs/<term-slug>/assets/illustrations/illustration_2.png
```

Upload each to VideoDB:
```python
img = coll.upload(file_path="outputs/<term-slug>/assets/illustrations/illustration_1.png")
# Record img.id in data/registry.json
```

---

### Step 5: Capture 3 Key Fact Screenshots (BROWSER-USE REQUIRED)

**Goal:** Find and screenshot 3 authoritative sections with key facts about the term.

**Navigate to medical fact pages:**

```bash
# Mayo Clinic
browser-use open "https://www.mayoclinic.org/search/search-results?q=<term>"

# Cleveland Clinic
browser-use open "https://my.clevelandclinic.org/search?q=<term>"

# NIH
browser-use open "https://medlineplus.gov/search?query=<term>"

# NHS
browser-use open "https://www.nhs.uk/search/results?q=<term>"
```

**Key fact selection:**
- Key fact 1: **Statistics/Prevalence** -- How common is it? Success rates? Key numbers.
- Key fact 2: **Risk factors/Causes** -- Who is at risk? What causes it?
- Key fact 3: **When to see a doctor** -- Warning signs, red flags, when to seek help.

For each key fact:
1. Navigate to the relevant section of the medical page
2. Close all popups
3. Screenshot the specific section (not the full page)

```bash
browser-use open "https://www.mayoclinic.org/diseases-conditions/..."
sleep 2
browser-use eval "document.querySelectorAll('[class*=\"cookie\"]').forEach(el => el.remove())"

# Scroll to risk factors section
browser-use eval "Array.from(document.querySelectorAll('h2, h3')).find(el => el.textContent.includes('Risk'))?.scrollIntoView()"
sleep 1
browser-use screenshot outputs/<term-slug>/assets/keyfacts/keyfact_2.png
```

**VERIFY PAGE CONTENT IS RELEVANT** before screenshotting:
```bash
browser-use eval "document.body.innerText.substring(0, 500)"
```
Review output: Does it match your term? Is it a 404 or generic page? If so, try a different URL.

Save as:
```
outputs/<term-slug>/assets/keyfacts/keyfact_1.png
outputs/<term-slug>/assets/keyfacts/keyfact_2.png
outputs/<term-slug>/assets/keyfacts/keyfact_3.png
```

Upload each to VideoDB and update `registry.json`.

---

### Step 6: Write Scripts & Generate Voiceovers

**Goal:** Write 10 voiceover scripts and generate TTS audio for each.

Use `research.md` and your collected sources as context.

**Script writing guidelines:**
- Clear, calm, educational tone -- like a trusted doctor explaining to a patient
- Use plain language -- define medical terms when first introduced
- Factual and evidence-based -- no speculation or personal advice
- Include the disclaimer spirit: "talk to your doctor" rather than "you should do X"

| Script | Guideline | Content |
|--------|-----------|---------|
| intro | 3-4 sentences | What is [term]? Who does it affect? Why understanding it matters. |
| hook_1 | 1-2 sentences | Introduce explainer video 1, what aspect it covers |
| hook_2 | 1-2 sentences | Introduce explainer video 2, what aspect it covers |
| illustration_transition | 1 sentence | Bridge to visual explanation ("Let's look at how this works visually") |
| illustration_1 | 3-4 sentences | Narrate the anatomy/overview diagram -- what are we looking at? |
| illustration_2 | 3-4 sentences | Narrate the process/mechanism -- what happens step by step? |
| keyfacts_transition | 1 sentence | Bridge to key takeaways ("Here are some important facts to know") |
| keyfact_1 | 2-3 sentences | Key statistics: how common, success rates, important numbers |
| keyfact_2 | 2-3 sentences | Risk factors and causes -- who should be aware? |
| keyfact_3 | 2-3 sentences | When to see a doctor, warning signs, empowering next steps |

**Generate each voiceover:**
```python
voice = coll.generate_voice(text=script, voice_name="Default")
# IMPORTANT: voice.length returns a STRING, not a float
# Cast to float before using in calculations or formatting
audio_id = voice.id
exact_duration = float(voice.length)  # This is the ground truth
```

Save all scripts to `outputs/<term-slug>/data/scripts.json`:
```json
{
  "intro": "[Term] is a [definition]. It affects [who]. Understanding [term] helps you...",
  "hook_1": "This explanation from [source] breaks down...",
  ...
}
```

Update `registry.json` voiceovers section with:
- `id` -- VideoDB audio asset ID
- `duration` -- exact duration from `float(voice.length)` (NOT estimated, cast to float)
- `script` -- the text used

---

### Step 7: Build the Video

**Goal:** Assemble the final video using the build template.

```bash
python templates/build_video.py outputs/<term-slug>/data/registry.json
```

This reads `data/registry.json`, builds a 5-track timeline, and generates the stream.

Output is saved to `outputs/<term-slug>/output/output.json`:
```json
{
  "stream_url": "https://play.videodb.io/v1/...",
  "player_url": "https://console.videodb.io/player?url=...",
  "duration_seconds": 195.3,
  "duration_formatted": "3:15"
}
```

**If the build fails:**
- `Clip duration greater than audio length` --> Your `registry.json` duration is wrong. Re-check `voice.length` for that audio ID.
- `Invalid request` --> Check that all asset IDs in registry.json are valid and uploaded.

---

## Registry Schema

`registry.json` is the single source of truth. Every asset ID, every duration, everything the build script needs.

```json
{
  "term": "string -- the medical term",
  "created": "YYYY-MM-DD",
  "background": {
    "image_id": "img-z-... -- VideoDB image ID for background",
    "music_id": "a-z-... -- VideoDB audio ID for background music",
    "music_duration": 120.0
  },
  "videos": {
    "video_1": {
      "label": "OSMOSIS -- displayed as text overlay",
      "source_url": "YouTube URL",
      "video_id": "m-z-... -- VideoDB video ID",
      "clip_start": 45.2,
      "clip_duration": 24.5
    },
    "video_2": { "...": "same structure" }
  },
  "illustrations": {
    "illustration_1": { "image_id": "img-z-..." },
    "illustration_2": { "image_id": "img-z-..." }
  },
  "keyfacts": {
    "keyfact_1": { "image_id": "img-z-..." },
    "keyfact_2": { "image_id": "img-z-..." },
    "keyfact_3": { "image_id": "img-z-..." }
  },
  "voiceovers": {
    "intro": { "id": "a-z-...", "duration": 14.5, "script": "..." },
    "hook_1": { "id": "a-z-...", "duration": 7.2, "script": "..." },
    "hook_2": { "id": "a-z-...", "duration": 7.8, "script": "..." },
    "illustration_transition": { "id": "a-z-...", "duration": 4.5, "script": "..." },
    "illustration_1": { "id": "a-z-...", "duration": 16.3, "script": "..." },
    "illustration_2": { "id": "a-z-...", "duration": 15.8, "script": "..." },
    "keyfacts_transition": { "id": "a-z-...", "duration": 4.2, "script": "..." },
    "keyfact_1": { "id": "a-z-...", "duration": 12.1, "script": "..." },
    "keyfact_2": { "id": "a-z-...", "duration": 11.5, "script": "..." },
    "keyfact_3": { "id": "a-z-...", "duration": 12.8, "script": "..." }
  }
}
```

---

## Background Assets

Default background image and music are shipped in `assets/`:
- `assets/medical-bg.jpg` -- clean light medical background
- `assets/medical-music.mp3` -- calm background music

**First-time setup:** Upload both to VideoDB and record their IDs.

```python
bg_img = coll.upload(file_path="assets/medical-bg.jpg")
bg_music = coll.upload(file_path="assets/medical-music.mp3")
```

These IDs can be reused across multiple runs (same VideoDB collection). Store them at the top of each `registry.json`.

---

## Quality Checklist

Before delivering the final video:

- [ ] 2 YouTube clips from 2 different medical education sources
- [ ] Each clip is ~25s, clearly explains a key concept
- [ ] 2 medical illustrations are clear, labeled diagrams
- [ ] 3 key fact screenshots from authoritative sources
- [ ] All 10 voiceover scripts are factual, clear, and accessible
- [ ] All durations in registry.json match actual `voice.length` values
- [ ] No medical advice given -- educational only
- [ ] All sources are authoritative (Mayo Clinic, NIH, Cleveland Clinic, NHS, etc.)
- [ ] Build completes without errors
- [ ] Video plays correctly at the output URL
