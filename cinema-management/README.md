# Cinema Management Video Agent

This agent turns an indexed film into a short management training video. It searches a Twelve Labs index for scenes related to a management theme, asks Pegasus to interpret those scenes, generates voiceover narration, and uses VideoDB to assemble a playable HLS stream.

## Demo

The included defaults build a management lesson from *The Caine Mutiny*:

```env
FILM_TITLE=The Caine Mutiny
FILM_INDEX_ID=69c5ce575905babfd4fb0a9b
MANAGEMENT_THEME=authority, insubordination and the cost of blind obedience
```

## Requirements

```bash
pip install twelvelabs videodb python-dotenv imageio-ffmpeg
```

Set credentials in your shell or in a repo-root `.env` file:

```env
TWELVELABS_API_KEY=your_twelve_labs_key
VIDEO_DB_API_KEY=your_videodb_key
```

The Twelve Labs index must already contain the film, have Marengo enabled for search, have Pegasus enabled for analysis, and expose an HLS stream for the indexed asset.

## Run

From the repo root:

```bash
python cinema-management/agent.py
```

With explicit values:

```bash
python cinema-management/agent.py \
  --film-title "The Caine Mutiny" \
  --index-id "69c5ce575905babfd4fb0a9b" \
  --theme "authority, insubordination and the cost of blind obedience"
```

Successful output includes:

```text
STREAM_URL=https://play.videodb.io/v1/...
PLAYER_URL=https://console.videodb.io/player?url=https://play.videodb.io/v1/...
```

The run metadata is saved under:

```text
cinema-management/outputs/<slug>/result.json
```

## How It Works

1. Searches the Twelve Labs index with management-oriented queries.
2. Deduplicates overlapping scene hits and keeps a short chronological storyboard.
3. Uses Pegasus analysis to frame each scene as a management lesson.
4. Retrieves the indexed asset HLS URL from Twelve Labs.
5. Cuts the selected HLS ranges into short local MP4 clips, uploads those clips to VideoDB, generates narration, and builds a multi-track timeline.
6. Prints a playable HLS stream URL and VideoDB player URL.

## Output Files

```text
cinema-management/
├── README.md
├── SKILL.md
├── AGENTS.md
├── agent.py
└── outputs/
    └── <slug>/
        ├── search_results.json
        ├── scenes.json
        └── result.json
```

## Notes

- The agent does not upload or index the film itself; it expects an existing Twelve Labs index.
- If the indexed asset was not created with video streaming enabled, Twelve Labs will not return an HLS URL and the script will stop with a clear error.
- Pegasus analysis is used when available. If it fails, the agent still creates management-framed fallback narration from the search metadata.
