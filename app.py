from __future__ import annotations

import base64
import io
import json
import os
import re
import urllib.error
import urllib.request
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from flask import Flask, jsonify, render_template_string, request, send_file
from PIL import Image, ImageDraw, ImageFont


app = Flask(__name__)


BRAND = {
    "cream": "#ECEEE6",
    "sage": "#7A9060",
    "olive": "#2F3028",
    "light_sage": "#95AB76",
    "dark_sage": "#5C6E48",
    "grid": "#D6D8CC",
    "ink": "#2F3028",
    "muted": "#6B7166",
}

SLIDE_THEME = {
    "dark": {
        "bg": BRAND["olive"],
        "text": BRAND["cream"],
        "accent": BRAND["light_sage"],
        "stroke": "#4A5440",
    },
    "light": {
        "bg": BRAND["cream"],
        "text": BRAND["ink"],
        "accent": BRAND["sage"],
        "stroke": "#D1D5C7",
    },
}

# Fix 1: ship bundled fonts so the app works on Vercel/Linux (no C:\Windows\Fonts)
FONT_DIR = os.path.join(os.path.dirname(__file__), "fonts")

WINDOWS_FONT_CANDIDATES = {
    "display_bold": [
        os.path.join(FONT_DIR, "LibreBaskerville-Bold.ttf"),
        r"C:\Windows\Fonts\georgiab.ttf",
        r"C:\Windows\Fonts\timesbd.ttf",
        r"C:\Windows\Fonts\times.ttf",
    ],
    "display_italic": [
        os.path.join(FONT_DIR, "LibreBaskerville-Italic.ttf"),
        r"C:\Windows\Fonts\georgiai.ttf",
        r"C:\Windows\Fonts\timesi.ttf",
    ],
    "sans_regular": [
        os.path.join(FONT_DIR, "NotoSans-Regular.ttf"),
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        r"C:\Windows\Fonts\segoeui.ttf",
        r"C:\Windows\Fonts\arial.ttf",
    ],
    "sans_bold": [
        os.path.join(FONT_DIR, "NotoSans-SemiBold.ttf"),
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        r"C:\Windows\Fonts\seguisb.ttf",
        r"C:\Windows\Fonts\arialbd.ttf",
    ],
}

CANVAS_SIZE = (1080, 1080)
DEFAULT_SLIDES = 6
MAX_SLIDES = 8
MIN_SLIDES = 4


@dataclass
class SlidePlan:
    index: int
    total: int
    label: str
    headline: str
    accent_line: str
    footer: str
    theme: str
    tone: str
    palette: str
    layout: str


app = Flask(__name__)


def hex_to_rgb(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    return tuple(int(value[index : index + 2], 16) for index in (0, 2, 4))


def clean_text(value: str | None, fallback: str = "") -> str:
    text = re.sub(r"\s+", " ", (value or "").strip())
    return text or fallback


def split_lines(text: str, width: int, font) -> list[str]:
    words = clean_text(text, "").split()
    if not words:
        return []

    lines: list[str] = []
    current: list[str] = []
    for word in words:
        candidate = " ".join(current + [word])
        bbox = font.getbbox(candidate)
        if bbox[2] - bbox[0] <= width:
            current.append(word)
        else:
            if current:
                lines.append(" ".join(current))
            current = [word]
    if current:
        lines.append(" ".join(current))
    return lines


def load_font(candidates: list[str], size: int):
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size=size)
            except OSError:
                continue
    return ImageFont.load_default()


FONT_DISPLAY = load_font(WINDOWS_FONT_CANDIDATES["display_bold"], 84)
FONT_DISPLAY_LG = load_font(WINDOWS_FONT_CANDIDATES["display_bold"], 102)
FONT_DISPLAY_XL = load_font(WINDOWS_FONT_CANDIDATES["display_bold"], 114)
FONT_ITALIC = load_font(WINDOWS_FONT_CANDIDATES["display_italic"], 32)
FONT_SMALL = load_font(WINDOWS_FONT_CANDIDATES["sans_regular"], 20)
FONT_SMALL_BOLD = load_font(WINDOWS_FONT_CANDIDATES["sans_bold"], 20)
FONT_TINY = load_font(WINDOWS_FONT_CANDIDATES["sans_regular"], 16)


