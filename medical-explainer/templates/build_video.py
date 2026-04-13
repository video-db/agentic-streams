"""
Medical Explainer Video Builder
Reads registry.json and assembles a professional medical explainer video using VideoDB.

Usage:
    python build_video.py <path-to-registry.json>

Architecture: 5-track timeline
    1. bg_track     -- Background image (full duration, Fit.crop)
    2. visual_track -- Content: images/videos (scale 0.75, Fit.contain, centered)
    3. text_track   -- Section labels (white on teal box)
    4. audio_track  -- Voiceovers (full volume)
    5. music_track  -- Background music (12% volume, looped)

Structure: title (4s) -> intro -> 2 explainer clips -> 2 illustrations -> 3 key facts -> outro (5s)
"""

import json
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


def make_text(text, size=88, width=None, height=None, max_chars_per_line=35):
    """White text on teal box, white border, shadow.

    Auto-sizes background box to fit text if width/height not specified.
    Long single lines are automatically wrapped to max_chars_per_line.

    Formula: width ~ longest_line * size * 0.65 + 40px padding
             height ~ line_count * size * 1.3 + 30px padding
    """
    # Auto-wrap long lines
    lines = text.split('\n')
    wrapped_lines = []
    for line in lines:
        if len(line) > max_chars_per_line:
            words = line.split(' ')
            current_line = []
            for word in words:
                test_line = ' '.join(current_line + [word])
                if len(test_line) <= max_chars_per_line:
                    current_line.append(word)
                else:
                    if current_line:
                        wrapped_lines.append(' '.join(current_line))
                    current_line = [word]
            if current_line:
                wrapped_lines.append(' '.join(current_line))
        else:
            wrapped_lines.append(line)

    text = '\n'.join(wrapped_lines)

    if width is None:
        lines = text.split('\n')
        longest_line = max(len(line) for line in lines)
        width = int(longest_line * size * 0.65 + 40)
        width = max(width, 400)
        width = min(width, 1600)

    if height is None:
        line_count = text.count('\n') + 1
        height = int(line_count * size * 1.3 + 30)
        height = max(height, 100)
        height = min(height, 500)

    return TextAsset(
        text=text,
        font=Font(family="Clear Sans", size=size, color="#FFFFFF", opacity=1.0),
        background=Background(
            width=width,
            height=height,
            color="#0d6e6e",
            opacity=0.90,
            text_alignment=TextAlignment.center,
        ),
        border=Border(color="#FFFFFF", width=2.0),
        shadow=Shadow(color="#000000", x=3, y=3),
    )


