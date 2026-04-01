# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "videodb",
#   "python-dotenv",
#   "pillow",
#   "requests",
# ]
# ///

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import json
import os
from typing import Optional

from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont
import requests
import videodb
from videodb import SearchType
from videodb.editor import Timeline, Track, Clip, ImageAsset, AudioAsset, VideoAsset, Fit, Transition

ROOT = Path(__file__).resolve().parent.parent
DAY = ROOT / "2026-04-01"
ASSETS = ROOT / "assets" / "2026-04-01"
REPORT = ROOT / "reports" / "2026-04-01-midday-financial-news-brief.md"
OUT = DAY / "video_build"
OUT.mkdir(parents=True, exist_ok=True)
ET = ZoneInfo("America/New_York")

W, H = 1280, 720
BG = "#0b1020"
FG = "#f3f5f7"
MUTED = "#a9b3c1"
ACCENT = "#59c3ff"
GREEN = "#5fd38d"
RED = "#ff6b6b"
YELLOW = "#ffd166"


@dataclass
class Scene:
    kind: str
    image_path: Optional[Path] = None
    narration: Optional[str] = None
    duration: float | None = None
    video_id: Optional[str] = None
    video_start: float = 0.0
    video_volume: float = 1.0


def font(size: int, bold: bool = False):
    candidates = []
    if bold:
        candidates += [
            "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
            "/Library/Fonts/Arial Bold.ttf",
        ]
    candidates += [
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/Library/Fonts/Arial.ttf",
        "/System/Library/Fonts/Supplemental/Helvetica.ttc",
    ]
    for c in candidates:
        if Path(c).exists():
            return ImageFont.truetype(c, size=size)
    return ImageFont.load_default()


def draw_wrapped(draw, text, xy, max_width, font_obj, fill=FG, line_gap=10):
    x, y = xy
    words = text.split()
    lines = []
    cur = ""
    for word in words:
        trial = word if not cur else cur + " " + word
        bbox = draw.textbbox((0, 0), trial, font=font_obj)
        if bbox[2] - bbox[0] <= max_width:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    for line in lines:
        draw.text((x, y), line, font=font_obj, fill=fill)
        bbox = draw.textbbox((x, y), line, font=font_obj)
        y += (bbox[3] - bbox[1]) + line_gap
    return y


def card(title: str, subtitle: str | None = None, bullets=None, footer: str | None = None, accent=ACCENT, out_name="card.png"):
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle((40, 40, W - 40, H - 40), radius=26, outline="#22304d", width=3, fill="#11182d")
    draw.rounded_rectangle((60, 60, 78, 140), radius=9, fill=accent)
    title_font = font(46, bold=True)
    body_font = font(30)
    small_font = font(24)
    y = 78
    draw.text((100, y), title, font=title_font, fill=FG)
    y += 78
    if subtitle:
        y = draw_wrapped(draw, subtitle, (100, y), W - 180, body_font, fill=MUTED, line_gap=12) + 18
    if bullets:
        for bullet in bullets:
            fill = FG
            dot = accent
            if bullet.startswith("+"):
                dot = GREEN
            elif bullet.startswith("-"):
                dot = RED
            elif bullet.startswith("!"):
                dot = YELLOW
            content = bullet[1:].strip() if bullet[:1] in "+-!" else bullet
            draw.ellipse((108, y + 10, 124, y + 26), fill=dot)
            y = draw_wrapped(draw, content, (145, y), W - 220, body_font, fill=fill, line_gap=12) + 10
    if footer:
        draw.line((100, H - 110, W - 100, H - 110), fill="#2a3857", width=2)
        draw.text((100, H - 90), footer, font=small_font, fill=MUTED)
    path = OUT / out_name
    img.save(path)
    return path


def chart_slide(title: str, chart_png: Path, footer: str, out_name: str):
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle((30, 30, W - 30, H - 30), radius=24, outline="#22304d", width=3, fill="#11182d")
    draw.text((70, 55), title, font=font(42, bold=True), fill=FG)
    chart = Image.open(chart_png).convert("RGB")
    chart.thumbnail((W - 140, H - 220))
    x = (W - chart.width) // 2
    y = 130
    img.paste(chart, (x, y))
    draw.text((70, H - 80), footer, font=font(24), fill=MUTED)
    path = OUT / out_name
    img.save(path)
    return path