PLATFORM_GUIDES = {
    "linkedin": {
        "voice": "thoughtful, credible, and concise",
        "cta": "Invite reflection or a soft next step.",
    },
    "instagram": {
        "voice": "warm, scannable, and emotionally grounded",
        "cta": "Keep it readable and visually clean.",
    },
}


def try_ollama(prompt: str, model: str) -> str | None:
    host = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")
    endpoint = host.rstrip("/") + "/api/generate"
    payload = json.dumps({"model": model, "prompt": prompt, "stream": False}).encode("utf-8")
    request_obj = urllib.request.Request(
        endpoint,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request_obj, timeout=45) as response:
            data = json.loads(response.read().decode("utf-8"))
        return clean_text(data.get("response", ""))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, ValueError):
        return None


def parse_keywords(keywords: str) -> list[str]:
    items: list[str] = []
    for part in re.split(r"[,/|]", keywords or ""):
        token = re.sub(r"[^a-zA-Z0-9 ]+", "", part).strip()
        if token:
            items.append(token)
    return items


def prompt_for_ai(payload: dict[str, Any]) -> str:
    return f"""
You are designing a premium carousel post in a calm editorial style.

Brand palette:
- Warm Cream #ECEEE6
- Sage Green #7A9060
- Deep Olive #2F3028
- Light Sage #95AB76
- Dark Sage #5C6E48

Reference style:
- Minimal, grid-based, large serif headlines
- Calm spacing, restrained copy, elegant contrast
- 1080x1080 carousel slides
- Same font sizing and visual system across all slides

Content brief:
- Brand name: {payload['company_name']}
- Platform: {payload['platform']}
- Theme: {payload['theme']}
- Topic: {payload['topic']}
- Message: {payload['message']}
- Tone: {payload['tone']}
- Audience: {payload['audience']}
- Keywords: {payload['keywords']}
- Slide count: {payload['slide_count']}

Return a JSON array with exactly {payload['slide_count']} items.
Each item must have:
- label
- headline
- subheadline
- footer

Keep the copy short, premium, and slide-friendly.
""".strip()


def build_slide_plan(payload: dict[str, Any]) -> list[SlidePlan]:
    slide_count = max(MIN_SLIDES, min(MAX_SLIDES, int(payload["slide_count"])))
    keywords = parse_keywords(payload["keywords"])
    guide = PLATFORM_GUIDES.get(payload["platform"], PLATFORM_GUIDES["linkedin"])
    topic = clean_text(payload["topic"], "A question worth building from")
    message = clean_text(payload["message"], "Clarity through calm design.")
    theme = clean_text(payload["theme"], "warm cream, sage green, deep olive")
    tone = clean_text(payload["tone"], guide["voice"])
    audience = clean_text(payload["audience"], "your audience")
    company = clean_text(payload["company_name"], "Your Brand")

    sections = [
        ("THE QUESTION", topic, message),
        ("THE SHIFT", f"{topic} became a system.", f"Built for {audience} who need clarity.") ,
        ("THE CLARITY", f"Not a data problem.", f"A visibility problem.") ,
        ("THE BUILD", f"A calmer way to explain {keywords[0] if keywords else 'the work'}.", message),
        ("THE PRODUCT", f"What the carousel needs to say.", f"Short, clean, and easy to trust."),
        ("THE MOMENT", f"Still early.", f"But already in motion."),
        ("THE RISK", f"That's how things get missed.", f"Every time. Quietly."),
        ("THE CLOSING", f"{company} is ready.", f"{guide['cta']}") ,
    ]

    plans: list[SlidePlan] = []
    for index in range(slide_count):
        label, headline, subheadline = sections[index % len(sections)]
        plans.append(
            SlidePlan(
                index=index + 1,
                total=slide_count,
                label=label,
                headline=headline,
                accent_line=subheadline,
                footer=company,
                theme=theme,
                tone=tone,
                palette="warm cream / sage / deep olive",
                layout="carousel",
            )
        )
    return plans


