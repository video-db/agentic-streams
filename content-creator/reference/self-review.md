# Self-Review

Self-review is **mandatory**. Always run at least one review cycle after the first composition. `MAX_ITERATIONS` (from SKILL.md config) is the maximum number of review-fix cycles — not a toggle. You are a director watching your rough cut. Watch it, critique it, fix it, recut it.

## How to "Watch" the Draft

You can't literally watch video, but you can extract frames, look at them, and read AI descriptions of every second. Use the `videodb` skill to:

### Step 1: Upload the stream

Upload the composed stream URL as a new video asset in VideoDB.

### Step 2: Index spoken words

Transcribes the narration so you can read what was actually said:

```python
video.index_spoken_words()
```

### Step 3: Extract scenes with frames

Extract scenes at 1-second intervals with 2 frames each. This gives you both AI descriptions AND actual frame images you can look at:

```python
from videodb import SceneExtractionType

scene_collection = video.extract_scenes(
    extraction_type=SceneExtractionType.time_based,
    extraction_config={"time": 1, "select_frames": ["first", "last"]},
)
```

**Returns:** a `SceneCollection` with a `.scenes` list. Each `Scene` has:
- `.start` — start time in seconds
- `.end` — end time in seconds
- `.description` — text description (empty until you call `.describe()`)
- `.frames` — list of `Frame` objects, each with `.url` and `.frame_time`

### Step 4: Index scenes for AI descriptions

Run `index_scenes` to get AI-generated descriptions of each second:

```python
import re

try:
    scene_index_id = video.index_scenes(
        extraction_type=SceneExtractionType.time_based,
        extraction_config={"time": 1, "select_frames": ["first", "last"]},
        prompt="Describe the visual content: what type of visual is this (animated chart, browser/webpage, text on screen, video clip, static image)? What does it show? What text is visible on screen? Is there motion or is it static?",
    )
except Exception as e:
    match = re.search(r"id\s+([a-f0-9]+)", str(e))
    if match:
        scene_index_id = match.group(1)
    else:
        raise
```

### Step 5: Read back everything

**Transcript (what was said):**

```python
transcript = video.get_transcript()       # list of {start, end, text}
transcript_text = video.get_transcript_text()  # full text string
```

**Scene index records (AI descriptions per second):**

`get_scene_index()` returns a list of dicts, each with `start`, `end`, `description`:

```python
scene_records = video.get_scene_index(scene_index_id)
for record in scene_records:
    print(f"[{record['start']}-{record['end']}] {record['description']}")
```