def screenshot_slide(title: str, screenshot_path: Path, crop_box, footer: str, out_name: str, accent=ACCENT):
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle((30, 30, W - 30, H - 30), radius=24, outline="#22304d", width=3, fill="#11182d")
    draw.rounded_rectangle((60, 58, 76, 118), radius=8, fill=accent)
    draw.text((95, 52), title, font=font(38, bold=True), fill=FG)

    shot = Image.open(screenshot_path).convert("RGB")
    crop = shot.crop(crop_box)
    crop.thumbnail((W - 120, H - 210))
    frame_x = (W - crop.width) // 2
    frame_y = 120
    draw.rounded_rectangle((frame_x - 8, frame_y - 8, frame_x + crop.width + 8, frame_y + crop.height + 8), radius=16, fill="#e9edf3")
    img.paste(crop, (frame_x, frame_y))
    draw.text((70, H - 80), footer, font=font(24), fill=MUTED)
    path = OUT / out_name
    img.save(path)
    return path


def fetch_series(symbol: str, days: int = 7):
    import time
    end = int(time.time())
    start = end - days * 24 * 3600
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?period1={start}&period2={end}&interval=5m&includePrePost=true&events=div%2Csplits"
    j = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=20).json()["chart"]["result"][0]
    closes = j["indicators"]["quote"][0]["close"]
    out = []
    for ts, close in zip(j["timestamp"], closes):
        if close is None:
            continue
        dt = datetime.fromtimestamp(ts, timezone.utc).astimezone(ET)
        out.append((dt, float(close)))
    return out