def build_slide_plan_from_ai(payload: dict[str, Any], ai_text: str) -> list[SlidePlan] | None:
    try:
        raw = json.loads(ai_text)
        if not isinstance(raw, list):
            return None

        plans: list[SlidePlan] = []
        for idx, item in enumerate(raw[: payload["slide_count"]]):
            plans.append(
                SlidePlan(
                    index=idx + 1,
                    total=payload["slide_count"],
                    label=clean_text(item.get("label"), f"SLIDE {idx + 1}"),
                    headline=clean_text(item.get("headline"), payload["topic"]),
                    accent_line=clean_text(item.get("subheadline"), payload["message"]),
                    footer=clean_text(item.get("footer"), payload["company_name"]),
                    theme=clean_text(payload["theme"], "warm cream / sage / deep olive"),
                    tone=clean_text(payload["tone"], PLATFORM_GUIDES[payload["platform"]]["voice"]),
                    palette="warm cream / sage / deep olive",
                    layout="carousel",
                )
            )
        return plans if len(plans) == payload["slide_count"] else None
    except json.JSONDecodeError:
        return None


def draw_grid(draw: ImageDraw.ImageDraw, width: int, height: int, color: str, step: int = 60) -> None:
    stroke = hex_to_rgb(color)
    for x in range(0, width + 1, step):
        draw.line([(x, 0), (x, height)], fill=stroke, width=1)
    for y in range(0, height + 1, step):
        draw.line([(0, y), (width, y)], fill=stroke, width=1)


def draw_corners(draw: ImageDraw.ImageDraw, width: int, height: int, accent: str, filled: bool = True) -> None:
    fill = hex_to_rgb(accent)
    r = 26
    for box in [
        (10, 10, 10 + r, 10 + r),
        (width - 10 - r, 10, width - 10, 10 + r),
        (10, height - 10 - r, 10 + r, height - 10),
        (width - 10 - r, height - 10 - r, width - 10, height - 10),
    ]:
        draw.ellipse(box, fill=fill if filled else None, outline=fill, width=3)


def draw_frame(draw: ImageDraw.ImageDraw, width: int, height: int, theme_key: str, plan: SlidePlan) -> None:
    theme = SLIDE_THEME[theme_key]
    bg = hex_to_rgb(theme["bg"])
    text = hex_to_rgb(theme["text"])
    accent = hex_to_rgb(theme["accent"])
    stroke = theme["stroke"]

    draw.rectangle([(0, 0), (width, height)], fill=bg)
    draw_grid(draw, width, height, stroke, step=62)
    draw_corners(draw, width, height, theme["accent"])

    label_text = " ".join(plan.label.upper())
    label_bbox = draw.textbbox((0, 0), label_text, font=FONT_TINY)
    label_width = label_bbox[2] - label_bbox[0]
    draw.text(((width - label_width) / 2, 40), label_text, font=FONT_TINY, fill=text)
    draw.line([(106, 48), (160, 48)], fill=accent, width=2)
    draw.line([(width - 160, 48), (width - 106, 48)], fill=accent, width=2)

    index_text = f"{plan.index:02d} / {plan.total:02d}"
    draw.text((86, 106), index_text, font=FONT_TINY, fill=text)
    draw.text((84, height - 54), clean_text(plan.footer, "SEREAI LABS"), font=FONT_SMALL_BOLD, fill=accent)
    draw.text((width - 86, height - 54), "→", font=FONT_SMALL_BOLD, fill=text)


def draw_multiline(draw: ImageDraw.ImageDraw, lines: list[str], x: int, y: int, font, fill: str, gap: int) -> int:
    current_y = y
    color = hex_to_rgb(fill)
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        draw.text((x, current_y), line, font=font, fill=color)
        current_y += (bbox[3] - bbox[1]) + gap
    return current_y