**Frame images (actually look at what's on screen):**

Each scene from `extract_scenes` has frame images with URLs. Download them to the run's `WORK_DIR` and look at them:

```python
frames_dir = Path(WORK_DIR) / "frames"
frames_dir.mkdir(parents=True, exist_ok=True)

for scene in scene_collection.scenes:
    print(f"\n--- Scene {scene.start}s - {scene.end}s ---")
    print(f"Description: {scene.description}")
    for frame in scene.frames:
        print(f"  Frame at {frame.frame_time}s: {frame.url}")
        # Download to WORK_DIR/frames/ then use Read tool to view
```

**Look at the frames.** Don't just read descriptions — download and view the frame images using the Read tool. The AI descriptions from `get_scene_index` can miss details or be vague. The frame images are ground truth. Check:
- Is the visual actually what you intended? (a chart, a browser, text, a video clip)
- Is text readable? Are data call-outs visible?
- Does the frame look polished or broken?

### Step 6 (optional): Retrieve scenes later

If you need to retrieve the scene collection in a later iteration without re-extracting:

```python
collections = video.list_scene_collection()
scene_collection = video.get_scene_collection(collections[0]["scene_collection_id"])
```

### What you now have

- **What you intended** — the script + the timeline from composition
- **What was said** — transcript from spoken word indexing
- **What the AI sees** — scene descriptions from `get_scene_index()`
- **What actually appears** — frame images from `extract_scenes()` that you can look at directly

## Build the Intended Timeline

During composition (Phase 4), you placed clips at specific timestamps using `add_clip(start, clip)`. You know exactly what should be at each second of the video. Build a lookup from this data:

```
second  0-2:   hook     / motion_scene    / visual: "Aerial drone shot of tech campus"
second  2-8:   hook     / motion_scene    / narration: "In the last 12 months, something shifted..."
second  8-10:  context  / browser_capture / visual: "Google search results for AI adoption"
second 10-20:  context  / browser_capture / narration: "According to Gartner's latest report..."
second 20-22:  insight1 / data_viz        / visual: "Animated bar chart, adoption rates by industry"
second 22-33:  insight1 / data_viz        / narration: "The tech sector leads at 73 percent..."
...
```

This is your ground truth. You already have all of this from the script segments and the `add_clip()` calls. Structure it as a list:

```python
intended_timeline = [
    {"start": 0, "end": 2, "segment": "hook", "visual_type": "motion_scene", "visual_direction": "Aerial drone shot...", "narration": None},
    {"start": 2, "end": 8, "segment": "hook", "visual_type": "motion_scene", "visual_direction": "Aerial drone shot...", "narration": "In the last 12 months..."},
    {"start": 8, "end": 20, "segment": "context", "visual_type": "browser_capture", "visual_direction": "Google search for AI adoption", "narration": "According to Gartner..."},
    # ...
]
```

## Align and Compare

Walk through the scene records and frame images, aligning each second against the intended timeline:

1. **Look up** what the intended timeline says should be at this second (segment, visual type, visual direction)
2. **Read** the AI description from `get_scene_index()` for that timestamp
3. **Look at** the frame image from `extract_scenes()` for that timestamp — actually view it
4. **Compare**: does both the description AND the frame match the intent?

The frame images are the most reliable signal. AI descriptions can be vague ("a dark screen with some text") but looking at the frame tells you exactly what's there.

**What to flag:**

| Intended | What you see in the frame | Verdict |
|----------|--------------------------|---------|
| `data_viz` — "animated bar chart" | A colorful bar chart with labeled axes | Match |
| `data_viz` — "animated bar chart" | White text on dark background, no chart | Mismatch — wrong asset |
| `browser_capture` — "Google search results" | A Chrome browser showing Google results | Match |
| `motion_scene` — "drone shot of campus" | A static photo of a building, no motion blur | Mismatch — static image, not video |
| `kinetic_text` — "73% stat on screen" | Large bold "73%" centered on screen | Match |

Build a mismatch report:

```python
mismatches = []
for intended in intended_timeline:
    matching_records = [r for r in scene_records if r["start"] >= intended["start"] and r["start"] < intended["end"]]
    matching_frames = [
        (scene, frame)
        for scene in scene_collection.scenes
        for frame in scene.frames
        if frame.frame_time >= intended["start"] and frame.frame_time < intended["end"]
    ]

    for record in matching_records:
        # Check AI description
        if not visuals_match(intended["visual_direction"], record["description"]):
            mismatches.append({
                "time": f"{record['start']}-{record['end']}",
                "segment": intended["segment"],
                "expected": intended["visual_direction"],
                "actual_description": record["description"],
            })

    # Also look at the frame images for this time range
    for scene, frame in matching_frames:
        # Use Read tool on frame.url to actually see the image
        # Visual inspection catches things descriptions miss
        pass
```

## Critique Framework

Check each of these. Collect all issues before deciding what to fix.

### 1. Narration Accuracy

Compare intended narration (from script) with actual transcript (from indexing).

**Check:**
- Did the voiceover say what you wrote? TTS can mangle numbers, names, or technical terms.
- Are all key facts present in the spoken audio?
- Is the pacing natural, or did it rush/drag?

**If broken:** Regenerate voice for the affected segment with adjusted text (spell out numbers, simplify names).

### 2. Visual-Narration Alignment

Use the mismatch report from the Align and Compare step.

**Check:**
- When narration talks about market growth, is the visual showing a chart or relevant scene — or something random?
- Are data call-outs visible during the right narration moments?
- Is the title card visible at the start?

**If broken:** The visual for that segment doesn't match. Regenerate the asset with a clearer prompt, or swap the visual type entirely.

### 3. Pacing

Check segment durations against [composition.md](composition.md) rules.

**Check:**
- Any segment under 8 seconds or over 20 seconds?
- Dead air (no narration AND no music)?
- Hook has 2-3 seconds of visual before narration starts?
- Outro breathes (narration ends before video does)?

**If broken:** Adjust segment timing — regenerate narration (shorten/lengthen text) or adjust clip durations.

### 4. Visual Variety

**Check:**
- Two consecutive segments with the same visual type?
- More than 2 segments using `image_scene` (slideshow feel)?
- At least one `data_viz` or `browser_capture` segment?

**If broken:** Swap the visual type of the offending segment and regenerate its asset.

### 5. Overall Flow

**Check:**
- Does it start strong? (hook = most attention-grabbing moment)
- Does it end cleanly? (no abrupt cut, outro card feels intentional)
- Background music audible but not overpowering?
- Transitions smooth, not jarring?

**If broken:** Composition issue — adjust timeline arrangement per [composition.md](composition.md).

### 6. Overlay Design Quality

**Check:**
- Every text overlay rated "bold" or "adequate" (see Pass 3 criteria)?
- No callout with font size below 36px at 720p?
- Hero stat screens using font size 52px+ and filling at least 60% of frame width?
- Every callout has a semi-opaque background bar or strong shadow for contrast?
- No `Position.center` + `Background` combination on TextAssets (known rendering issue)?

**If broken:** Increase font size and background opacity in the timeline. If TextAsset still renders poorly, replace with an AI-generated image that has the text baked into the visual. See design standards in [asset-production.md](asset-production.md).

## Critique: Four Passes

### Pass 1: Narration-Visual Sync

Before anything else, verify that what the viewer **hears** at each second matches what they **see**. This is the most common failure mode — the narration mentions a product, stat, or entity while the visual is still showing the previous segment, a transition, or a loading screen.

**Build anchor moments from the script.** If the script included `visual_sync_anchors`, use those directly. Otherwise, scan the word-level transcript (`video.get_transcript()` returns `{start, end, text}` per word) and identify every moment where the narration names a specific entity: a product, a person, a number, a URL, a company.

```python
transcript = video.get_transcript()

# Example: find when "call" + "md" appears (product mention)
anchors = []
for i, word in enumerate(transcript):
    text = word["text"].lower().strip()
    if text in ("call", "243", "stars", "hacker", "skills", "pair", "programmer"):
        anchors.append({
            "time": word["start"],
            "word": word["text"],
            "context": " ".join(t["text"] for t in transcript[max(0,i-2):i+3]),
        })
```

**For each anchor, find the frame at that exact timestamp and check:**

1. Look up the intended timeline — what segment and visual should be playing at `anchor["time"]`?
2. Find the extracted frame closest to `anchor["time"]` and view it
3. Does the frame show the thing the narration is naming?

**Log the results in a sync table:**

```
ANCHOR       | TIME   | NARRATION SAYS          | FRAME SHOWS                    | VERDICT
-------------|--------|-------------------------|--------------------------------|--------
product_name | 14.0s  | "Call MD"               | call.md GitHub repo header     | MATCH
stat         | 36.4s  | "243 stars"             | dark background, no text yet   | MISMATCH
source       | 49.1s  | "Hacker News"           | HN Show HN post visible        | MATCH
concept      | 64.4s  | "video database"        | AI-generated eyes video         | MATCH (abstract OK)
```

**What counts as a mismatch:**
- Narration names a specific product/repo but the browser capture is still on a different page
- Narration quotes a stat but the data callout hasn't appeared yet (or already disappeared)
- Narration says "as you can see here..." but the visual is a generic AI image, not evidence
- A browser capture segment is still loading/blank when the narration has already started describing content

**What counts as acceptable:**
- Narration discusses an abstract concept while an atmospheric video plays (no specific entity to match)
- Narration mentions something 0.5-1s before the visual appears (minor lead is natural)
- Narration references something shown 1-2s earlier (viewer memory bridges the gap)

**If mismatched:** Either shift the visual clip timing to align with the narration, or adjust the narration text so the entity mention falls when the visual is on screen. For browser captures, increase the `start` trim on `VideoAsset` to skip past loading frames, or add an extra `time.sleep()` in the Playwright script to hold on the relevant content longer.

### Pass 2: Visual inspection (you do this)

Before running the LLM critique, **look at the frame images yourself**. For each segment in the intended timeline, find the corresponding frames and view them:

```python
for intended in intended_timeline:
    print(f"\n=== {intended['segment']} ({intended['start']}s - {intended['end']}s) ===")
    print(f"Expected: {intended['visual_type']} — {intended['visual_direction']}")

    for scene in scene_collection.scenes:
        for frame in scene.frames:
            if intended["start"] <= frame.frame_time < intended["end"]:
                print(f"  Frame at {frame.frame_time}s: {frame.url}")
                # Read/view this URL to see the actual frame
```

For each frame you look at, ask:
- Does this match what I intended for this segment?
- Is the visual type right? (chart vs browser vs text vs video clip vs image)
- Is text readable? Are data call-outs visible?
- Does it look polished or broken/glitchy?

Record your observations for each segment.

### Pass 3: Design Taste

Go back through every frame that contains a text overlay — title cards, data callouts, kinetic text, attribution lines — and evaluate them as a **graphic designer**, not just a QA tester. "Visible" is not the bar. The bar is: **would this overlay look at home on a Bloomberg segment, a Netflix documentary title card, or a MKBHD intro?**

**For each text overlay frame, rate it on this scale:**

| Rating | Definition | Action |
|--------|-----------|--------|
| **Bold** | Fills the screen, impossible to miss, looks professionally designed | Keep |
| **Adequate** | Readable, decent contrast, but doesn't command attention | Fix if iterations remain |
| **Weak** | Technically present but a viewer at 1x speed would miss it entirely | **Mandatory fix** |

**Checklist for each overlay:**

1. **Size test:** Is the font large enough? At 1280x720, callouts need >= 36px, hero stats need >= 52px. If the text occupies less than 20% of the frame width, it's too small.
2. **Contrast test:** Does the text pop against its background? White text on a bright image with no background bar = invisible. Every callout needs either a semi-opaque background bar or a strong text shadow/border.
3. **Glance test:** If you saw this frame for exactly 1 second at normal playback speed, would you catch and read the callout? If the answer is "maybe" or "I'd have to look for it," it's too weak.
4. **Screenshot test:** If someone screenshots this frame and posts it on social media, would the overlay text be legible and look intentional? If it looks like an afterthought, redesign it.
5. **Layering test:** Does the callout feel like it belongs on this visual, or does it look pasted on? Good overlays have background bars, shadows, or positioning that integrates with the frame. Bad overlays are raw text floating over a busy image.

**Common failures to catch:**

- Data callout with font size 30 on a busy browser capture — vanishes at playback speed
- Title card that's technically centered but uses a thin font that looks like a watermark
- Kinetic text "hero stat" that's the same size as a subtitle — should dominate the screen
- Background bar too narrow (< 30% frame width) making the callout look like a tooltip instead of a lower-third
- Text color that blends with the underlying visual (cyan text on a blue-toned image)

**If an overlay is rated "weak":** Either increase the font size / background opacity and recompose, or replace the `TextAsset` overlay entirely with an AI-generated image that has the text baked in (more reliable for hero stats and title cards). See the design standards in [asset-production.md](asset-production.md) for concrete minimums.

### Pass 4: LLM critique (automated)

Use the `videodb` skill's `generate_text` with your observations, the transcript, and the scene descriptions:

```
You are a video director reviewing a rough cut of a briefing. Compare the intended plan against what was actually produced.

INTENDED TIMELINE (what should be at each timestamp):
{paste the intended_timeline data}

ACTUAL TRANSCRIPT (what was spoken):
{paste the transcript text with timestamps}

AI SCENE DESCRIPTIONS (per second):
{paste the scene_records from get_scene_index()}

VISUAL INSPECTION NOTES (from viewing frame images):
{paste your observations from Pass 1}

Review as a director:

1. NARRATION: Does the spoken audio match the intended narration? Flag mangled words, missing facts, or pacing issues.

2. NARRATION-VISUAL SYNC: For every anchor moment (where narration names a product, stat, or entity), is that entity visible on screen at that exact timestamp? Flag any case where the narration is ahead of or behind the visuals.

3. VISUAL ALIGNMENT: At each timestamp, does the scene description and the visual inspection match what the intended timeline says should be there? Flag mismatches.

4. DESIGN TASTE: For every text overlay (title cards, data callouts, kinetic text), evaluate: Is it large enough to notice at 1x playback? Does it look professionally designed or like an afterthought? Would it survive a screenshot posted to social media? Rate each as bold/adequate/weak. Any "weak" overlay is a critical issue.

5. PACING: Any segments under 8s or over 20s? Dead air? Does the hook breathe before narration? Does the outro breathe after narration ends?

6. VISUAL VARIETY: Consecutive segments with identical visual types? More than 2 static image segments? Missing data_viz or browser_capture?

7. CREATIVE DIRECTION: Step back and look at the whole piece. Does the order of segments make sense? Would rearranging segments improve the flow? Is there a better way to mix browser recordings, AI clips, data viz, and text to create a more dynamic result?

For each issue:
- TIMESTAMP: when it occurs
- SEGMENT: which segment
- PROBLEM: what's wrong
- FIX: specific action (regenerate asset, swap visual type, rearrange segments, adjust timing, recompose)
- SEVERITY: critical (must fix) or minor (fix if iterations remain)

If the piece is strong and no issues found, say "PASS".
```

## Director Pass

After running the critique, don't just patch bugs — think like a director:

**You have full creative authority to restructure the composition.**

- **Rearrange segments** if the flow doesn't work. Move a strong browser capture earlier to build credibility. Push a weaker genai image later where it matters less.
- **Swap asset types** mid-iteration. A genai image isn't landing? Replace it with kinetic text or a browser capture. A motion_scene feels generic? Replace it with a data_viz that actually shows something.
- **Mix and layer.** The final timeline should be a fluid mix of browser recordings, AI-generated clips, data visualizations, and kinetic text — not uniform blocks of the same type. If the scene index reveals monotony, break it up.
- **Adjust pacing.** Shorten segments that drag. Extend ones that need breathing room. Move the strongest visual to the hook if it's currently buried in the middle.
- **Recompose entirely** if needed. Don't be precious about the first composition. If the rough cut reveals that the segment order doesn't work, rebuild the timeline from scratch with the same assets in a better arrangement.

The scene index gives you the rough cut. The next iteration is your director's cut.

## Fix Strategy

Minimize regeneration work — fix only what's needed:

| Problem | Fix | What to Regenerate |
|---------|-----|-------------------|
| Narration mismatch | Adjust text, regenerate voice | Voice for that segment only |
| Visual doesn't match narration | Change prompt or visual type | Visual asset for that segment only |
| Segment too short/long | Adjust narration length | Voice + visual timing for that segment |
| Consecutive same visual type | Swap one segment's visual type | Visual asset for one segment |
| Music too loud/quiet | Adjust volume on music track | Nothing — just recompose timeline |
| Missing data call-out | Add TextAsset to timeline | Nothing — just recompose timeline |
| Flow/order doesn't work | Rearrange segments on timeline | Nothing — just recompose timeline |
| Weak segment buried in middle | Move it to hook position | Nothing — just recompose timeline |
| Asset type not working for segment | Swap visual_type, regenerate | New visual asset for that segment |
| Narration-visual sync drift | Shift clip start time or trim capture | Nothing — just recompose timeline |
| Narration ahead of loading browser | Increase `VideoAsset(start=N)` to skip blank frames | Nothing — just recompose timeline |
| Weak/invisible text overlay | Increase font size + bg opacity, or replace with text-embedded image | Regenerate image if switching to baked-in text |
| Callout appears before narration mentions it | Delay callout `add_clip` start by 1-2 seconds | Nothing — just recompose timeline |

**After fixing:** Recompose the timeline with the updated/rearranged assets and generate a new stream URL. This is the next draft version.

## Iteration Rules

- **Mandatory.** Always run at least one review cycle. No exceptions.
- **Max iterations:** Respects `MAX_ITERATIONS` from SKILL.md config (default: 5).
- **When to stop early:** Critique returns "PASS" or only has minor issues that don't affect comprehension. Earliest possible stop: after iteration 1.
- **When to keep going:** Critical issues remain (narration saying wrong things, visuals completely mismatched, dead air, monotonous flow).
- **Diminishing returns:** If the same issue persists after 2 fix attempts, accept it and move on. Some TTS or image generation issues can't be fully resolved.

## Delivery

When the review passes or you've hit the iteration limit:

1. Print the **final stream URL** and the **console player URL** (`https://console.videodb.io/player?url={STREAM_URL}`)
   - For public sharing, manually convert to: `https://player.videodb.io/watch?v={STREAM_URL}`
2. Print a **segment breakdown** with timestamps:
   ```
   00:00 - 00:08  Hook: [visual_type] — "opening narration preview..."
   00:08 - 00:20  Context: [visual_type] — "context narration preview..."
   ...
   ```
3. Note how many iterations were used and what was fixed in each
4. If at iteration limit with remaining issues, note what couldn't be resolved
