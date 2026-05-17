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
    "cream_alt": "#E8EBE0",
    "sage": "#7A9060",
    "sage_light": "#95AB76",
    "sage_dark": "#5A5E4A",
    "olive": "#2F3028",
    "olive_mid": "#3E4035",
    "olive_dark": "#1E2018",
    "grid": "#D4D6CC",
    "white": "#FFFFFF",
}

THEMES = {
    "sereai": {
        "name": "SEREAI PPTX",
        "bg": BRAND["cream"],
        "bg_alt": BRAND["cream_alt"],
        "text": BRAND["olive"],
        "text_strong": BRAND["olive_dark"],
        "muted": BRAND["sage_dark"],
        "accent": BRAND["sage"],
        "accent_light": BRAND["sage_light"],
        "accent_dark": BRAND["olive_mid"],
        "grid": BRAND["grid"],
        "white": BRAND["white"],
    },
}

DEFAULT_THEME = "sereai"

WINDOWS_FONT_CANDIDATES = {
    "display_bold": [
        r"C:\Windows\Fonts\georgiab.ttf",
        r"C:\Windows\Fonts\timesbd.ttf",
        r"C:\Windows\Fonts\times.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
    ],
    "display_italic": [
        r"C:\Windows\Fonts\georgiai.ttf",
        r"C:\Windows\Fonts\timesi.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Italic.ttf",
    ],
    "sans_regular": [
        r"C:\Windows\Fonts\calibri.ttf",
        r"C:\Windows\Fonts\segoeui.ttf",
        r"C:\Windows\Fonts\arial.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ],
    "sans_bold": [
        r"C:\Windows\Fonts\calibrib.ttf",
        r"C:\Windows\Fonts\seguisb.ttf",
        r"C:\Windows\Fonts\arialbd.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
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
    header: str
    headline: str
    hook: str
    bullets: list[str]
    cta: str
    footer_line: str
    footer_left: str
    footer_right: str
    swipe_text: str
    theme_key: str


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
            except (OSError, Exception):
                continue
    # Fallback: try to load a default larger font
    try:
        return ImageFont.load_default()
    except:
        return ImageFont.load_default()


# Load fonts at app startup, but will retry on each slide if needed
_FONT_CACHE = {}


def get_font(font_type: str, size: int):
    """Get font with fallback - called on each slide generation"""
    key = (font_type, size)
    if key in _FONT_CACHE:
        return _FONT_CACHE[key]
    
    if font_type not in WINDOWS_FONT_CANDIDATES:
        font = ImageFont.load_default()
    else:
        font = load_font(WINDOWS_FONT_CANDIDATES[font_type], size)
    
    _FONT_CACHE[key] = font
    return font


# Pre-load primary fonts
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


def try_openai(prompt: str, model: str) -> str | None:
    endpoint = "https://api.openai.com/v1/chat/completions"
    payload = json.dumps(
        {
            "model": model,
            "temperature": 0.5,
            "messages": [{"role": "user", "content": prompt}],
        }
    ).encode("utf-8")
    request_obj = urllib.request.Request(
        endpoint,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {os.environ.get('OPENAI_API_KEY','')}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request_obj, timeout=45) as response:
            data = json.loads(response.read().decode("utf-8"))
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        return clean_text(content)
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, ValueError):
        return None


def try_anthropic(prompt: str, model: str) -> str | None:
    endpoint = "https://api.anthropic.com/v1/messages"
    payload = json.dumps(
        {
            "model": model,
            "max_tokens": 1200,
            "temperature": 0.5,
            "messages": [{"role": "user", "content": prompt}],
        }
    ).encode("utf-8")
    request_obj = urllib.request.Request(
        endpoint,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "x-api-key": os.environ.get("ANTHROPIC_API_KEY", ""),
            "anthropic-version": "2023-06-01",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request_obj, timeout=45) as response:
            data = json.loads(response.read().decode("utf-8"))
        content = data.get("content", [{}])[0].get("text", "")
        return clean_text(content)
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, ValueError):
        return None


def select_llm_provider() -> tuple[str, str]:
    provider = clean_text(os.environ.get("LLM_PROVIDER"), "").lower()
    openai_key = clean_text(os.environ.get("OPENAI_API_KEY"), "")
    anthropic_key = clean_text(os.environ.get("ANTHROPIC_API_KEY"), "")
    ollama_model = clean_text(os.environ.get("OLLAMA_MODEL"), "")

    if provider == "openai" and openai_key:
        return "openai", clean_text(os.environ.get("OPENAI_MODEL"), "gpt-4o-mini")
    if provider == "anthropic" and anthropic_key:
        return "anthropic", clean_text(os.environ.get("ANTHROPIC_MODEL"), "claude-3-5-sonnet-latest")
    if provider == "ollama" and ollama_model:
        return "ollama", ollama_model

    if openai_key:
        return "openai", clean_text(os.environ.get("OPENAI_MODEL"), "gpt-4o-mini")
    if anthropic_key:
        return "anthropic", clean_text(os.environ.get("ANTHROPIC_MODEL"), "claude-3-5-sonnet-latest")
    if ollama_model:
        return "ollama", ollama_model
    return "", ""


def parse_keywords(keywords: str) -> list[str]:
    items: list[str] = []
    for part in re.split(r"[,/|]", keywords or ""):
        token = re.sub(r"[^a-zA-Z0-9 ]+", "", part).strip()
        if token:
            items.append(token)
    return items


def normalize_bullets(value: Any) -> list[str]:
    if isinstance(value, list):
        return [clean_text(item, "") for item in value if clean_text(item, "")]
    if isinstance(value, str):
        parts = [clean_text(part, "") for part in re.split(r"[;\n•]", value) if clean_text(part, "")]
        return parts
    return []


def resolve_theme_key(value: str | None) -> str:
    key = clean_text(value, DEFAULT_THEME).lower()
    return key if key in THEMES else DEFAULT_THEME


def prompt_for_ai(payload: dict[str, Any]) -> str:
    return f"""
You are a senior brand designer and carousel strategist.
Design a premium LinkedIn/Instagram carousel that mirrors the reference PPTX style.

Brand palette:
- Warm Cream #ECEEE6
- Sage Green #7A9060
- Deep Olive #2F3028
- Light Sage #95AB76
- Dark Sage #5A5E4A
- Soft Grid #D4D6CC

Reference style:
- Minimal, grid-based, large serif headlines
- Calm spacing, restrained copy, elegant contrast
- 1080x1080 carousel slides
- Same font sizing and visual system across all slides
- Top header shows a section label + slide count (e.g., "THE SCENARIO — 02 / 08")
- Footer shows brand name on the left and a page cue on the right (e.g., "02 / 08 →")
- Cover slide uses a "SWIPE TO EXPLORE →" cue
- Include hook lines and where needed a bullet list

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
- Website (optional): {payload.get('website','')}

Return a JSON array with exactly {payload['slide_count']} items.
Each item must have:
- label (short internal label)
- header (section title shown at top, e.g., THE PROBLEM)
- headline (main large serif copy)
- hook (short supporting line)
- bullets (array of short bullet lines, optional)
- cta (short CTA line, optional)
- footer_line (short line above footer, optional)
- swipe_text (e.g., "SWIPE TO EXPLORE →", optional)

Keep the copy short, premium, and slide-friendly.
Return JSON only with no markdown or commentary.
""".strip()


def build_slide_plan(payload: dict[str, Any]) -> list[SlidePlan]:
    slide_count = max(MIN_SLIDES, min(MAX_SLIDES, int(payload["slide_count"])))
    keywords = parse_keywords(payload["keywords"])
    topic = clean_text(payload["topic"], "A question worth building from")
    message = clean_text(payload["message"], "Clarity through calm design.")
    theme_key = resolve_theme_key(payload.get("theme_preset"))
    company = clean_text(payload["company_name"], "Your Brand")
    website = clean_text(payload.get("website"), "")
    outline_raw = clean_text(payload.get("slide_outline"), "")

    def footer_right(index: int) -> str:
        return f"{index:02d} / {slide_count:02d}" + (" →" if index < slide_count else "")

    if outline_raw:
        lines = [line.strip() for line in outline_raw.splitlines() if line.strip()]
        plans: list[SlidePlan] = []
        for idx, line in enumerate(lines[:slide_count]):
            header = ""
            headline = line
            hook = ""
            if ":" in line:
                header, headline = line.split(":", 1)
            if "|" in headline:
                headline, hook = headline.split("|", 1)
            header = clean_text(header, f"SLIDE {idx + 1}")
            headline = clean_text(headline, topic)
            hook = clean_text(hook, message)
            plans.append(
                SlidePlan(
                    index=idx + 1,
                    total=slide_count,
                    label=header,
                    header=header,
                    headline=headline,
                    hook=hook,
                    bullets=[],
                    cta="",
                    footer_line=message,
                    footer_left=company,
                    footer_right=footer_right(idx + 1),
                    swipe_text="SWIPE TO EXPLORE →" if idx == 0 else "",
                    theme_key=theme_key,
                )
            )
        if plans:
            return plans

    bullet_seeds = keywords[:3] or ["History", "Signals", "Context"]
    problem_bullets = [f"Prior {seed.lower()} signals were missed." for seed in bullet_seeds]
    approach_bullets = [
        f"Remember the full {topic.lower()} journey.",
        f"Connect past and present {keywords[0].lower() if keywords else 'insight'}.",
        "Support calmer, informed decisions.",
    ]

    sections = [
        {
            "label": "COVER",
            "header": company,
            "headline": topic,
            "hook": message,
            "bullets": [],
            "cta": "",
            "footer_line": message,
            "swipe_text": "SWIPE TO EXPLORE →",
        },
        {
            "label": "THE SCENARIO",
            "header": "THE SCENARIO",
            "headline": f"{topic}",
            "hook": "A routine decision. Happens every day.",
            "bullets": [],
            "cta": "",
            "footer_line": message,
            "swipe_text": "",
        },
        {
            "label": "THE PROBLEM",
            "header": "THE PROBLEM",
            "headline": "But they don't know:",
            "hook": "",
            "bullets": problem_bullets,
            "cta": "",
            "footer_line": message,
            "swipe_text": "",
        },
        {
            "label": "ROOT CAUSE",
            "header": "ROOT CAUSE",
            "headline": "Because that information isn't connected.",
            "hook": "It exists. But it's not visible when it matters.",
            "bullets": [],
            "cta": "",
            "footer_line": message,
            "swipe_text": "",
        },
        {
            "label": "THE INSIGHT",
            "header": "THE INSIGHT",
            "headline": "That's the real problem.",
            "hook": "Not lack of data. Lack of context.",
            "bullets": [],
            "cta": "",
            "footer_line": message,
            "swipe_text": "",
        },
        {
            "label": "OUR APPROACH",
            "header": "OUR APPROACH",
            "headline": f"At {company}, we're building systems that:",
            "hook": "",
            "bullets": approach_bullets,
            "cta": "",
            "footer_line": message,
            "swipe_text": "",
        },
        {
            "label": "THE VISION",
            "header": "THE VISION",
            "headline": f"Because better decisions start with better context.",
            "hook": message,
            "bullets": [],
            "cta": "",
            "footer_line": message,
            "swipe_text": "",
        },
        {
            "label": "FOLLOW US",
            "header": "FOLLOW US",
            "headline": company,
            "hook": "We're building systems that actually understand.",
            "bullets": [],
            "cta": f"Follow {company}",
            "footer_line": website or message,
            "swipe_text": "",
        },
    ]

    plans: list[SlidePlan] = []
    for index in range(slide_count):
        section = sections[index % len(sections)]
        plans.append(
            SlidePlan(
                index=index + 1,
                total=slide_count,
                label=section["label"],
                header=section["header"],
                headline=section["headline"],
                hook=section["hook"],
                bullets=section["bullets"],
                cta=section["cta"],
                footer_line=section["footer_line"],
                footer_left=company,
                footer_right=footer_right(index + 1),
                swipe_text=section["swipe_text"] if index == 0 else "",
                theme_key=theme_key,
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
            header = clean_text(
                item.get("header"),
                clean_text(payload["company_name"], "Your Brand") if idx == 0 else f"SLIDE {idx + 1}",
            )
            headline = clean_text(item.get("headline"), payload["topic"])
            hook = clean_text(item.get("hook"), payload["message"])
            footer_line = clean_text(item.get("footer_line"), payload["message"])
            bullets = normalize_bullets(item.get("bullets"))
            cta = clean_text(item.get("cta"), "")
            swipe_text = clean_text(item.get("swipe_text"), "")
            plans.append(
                SlidePlan(
                    index=idx + 1,
                    total=payload["slide_count"],
                    label=clean_text(item.get("label"), header),
                    header=header,
                    headline=headline,
                    hook=hook,
                    bullets=bullets,
                    cta=cta,
                    footer_line=footer_line,
                    footer_left=clean_text(payload["company_name"], "Your Brand"),
                    footer_right=f"{idx + 1:02d} / {payload['slide_count']:02d}" + (" →" if idx + 1 < payload["slide_count"] else ""),
                    swipe_text=swipe_text,
                    theme_key=resolve_theme_key(payload.get("theme_preset")),
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


def draw_frame(draw: ImageDraw.ImageDraw, width: int, height: int, theme_key: str) -> None:
    theme = THEMES.get(theme_key, THEMES[DEFAULT_THEME])
    bg = hex_to_rgb(theme["bg"])
    draw.rectangle([(0, 0), (width, height)], fill=bg)
    draw_grid(draw, width, height, theme["grid"], step=60)


def draw_multiline(draw: ImageDraw.ImageDraw, lines: list[str], x: int, y: int, font, fill: str, gap: int) -> int:
    current_y = y
    color = hex_to_rgb(fill)
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        draw.text((x, current_y), line, font=font, fill=color)
        current_y += (bbox[3] - bbox[1]) + gap
    return current_y


def draw_right_text(draw: ImageDraw.ImageDraw, text: str, x: int, y: int, font, fill: str) -> None:
    color = hex_to_rgb(fill)
    bbox = draw.textbbox((0, 0), text, font=font)
    draw.text((x - (bbox[2] - bbox[0]), y), text, font=font, fill=color)


def draw_bullets(
    draw: ImageDraw.ImageDraw,
    bullets: list[str],
    x: int,
    y: int,
    max_width: int,
    font,
    fill: str,
    gap: int = 10,
) -> int:
    current_y = y
    color = hex_to_rgb(fill)
    for idx, bullet in enumerate(bullets, start=1):
        label = f"{idx}"
        label_bbox = draw.textbbox((0, 0), label, font=font)
        label_width = label_bbox[2] - label_bbox[0]
        draw.text((x, current_y), label, font=font, fill=color)
        line_x = x + label_width + 16
        bullet_lines = split_lines(bullet, max_width - line_x + x, font)
        if not bullet_lines:
            bullet_lines = [bullet]
        for line in bullet_lines:
            draw.text((line_x, current_y), line, font=font, fill=color)
            current_y += (label_bbox[3] - label_bbox[1]) + gap
        current_y += 6
    return current_y


def generate_carousel_slide(plan: SlidePlan) -> Image.Image:
    width, height = CANVAS_SIZE
    theme = THEMES.get(plan.theme_key, THEMES[DEFAULT_THEME])
    img = Image.new("RGB", (width, height), color=hex_to_rgb(theme["bg"]))
    draw = ImageDraw.Draw(img)
    draw_frame(draw, width, height, plan.theme_key)

    text = theme["text"]
    accent = theme["accent"]
    muted = theme["muted"]
    left = 92
    right = width - 92
    header_y = 78

    if plan.index == 1:
        draw.text((left, header_y), clean_text(plan.header, "Your Brand").upper(), font=FONT_SMALL_BOLD, fill=hex_to_rgb(text))
        draw_right_text(
            draw,
            f"{plan.index:02d} / {plan.total:02d}",
            right,
            header_y,
            FONT_SMALL_BOLD,
            text,
        )
    else:
        header_text = f"{clean_text(plan.header, 'SLIDE').upper()} — {plan.index:02d} / {plan.total:02d}"
        draw.text((left, header_y), header_text, font=FONT_SMALL_BOLD, fill=hex_to_rgb(text))

    draw.line([(left, header_y + 34), (left + 70, header_y + 34)], fill=hex_to_rgb(accent), width=3)

    content_top = 210
    max_text = right - left
    headline_font = FONT_DISPLAY_XL if plan.index in (1, 2) else FONT_DISPLAY_LG
    headline_lines = split_lines(plan.headline, max_text, headline_font)
    if not headline_lines:
        headline_lines = ["Still early.", "But already in motion."]
    current_y = draw_multiline(draw, headline_lines, left, content_top, headline_font, text, 12)

    if plan.hook:
        hook_lines = split_lines(plan.hook, max_text, FONT_ITALIC)
        if hook_lines:
            current_y = draw_multiline(draw, hook_lines[:2], left, current_y + 18, FONT_ITALIC, muted, 6)

    if plan.bullets:
        current_y = draw_bullets(draw, plan.bullets, left, current_y + 22, max_text, FONT_SMALL_BOLD, text, gap=8)

    if plan.cta:
        cta_lines = split_lines(plan.cta, max_text, FONT_SMALL_BOLD)
        draw_multiline(draw, cta_lines, left, current_y + 18, FONT_SMALL_BOLD, accent, 6)

    if plan.footer_line:
        draw.text((left, height - 150), plan.footer_line, font=FONT_ITALIC, fill=hex_to_rgb(muted))

    draw.text((left, height - 70), plan.footer_left, font=FONT_SMALL_BOLD, fill=hex_to_rgb(text))

    footer_right = plan.swipe_text or plan.footer_right
    if footer_right:
        draw_right_text(draw, footer_right, right, height - 70, FONT_SMALL_BOLD, text)

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
        "theme_preset": clean_text(data.get("theme_preset"), DEFAULT_THEME),
        "topic": clean_text(data.get("topic"), "It started as a question."),
        "message": clean_text(data.get("message"), "Clinical insight through continuous memory."),
        "tone": clean_text(data.get("tone"), "calm, premium, and editorial"),
        "audience": clean_text(data.get("audience"), "your audience"),
        "keywords": clean_text(data.get("keywords"), "clarity, trust, calm, editorial"),
        "website": clean_text(data.get("website"), ""),
        "slide_outline": clean_text(data.get("slide_outline"), ""),
        "slide_count": slide_count,
    }


def create_slide_bundle(payload: dict[str, Any]) -> dict[str, Any]:
    if payload.get("slide_outline"):
        plans = build_slide_plan(payload)
        source = "outline"
    else:
        provider, model = select_llm_provider()
        ai_text = None
        source = "fallback"
        if provider == "openai":
            ai_text = try_openai(prompt_for_ai(payload), model)
            source = "openai"
        elif provider == "anthropic":
            ai_text = try_anthropic(prompt_for_ai(payload), model)
            source = "anthropic"
        elif provider == "ollama":
            ai_text = try_ollama(prompt_for_ai(payload), model)
            source = "ollama"

        plans = build_slide_plan_from_ai(payload, ai_text or "") if ai_text else None
        if not plans:
            plans = build_slide_plan(payload)
            source = "fallback"

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
        "source": source,
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
        <p class="lede">Give the agent your own prompt and it will build a consistent carousel deck in the same visual language as your reference PPTX: same font family feel, same sizes, same grid structure, same palette, and downloadable PNG slides.</p>
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
            <label for="theme_preset">Theme preset</label>
            <select id="theme_preset" name="theme_preset">
              <option value="sereai" selected>SEREAI PPTX</option>
            </select>
          </div>

          <div>
            <label for="topic">Prompt / topic</label>
            <input id="topic" name="topic" value="It started as a question. Now it's something real." />
          </div>

          <div>
            <label for="message">Message</label>
            <textarea id="message" name="message">Clinical insight through continuous memory.</textarea>
          </div>

          <div>
            <label for="website">Website / handle (optional)</label>
            <input id="website" name="website" value="aidot.tech" />
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

          <div>
            <label for="slide_outline">Slide outline (optional, one line per slide)</label>
            <textarea id="slide_outline" name="slide_outline" placeholder="THE SCENARIO: The moment something shifts | A routine decision happens every day"></textarea>
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
        <div class="footer-note">The agent will use OpenAI, Anthropic, or Ollama when keys are available. Otherwise it stays fully usable offline with the same visual system.</div>
      </section>
    </div>
  </div>

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
      theme_preset: 'sereai',
      topic: "It started as a question. Now it's something real.",
      message: 'Clinical insight through continuous memory.',
      tone: 'calm, premium, and editorial',
      audience: 'customers, prospects, and community followers',
      keywords: 'clarity, trust, calm, editorial',
      website: 'aidot.tech',
      slide_outline: '',
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

    downloadAllButton.addEventListener('click', () => {
      if (!currentBundle) return;
      const params = new URLSearchParams();
      params.set('bundle', JSON.stringify(currentBundle));
      window.location.href = '/api/download-zip?' + params.toString();
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

      const response = await fetch('/api/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      const data = await response.json();
      currentBundle = data;
      const sourceLabels = {
        openai: 'Planned with OpenAI',
        anthropic: 'Planned with Anthropic',
        ollama: 'Planned with local Ollama',
        outline: 'Built from your slide outline',
        fallback: 'Built with the offline carousel engine',
      };
      sourcePill.textContent = sourceLabels[data.source] || 'Carousel ready';
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


@app.get("/api/download-zip")
def api_download_zip():
    bundle_raw = request.args.get("bundle", "")
    if not bundle_raw:
        return jsonify({"error": "Missing bundle data"}), 400

    try:
        bundle = json.loads(bundle_raw)
        slides = bundle.get("slides", [])
    except json.JSONDecodeError:
        return jsonify({"error": "Invalid bundle data"}), 400

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
        for slide in slides:
            image_data = base64.b64decode(slide["image"])
            archive.writestr(slide["filename"], image_data)
    zip_buffer.seek(0)
    filename = f"carousel_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.zip"
    return send_file(zip_buffer, as_attachment=True, download_name=filename, mimetype="application/zip")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    app.run(host="0.0.0.0", port=port, debug=True)
