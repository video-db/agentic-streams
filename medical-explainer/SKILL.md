---
name: medical-explainer-video-agent
description: Create accessible medical explainer videos. Given a medical term or procedure, autonomously researches trusted sources, finds YouTube explainer clips, captures medical illustrations and key facts, then assembles a narrated video with voiceovers, background music, and clean text overlays using VideoDB.
---

# Medical Explainer Video Agent Skill

Use this skill when the user wants to:
- Create an explainer video for a medical term or procedure
- Turn a complex medical concept into an accessible visual explanation
- Combine YouTube medical clips, illustrations, and key facts into a professional explainer video

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
- **VideoDB skill** -- video upload, indexing, search, TTS, timeline editing
- **Browser use skill** -- ALL internet research, searching, screenshots, scroll recordings
- **File read/write** -- manage registry, scripts, and output files
- **Bash / Python** -- run the build script

## CRITICAL: No Hallucinated Data

**Every URL, every fact, every piece of content MUST come from actual browser navigation.**

- You MUST use browser-use to visit real websites and find real URLs
- You MUST NOT generate YouTube URLs from memory -- go to youtube.com and search
- You MUST NOT create fake medical illustrations -- screenshot real diagrams from trusted sources
- You MUST NOT write medical information from LLM knowledge alone -- browse real medical pages first
- If browser-use is not working, STOP and tell the user. Do NOT proceed with made-up data.

**Browser-use is your internet.** It handles both discovery (searching YouTube, medical sites) AND capture (screenshots, scroll recordings). There is no other search tool.

## CRITICAL: Medical Accuracy

**All medical information must come from authoritative sources.**

- **Preferred sources:** Mayo Clinic, NIH (MedlinePlus), Cleveland Clinic, NHS, Johns Hopkins Medicine, WebMD
- **YouTube channels:** Osmosis, Khan Academy Medicine, Nucleus Medical Media, Armando Hasudungan, Ninja Nerd
- Do NOT use unverified blogs, social media posts, or non-medical YouTube channels
- Always include a disclaimer that the video is for educational purposes only

## Video Structure (fixed, deterministic)

Every medical explainer follows the same structure:

```
Title card (4s) --> Intro voiceover (definition + why it matters)
--> Explainer clip 1 (hook + clip) --> Explainer clip 2 (hook + clip)
--> Illustration transition --> Illustration 1 --> Illustration 2
--> Key facts transition --> Key fact 1 --> Key fact 2 --> Key fact 3
--> Outro (5s)

Total: ~3-4 minutes (varies based on generated voiceover lengths)
```

**Note:** Only the title card (4s) and outro (5s) have fixed durations. Everything else is dynamically sized based on the actual voiceover durations returned by VideoDB TTS. The `build_video.py` template reads exact durations from `registry.json` -- nothing is hardcoded.

## Inputs

The only required input is:
- **term** -- e.g., "angioplasty", "Type 2 Diabetes", "MRI scan", "ACL tear"

Optional:
- Custom background image (default: shipped `assets/medical-bg.jpg`)
- Custom background music (default: shipped `assets/medical-music.mp3`)

## Workflow

### Step 1: Research the medical term (USE BROWSER-USE)
Use browser-use to actually browse the internet and gather real medical information:

1. Navigate to Mayo Clinic: `mayoclinic.org/search/search-results?q=<term>`
2. Navigate to NIH MedlinePlus: `medlineplus.gov/search?query=<term>`
3. Visit 2-3 top results from these trusted medical sites
4. Read the actual page content

**Do NOT write research from LLM memory.** Every fact in `research.md` must trace back to a real URL you visited.

Save to `outputs/<term-slug>/data/research.md` -- include source URLs for every claim.

Research should cover:
- Definition (what is it?)
- How it works / what happens during the procedure
- Who needs it / risk factors
- What to expect (preparation, during, recovery)
- Key statistics or facts
- Common misconceptions

### Step 2: Find 2 YouTube explainer videos (USE BROWSER-USE)
Use browser-use to navigate to YouTube and find real videos:

1. Open `youtube.com` --> search `<term> medical explanation`
2. Click on a real result --> copy the URL from the browser
3. Repeat for a second channel

**Preferred YouTube channels to search:**
- Osmosis (excellent animated medical explainers)
- Khan Academy Medicine
- Nucleus Medical Media (3D medical animations)
- Armando Hasudungan (illustrated medical lectures)
- Ninja Nerd (detailed medical education)
- Mayo Clinic (official patient education)
- Cleveland Clinic (official patient education)

**Criteria:**
- 2 different sources for diverse explanation styles
- Recent and relevant to the term
- 2-15 minutes long, English language
- Educational focus (not news coverage or personal stories)
- **Every URL must come from actually visiting youtube.com** -- not from LLM knowledge

Save URLs to `outputs/<term-slug>/data/videos.json`

### Step 3: Process YouTube videos with VideoDB
For each of the 2 videos:
1. Upload to VideoDB: `coll.upload(url=youtube_url)`
2. Index spoken words: `video.index_spoken_words(force=True)`
3. Semantic search for the best ~25 second clip: `video.search(query)`
4. Select a clip that clearly explains a key concept

**Search query tips:**
- Keep queries short (3-5 words): "how angioplasty works", "diabetes insulin resistance"
- Focus on the explanatory segment, not introductions or outros
- Pick clips that are self-contained and visually informative

Update `registry.json` with video IDs, clip start times, and durations.

