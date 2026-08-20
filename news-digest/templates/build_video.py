"""
News Digest Video Builder
Reads registry.json and assembles a professional news digest video using VideoDB.

Usage:
    python build_video.py <path-to-registry.json>

Architecture: 5-track timeline
    1. bg_track     — Background image (full duration, Fit.crop)
    2. visual_track — Content: images/videos (scale 0.75, Fit.contain, centered)
    3. text_track   — Section labels (Option C: white on blue box)
    4. audio_track  — Voiceovers (full volume)
    5. music_track  — Background music (15% volume, looped)

Structure: title (4s) → intro → 3 news clips → 3 tweets → 2 articles → outro (5s)
"""

import json
import math
import sys
from pathlib import Path

from dotenv import load_dotenv
load_dotenv(".env")

import videodb
from videodb.editor import (
    Timeline, Track, Clip,
    VideoAsset, ImageAsset, AudioAsset, TextAsset,
    Fit, Position, Transition,
    Font, Border, Shadow, Background, TextAlignment,
)

# ============================================================
# CONSTANTS
# ============================================================

TITLE_DUR = 4.0
OUTRO_DUR = 5.0
LABEL_DUR = 3.0   # text label shown before muted video preview during hooks
SCALE = 0.75      # content scale (padding around visuals)
FADE = Transition(in_="fade", out="fade", duration=0.5)
FADE_IN = Transition(in_="fade", duration=0.5)
FADE_OUT = Transition(out="fade", duration=0.5)


TEXT_MAX_WIDTH = 1600   # 160px horizontal safe area on a 1920px frame
TEXT_MAX_HEIGHT = 500
TEXT_MIN_WIDTH = 400
TEXT_MIN_HEIGHT = 100
TEXT_PADDING_X = 80
TEXT_PADDING_Y = 40
# Use one full em per character as a conservative bound. This deliberately
# overestimates typical Clear Sans glyphs so wide uppercase titles stay padded.
CHAR_WIDTH_FACTOR = 1.0
LINE_HEIGHT_FACTOR = 1.3


def _wrap_line(line, max_chars):
    """Wrap one line at word boundaries, splitting an oversized token if needed."""
    if not line:
        return [""]

    wrapped = []
    current = ""
    for word in line.split():
        chunks = [word[i:i + max_chars] for i in range(0, len(word), max_chars)]
        for chunk in chunks:
            candidate = f"{current} {chunk}".strip()
            if len(candidate) <= max_chars:
                current = candidate
            else:
                if current:
                    wrapped.append(current)
                current = chunk
    if current:
        wrapped.append(current)
    return wrapped


def _layout_text_box(
    text,
    size,
    width=None,
    height=None,
    max_chars_per_line=35,
):
    """Return wrapped text and dimensions that fit inside the frame-safe box."""
    if max_chars_per_line < 1:
        raise ValueError("max_chars_per_line must be at least 1")

    box_width_limit = min(width or TEXT_MAX_WIDTH, TEXT_MAX_WIDTH)
    box_height_limit = min(height or TEXT_MAX_HEIGHT, TEXT_MAX_HEIGHT)
    fitted_size = size

    while True:
        usable_width = max(1, box_width_limit - 2 * TEXT_PADDING_X)
        safe_chars = max(
            1,
            math.floor(usable_width / (fitted_size * CHAR_WIDTH_FACTOR)),
        )
        wrap_at = min(max_chars_per_line, safe_chars)
        wrapped_lines = []
        for source_line in text.split("\n"):
            wrapped_lines.extend(_wrap_line(source_line, wrap_at))

        line_count = len(wrapped_lines)
        required_height = math.ceil(
            line_count * fitted_size * LINE_HEIGHT_FACTOR + 2 * TEXT_PADDING_Y
        )
        if required_height <= box_height_limit:
            break
        if fitted_size <= 32:
            raise ValueError("text is too long to fit inside the safe text box")
        fitted_size -= 2

    longest_line = max((len(line) for line in wrapped_lines), default=0)
    required_width = math.ceil(
        longest_line * fitted_size * CHAR_WIDTH_FACTOR + 2 * TEXT_PADDING_X
    )
    box_width = min(width, TEXT_MAX_WIDTH) if width else max(
        TEXT_MIN_WIDTH,
        min(required_width, TEXT_MAX_WIDTH),
    )
    box_height = min(height, TEXT_MAX_HEIGHT) if height else max(
        TEXT_MIN_HEIGHT,
        min(required_height, TEXT_MAX_HEIGHT),
    )

    return "\n".join(wrapped_lines), fitted_size, box_width, box_height