def generate_carousel_slide(plan: SlidePlan) -> Image.Image:
    width, height = CANVAS_SIZE
    bg_mode = "dark" if plan.index % 2 == 1 else "light"
    theme = SLIDE_THEME[bg_mode]
    img = Image.new("RGB", (width, height), color=hex_to_rgb(theme["bg"]))
    draw = ImageDraw.Draw(img)
    draw_frame(draw, width, height, bg_mode, plan)

    text = theme["text"]
    accent = theme["accent"]
    left = 84
    top = 210
    max_text = 790

    # top rule and section label system
    draw.line([(left, 176), (left + 70, 176)], fill=hex_to_rgb(accent), width=4)

    headline_font = FONT_DISPLAY_XL if plan.index in (1, 2, 3) else FONT_DISPLAY_LG
    headline_lines = split_lines(plan.headline, max_text, headline_font)
    if not headline_lines:
        headline_lines = ["Still early.", "But already in motion."]
    current_y = draw_multiline(draw, headline_lines, left, top, headline_font, text, 10)

    draw.line([(left, current_y + 18), (left + 70, current_y + 18)], fill=hex_to_rgb(accent), width=4)

    sub_lines = split_lines(plan.accent_line, max_text, FONT_ITALIC)
    if sub_lines:
        draw_multiline(draw, sub_lines[:2], left, current_y + 34, FONT_ITALIC, accent, 8)

    # footer commentary to mimic the reference slides
    footer_y = height - 150
    draw.text((left, footer_y), clean_text(plan.tone, "Clinical insight through continuous memory."), font=FONT_ITALIC, fill=hex_to_rgb(text))

    return img


def image_to_base64(img: Image.Image) -> str:
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def image_to_bytes(img: Image.Image) -> io.BytesIO:
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer


def normalize_payload(data: dict[str, Any]) -> dict[str, Any]:
    slide_count = data.get("slide_count", DEFAULT_SLIDES)
    try:
        slide_count = int(slide_count)
    except (TypeError, ValueError):
        slide_count = DEFAULT_SLIDES
    slide_count = max(MIN_SLIDES, min(MAX_SLIDES, slide_count))

    return {
        "company_name": clean_text(data.get("company_name"), "Your Brand"),
        "platform": clean_text(data.get("platform"), "linkedin").lower(),
        "theme": clean_text(data.get("theme"), "warm cream, sage green, deep olive"),
        "topic": clean_text(data.get("topic"), "It started as a question."),
        "message": clean_text(data.get("message"), "Clinical insight through continuous memory."),
        "tone": clean_text(data.get("tone"), "calm, premium, and editorial"),
        "audience": clean_text(data.get("audience"), "your audience"),
        "keywords": clean_text(data.get("keywords"), "clarity, trust, calm, editorial"),
        "slide_count": slide_count,
    }


def create_slide_bundle(payload: dict[str, Any]) -> dict[str, Any]:
    model = clean_text(os.environ.get("OLLAMA_MODEL"), "")
    ai_text = None
    if model:
        ai_text = try_ollama(prompt_for_ai(payload), model)

    plans = build_slide_plan_from_ai(payload, ai_text or "") if ai_text else None
    if not plans:
        plans = build_slide_plan(payload)

    images = [generate_carousel_slide(plan) for plan in plans]
    encoded = [image_to_base64(img) for img in images]

    slide_files = []
    for plan, img in zip(plans, images, strict=False):
        slide_files.append(
            {
                "index": plan.index,
                "label": plan.label,
                "filename": f"carousel_slide_{plan.index:02d}.png",
                "image": image_to_base64(img),
            }
        )

    return {
        "platform": payload["platform"],
        "slide_count": len(plans),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source": "ollama" if ai_text else "fallback",
        "slides": slide_files,
        "cover": encoded[0] if encoded else "",
    }