### Step 4: Capture 2 medical illustrations (USE BROWSER-USE)
Use browser-use to find and screenshot medical diagrams:

1. Navigate to trusted medical sites with visual content
2. Find clear, labeled diagrams or illustrations of the term/procedure
3. Screenshot the illustration

**Good sources for medical illustrations:**
- Mayo Clinic procedure pages (often have diagrams)
- NIH/MedlinePlus (medical illustrations library)
- Cleveland Clinic health articles
- NHS condition pages

**Criteria:**
- Clear, labeled diagrams (not stock photos)
- Shows anatomy, process flow, or mechanism
- Illustration 1: Anatomy or overview of the condition/procedure
- Illustration 2: Step-by-step process or mechanism of action

**CLOSE ALL POPUPS before screenshotting** (cookie banners, newsletter prompts, etc.)

Save to `outputs/<term-slug>/assets/illustrations/illustration_1.png`, `illustration_2.png`
Upload each to VideoDB and update `data/registry.json`.

### Step 5: Capture 3 key fact screenshots (USE BROWSER-USE)
Use browser-use to find and capture key fact sections:

1. Navigate to authoritative medical pages
2. Find sections with key statistics, risk factors, or important takeaways
3. Screenshot the relevant section

**Criteria:**
- Key fact 1: Statistics or prevalence (how common, success rates)
- Key fact 2: Risk factors or causes
- Key fact 3: When to see a doctor / warning signs

Save to `outputs/<term-slug>/assets/keyfacts/keyfact_1.png`, `keyfact_2.png`, `keyfact_3.png`
Upload each to VideoDB and update `data/registry.json`.

### Step 6: Write scripts & generate voiceovers
Write **10 voiceover scripts** based on research and collected sources:

| Script | Guideline | Content |
|--------|-----------|---------|
| intro | 3-4 sentences | Define the term, who it affects, why understanding it matters |
| hook_1 | 1-2 sentences | Introduce explainer video 1, what it covers |
| hook_2 | 1-2 sentences | Introduce explainer video 2, what it covers |
| illustration_transition | 1 sentence | Bridge to visual explanation section |
| illustration_1 | 3-4 sentences | Narrate what the diagram shows, explain the anatomy or process |
| illustration_2 | 3-4 sentences | Narrate the mechanism or step-by-step process shown |
| keyfacts_transition | 1 sentence | Bridge to key takeaways section |
| keyfact_1 | 2-3 sentences | Key statistics, prevalence, or success rates |
| keyfact_2 | 2-3 sentences | Risk factors, causes, or who is affected |
| keyfact_3 | 2-3 sentences | When to see a doctor, warning signs, or next steps |

**Tone:** Clear, calm, educational. Like a trusted doctor explaining to a patient. Avoid medical jargon unless defined. Accessible to a general audience.

**Duration note:** Do NOT target specific second counts. Write natural scripts following the sentence guidelines above. Generate via TTS, then record the **exact duration** returned by `audio.length` into `registry.json`. The build template handles all timing dynamically.

Generate each using VideoDB TTS: `coll.generate_voice(text=script, voice_name="Default")`

Save scripts to `data/scripts.json`. Update `data/registry.json` with audio IDs and **exact durations** (from `audio.length`).

### Step 7: Build the video
Run the build template:
```bash
python templates/build_video.py outputs/<term-slug>/data/registry.json
```

This assembles the 5-track timeline and generates the final stream URL.
Output saved to `outputs/<term-slug>/output/output.json`.

## Per-run folder structure

All runs go inside `outputs/` within the skill directory. **Never** create run folders at the skill root. **Never** place loose files at the topic folder root -- everything goes in a subfolder.

```
medical-explainer/
├── SKILL.md
├── AGENTS.md
├── README.md
├── assets/                             # Shipped defaults (bg, music)
├── templates/
└── outputs/                            # ALL runs go here
    └── <term-slug>/                    # e.g., "angioplasty"
        │
        ├── assets/                     # Physical files (viewable media)
        │   ├── illustrations/          #   Medical diagram PNGs
        │   │   ├── illustration_1.png
        │   │   └── illustration_2.png
        │   └── keyfacts/               #   Key fact screenshot PNGs
        │       ├── keyfact_1.png
        │       ├── keyfact_2.png
        │       └── keyfact_3.png
        │
        ├── data/                       # Digital metadata (IDs, scripts, research)
        │   ├── research.md             #   Medical research brief
        │   ├── scripts.json            #   All 10 voiceover scripts
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
- `data/` = metadata, IDs, scripts -- everything VideoDB and the build template need
- `_build/` = intermediate files created during processing (prefixed with `_` to signal "ignore")
- `output/` = the final video URL and metadata
- **Zero files at the topic root** -- everything in a subfolder

## Shipped assets

Default background and music are in `assets/`:
- `assets/medical-bg.jpg` -- Clean light medical/health background
- `assets/medical-music.mp3` -- Calm, reassuring background music

Users can replace these with their own files. Upload to VideoDB and update registry.

## Deliverables

A successful run produces:
- `output/output.json` with playable stream URL
- All physical media preserved in `assets/`
- Full `data/registry.json` for reproducibility

## Reference

See `outputs/` folder for complete agent-generated examples with full registry structure and asset organization.

## Reference docs

- `README.md` -- Overview, setup, and usage guide
- `AGENTS.md` -- Detailed agent workflow, error handling, quality criteria
- `templates/build_video.py` -- Timeline builder (reads registry.json)