def make_text(text, size=88, width=None, height=None, max_chars_per_line=35):
    """Option C style: white text, wide blue box, white border, shadow.

    Text is wrapped against the actual frame-safe pixel width, not only a fixed
    character count. The font is reduced when necessary to keep every line and
    its padding inside the maximum box height.
    """
    text, size, width, height = _layout_text_box(
        text,
        size,
        width=width,
        height=height,
        max_chars_per_line=max_chars_per_line,
    )

    return TextAsset(
        text=text,
        font=Font(family="Clear Sans", size=size, color="#FFFFFF", opacity=1.0),
        background=Background(
            width=width,
            height=height,
            color="#1a3a5c",
            opacity=0.90,
            text_alignment=TextAlignment.center,
        ),
        border=Border(color="#FFFFFF", width=2.0),
        shadow=Shadow(color="#000000", x=3, y=3),
    )


def build_video(registry_path: str) -> dict:
    """Build a news digest video from a registry.json file.

    Args:
        registry_path: Path to registry.json

    Returns:
        dict with stream_url, player_url, duration
    """
    reg = json.loads(Path(registry_path).read_text())

    conn = videodb.connect()

    bg = reg["background"]
    vids = reg["videos"]
    tweets = reg["tweets"]
    articles = reg["articles"]
    vo = reg["voiceovers"]

    # --- Calculate total duration ---
    content_dur = (
        TITLE_DUR
        + vo["intro"]["duration"]
        + vo["hook_1"]["duration"] + vids["video_1"]["clip_duration"]
        + vo["hook_2"]["duration"] + vids["video_2"]["clip_duration"]
        + vo["hook_3"]["duration"] + vids["video_3"]["clip_duration"]
        + vo["tweet_transition"]["duration"]
        + vo["tweet_1"]["duration"]
        + vo["tweet_2"]["duration"]
        + vo["tweet_3"]["duration"]
        + vo["article_transition"]["duration"]
        + vo["article_1"]["duration"]
        + vo["article_2"]["duration"]
    )
    total_dur = content_dur + OUTRO_DUR

    # --- Build timeline ---
    timeline = Timeline(conn)
    timeline.background = "#0d0d1a"
    timeline.resolution = "1920x1080"

    bg_track = Track()
    visual_track = Track()
    text_track = Track()
    audio_track = Track()
    music_track = Track()

    # Background image
    bg_track.add_clip(0, Clip(
        asset=ImageAsset(id=bg["image_id"]),
        duration=total_dur,
        fit=Fit.crop,
    ))

    # Background music looped at 15%
    music_len = bg["music_duration"]
    music_loops = int(total_dur // music_len) + 1
    for i in range(music_loops):
        start = i * music_len
        remaining = total_dur - start
        d = min(music_len, remaining)
        if d > 0:
            music_track.add_clip(start, Clip(
                asset=AudioAsset(id=bg["music_id"], volume=0.15),
                duration=d,
            ))

    t = 0.0

    # --- TITLE CARD ---
    text_track.add_clip(t, Clip(
        asset=make_text(
            reg["topic"].upper() + "\nNEWS DIGEST",
            size=96,
        ),
        duration=TITLE_DUR,
        position=Position.center,
    ))
    t += TITLE_DUR

    # --- INTRO ---
    audio_track.add_clip(t, Clip(
        asset=AudioAsset(id=vo["intro"]["id"]),
        duration=vo["intro"]["duration"],
    ))
    # Show first tweet as intro visual
    visual_track.add_clip(t, Clip(
        asset=ImageAsset(id=tweets["tweet_1"]["image_id"]),
        duration=vo["intro"]["duration"],
        fit=Fit.contain, scale=SCALE, position=Position.center, transition=FADE,
    ))
    t += vo["intro"]["duration"]

    # --- 3 NEWS CLIPS ---
    for i in range(1, 4):
        vid = vids[f"video_{i}"]
        hook = vo[f"hook_{i}"]
        hook_dur = hook["duration"]
        preview_dur = hook_dur - LABEL_DUR
        clip_start = vid["clip_start"]
        clip_dur = vid["clip_duration"]
        preview_start = max(0, clip_start - preview_dur)

        # Text label (3s)
        text_track.add_clip(t, Clip(
            asset=make_text(vid["label"], size=88),  # auto-sizes
            duration=LABEL_DUR,
            position=Position.center,
        ))

        # Hook voiceover
        audio_track.add_clip(t, Clip(
            asset=AudioAsset(id=hook["id"]),
            duration=hook_dur,
        ))

        # Muted video preview after text
        visual_track.add_clip(t + LABEL_DUR, Clip(
            asset=VideoAsset(id=vid["video_id"], start=preview_start, volume=0),
            duration=preview_dur,
            fit=Fit.contain, scale=SCALE, position=Position.center, transition=FADE_IN,
        ))
        t += hook_dur

        # Actual clip with original audio
        visual_track.add_clip(t, Clip(
            asset=VideoAsset(id=vid["video_id"], start=clip_start, volume=1),
            duration=clip_dur,
            fit=Fit.contain, scale=SCALE, position=Position.center, transition=FADE,
        ))
        t += clip_dur

    # --- SOCIAL MEDIA ---
    text_track.add_clip(t, Clip(
        asset=make_text("SOCIAL MEDIA\nREACTIONS", size=80),  # auto-sizes
        duration=vo["tweet_transition"]["duration"],
        position=Position.center,
    ))
    audio_track.add_clip(t, Clip(
        asset=AudioAsset(id=vo["tweet_transition"]["id"]),
        duration=vo["tweet_transition"]["duration"],
    ))
    t += vo["tweet_transition"]["duration"]

    for i in range(1, 4):
        tw_vo = vo[f"tweet_{i}"]
        visual_track.add_clip(t, Clip(
            asset=ImageAsset(id=tweets[f"tweet_{i}"]["image_id"]),
            duration=tw_vo["duration"],
            fit=Fit.contain, scale=SCALE, position=Position.center, transition=FADE,
        ))
        audio_track.add_clip(t, Clip(
            asset=AudioAsset(id=tw_vo["id"]),
            duration=tw_vo["duration"],
        ))
        t += tw_vo["duration"]

    # --- ARTICLES ---
    text_track.add_clip(t, Clip(
        asset=make_text("DEEP ANALYSIS", size=80),  # auto-sizes
        duration=vo["article_transition"]["duration"],
        position=Position.center,
    ))
    audio_track.add_clip(t, Clip(
        asset=AudioAsset(id=vo["article_transition"]["id"]),
        duration=vo["article_transition"]["duration"],
    ))
    t += vo["article_transition"]["duration"]

    for i in range(1, 3):
        art = articles[f"article_{i}"]
        art_vo = vo[f"article_{i}"]
        art_dur = art_vo["duration"]
        scroll_dur = art["scroll_duration"]
        screenshot_dur = art_dur - scroll_dur

        audio_track.add_clip(t, Clip(
            asset=AudioAsset(id=art_vo["id"]),
            duration=art_dur,
        ))
        visual_track.add_clip(t, Clip(
            asset=VideoAsset(id=art["scroll_id"], volume=0),
            duration=scroll_dur,
            fit=Fit.contain, scale=SCALE, position=Position.center, transition=FADE_IN,
        ))
        visual_track.add_clip(t + scroll_dur, Clip(
            asset=ImageAsset(id=art["screenshot_id"]),
            duration=screenshot_dur,
            fit=Fit.contain, scale=SCALE, position=Position.center, transition=FADE_OUT,
        ))
        t += art_dur

    # --- OUTRO ---
    text_track.add_clip(t, Clip(
        asset=make_text("POWERED BY VIDEODB", size=80),  # auto-sizes
        duration=OUTRO_DUR,
        position=Position.center,
    ))

    # --- ASSEMBLE ---
    timeline.add_track(bg_track)
    timeline.add_track(visual_track)
    timeline.add_track(text_track)
    timeline.add_track(audio_track)
    timeline.add_track(music_track)

    stream_url = timeline.generate_stream()
    total = t + OUTRO_DUR

    result = {
        "stream_url": stream_url,
        "player_url": f"https://console.videodb.io/player?url={stream_url}",
        "duration_seconds": round(total, 1),
        "duration_formatted": f"{int(total // 60)}:{int(total % 60):02d}",
    }
    return result


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python build_video.py <path-to-registry.json>")
        sys.exit(1)

    registry_path = sys.argv[1]
    result = build_video(registry_path)

    # Save output.json in output/ folder (sibling of data/)
    topic_dir = Path(registry_path).parent.parent  # data/ -> topic-slug/
    output_dir = topic_dir / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "output.json"
    output_path.write_text(json.dumps(result, indent=2))

    print(json.dumps(result, indent=2))
    print(f"\nPlayer: {result['player_url']}")