PAGE = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Brand Carousel Agent</title>
  <style>
    :root {
      --cream: #eceee6;
      --sage: #7a9060;
      --sage-light: #95ab76;
      --sage-dark: #5c6e48;
      --olive: #2f3028;
      --ink: #24261f;
      --border: rgba(47, 48, 40, 0.08);
      --shadow: 0 24px 70px rgba(47, 48, 40, 0.12);
    }

    * { box-sizing: border-box; }

    html, body {
      margin: 0;
      min-height: 100%;
      color: var(--ink);
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background:
        radial-gradient(circle at top left, rgba(122, 144, 96, 0.14), transparent 24%),
        radial-gradient(circle at 80% 10%, rgba(149, 171, 118, 0.16), transparent 18%),
        linear-gradient(180deg, #f6f5ef 0%, #eceee6 58%, #e6e7df 100%);
    }

    body::before {
      content: "";
      position: fixed;
      inset: 0;
      pointer-events: none;
      background-image: linear-gradient(rgba(47, 48, 40, 0.06) 1px, transparent 1px), linear-gradient(90deg, rgba(47, 48, 40, 0.06) 1px, transparent 1px);
      background-size: 44px 44px;
      opacity: 0.42;
      mask-image: linear-gradient(180deg, rgba(0,0,0,0.24), transparent 74%);
    }

    .shell {
      position: relative;
      max-width: 1320px;
      margin: 0 auto;
      padding: 28px 20px 44px;
    }

    .hero {
      display: grid;
      grid-template-columns: 1.15fr 0.85fr;
      gap: 20px;
      align-items: start;
      margin-bottom: 18px;
    }

    .brand {
      display: inline-flex;
      align-items: center;
      gap: 10px;
      padding: 8px 12px;
      border-radius: 999px;
      background: rgba(255,255,255,0.46);
      border: 1px solid var(--border);
      box-shadow: var(--shadow);
      width: fit-content;
    }

    .dot {
      width: 10px;
      height: 10px;
      border-radius: 50%;
      background: var(--sage);
      box-shadow: 0 0 0 6px rgba(122, 144, 96, 0.16);
    }

    .eyebrow {
      margin: 0 0 10px;
      letter-spacing: 0.22em;
      text-transform: uppercase;
      font-size: 11px;
      color: rgba(47,48,40,0.62);
    }

    h1 {
      font-family: Georgia, "Times New Roman", serif;
      font-size: clamp(44px, 7vw, 88px);
      line-height: 0.96;
      letter-spacing: -0.04em;
      margin: 0 0 16px;
      color: var(--olive);
      max-width: 11ch;
    }

    .lede {
      font-size: 17px;
      line-height: 1.7;
      max-width: 62ch;
      color: rgba(31, 36, 29, 0.78);
      margin: 0;
    }

    .panel, .card {
      background: rgba(255,255,255,0.72);
      border: 1px solid var(--border);
      border-radius: 24px;
      box-shadow: var(--shadow);
      backdrop-filter: blur(14px);
    }

    .meta-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 12px;
    }

    .swatch {
      min-height: 150px;
      display: flex;
      flex-direction: column;
      justify-content: flex-end;
      overflow: hidden;
    }

    .swatch .fill { min-height: 86px; }
    .swatch .body { padding: 16px 18px 18px; }

    .label {
      text-transform: uppercase;
      letter-spacing: 0.18em;
      font-size: 11px;
      color: rgba(47,48,40,0.56);
      margin: 0 0 8px;
    }

    .value {
      font-size: 20px;
      font-weight: 650;
      margin: 0 0 6px;
      color: var(--olive);
    }

    .code {
      margin: 0;
      color: rgba(31, 36, 29, 0.68);
      font-size: 14px;
    }

    .workspace {
      display: grid;
      grid-template-columns: 0.9fr 1.1fr;
      gap: 20px;
      align-items: start;
      margin-top: 10px;
    }

    form { padding: 22px; }

    .fields { display: grid; gap: 14px; }

    .field-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 12px;
    }

    label {
      display: block;
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.16em;
      color: rgba(47,48,40,0.62);
      margin-bottom: 7px;
    }

    input, select, textarea {
      width: 100%;
      border: 1px solid rgba(47,48,40,0.12);
      border-radius: 16px;
      background: rgba(236, 238, 230, 0.84);
      color: var(--olive);
      padding: 13px 14px;
      font: inherit;
      outline: none;
      transition: border-color 0.2s ease, transform 0.2s ease, box-shadow 0.2s ease;
    }

    textarea { min-height: 108px; resize: vertical; }

    input:focus, select:focus, textarea:focus {
      border-color: rgba(122, 144, 96, 0.8);
      box-shadow: 0 0 0 4px rgba(122, 144, 96, 0.12);
      transform: translateY(-1px);
    }

    .actions {
      display: flex;
      gap: 12px;
      flex-wrap: wrap;
      margin-top: 6px;
    }

    button {
      border: 0;
      border-radius: 999px;
      padding: 13px 18px;
      font: inherit;
      font-weight: 700;
      cursor: pointer;
      transition: transform 0.2s ease, box-shadow 0.2s ease, opacity 0.2s ease;
    }

    button:hover { transform: translateY(-1px); }

    .primary {
      background: var(--olive);
      color: var(--cream);
      box-shadow: 0 14px 30px rgba(47,48,40,0.18);
    }

    .ghost {
      background: rgba(255,255,255,0.52);
      color: var(--olive);
      border: 1px solid rgba(47,48,40,0.08);
    }

    .output { padding: 22px; }

    .output-head {
      display: flex;
      justify-content: space-between;
      gap: 12px;
      align-items: center;
      margin-bottom: 16px;
    }

    .pill {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 8px 12px;
      border-radius: 999px;
      background: rgba(122,144,96,0.12);
      color: var(--sage-dark);
      font-size: 12px;
      font-weight: 650;
      text-align: right;
    }

    .muted {
      color: rgba(31,36,29,0.68);
      font-size: 13px;
      margin: 0;
    }

    .slides {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 14px;
      margin-top: 16px;
    }

    .slide-card {
      overflow: hidden;
      border-radius: 22px;
      border: 1px solid rgba(47,48,40,0.09);
      background: rgba(255,255,255,0.86);
    }

    .slide-preview {
      width: 100%;
      display: block;
      aspect-ratio: 1 / 1;
      object-fit: cover;
      background: #f3f3f0;
    }

    .slide-meta {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 12px;
      padding: 12px 14px;
      border-top: 1px solid rgba(47,48,40,0.08);
      background: rgba(255,255,255,0.72);
    }

    .slide-title {
      margin: 0;
      font-size: 13px;
      letter-spacing: 0.12em;
      text-transform: uppercase;
      color: rgba(47,48,40,0.72);
    }

    .download-btn {
      background: rgba(122, 144, 96, 0.12);
      color: var(--sage-dark);
      border: 1px solid rgba(122, 144, 96, 0.18);
      border-radius: 12px;
      padding: 10px 12px;
      font-size: 13px;
      font-weight: 600;
      cursor: pointer;
      width: 100%;
    }

    .zip-row {
      display: flex;
      gap: 12px;
      flex-wrap: wrap;
      margin-top: 14px;
    }

    .footer-note {
      margin-top: 14px;
      font-size: 12px;
      color: rgba(31,36,29,0.62);
    }

    @media (max-width: 980px) {
      .hero, .workspace { grid-template-columns: 1fr; }
      .slides { grid-template-columns: 1fr; }
    }

    @media (max-width: 640px) {
      .shell { padding: 18px 14px 28px; }
      .field-grid, .meta-grid { grid-template-columns: 1fr; }
      form, .output { padding: 16px; }
    }
  </style>
