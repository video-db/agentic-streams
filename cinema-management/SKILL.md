---
name: cinema-management-video-agent
description: Turn a searchable film index into a management training video. Given a Twelve Labs index ID, film title, and management theme, finds relevant scenes with Marengo search, uses Pegasus analysis for scene interpretation, generates management-framed narration, and assembles a streamable video with VideoDB.
---

# Cinema Management Video Agent

Use this skill when the user wants to:
- Turn scenes from an indexed film into a management lesson.
- Search an existing Twelve Labs index for leadership, authority, ethics, obedience, conflict, or organizational behavior moments.
- Generate a narrated training video that uses real film scenes as evidence.
- Produce a playable HLS stream URL with VideoDB.

## Demo Configuration

```env
FILM_TITLE=The Caine Mutiny
FILM_INDEX_ID=69c5ce575905babfd4fb0a9b
MANAGEMENT_THEME=authority, insubordination and the cost of blind obedience
```

## Setup

Install the required Python packages:

```bash
pip install twelvelabs videodb python-dotenv imageio-ffmpeg
```

Set API keys in the environment or in a repo-root `.env` file:

```env
TWELVELABS_API_KEY=your_twelve_labs_key
VIDEO_DB_API_KEY=your_videodb_key
```

The Twelve Labs index must already contain the target film and must support:
- Marengo search for `visual`, `audio`, and/or `transcription`.
- Pegasus analysis for management-framed scene interpretation.
- HLS retrieval through indexed-asset metadata if VideoDB will compose directly from the indexed source.

## Inputs

Required:
- `index_id`: Twelve Labs index ID.
- `theme`: Management theme used to search and frame narration.

Optional:
- `film_title`: Used for titles, prompts, and output metadata.
- `scene_count`: Defaults to `5`; valid range is `3` to `6`.
- `clip_padding`: Seconds added before and after each selected search hit.

## Pipeline

### 1. Pre-flight

Verify `TWELVELABS_API_KEY` and `VIDEO_DB_API_KEY`, load `.env`, create a unique run folder under `outputs/<slug>/`, and connect to both services.

### 2. Search Scenes

Run several Twelve Labs search queries against the supplied index:
- the raw management theme
- authority and command breakdown
- insubordination and dissent
- blind obedience and moral responsibility
- consequences of poor leadership

Search should request `visual`, `audio`, and `transcription` options, then gracefully retry with smaller option sets if the index does not support all modalities.

### 3. Select a Storyboard

Deduplicate overlapping results, normalize clip durations, keep `3-6` strong scenes, and order them chronologically. Each scene should include:
- `video_id`
- `start`
- `end`
- `duration`
- `score` or `rank`
- any available transcript text
- a generated management lesson

### 4. Pegasus Interpretation

For each selected scene, use Twelve Labs Pegasus analysis when available. The prompt should ask for:
- what happens in the timestamp range
- the authority or obedience dynamic
- the management lesson
- a concise voiceover script

If analysis fails, create a deterministic fallback voiceover from the search hit metadata and theme.

### 5. VideoDB Composition

Retrieve the indexed asset HLS URL from Twelve Labs, cut each selected range into a short local MP4 with ffmpeg, upload those short clips to VideoDB, generate voiceover audio for each scene, then assemble:
- film clips as the visual track
- generated narration as the audio track
- title, scene label, and closing `TextAsset` overlays

The final script must print:

```text
STREAM_URL=https://...
PLAYER_URL=https://console.videodb.io/player?url=https://...
```

It must also save `outputs/<slug>/result.json`.

## Quality Rules

- Use the film index as the source of truth. Do not invent scene details.
- Prefer 4-6 short scenes over one long excerpt.
- Keep narration management-focused: leadership responsibility, command climate, dissent, compliance pressure, and decision cost.
- Mute or lower film audio under voiceover so narration is intelligible.
- Fail clearly if the Twelve Labs indexed asset does not expose an HLS URL; VideoDB needs an accessible source stream to compose film clips.

## Run

```bash
python cinema-management/agent.py
```

With overrides:

```bash
python cinema-management/agent.py \
  --film-title "The Caine Mutiny" \
  --index-id "69c5ce575905babfd4fb0a9b" \
  --theme "authority, insubordination and the cost of blind obedience"
```

## Deliverables

A successful run produces:
- terminal logs listing selected scenes and narration durations
- `outputs/<slug>/result.json`
- raw HLS stream URL
- VideoDB console player URL
