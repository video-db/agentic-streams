#!/usr/bin/env python3
"""
Cinema Management Video Agent.

Searches a Twelve Labs film index for management-relevant scenes, generates
voiceover scripts, and assembles a streamable management lesson with VideoDB.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import signal
import subprocess
import sys
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

try:
    from dotenv import load_dotenv as _load_dotenv
except ImportError:
    _load_dotenv = None


DEFAULT_FILM_TITLE = "The Caine Mutiny"
DEFAULT_FILM_INDEX_ID = "69c5ce575905babfd4fb0a9b"
DEFAULT_MANAGEMENT_THEME = "authority, insubordination and the cost of blind obedience"
DEFAULT_SCENE_COUNT = 5
MIN_SCENE_COUNT = 3
MAX_SCENE_COUNT = 6
MIN_CLIP_DURATION = 12.0
MAX_CLIP_DURATION = 35.0
CLIP_PADDING = 3.0
TWELVE_LABS_REQUEST_OPTIONS = {"timeout_in_seconds": 30, "max_retries": 1}
OUTER_API_TIMEOUT_SECONDS = 45

ROOT = Path(__file__).resolve().parent


@dataclass
class Scene:
    video_id: str
    start: float
    end: float
    duration: float
    query: str
    rank: int | None = None
    score: float | None = None
    confidence: str | None = None
    transcription: str | None = None
    thumbnail_url: str | None = None
    analysis: str | None = None
    voiceover: str | None = None
    lesson_title: str | None = None
    source_hls_url: str | None = None
    local_clip_path: str | None = None
    videodb_video_id: str | None = None
    voiceover_audio_id: str | None = None
    voiceover_duration: float | None = None


def load_environment() -> None:
    if _load_dotenv is None:
        return
    _load_dotenv()
    _load_dotenv(ROOT / ".env")
    _load_dotenv(ROOT.parent / ".env")


def require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def make_slug(film_title: str) -> str:
    clean = re.sub(r"[^a-z0-9]+", "-", film_title.lower()).strip("-")
    return f"{clean or 'film'}-{uuid.uuid4().hex[:8]}"


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def get_attr(obj: Any, *names: str, default: Any = None) -> Any:
    current = obj
    for name in names:
        if current is None:
            return default
        if isinstance(current, dict):
            current = current.get(name)
        else:
            current = getattr(current, name, None)
    return default if current is None else current


def call_with_timeout(label: str, timeout_seconds: int, func: Any) -> Any:
    if not hasattr(signal, "SIGALRM"):
        return func()

    def _handler(signum: int, frame: Any) -> None:
        raise TimeoutError(f"{label} timed out after {timeout_seconds}s")

    previous_handler = signal.signal(signal.SIGALRM, _handler)
    signal.alarm(timeout_seconds)
    try:
        return func()
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, previous_handler)


def import_twelvelabs(api_key: str) -> Any:
    try:
        from twelvelabs import TwelveLabs
    except ImportError as exc:
        raise RuntimeError(
            "Missing dependency 'twelvelabs'. Install with: pip install twelvelabs"
        ) from exc
    return TwelveLabs(api_key=api_key)


def import_videodb() -> tuple[Any, Any]:
    try:
        import videodb
        from videodb.editor import (
            AudioAsset,
            Background,
            Border,
            Clip,
            Fit,
            Font,
            Position,
            TextAlignment,
            TextAsset,
            Timeline,
            Track,
            Transition,
            VideoAsset,
        )
    except ImportError as exc:
        raise RuntimeError(
            "Missing dependency 'videodb'. Install with: pip install videodb python-dotenv"
        ) from exc

    editor = {
        "AudioAsset": AudioAsset,
        "Background": Background,
        "Border": Border,
        "Clip": Clip,
        "Fit": Fit,
        "Font": Font,
        "Position": Position,
        "TextAlignment": TextAlignment,
        "TextAsset": TextAsset,
        "Timeline": Timeline,
        "Track": Track,
        "Transition": Transition,
        "VideoAsset": VideoAsset,
    }
    return videodb, editor


def resolve_ffmpeg() -> str:
    try:
        import imageio_ffmpeg

        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError as exc:
        raise RuntimeError(
            "Missing dependency 'imageio-ffmpeg'. Install with: pip install imageio-ffmpeg"
        ) from exc


def extract_scene_clips(scenes: list[Scene], run_dir: Path) -> None:
    ffmpeg = resolve_ffmpeg()
    clips_dir = run_dir / "clips"
    clips_dir.mkdir(parents=True, exist_ok=True)

    for idx, scene in enumerate(scenes, start=1):
        if not scene.source_hls_url:
            raise RuntimeError(f"Scene {idx} is missing source_hls_url")
        out_path = clips_dir / f"scene_{idx:02d}.mp4"
        command = [
            ffmpeg,
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-ss",
            f"{scene.start:.2f}",
            "-i",
            scene.source_hls_url,
            "-t",
            f"{scene.duration:.2f}",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "23",
            "-c:a",
            "aac",
            "-movflags",
            "+faststart",
            str(out_path),
        ]
        print(f"ffmpeg: extracting scene {idx} to {out_path}", flush=True)
        try:
            subprocess.run(
                command,
                check=True,
                timeout=max(90, int(scene.duration * 6)),
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError as exc:
            raise RuntimeError(
                f"ffmpeg failed for scene {idx}: {exc.stderr.strip() or exc.stdout.strip()}"
            ) from exc
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError(f"ffmpeg timed out while extracting scene {idx}") from exc

        scene.local_clip_path = str(out_path)


def management_queries(film_title: str, theme: str) -> list[str]:
    return [
        f"{film_title} scenes about {theme}",
        f"{film_title} authority conflict command breakdown insubordination",
        f"{film_title} blind obedience following orders moral responsibility",
        f"{film_title} leadership failure command climate crew dissent",
        f"{film_title} officers arguing about authority and duty",
        f"{film_title} consequences of poor leadership and obedience",
    ]


def iter_search_items(page: Any) -> Iterable[Any]:
    if page is None:
        return []
    items = get_attr(page, "items")
    if items:
        return items
    data = get_attr(page, "data")
    if data:
        return data
    if hasattr(page, "__iter__") and not isinstance(page, (dict, str, bytes)):
        return page
    return []


def search_once(client: Any, index_id: str, query: str, search_options: list[str]) -> list[Any]:
    kwargs = {
        "index_id": index_id,
        "query_text": query,
        "operator": "or",
        "page_limit": 10,
        "request_options": TWELVE_LABS_REQUEST_OPTIONS,
    }

    try:
        result = call_with_timeout(
            f"Twelve Labs search '{query}'",
            OUTER_API_TIMEOUT_SECONDS,
            lambda: client.search.query(search_options=search_options, **kwargs),
        )
    except TypeError:
        result = call_with_timeout(
            f"Twelve Labs search '{query}'",
            OUTER_API_TIMEOUT_SECONDS,
            lambda: client.search.query(options=search_options, **kwargs),
        )

    return list(iter_search_items(result))


def search_scenes(client: Any, index_id: str, film_title: str, theme: str) -> list[dict[str, Any]]:
    option_sets = [
        ["visual", "audio", "transcription"],
        ["visual", "transcription"],
        ["visual", "audio"],
        ["visual"],
        ["transcription"],
    ]
    raw: list[dict[str, Any]] = []

    for query in management_queries(film_title, theme):
        last_error: Exception | None = None
        for options in option_sets:
            print(f"Search: {query} options={options}", flush=True)
            try:
                items = search_once(client, index_id, query, options)
                for item in items:
                    start = get_attr(item, "start")
                    end = get_attr(item, "end")
                    video_id = get_attr(item, "video_id") or get_attr(item, "id")
                    if video_id is None or start is None or end is None:
                        continue
                    raw.append(
                        {
                            "video_id": str(video_id),
                            "start": float(start),
                            "end": float(end),
                            "query": query,
                            "options": options,
                            "rank": get_attr(item, "rank"),
                            "score": get_attr(item, "score"),
                            "confidence": get_attr(item, "confidence"),
                            "transcription": get_attr(item, "transcription"),
                            "thumbnail_url": get_attr(item, "thumbnail_url"),
                        }
                    )
                break
            except Exception as exc:  # SDK/API errors vary by installed version.
                last_error = exc
                continue
        if last_error and not raw:
            print(f"Search warning for query '{query}': {last_error}", file=sys.stderr)

    return raw


def normalize_scene(hit: dict[str, Any], padding: float) -> Scene:
    raw_start = max(0.0, float(hit["start"]) - padding)
    raw_end = max(raw_start + 1.0, float(hit["end"]) + padding)
    duration = raw_end - raw_start

    if duration < MIN_CLIP_DURATION:
        raw_end = raw_start + MIN_CLIP_DURATION
    elif duration > MAX_CLIP_DURATION:
        midpoint = (raw_start + raw_end) / 2
        raw_start = max(0.0, midpoint - MAX_CLIP_DURATION / 2)
        raw_end = raw_start + MAX_CLIP_DURATION

    return Scene(
        video_id=hit["video_id"],
        start=round(raw_start, 2),
        end=round(raw_end, 2),
        duration=round(raw_end - raw_start, 2),
        query=hit["query"],
        rank=hit.get("rank"),
        score=hit.get("score"),
        confidence=hit.get("confidence"),
        transcription=hit.get("transcription"),
        thumbnail_url=hit.get("thumbnail_url"),
    )


def overlaps(a: Scene, b: Scene) -> bool:
    if a.video_id != b.video_id:
        return False
    return max(a.start, b.start) < min(a.end, b.end)


def select_scenes(raw_hits: list[dict[str, Any]], scene_count: int, padding: float) -> list[Scene]:
    candidates = [normalize_scene(hit, padding) for hit in raw_hits]

    def sort_key(scene: Scene) -> tuple[int, float, float]:
        rank = scene.rank if isinstance(scene.rank, int) else 9999
        score = scene.score if isinstance(scene.score, (int, float)) else 0.0
        return (rank, -float(score), scene.start)

    selected: list[Scene] = []
    for scene in sorted(candidates, key=sort_key):
        if any(overlaps(scene, existing) for existing in selected):
            continue
        selected.append(scene)
        if len(selected) >= scene_count:
            break

    return sorted(selected, key=lambda s: (s.video_id, s.start))


def fallback_voiceover(scene: Scene, film_title: str, theme: str, scene_number: int) -> str:
    transcript_hint = ""
    if scene.transcription:
        transcript_hint = f" The dialogue centers on: {scene.transcription.strip()[:180]}"
    return (
        f"Scene {scene_number} from {film_title} puts the theme of {theme} into a concrete "
        f"management situation.{transcript_hint} Watch how authority is exercised, how dissent "
        "is handled, and what the organization pays when people either resist or obey without judgment."
    )


def analyze_scene(client: Any, scene: Scene, film_title: str, theme: str, scene_number: int) -> tuple[str, str, str]:
    prompt = (
        f"You are creating a management training video from {film_title}. "
        f"Focus on the scene from {scene.start:.1f}s to {scene.end:.1f}s. "
        f"Theme: {theme}. "
        "Return three concise sections with labels: SUMMARY, LESSON, VOICEOVER. "
        "VOICEOVER must be 2-3 sentences, suitable for narration over the clip, and should not invent dialogue."
    )

    try:
        print(
            f"Pegasus analysis: scene {scene_number} {scene.start:.1f}s-{scene.end:.1f}s",
            flush=True,
        )
        response = call_with_timeout(
            f"Pegasus analysis for scene {scene_number}",
            OUTER_API_TIMEOUT_SECONDS,
            lambda: client.analyze(
                video_id=scene.video_id,
                prompt=prompt,
                temperature=0.2,
                max_tokens=500,
                request_options=TWELVE_LABS_REQUEST_OPTIONS,
            ),
        )
        analysis = str(get_attr(response, "data", default=response)).strip()
    except Exception as exc:
        analysis = f"Pegasus analysis unavailable: {exc}"
        return analysis, f"Scene {scene_number}: Management Lens", fallback_voiceover(scene, film_title, theme, scene_number)

    lesson = extract_labeled_text(analysis, "LESSON") or f"Scene {scene_number}: Management Lens"
    voiceover = extract_labeled_text(analysis, "VOICEOVER") or fallback_voiceover(scene, film_title, theme, scene_number)
    return analysis, compact_label(lesson, scene_number), clean_voiceover(voiceover)


def extract_labeled_text(text: str, label: str) -> str | None:
    pattern = re.compile(
        rf"{label}\s*:?\s*(.*?)(?=\n[A-Z][A-Z ]{{2,}}\s*:|\Z)",
        re.DOTALL,
    )
    match = pattern.search(text)
    if not match:
        return None
    value = re.sub(r"\s+", " ", match.group(1)).strip(" -")
    return value or None


def compact_label(text: str, scene_number: int) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) > 70:
        text = text[:67].rstrip() + "..."
    if not text.lower().startswith("scene"):
        text = f"Scene {scene_number}: {text}"
    return text


def clean_voiceover(text: str) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    return text.strip('"')


def retrieve_hls_url(client: Any, index_id: str, video_id: str) -> str:
    errors: list[str] = []

    retrievals = [
        lambda: client.indexes.indexed_assets.retrieve(
            index_id, video_id, request_options=TWELVE_LABS_REQUEST_OPTIONS
        ),
        lambda: client.index.video.retrieve(
            index_id, video_id, request_options=TWELVE_LABS_REQUEST_OPTIONS
        ),
    ]

    for retrieve in retrievals:
        try:
            print(f"Retrieving HLS: video={video_id}", flush=True)
            asset = call_with_timeout(
                f"Twelve Labs HLS retrieval for {video_id}",
                OUTER_API_TIMEOUT_SECONDS,
                retrieve,
            )
        except Exception as exc:
            errors.append(str(exc))
            continue

        hls_url = (
            get_attr(asset, "hls", "video_url")
            or get_attr(asset, "hls", "url")
            or get_attr(asset, "hls_url")
            or get_attr(asset, "video_url")
            or get_attr(asset, "source", "url")
        )
        if hls_url:
            return str(hls_url)

    detail = "; ".join(errors[-2:]) if errors else "asset did not contain hls.video_url"
    raise RuntimeError(
        f"No HLS stream URL found for Twelve Labs video_id={video_id}. "
        f"Ensure the indexed asset was created with video streaming enabled. Detail: {detail}"
    )


def make_text_asset(editor: dict[str, Any], text: str, size: int = 64) -> Any:
    TextAsset = editor["TextAsset"]
    Font = editor["Font"]
    Background = editor["Background"]
    Border = editor["Border"]
    TextAlignment = editor["TextAlignment"]

    return TextAsset(
        text=wrap_text(text, 30),
        font=Font(family="Clear Sans", size=size, color="#FFFFFF", opacity=1.0),
        background=Background(
            width=1280,
            height=240,
            color="#101820",
            opacity=0.86,
            text_alignment=TextAlignment.center,
        ),
        border=Border(color="#D7B56D", width=2.0),
    )


def wrap_text(text: str, max_chars: int) -> str:
    words = text.split()
    lines: list[str] = []
    current: list[str] = []
    for word in words:
        candidate = " ".join(current + [word])
        if len(candidate) <= max_chars:
            current.append(word)
        else:
            if current:
                lines.append(" ".join(current))
            current = [word]
    if current:
        lines.append(" ".join(current))
    return "\n".join(lines)


def asset_id(asset: Any) -> str:
    value = get_attr(asset, "id") or get_attr(asset, "asset_id")
    if not value:
        raise RuntimeError(f"VideoDB asset did not expose an id: {asset!r}")
    return str(value)


def asset_duration(asset: Any, fallback: float) -> float:
    value = get_attr(asset, "length") or get_attr(asset, "duration")
    try:
        return float(value)
    except (TypeError, ValueError):
        return fallback


def compose_with_videodb(scenes: list[Scene], film_title: str, theme: str) -> dict[str, Any]:
    require_env("VIDEO_DB_API_KEY")
    videodb, editor = import_videodb()

    print("VideoDB: connecting", flush=True)
    conn = call_with_timeout(
        "VideoDB connect",
        OUTER_API_TIMEOUT_SECONDS,
        lambda: videodb.connect(),
    )
    print("VideoDB: loading default collection", flush=True)
    coll = call_with_timeout(
        "VideoDB get_collection",
        OUTER_API_TIMEOUT_SECONDS,
        lambda: conn.get_collection(),
    )

    source_video_ids: dict[str, str] = {}
    for scene in scenes:
        if not scene.local_clip_path:
            raise RuntimeError(f"Scene missing local_clip_path for video_id={scene.video_id}")
        if scene.local_clip_path not in source_video_ids:
            print(f"VideoDB: uploading local clip {scene.local_clip_path}", flush=True)
            uploaded = call_with_timeout(
                f"VideoDB upload local clip for {scene.video_id}",
                OUTER_API_TIMEOUT_SECONDS,
                lambda: coll.upload(file_path=scene.local_clip_path),
            )
            source_video_ids[scene.local_clip_path] = asset_id(uploaded)
        scene.videodb_video_id = source_video_ids[scene.local_clip_path]

        print(f"VideoDB: generating voiceover for {scene.lesson_title}", flush=True)
        audio = call_with_timeout(
            f"VideoDB generate_voice for {scene.lesson_title}",
            OUTER_API_TIMEOUT_SECONDS,
            lambda: coll.generate_voice(text=scene.voiceover or "", voice_name="Default"),
        )
        scene.voiceover_audio_id = asset_id(audio)
        # VideoDB validates requested clip duration against the exact media length.
        # Use a small safety margin because SDK-reported durations can round up.
        scene.voiceover_duration = max(0.1, asset_duration(audio, scene.duration) - 0.2)
        print(
            f"Voiceover: {scene.lesson_title} "
            f"({scene.voiceover_duration:.1f}s audio over {scene.duration:.1f}s scene)"
        )

    Timeline = editor["Timeline"]
    Track = editor["Track"]
    Clip = editor["Clip"]
    VideoAsset = editor["VideoAsset"]
    AudioAsset = editor["AudioAsset"]
    Fit = editor["Fit"]
    Position = editor["Position"]
    Transition = editor["Transition"]

    timeline = Timeline(conn)
    timeline.background = "#090C10"
    timeline.resolution = "1920x1080"

    visual_track = Track()
    text_track = Track()
    audio_track = Track()
    fade = Transition(in_="fade", out="fade", duration=0.4)

    t = 0.0
    title_duration = 5.0
    text_track.add_clip(
        t,
        Clip(
            asset=make_text_asset(editor, f"{film_title}\nManagement Lens", size=76),
            duration=title_duration,
            position=Position.center,
            transition=fade,
        ),
    )
    text_track.add_clip(
        t + 2.6,
        Clip(
            asset=make_text_asset(editor, theme, size=44),
            duration=title_duration - 2.6,
            position=Position.bottom,
        ),
    )
    t += title_duration

    for idx, scene in enumerate(scenes, start=1):
        clip_duration = scene.duration
        audio_duration = float(scene.voiceover_duration or scene.duration)
        segment_duration = max(clip_duration, audio_duration)
        visual_track.add_clip(
            t,
            Clip(
                asset=VideoAsset(id=scene.videodb_video_id, start=0, volume=0.18),
                duration=clip_duration,
                fit=Fit.crop,
                position=Position.center,
                transition=fade,
            ),
        )
        text_track.add_clip(
            t,
            Clip(
                asset=make_text_asset(editor, scene.lesson_title or f"Scene {idx}", size=46),
                duration=min(5.0, segment_duration),
                position=Position.bottom,
            ),
        )
        audio_track.add_clip(
            t,
            Clip(
                asset=AudioAsset(id=scene.voiceover_audio_id),
                duration=float(scene.voiceover_duration or scene.duration),
            ),
        )
        t += segment_duration

    closing_duration = 5.0
    text_track.add_clip(
        t,
        Clip(
            asset=make_text_asset(editor, "Management takeaway\nAuthority requires judgment.", size=64),
            duration=closing_duration,
            position=Position.center,
            transition=fade,
        ),
    )
    t += closing_duration

    timeline.add_track(visual_track)
    timeline.add_track(text_track)
    timeline.add_track(audio_track)

    print("VideoDB: generating final stream", flush=True)
    stream_url = call_with_timeout(
        "VideoDB generate_stream",
        OUTER_API_TIMEOUT_SECONDS * 2,
        lambda: timeline.generate_stream(),
    )
    return {
        "stream_url": stream_url,
        "player_url": f"https://console.videodb.io/player?url={stream_url}",
        "duration_seconds": round(t, 1),
        "duration_formatted": f"{int(t // 60)}:{int(t % 60):02d}",
    }


def build(args: argparse.Namespace) -> dict[str, Any]:
    load_environment()
    require_env("TWELVELABS_API_KEY")
    require_env("VIDEO_DB_API_KEY")

    film_title = args.film_title
    index_id = args.index_id
    theme = args.theme
    scene_count = max(MIN_SCENE_COUNT, min(MAX_SCENE_COUNT, args.scene_count))
    run_dir = ROOT / "outputs" / make_slug(film_title)
    run_dir.mkdir(parents=True, exist_ok=True)

    print(f"Run folder: {run_dir}", flush=True)
    print(f"Searching Twelve Labs index {index_id} for: {theme}", flush=True)

    client = import_twelvelabs(require_env("TWELVELABS_API_KEY"))
    raw_hits = search_scenes(client, index_id, film_title, theme)
    write_json(run_dir / "search_results.json", raw_hits)

    if not raw_hits:
        raise RuntimeError("Twelve Labs search returned no usable scene hits.")

    scenes = select_scenes(raw_hits, scene_count, args.clip_padding)
    if len(scenes) < MIN_SCENE_COUNT:
        raise RuntimeError(
            f"Only found {len(scenes)} usable scenes; need at least {MIN_SCENE_COUNT}."
        )

    print("Selected scenes:", flush=True)
    for idx, scene in enumerate(scenes, start=1):
        print(
            f"  {idx}. video={scene.video_id} {scene.start:.1f}s-{scene.end:.1f}s query='{scene.query}'",
            flush=True,
        )
        analysis, lesson_title, voiceover = analyze_scene(client, scene, film_title, theme, idx)
        scene.analysis = analysis
        scene.lesson_title = lesson_title
        scene.voiceover = voiceover
        scene.source_hls_url = retrieve_hls_url(client, index_id, scene.video_id)

    extract_scene_clips(scenes, run_dir)
    write_json(run_dir / "scenes.json", [asdict(scene) for scene in scenes])

    result = compose_with_videodb(scenes, film_title, theme)
    result.update(
        {
            "film_title": film_title,
            "index_id": index_id,
            "theme": theme,
            "scene_count": len(scenes),
            "scenes": [asdict(scene) for scene in scenes],
            "run_dir": str(run_dir),
        }
    )
    write_json(run_dir / "result.json", result)
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a cinema management video from a Twelve Labs index.")
    parser.add_argument("--film-title", default=os.getenv("FILM_TITLE", DEFAULT_FILM_TITLE))
    parser.add_argument("--index-id", default=os.getenv("FILM_INDEX_ID", DEFAULT_FILM_INDEX_ID))
    parser.add_argument("--theme", default=os.getenv("MANAGEMENT_THEME", DEFAULT_MANAGEMENT_THEME))
    parser.add_argument("--scene-count", type=int, default=DEFAULT_SCENE_COUNT)
    parser.add_argument("--clip-padding", type=float, default=CLIP_PADDING)
    return parser.parse_args()


def main() -> int:
    try:
        result = build(parse_args())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(json.dumps({k: result[k] for k in ("stream_url", "player_url", "duration_formatted")}, indent=2))
    print(f"STREAM_URL={result['stream_url']}")
    print(f"PLAYER_URL={result['player_url']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