</head>
<body>
  <div class="shell">
    <div class="hero">
      <div>
        <div class="brand"><span class="dot"></span><strong>Brand Carousel Agent</strong></div>
        <p class="eyebrow">Warm cream, sage green, deep olive</p>
        <h1>Generate the same kind of carousel slides, every time.</h1>
        <p class="lede">Give the agent your own prompt and it will build a consistent carousel deck in the same visual language as your reference images: same font family feel, same sizes, same grid structure, same palette, and downloadable PNG slides.</p>
      </div>
      <div class="meta-grid">
        <div class="card swatch">
          <div class="fill" style="background: var(--cream);"></div>
          <div class="body">
            <p class="label">Primary</p>
            <p class="value">Warm Cream</p>
            <p class="code">#ECEEE6</p>
          </div>
        </div>
        <div class="card swatch">
          <div class="fill" style="background: var(--sage);"></div>
          <div class="body">
            <p class="label">Secondary</p>
            <p class="value">Sage Green</p>
            <p class="code">#7A9060</p>
          </div>
        </div>
        <div class="card swatch">
          <div class="fill" style="background: var(--olive);"></div>
          <div class="body">
            <p class="label">Support</p>
            <p class="value">Deep Olive Dark</p>
            <p class="code">#2F3028</p>
          </div>
        </div>
        <div class="card swatch">
          <div class="fill" style="background: linear-gradient(135deg, var(--sage-light), var(--sage-dark));"></div>
          <div class="body">
            <p class="label">Accent</p>
            <p class="value">Light and Dark Sage</p>
            <p class="code">#95AB76 / #5C6E48</p>
          </div>
        </div>
      </div>
    </div>

    <div class="workspace">
      <form id="generator" class="card">
        <div class="fields">
          <div class="field-grid">
            <div>
              <label for="company_name">Company name</label>
              <input id="company_name" name="company_name" value="Your Brand" />
            </div>
            <div>
              <label for="platform">Platform</label>
              <select id="platform" name="platform">
                <option value="linkedin">LinkedIn</option>
                <option value="instagram">Instagram</option>
              </select>
            </div>
          </div>

          <div>
            <label for="theme">Theme</label>
            <input id="theme" name="theme" value="Warm cream, sage green, deep olive, premium editorial carousel" />
          </div>

          <div>
            <label for="topic">Prompt / topic</label>
            <input id="topic" name="topic" value="It started as a question. Now it's something real." />
          </div>

          <div>
            <label for="message">Message</label>
            <textarea id="message" name="message">Clinical insight through continuous memory.</textarea>
          </div>

          <div class="field-grid">
            <div>
              <label for="tone">Tone</label>
              <input id="tone" name="tone" value="calm, premium, and editorial" />
            </div>
            <div>
              <label for="audience">Audience</label>
              <input id="audience" name="audience" value="customers, prospects, and community followers" />
            </div>
          </div>

          <div class="field-grid">
            <div>
              <label for="keywords">Keywords</label>
              <input id="keywords" name="keywords" value="clarity, trust, calm, editorial" />
            </div>
            <div>
              <label for="slide_count">Carousel slides</label>
              <select id="slide_count" name="slide_count">
                <option value="4">4 slides</option>
                <option value="5">5 slides</option>
                <option value="6" selected>6 slides</option>
                <option value="7">7 slides</option>
                <option value="8">8 slides</option>
              </select>
            </div>
          </div>

          <div class="actions">
            <button class="primary" type="submit">Generate carousel</button>
            <button class="ghost" id="resetButton" type="button">Reset prompt</button>
          </div>
        </div>
      </form>

      <section class="card output">
        <div class="output-head">
          <div>
            <p class="eyebrow" style="margin-bottom:6px;">Results</p>
            <h2 style="margin:0;font-family:Georgia, 'Times New Roman', serif;font-size:32px;line-height:1.02;color:var(--olive);">Ready to publish</h2>
          </div>
          <div class="pill" id="sourcePill">Waiting for your prompt</div>
        </div>
        <p class="muted" id="timestamp">Generate a carousel to see downloadable slide images here.</p>
        <div class="zip-row">
          <button class="primary" id="downloadAllButton" type="button" disabled>Download all slides as ZIP</button>
        </div>
        <div class="slides" id="slides"></div>
        <div class="footer-note">If Ollama is set up locally, the agent will use it for carousel planning. Otherwise it stays fully usable offline with the same visual system.</div>
      </section>
    </div>
  </div>

  <!-- Fix 3: JSZip for client-side ZIP (avoids URL size limits on Vercel) -->
  <script src="https://cdnjs.cloudflare.com/ajax/libs/jszip/3.10.1/jszip.min.js"></script>
  <script>
    const form = document.getElementById('generator');
    const resetButton = document.getElementById('resetButton');
    const sourcePill = document.getElementById('sourcePill');
    const timestamp = document.getElementById('timestamp');
    const slidesEl = document.getElementById('slides');
    const downloadAllButton = document.getElementById('downloadAllButton');

    let currentBundle = null;

    const defaults = {
      company_name: 'Your Brand',
      platform: 'linkedin',
      theme: 'Warm cream, sage green, deep olive, premium editorial carousel',
      topic: "It started as a question. Now it's something real.",
      message: 'Clinical insight through continuous memory.',
      tone: 'calm, premium, and editorial',
      audience: 'customers, prospects, and community followers',
      keywords: 'clarity, trust, calm, editorial',
      slide_count: '6',
    };

    function applyDefaults() {
      Object.entries(defaults).forEach(([key, value]) => {
        const element = form.elements[key];
        if (element) {
          element.value = value;
        }
      });
    }

    function renderSlides(slides) {
      slidesEl.innerHTML = '';
      slides.forEach((slide) => {
        const card = document.createElement('div');
        card.className = 'slide-card';
        card.innerHTML = `
          <img class="slide-preview" src="data:image/png;base64,${slide.image}" alt="${slide.label}">
          <div class="slide-meta">
            <div>
              <p class="slide-title">${slide.label}</p>
            </div>
          </div>
          <div style="padding:12px 14px 14px;">
            <a class="download-btn" href="data:image/png;base64,${slide.image}" download="${slide.filename}">Download ${slide.index.toString().padStart(2, '0')}</a>
          </div>
        `;
        slidesEl.appendChild(card);
      });
    }

    // Fix 3: build the ZIP entirely in the browser using JSZip — no server round-trip,
    // no URL size limits, works on Vercel Hobby without extra routes.
    downloadAllButton.addEventListener('click', async () => {
      if (!currentBundle) return;
      downloadAllButton.textContent = 'Preparing ZIP...';
      downloadAllButton.disabled = true;
      const zip = new JSZip();
      for (const slide of currentBundle.slides) {
        zip.file(slide.filename, slide.image, { base64: true });
      }
      const blob = await zip.generateAsync({ type: 'blob' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'carousel.zip';
      a.click();
      URL.revokeObjectURL(url);
      downloadAllButton.textContent = 'Download all slides as ZIP';
      downloadAllButton.disabled = false;
    });

    resetButton.addEventListener('click', () => {
      applyDefaults();
    });

    form.addEventListener('submit', async (event) => {
      event.preventDefault();
      const payload = Object.fromEntries(new FormData(form).entries());
      sourcePill.textContent = 'Generating...';
      timestamp.textContent = 'Building your carousel slides.';
      slidesEl.innerHTML = '';
      downloadAllButton.disabled = true;

      // Fix 2: proper error handling — surface server errors instead of hanging on "Generating..."
      let response, data;
      try {
        response = await fetch('/api/generate', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });

        if (!response.ok) {
          const errText = await response.text();
          sourcePill.textContent = 'Error';
          timestamp.textContent = 'Generation failed (' + response.status + '). Check server logs.';
          console.error('Server error:', errText);
          return;
        }

        data = await response.json();
      } catch (err) {
        sourcePill.textContent = 'Network error';
        timestamp.textContent = 'Could not reach the server. Try again.';
        console.error('Fetch error:', err);
        return;
      }

      currentBundle = data;
      sourcePill.textContent = data.source === 'ollama' ? 'Planned with local Ollama' : 'Built with the offline carousel engine';
      timestamp.textContent = `Created ${new Date(data.created_at).toLocaleString()} · ${data.slide_count} slides`;
      renderSlides(data.slides || []);
      downloadAllButton.disabled = false;
    });
  </script>
</body>
</html>
"""


@app.get("/")
def index() -> str:
    return render_template_string(PAGE)


@app.post("/api/generate")
def api_generate():
    payload = normalize_payload(request.get_json(force=True, silent=True) or {})
    bundle = create_slide_bundle(payload)
    return jsonify(bundle)


# Fix 3 (server side): Keep a POST route as a fallback for server-generated ZIPs.
# The frontend now uses JSZip client-side, but this route is retained for API consumers.
@app.post("/api/download-zip")
def api_download_zip():
    payload = normalize_payload(request.get_json(force=True) or {})
    bundle = create_slide_bundle(payload)

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
        for slide in bundle["slides"]:
            image_data = base64.b64decode(slide["image"])
            archive.writestr(slide["filename"], image_data)
    zip_buffer.seek(0)
    filename = f"carousel_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.zip"
    return send_file(zip_buffer, as_attachment=True, download_name=filename, mimetype="application/zip")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    app.run(host="0.0.0.0", port=port, debug=True)
