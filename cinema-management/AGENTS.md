# Agent Instructions

## Goal

Build management training videos from existing Twelve Labs film indexes. The agent should search real indexed scenes, interpret them through a management theme, and compose a narrated stream with VideoDB.

## Required Inputs

Default demo values:

```env
FILM_TITLE=The Caine Mutiny
FILM_INDEX_ID=69c5ce575905babfd4fb0a9b
MANAGEMENT_THEME=authority, insubordination and the cost of blind obedience
```

Required secrets:

```env
TWELVELABS_API_KEY=
VIDEO_DB_API_KEY=
```

Do not commit real API keys.

## Execution Workflow

### 1. Pre-flight

Load `.env`, verify both API keys, and create `outputs/<slug>/` with:

```text
outputs/<slug>/
├── search_results.json
├── scenes.json
└── result.json
```

The slug should make parallel runs safe.

### 2. Twelve Labs Search

Use `client.search.query(...)` with:

```python
client.search.query(
    index_id=index_id,
    query_text=query,
    search_options=["visual", "audio", "transcription"],
    operator="or",
    page_limit=10,
)
```

If the index rejects one or more options, retry in this order:

```python
["visual", "transcription"]
["visual", "audio"]
["visual"]
["transcription"]
```

Search with multiple management-oriented queries rather than relying on one broad prompt.

### 3. Scene Selection

Normalize hits into records with:

```json
{
  "video_id": "...",
  "start": 123.4,
  "end": 139.2,
  "duration": 15.8,
  "query": "...",
  "rank": 1,
  "score": null,
  "confidence": null,
  "transcription": "..."
}
```

Clip rules:
- Add small padding around hits when possible.
- Keep each scene roughly `12-35` seconds.
- Deduplicate overlapping results from the same `video_id`.
- Keep at least `3` scenes and target `5`.
- Order final scenes chronologically.

### 4. Pegasus Analysis

Use `client.analyze(video_id=..., prompt=..., temperature=0.2, max_tokens=...)` when available. Prompt Pegasus to return a concise interpretation for the selected timestamp range:
- scene summary
- authority dynamic
- management lesson
- 2-3 sentence voiceover script

If Pegasus fails because the index lacks Pegasus support, keep the run going with a fallback script based on the theme, timestamp, and transcript.

### 5. HLS Retrieval

For each source `video_id`, retrieve the indexed asset:

```python
asset = client.indexes.indexed_assets.retrieve(index_id, video_id)
```

Use `asset.hls.video_url` when available. If the current SDK shape differs, inspect equivalent object or dict fields. If no HLS URL is available, fail with a clear message that the indexed asset must have video streaming enabled.

### 6. VideoDB Composition

Cut each selected HLS range into a short local MP4 first. The full film HLS can be slow or too large for direct VideoDB ingestion during iteration.

Connect with `videodb.connect()`, upload each local clip, generate scene narration with:

```python
coll.generate_voice(text=voiceover, voice_name="Default")
```

Assemble with VideoDB editor primitives:
- `Timeline`
- `Track`
- `Clip`
- `VideoAsset`
- `AudioAsset`
- `TextAsset`

Use a title card, scene labels, film clips, narration audio, and a closing card. Lower or mute source film audio under narration.

### 7. Output

Print:

```text
STREAM_URL=<raw-hls-url>
PLAYER_URL=https://console.videodb.io/player?url=<raw-hls-url>
```

Save the same URLs, selected scenes, scripts, and durations to `outputs/<slug>/result.json`.

## Validation

Run:

```bash
python -m py_compile cinema-management/agent.py
```

Then run the end-to-end script only when valid Twelve Labs and VideoDB keys are configured.

## Failure Handling

- Missing env vars: fail before any API calls.
- Search returns fewer than 3 usable scenes: fail and print the queries tried.
- Pegasus unavailable: warn and use fallback voiceover scripts.
- HLS missing: fail clearly; VideoDB cannot compose film clips without an accessible stream.
- VideoDB render failure: save intermediate `scenes.json` before exiting so the search work is preserved.