def build_video(registry_path: str) -> dict:
    """Build a medical explainer video from a registry.json file.

    Args:
        registry_path: Path to registry.json

    Returns:
        dict with stream_url, player_url, duration
    """
    reg = json.loads(Path(registry_path).read_text())

    conn = videodb.connect()

    bg = reg["background"]
    vids = reg["videos"]
    illustrations = reg["illustrations"]
    keyfacts = reg["keyfacts"]
    vo = reg["voiceovers"]

    # --- Calculate total duration ---
    content_dur = (
        TITLE_DUR
        + vo["intro"]["duration"]
        + vo["hook_1"]["duration"] + vids["video_1"]["clip_duration"]
        + vo["hook_2"]["duration"] + vids["video_2"]["clip_duration"]
        + vo["illustration_transition"]["duration"]
        + vo["illustration_1"]["duration"]
        + vo["illustration_2"]["duration"]
        + vo["keyfacts_transition"]["duration"]
        + vo["keyfact_1"]["duration"]
        + vo["keyfact_2"]["duration"]
        + vo["keyfact_3"]["duration"]
    )
    total_dur = content_dur + OUTRO_DUR

    # --- Build timeline ---
    timeline = Timeline(conn)
    timeline.background = "#0a1a2a"
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

    # Background music looped at 12%
    music_len = bg["music_duration"]
    music_loops = int(total_dur // music_len) + 1
    for i in range(music_loops):
        start = i * music_len
        remaining = total_dur - start
        d = min(music_len, remaining)
        if d > 0:
            music_track.add_clip(start, Clip(
                asset=AudioAsset(id=bg["music_id"], volume=0.12),
                duration=d,
            ))

    t = 0.0

    # --- TITLE CARD ---
    text_track.add_clip(t, Clip(
        asset=make_text(
            reg["term"].upper() + "\nMEDICAL EXPLAINER",
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
    # Show first illustration as intro visual
    visual_track.add_clip(t, Clip(
        asset=ImageAsset(id=illustrations["illustration_1"]["image_id"]),
        duration=vo["intro"]["duration"],
        fit=Fit.contain, scale=SCALE, position=Position.center, transition=FADE,
    ))
    t += vo["intro"]["duration"]

    # --- 2 EXPLAINER CLIPS ---
    for i in range(1, 3):
        vid = vids[f"video_{i}"]
        hook = vo[f"hook_{i}"]
        hook_dur = hook["duration"]
        preview_dur = hook_dur - LABEL_DUR
        clip_start = vid["clip_start"]
        clip_dur = vid["clip_duration"]
        preview_start = max(0, clip_start - preview_dur)

        # Text label (3s)
        text_track.add_clip(t, Clip(
            asset=make_text(vid["label"], size=88),
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

    # --- ILLUSTRATIONS ---
    text_track.add_clip(t, Clip(
        asset=make_text("HOW IT WORKS", size=80),
        duration=vo["illustration_transition"]["duration"],
        position=Position.center,
    ))
    audio_track.add_clip(t, Clip(
        asset=AudioAsset(id=vo["illustration_transition"]["id"]),
        duration=vo["illustration_transition"]["duration"],
    ))
    t += vo["illustration_transition"]["duration"]

    for i in range(1, 3):
        ill_vo = vo[f"illustration_{i}"]
        visual_track.add_clip(t, Clip(
            asset=ImageAsset(id=illustrations[f"illustration_{i}"]["image_id"]),
            duration=ill_vo["duration"],
            fit=Fit.contain, scale=SCALE, position=Position.center, transition=FADE,
        ))
        audio_track.add_clip(t, Clip(
            asset=AudioAsset(id=ill_vo["id"]),
            duration=ill_vo["duration"],
        ))
        t += ill_vo["duration"]

    # --- KEY FACTS ---
    text_track.add_clip(t, Clip(
        asset=make_text("KEY FACTS", size=80),
        duration=vo["keyfacts_transition"]["duration"],
        position=Position.center,
    ))
    audio_track.add_clip(t, Clip(
        asset=AudioAsset(id=vo["keyfacts_transition"]["id"]),
        duration=vo["keyfacts_transition"]["duration"],
    ))
    t += vo["keyfacts_transition"]["duration"]

    for i in range(1, 4):
        kf_vo = vo[f"keyfact_{i}"]
        visual_track.add_clip(t, Clip(
            asset=ImageAsset(id=keyfacts[f"keyfact_{i}"]["image_id"]),
            duration=kf_vo["duration"],
            fit=Fit.contain, scale=SCALE, position=Position.center, transition=FADE,
        ))
        audio_track.add_clip(t, Clip(
            asset=AudioAsset(id=kf_vo["id"]),
            duration=kf_vo["duration"],
        ))
        t += kf_vo["duration"]

    # --- OUTRO ---
    text_track.add_clip(t, Clip(
        asset=make_text("POWERED BY VIDEODB", size=80),
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
    topic_dir = Path(registry_path).parent.parent  # data/ -> term-slug/
    output_dir = topic_dir / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "output.json"
    output_path.write_text(json.dumps(result, indent=2))

    print(json.dumps(result, indent=2))
    print(f"\nPlayer: {result['player_url']}")