def draw_chart(series_list, title: str, footer: str, out_name: str, ylabel: str = ""):
    width, height = 1200, 675
    img = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(img)
    colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd"]

    title_font = font(28, bold=True)
    legend_font = font(17)
    axis_font = font(15)
    footer_font = font(18)

    title_y = 18
    legend_y = 58
    plot_top = 105
    plot_bottom = 585
    plot_left = 92
    plot_right = 1145
    footer_y = 628

    all_x = [x for s in series_list for x, _ in s["data"]]
    all_y = [y for s in series_list for _, y in s["data"]]
    min_x, max_x = min(all_x), max(all_x)
    min_y, max_y = min(all_y), max(all_y)
    if min_y == max_y:
        min_y -= 1
        max_y += 1
    pad = (max_y - min_y) * 0.08
    min_y -= pad
    max_y += pad

    def sx(dt):
        frac = (dt.timestamp() - min_x.timestamp()) / (max_x.timestamp() - min_x.timestamp() or 1)
        return plot_left + frac * (plot_right - plot_left)

    def sy(val):
        frac = (max_y - val) / (max_y - min_y)
        return plot_top + frac * (plot_bottom - plot_top)

    draw.text((36, title_y), title, font=title_font, fill="#111")

    lx = 36
    for idx, s in enumerate(series_list):
        color = s.get("color", colors[idx % len(colors)])
        draw.line((lx, legend_y + 9, lx + 24, legend_y + 9), fill=color, width=4)
        draw.text((lx + 32, legend_y), s["label"], font=legend_font, fill="#222")
        lx += 150 + int(draw.textbbox((0, 0), s["label"], font=legend_font)[2])

    if ylabel:
        bbox = draw.textbbox((0, 0), ylabel, font=axis_font)
        draw.text((width - (bbox[2] - bbox[0]) - 28, title_y + 4), ylabel, font=axis_font, fill="#666")

    for i in range(6):
        yv = min_y + (max_y - min_y) * i / 5
        py = sy(yv)
        draw.line((plot_left, py, plot_right, py), fill="#e8e8e8", width=1)
        label = f"{yv:.2f}"
        bbox = draw.textbbox((0, 0), label, font=axis_font)
        draw.text((plot_left - 14 - (bbox[2] - bbox[0]), py - 8), label, font=axis_font, fill="#555")

    from datetime import timedelta
    cur = min_x.replace(minute=0, second=0, microsecond=0)
    hours_span = max(1, int((max_x - min_x).total_seconds() // 3600))
    step_hours = 1 if hours_span <= 8 else 2
    while cur <= max_x:
        px = sx(cur)
        draw.line((px, plot_top, px, plot_bottom), fill="#f2f2f2", width=1)
        label = cur.strftime("%H:%M")
        bbox = draw.textbbox((0, 0), label, font=axis_font)
        draw.text((px - (bbox[2] - bbox[0]) / 2, plot_bottom + 10), label, font=axis_font, fill="#555")
        cur += timedelta(hours=step_hours)

    draw.line((plot_left, plot_top, plot_left, plot_bottom), fill="#999", width=2)
    draw.line((plot_left, plot_bottom, plot_right, plot_bottom), fill="#999", width=2)

    for idx, s in enumerate(series_list):
        color = s.get("color", colors[idx % len(colors)])
        points = [(sx(x), sy(y)) for x, y in s["data"]]
        draw.line(points, fill=color, width=3)

    draw.text((36, footer_y), footer, font=footer_font, fill="#666")
    path = OUT / out_name
    img.save(path)
    return path


def build_chart_pngs():
    out = {}
    for sym, label, color in [("^GSPC", "S&P 500", "#1f77b4"), ("^IXIC", "Nasdaq", "#ff7f0e"), ("^DJI", "Dow", "#2ca02c")]:
        rows = [r for r in fetch_series(sym) if r[0].date().isoformat() == "2026-04-01" and ((r[0].hour > 9 or (r[0].hour == 9 and r[0].minute >= 30)) and (r[0].hour < 16 or (r[0].hour == 16 and r[0].minute == 0)))]
        base = rows[0][1]
        out.setdefault("market_series", []).append({"label": label, "color": color, "data": [(x, (y / base - 1) * 100) for x, y in rows]})
    out["market-overview"] = draw_chart(out["market_series"], "U.S. Equity Indexes – Apr 1, 2026", "Intraday performance from open.", "market-overview.png", ylabel="% from open")

    cl = [r for r in fetch_series("CL=F") if r[0].date().isoformat() == "2026-04-01" and ((r[0].hour > 9 or (r[0].hour == 9 and r[0].minute >= 30)) and (r[0].hour < 16 or (r[0].hour == 16 and r[0].minute == 0)))]
    tnx = [r for r in fetch_series("^TNX") if r[0].date().isoformat() == "2026-04-01" and ((r[0].hour > 9 or (r[0].hour == 9 and r[0].minute >= 30)) and (r[0].hour < 16 or (r[0].hour == 16 and r[0].minute == 0)))]
    clb, tny = cl[0][1], tnx[0][1]
    out["oil-rates"] = draw_chart([
        {"label": "WTI crude", "color": "#d62728", "data": [(x, (y / clb - 1) * 100) for x, y in cl]},
        {"label": "US 10Y yield", "color": "#9467bd", "data": [(x, (y / tny - 1) * 100) for x, y in tnx]},
    ], "Oil and Rates – Apr 1, 2026", "Intraday performance from open.", "oil-rates.png", ylabel="% from open")

    for sym, name, title in [("INTC", "intc-intraday", "Intel intraday – Apr 1, 2026"), ("LLY", "lly-intraday", "Eli Lilly intraday – Apr 1, 2026")]:
        rows = [r for r in fetch_series(sym) if r[0].date().isoformat() == "2026-04-01" and ((r[0].hour > 9 or (r[0].hour == 9 and r[0].minute >= 30)) and (r[0].hour < 16 or (r[0].hour == 16 and r[0].minute == 0)))]
        out[name] = draw_chart([{"label": sym, "color": "#1f77b4", "data": rows}], title, "Intraday price in dollars.", f"{name}.png", ylabel="price")

    rows = [r for r in fetch_series("NKE") if (r[0].date().isoformat() in ["2026-03-31", "2026-04-01"]) and (r[0] >= datetime(2026, 3, 31, 15, 30, tzinfo=ET)) and (r[0] <= datetime(2026, 4, 1, 12, 30, tzinfo=ET))]
    out["nke-postearnings"] = draw_chart([{"label": "NKE", "color": "#d62728", "data": rows}], "Nike after-hours selloff and Apr 1 follow-through", "Window starts before Mar 31 earnings release and runs into Apr 1 midday.", "nke-postearnings.png", ylabel="price")
    return out


def build_scenes(chart_pngs, clip_proofs):
    shots = {
        "adp": ROOT / "2026-04-01" / "screenshots" / "adp-official.png",
        "intel": ROOT / "2026-04-01" / "screenshots" / "intel-official.png",
        "lly": ROOT / "2026-04-01" / "screenshots" / "lly-cnbc.png",
        "nike": ROOT / "2026-04-01" / "screenshots" / "nike-cnbc.png",
    }
    scenes = []
    scenes.append(Scene(
        kind="image",
        image_path=card(
            "Financial News Proof Brief",
            "April 1, 2026 · Midday update built from official releases, cleaned reporting, intraday market data, and selected video proof clips.",
            bullets=[
                "+ S&P 500 +0.38% from open",
                "+ Nasdaq +0.60% from open",
                "+ Dow +0.18% from open",
            ],
            footer="This cut combines source screenshots, charts, and selected YouTube clips located with VideoDB web search and transcript search.",
            out_name="01-title.png",
        ),
        narration="This is a proof first financial news brief for April first, twenty twenty six. As of about twelve twenty eight p.m. Eastern, the S and P five hundred was up zero point three eight percent from the open, the Nasdaq was up zero point six zero percent, and the Dow was up zero point one eight percent.",
    ))
    scenes.append(Scene(
        kind="image",
        image_path=chart_slide(
            "Market overview",
            chart_pngs["market-overview"],
            "Source: Yahoo Finance intraday data captured around 12:28 PM ET.",
            "02-market-overview.png",
        ),
        narration="The broad tape was constructive, with the Nasdaq leading. That suggests investors were willing to lean into select growth and company specific stories rather than trade the entire market off one macro shock.",
    ))
    scenes.append(Scene(
        kind="image",
        image_path=chart_slide(
            "Oil and rates context",
            chart_pngs["oil-rates"],
            "WTI crude stayed higher intraday while the ten year yield drifted slightly lower.",
            "03-oil-rates.png",
        ),
        narration="Oil stayed elevated intraday, but the ten year Treasury yield was slightly lower. That mix helps explain why risk appetite stayed intact even with geopolitical stress still in the background.",
    ))
    scenes.append(Scene(
        kind="image",
        image_path=screenshot_slide(
            "ADP official release",
            shots["adp"],
            (40, 110, 1400, 1250),
            "Official source crop showing headline and the opening section of the ADP report.",
            "04-adp-proof.png",
            accent=YELLOW,
        ),
        narration="On the macro side, A D P reported sixty two thousand private payroll gains in March, above expectations. This is the official report. But the composition matters. Hiring remained concentrated, especially in health care and construction.",
    ))
    if clip_proofs.get("adp"):
        cp = clip_proofs["adp"]
        scenes.append(Scene(kind="video", video_id=cp["video_id"], video_start=cp["start"], duration=cp["duration"], video_volume=1.0))
    scenes.append(Scene(
        kind="image",
        image_path=screenshot_slide(
            "Intel official release",
            shots["intel"],
            (260, 0, 1180, 1500),
            "Official Intel newsroom crop showing the headline and transaction details.",
            "05-intel-proof.png",
            accent=GREEN,
        ),
        narration="Intel was one of the clearest company specific winners. This official Intel newsroom release says the company will repurchase Apollo's forty nine percent stake in the Ireland fab joint venture for fourteen point two billion dollars. The market appears to have read that as a signal of stronger balance sheet confidence and strategic commitment.",
    ))
    scenes.append(Scene(
        kind="image",
        image_path=chart_slide(
            "Intel intraday",
            chart_pngs["intc-intraday"],
            "INTC was up roughly 3.9% from the open by about 12:28 PM ET.",
            "06-intel-chart.png",
        ),
        narration="The price action supports that interpretation. Intel materially outperformed the broader market through midday trading.",
    ))
    scenes.append(Scene(
        kind="image",
        image_path=screenshot_slide(
            "CNBC: Lilly obesity-pill approval",
            shots["lly"],
            (120, 120, 1060, 1500),
            "Media-source crop showing the headline and key points panel for the FDA approval story.",
            "07-lly-proof.png",
            accent=ACCENT,
        ),
        narration="Eli Lilly also traded higher after F D A approval of Foundayo, its G L P one obesity pill. This media source shows the approval headline and key points. The significance here is platform expansion.",
    ))
    if clip_proofs.get("lly"):
        cp = clip_proofs["lly"]
        scenes.append(Scene(kind="video", video_id=cp["video_id"], video_start=cp["start"], duration=cp["duration"], video_volume=1.0))
    scenes.append(Scene(
        kind="image",
        image_path=chart_slide(
            "Eli Lilly intraday",
            chart_pngs["lly-intraday"],
            "LLY was up roughly 2.4% from the open by about 12:28 PM ET.",
            "08-lly-chart.png",
        ),
        narration="The stock's positive response is directionally consistent with a favorable regulatory catalyst.",
    ))
    scenes.append(Scene(
        kind="image",
        image_path=screenshot_slide(
            "CNBC: Nike weak outlook",
            shots["nike"],
            (120, 120, 1060, 1500),
            "Media-source crop showing the weak outlook headline and the key points section.",
            "09-nke-proof.png",
            accent=RED,
        ),
        narration="Nike is the clearest negative example in this package. This media source shows the weak outlook headline. The company beat on revenue and earnings, but weak forward guidance dominated the story.",
    ))
    if clip_proofs.get("nike"):
        cp = clip_proofs["nike"]
        scenes.append(Scene(kind="video", video_id=cp["video_id"], video_start=cp["start"], duration=cp["duration"], video_volume=1.0))
    scenes.append(Scene(
        kind="image",
        image_path=chart_slide(
            "Nike after-hours selloff and Apr 1 follow-through",
            chart_pngs["nke-postearnings"],
            "From the Mar. 31 earnings window into Apr. 1 midday, NKE lost roughly 14.6%.",
            "10-nke-chart.png",
        ),
        narration="The chart shows why markets usually care more about the forward path than the quarter just reported. Nike's after hours selloff continued into the next day.",
    ))
    scenes.append(Scene(
        kind="image",
        image_path=card(
            "Bottom line",
            "The broad market held up, but the strongest evidence sat in company specific moves rather than one dominant macro driver.",
            bullets=[
                "+ Intel: capital confidence signal",
                "+ Lilly: regulatory and product catalyst",
                "- Nike: weak guidance and China pressure",
                "! ADP: supportive, but not decisive",
            ],
            footer="Built from reports/2026-04-01-midday-financial-news-brief.md",
            accent=ACCENT,
            out_name="11-closing.png",
        ),
        narration="So the cleanest read on today is this. The broad market was resilient, but the strongest evidence sat in company specific stories. Intel and Lilly gained on concrete catalysts, Nike fell on weak guidance, and the macro backdrop was supportive without being decisive.",
    ))
    return scenes


def get_existing_audio_map(coll):
    preferred = {
        "01-title.png": "Financial News Brief",
        "02-market-overview.png": "Nasdaq Leads Growth Stories",
        "03-oil-rates.png": "Oil Up, Yields Down, Risk Intact",
        "04-adp-proof.png": "ADP March Payrolls: Sector Concentration",
        "05-intel-proof.png": "Intel Repurchases Ireland Fab Stake",
        "06-intel-chart.png": "Intel Outperforms Broader Market",
        "07-lly-proof.png": "Lilly's Foundayo Approval Expands Platform",
        "08-lly-chart.png": "Favorable Regulatory Catalyst Drives Stock",
        "09-nke-proof.png": "Nike's Weak Outlook Dominates Story",
        "10-nke-chart.png": "Market's Forward Path Focus",
        "11-closing.png": "Market Resilience & Company Stories",
    }
    audios = coll.get_audios()
    by_name = {}
    for a in audios:
        by_name[a.name] = a
    return {k: by_name.get(v) for k, v in preferred.items()}


def build_clip_proofs(conn, coll):
    existing_result = OUT / "video_result.json"
    if existing_result.exists():
        try:
            data = json.loads(existing_result.read_text())
            existing = data.get("clip_proofs") or {}
        except Exception:
            existing = {}
    else:
        existing = {}

    plans = {
        "adp": {
            "url": "https://www.youtube.com/watch?v=ttobXa_laZA",
            "query": "private payroll data from adp just out 62000",
            "max_duration": 24.0,
        },
        "lly": {
            "url": "https://www.youtube.com/watch?v=4e6mQljmzm4",
            "query": "obesity pill led to around 12% weight loss",
            "fallback_start": 119.47,
            "fallback_duration": 24.0,
            "max_duration": 24.0,
        },
        "nike": {
            "url": "https://www.youtube.com/watch?v=mNvaVsMf9cA",
            "query": "North America strength China weakness",
            "fallback_start": 0.0,
            "fallback_duration": 22.0,
            "max_duration": 24.0,
        },
    }
    proofs = {}
    for key, plan in plans.items():
        if key in existing and existing[key].get("video_id"):
            proofs[key] = existing[key]
            print(f"reusing video proof: {key} -> {existing[key]['video_id']}")
            continue
        print(f"building video proof: {key}")
        video = coll.upload(url=plan["url"])
        video.index_spoken_words(force=True)
        start = plan.get("fallback_start", 0.0)
        duration = plan.get("fallback_duration", 20.0)
        try:
            result = video.search(plan["query"], search_type=SearchType.semantic)
            shot = result.get_shots()[0]
            start = max(0.0, float(shot.start))
            duration = min(float(shot.end - shot.start), plan.get("max_duration", 24.0))
            if duration < 8:
                duration = min(plan.get("fallback_duration", 18.0), plan.get("max_duration", 24.0))
        except Exception as e:
            print(f"search fallback for {key}: {e}")
        proofs[key] = {
            "video_id": video.id,
            "start": start,
            "duration": duration,
            "title": video.name,
            "url": plan["url"],
        }
        print(f"  clip {key}: video={video.id} start={start:.2f} duration={duration:.2f}")
    return proofs


def main():
    load_dotenv(ROOT / ".env")
    if not os.getenv("VIDEO_DB_API_KEY"):
        raise SystemExit("VIDEO_DB_API_KEY not found in environment or .env")

    chart_pngs = build_chart_pngs()

    conn = videodb.connect()
    coll = conn.get_collection()
    clip_proofs = build_clip_proofs(conn, coll)
    scenes = build_scenes(chart_pngs, clip_proofs)
    existing_audio_map = get_existing_audio_map(coll)

    prepared = []
    for i, scene in enumerate(scenes, 1):
        item = {"kind": scene.kind, "duration": scene.duration}
        if scene.kind == "image":
            img = coll.upload(file_path=str(scene.image_path))
            voice = existing_audio_map.get(scene.image_path.name)
            if voice is None and scene.narration:
                voice = coll.generate_voice(text=scene.narration, voice_name="Default")
            duration = scene.duration or max(float(getattr(voice, "length", 0) or 0), 4.0)
            item.update({"image": img, "voice": voice, "duration": duration, "name": scene.image_path.name})
            print(f"prepared image scene {i}: {scene.image_path.name} duration={duration}")
        else:
            duration = scene.duration or 15.0
            item.update({
                "video_id": scene.video_id,
                "video_start": scene.video_start,
                "video_volume": scene.video_volume,
                "duration": duration,
                "name": f"video:{scene.video_id}",
            })
            print(f"prepared video scene {i}: {scene.video_id} start={scene.video_start} duration={duration}")
        prepared.append(item)

    visual_track = Track()
    audio_track = Track()
    current = 0.0
    for item in prepared:
        if item["kind"] == "image":
            visual_track.add_clip(current, Clip(
                asset=ImageAsset(id=item["image"].id),
                duration=item["duration"],
                fit=Fit.contain,
                transition=Transition(in_="fade", out="fade", duration=0.7),
            ))
            if item.get("voice") is not None:
                audio_track.add_clip(current, Clip(
                    asset=AudioAsset(id=item["voice"].id, volume=1.0),
                    duration=item["duration"],
                ))
        else:
            visual_track.add_clip(current, Clip(
                asset=VideoAsset(id=item["video_id"], start=item["video_start"], volume=item.get("video_volume", 1.0)),
                duration=item["duration"],
                fit=Fit.contain,
                transition=Transition(in_="fade", out="fade", duration=0.7),
            ))
        current += item["duration"]

    timeline = Timeline(conn)
    timeline.resolution = "1280x720"
    timeline.background = "#000000"
    timeline.add_track(visual_track)
    timeline.add_track(audio_track)

    stream_url = timeline.generate_stream()
    result = {
        "stream_url": stream_url,
        "player_url": timeline.player_url,
        "scene_count": len(prepared),
        "approx_duration_seconds": current,
        "slides": [u["name"] for u in prepared],
        "clip_proofs": clip_proofs,
    }
    (OUT / "video_result.json").write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
