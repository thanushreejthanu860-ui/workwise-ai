"""Generate original, offline-friendly PNG illustrations for WorkWise AI.

All images are generated programmatically with Pillow — no external
assets, no copyright concerns. Run: python tools/generate_images.py

Outputs into static/images/:
  logo.png, hero-career.png, avatar-default.png, sdg8.png
  category-<name>.png        (5 category illustrations)
  company-<n>.png            (12 fictional company logos)
  role-<n>.png               (8 role illustrations for job details)
  tool-<wage|roadmap|interview>.png
  step-<1..4>.png            (how-it-works illustrations)
"""

import math
import os

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "static", "images")
os.makedirs(OUT, exist_ok=True)

# ---------------------------------------------------------------------------
# Design system
# ---------------------------------------------------------------------------
PURPLE = (109, 40, 217)
BLUE = (14, 165, 233)
TEAL = (6, 182, 212)
AMBER = (245, 158, 11)
GREEN = (22, 163, 74)
PINK = (236, 72, 153)
INDIGO = (79, 70, 229)
ORANGE = (249, 115, 22)

WHITE = (255, 255, 255)
DARK = (30, 36, 51)
LIGHT = (244, 246, 251)

# Fictional companies (must match app.py COMPANIES order)
COMPANIES = [
    "NovaByte Labs", "DataNest Analytics", "CloudOrbit Systems",
    "BrightBridge Technologies", "PixelForge Studio", "GreenGrid Mobility",
    "InsightLoop", "CodeVista", "SkillSpring", "NextWave Digital",
    "QuantLeaf Research", "UrbanPulse Ventures",
]
COMPANY_COLORS = [
    (PURPLE, BLUE), (INDIGO, TEAL), (BLUE, GREEN), (ORANGE, AMBER),
    (PINK, PURPLE), (GREEN, TEAL), (AMBER, ORANGE), (TEAL, BLUE),
    (PURPLE, PINK), (INDIGO, BLUE), (GREEN, AMBER), (ORANGE, PINK),
]

ROLES = [
    ("Data Analyst", "chart", (PURPLE, BLUE)),
    ("Data Scientist", "brain", (INDIGO, TEAL)),
    ("Software Developer", "code", (BLUE, PURPLE)),
    ("Web Developer", "globe", (TEAL, INDIGO)),
    ("Digital Marketing", "megaphone", (ORANGE, PINK)),
    ("HR Specialist", "people", (GREEN, BLUE)),
    ("Sales Executive", "target", (AMBER, ORANGE)),
    ("Business Analyst", "briefcase", (PURPLE, TEAL)),
]

FONT_CANDIDATES = [
    "C:/Windows/Fonts/segoeui.ttf",
    "C:/Windows/Fonts/arial.ttf",
    "C:/Windows/Fonts/calibri.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
]


def load_font(size, bold=True):
    """Load a TTF font with fallbacks."""
    for path in FONT_CANDIDATES:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                continue
    return ImageFont.load_default()


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def gradient(size, c1, c2, diagonal=True):
    """Create a gradient image (PIL Image)."""
    w, h = size
    img = Image.new("RGB", size, c1)
    px = img.load()
    for y in range(h):
        for x in range(0, w, 2):  # step 2 for speed, fill pairs below
            t = ((x / w) + (y / h)) / 2 if diagonal else (y / h)
            col = lerp(c1, c2, min(1, max(0, t)))
            px[x, y] = col
            if x + 1 < w:
                px[x + 1, y] = col
    return img


def rounded(draw, box, radius, **kwargs):
    draw.rounded_rectangle(box, radius=radius, **kwargs)


def fill_gradient(img, box, c1, c2):
    """Paste a gradient image into a rectangular region of img."""
    x0, y0, x1, y1 = box
    w, h = max(1, x1 - x0), max(1, y1 - y0)
    img.paste(gradient((w, h), c1, c2), (x0, y0))


def circle(draw, cx, cy, r, **kwargs):
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], **kwargs)


def draw_icon(draw, name, cx, cy, size, color=WHITE):
    """Draw a simple geometric icon centred on (cx, cy)."""
    s = size
    h = s / 2
    lw = max(3, s // 12)

    def line(pts, width=lw):
        draw.line(pts, fill=color, width=width, joint="curve")

    if name == "briefcase":
        rounded(draw, [cx - h, cy - h * 0.55, cx + h, cy + h * 0.75], s // 8,
                outline=color, width=lw)
        line([(cx - h * 0.45, cy - h * 0.55), (cx - h * 0.45, cy - h * 0.95),
              (cx + h * 0.45, cy - h * 0.95), (cx + h * 0.45, cy - h * 0.55)])
        line([(cx - h * 0.3, cy + h * 0.1), (cx + h * 0.3, cy + h * 0.1)])
    elif name == "chart":
        base = cy + h * 0.8
        for i, bh in enumerate([0.4, 0.7, 0.55, 0.95]):
            bx = cx - h * 0.75 + i * (s * 0.28)
            rounded(draw, [bx, base - bh * h * 1.4, bx + s * 0.16, base],
                    s // 16, fill=color)
        line([(cx - h, base), (cx + h, base)], lw)
    elif name == "brain":
        circle(draw, cx, cy, h * 0.85, outline=color, width=lw)
        line([(cx - h * 0.4, cy - h * 0.5), (cx - h * 0.1, cy),
              (cx - h * 0.4, cy + h * 0.5)])
        line([(cx + h * 0.4, cy - h * 0.5), (cx + h * 0.1, cy),
              (cx + h * 0.4, cy + h * 0.5)])
        circle(draw, cx, cy, s // 10, fill=color)
    elif name == "code":
        line([(cx - h * 0.5, cy - h * 0.6), (cx - h, cy), (cx - h * 0.5, cy + h * 0.6)])
        line([(cx + h * 0.5, cy - h * 0.6), (cx + h, cy), (cx + h * 0.5, cy + h * 0.6)])
        line([(cx + h * 0.15, cy - h * 0.8), (cx - h * 0.15, cy + h * 0.8)])
    elif name == "globe":
        circle(draw, cx, cy, h * 0.9, outline=color, width=lw)
        line([(cx - h * 0.9, cy), (cx + h * 0.9, cy)])
        draw.arc([cx - h * 0.45, cy - h * 0.9, cx + h * 0.45, cy + h * 0.9],
                 -90, 90, fill=color, width=lw)
        draw.arc([cx - h * 0.45, cy - h * 0.9, cx + h * 0.45, cy + h * 0.9],
                 90, 270, fill=color, width=lw)
    elif name == "megaphone":
        poly = [(cx - h * 0.8, cy - h * 0.35), (cx + h * 0.5, cy - h * 0.75),
                (cx + h * 0.5, cy + h * 0.75), (cx - h * 0.8, cy + h * 0.35)]
        draw.polygon(poly, outline=color, width=lw)
        line([(cx + h * 0.5, cy - h * 0.4), (cx + h * 0.85, cy - h * 0.55)])
        line([(cx + h * 0.5, cy + h * 0.4), (cx + h * 0.85, cy + h * 0.55)])
        arc = [cx - h * 1.0, cy - h * 0.5, cx - h * 0.2, cy + h * 0.5]
        draw.arc(arc, -60, 60, fill=color, width=lw)
    elif name == "people":
        circle(draw, cx - h * 0.45, cy - h * 0.35, h * 0.3, outline=color, width=lw)
        draw.arc([cx - h * 0.95, cy + h * 0.05, cx + h * 0.05, cy + h * 0.95],
                 180, 360, fill=color, width=lw)
        circle(draw, cx + h * 0.45, cy - h * 0.35, h * 0.3, outline=color, width=lw)
        draw.arc([cx - h * 0.05, cy + h * 0.05, cx + h * 0.95, cy + h * 0.95],
                 180, 360, fill=color, width=lw)
    elif name == "target":
        for r in [h * 0.9, h * 0.55, h * 0.2]:
            circle(draw, cx, cy, r, outline=color, width=lw)
    elif name == "brain2":
        circle(draw, cx, cy, h * 0.9, outline=color, width=lw)
    elif name == "coins":
        circle(draw, cx - h * 0.3, cy, h * 0.55, outline=color, width=lw)
        circle(draw, cx + h * 0.3, cy - h * 0.2, h * 0.55, outline=color, width=lw)
        line([(cx - h * 0.3, cy - h * 0.15), (cx - h * 0.3, cy + h * 0.15)])
    elif name == "map":
        line([(cx - h, cy + h * 0.6), (cx - h * 0.3, cy + h * 0.1),
              (cx + h * 0.1, cy + h * 0.5), (cx + h, cy - h * 0.2)], lw + 1)
        circle(draw, cx - h, cy + h * 0.6, s // 12, fill=color)
        circle(draw, cx + h, cy - h * 0.2, s // 12, fill=color)
    elif name == "mic":
        rounded(draw, [cx - h * 0.3, cy - h * 0.9, cx + h * 0.3, cy + h * 0.1],
                h * 0.3, outline=color, width=lw)
        arc = [cx - h * 0.7, cy - h * 0.3, cx + h * 0.7, cy + h * 0.7]
        draw.arc(arc, 0, 180, fill=color, width=lw)
        line([(cx, cy + h * 0.7), (cx, cy + h * 0.95)])
        line([(cx - h * 0.4, cy + h * 0.95), (cx + h * 0.4, cy + h * 0.95)])
    elif name == "rocket":
        draw.polygon([(cx, cy - h), (cx - h * 0.5, cy + h * 0.3),
                      (cx + h * 0.5, cy + h * 0.3)], outline=color, width=lw)
        circle(draw, cx, cy - h * 0.25, h * 0.18, fill=color)
        line([(cx - h * 0.5, cy + h * 0.3), (cx - h * 0.8, cy + h * 0.8)])
        line([(cx + h * 0.5, cy + h * 0.3), (cx + h * 0.8, cy + h * 0.8)])
        line([(cx, cy + h * 0.3), (cx, cy + h * 0.9)])
    elif name == "search":
        circle(draw, cx - h * 0.2, cy - h * 0.2, h * 0.55, outline=color, width=lw)
        line([(cx + h * 0.2, cy + h * 0.2), (cx + h * 0.8, cy + h * 0.8)], lw + 1)
    elif name == "doc":
        rounded(draw, [cx - h * 0.6, cy - h * 0.9, cx + h * 0.6, cy + h * 0.9],
                s // 12, outline=color, width=lw)
        for i in range(3):
            ly = cy - h * 0.4 + i * h * 0.4
            line([(cx - h * 0.35, ly), (cx + h * 0.35, ly)])
    elif name == "chartline":
        line([(cx - h, cy + h * 0.6), (cx - h * 0.3, cy),
              (cx + h * 0.1, cy + h * 0.35), (cx + h, cy - h * 0.5)], lw + 1)
        circle(draw, cx + h, cy - h * 0.5, s // 12, fill=color)
    else:
        circle(draw, cx, cy, h * 0.7, outline=color, width=lw)


def new_canvas(w, h, bg=LIGHT):
    img = Image.new("RGB", (w, h), bg)
    return img, ImageDraw.Draw(img)


def save(img, name):
    path = os.path.join(OUT, name)
    img.save(path, "PNG", optimize=True)
    print("created", path)


# ---------------------------------------------------------------------------
# 1. Logo (300x300)
# ---------------------------------------------------------------------------
def make_logo():
    size = (300, 300)
    img = gradient(size, PURPLE, BLUE)
    d = ImageDraw.Draw(img)
    # white rounded card
    rounded(d, [30, 30, 270, 270], 48, fill=WHITE)
    # gradient circle
    d.ellipse([70, 70, 230, 230], fill=PURPLE)
    # briefcase icon
    draw_icon(d, "briefcase", 150, 155, 90, WHITE)
    # "W" text
    font = load_font(44)
    d.text((150, 252), "W", font=font, fill=PURPLE, anchor="mm")
    save(img, "logo.png")


# ---------------------------------------------------------------------------
# 2. Hero illustration (640x520)
# ---------------------------------------------------------------------------
def make_hero():
    w, h = 640, 520
    img = gradient((w, h), (76, 29, 149), (6, 182, 212))
    d = ImageDraw.Draw(img)
    # soft circles
    for (cx, cy, r, a) in [(90, 90, 70, 40), (560, 120, 90, 35),
                             (120, 430, 80, 35), (540, 440, 60, 40)]:
        d.ellipse([cx - r, cy - r, cx + r, cy + r],
                  fill=lerp((76, 29, 149), WHITE, a / 100))
    # main card
    rounded(d, [70, 90, 400, 300], 24, fill=WHITE)
    rounded(d, [100, 120, 260, 138], 9, fill=PURPLE)
    for i, bh in enumerate([50, 80, 62, 95]):
        bx = 110 + i * 62
        rounded(d, [bx, 270 - bh, bx + 40, 270], 8, fill=lerp(PURPLE, BLUE, i / 3))
    # AI fit badge
    rounded(d, [290, 130, 390, 175], 22, fill=GREEN)
    f = load_font(26)
    d.text((340, 152), "AI Fit 86%", font=f, fill=WHITE, anchor="mm")
    # second card
    rounded(d, [250, 220, 570, 430], 24, fill=WHITE)
    draw_icon(d, "briefcase", 320, 290, 70, PURPLE)
    rounded(d, [290, 340, 530, 362], 11, fill=(226, 232, 240))
    rounded(d, [290, 375, 500, 397], 11, fill=(226, 232, 240))
    # floating chips
    for (cx, cy, label, col) in [(480, 90, "Remote", TEAL),
                                   (120, 330, "Fresher", AMBER),
                                   (520, 300, "₹ 25k", GREEN)]:
        rounded(d, [cx - 55, cy - 20, cx + 55, cy + 20], 20, fill=col)
        f2 = load_font(20)
        d.text((cx, cy), label, font=f2, fill=WHITE, anchor="mm")
    save(img, "hero-career.png")


# ---------------------------------------------------------------------------
# 3. Default avatar (200x200)
# ---------------------------------------------------------------------------
def make_avatar():
    size = (200, 200)
    img = gradient(size, PURPLE, BLUE)
    d = ImageDraw.Draw(img)
    circle(d, 100, 100, 96, fill=lerp(PURPLE, BLUE, 0.3))
    # person silhouette
    circle(d, 100, 82, 30, fill=WHITE)
    d.pieslice([48, 118, 152, 210], 180, 360, fill=WHITE)
    save(img, "avatar-default.png")


# ---------------------------------------------------------------------------
# 4. SDG 8 illustration (480x320)
# ---------------------------------------------------------------------------
def make_sdg():
    w, h = 480, 320
    img = gradient((w, h), (6, 95, 70), (16, 185, 129))
    d = ImageDraw.Draw(img)
    for (cx, cy, r) in [(60, 60, 50), (430, 70, 60), (80, 270, 55), (420, 260, 45)]:
        d.ellipse([cx - r, cy - r, cx + r, cy + r],
                  fill=lerp((6, 95, 70), WHITE, 18))
    # SDG badge
    rounded(d, [60, 90, 180, 210], 24, fill=WHITE)
    f = load_font(54)
    d.text((120, 150), "SDG 8", font=f, fill=(6, 95, 70), anchor="mm")
    # growth bars
    for i, bh in enumerate([60, 90, 120, 160, 200]):
        bx = 220 + i * 48
        rounded(d, [bx, 260 - bh, bx + 30, 260], 8,
                fill=lerp(WHITE, (253, 230, 138), i / 4))
    # arrow
    d.line([(210, 240), (440, 90)], fill=(253, 230, 138), width=8)
    d.polygon([(440, 90), (415, 95), (430, 115)], fill=(253, 230, 138))
    save(img, "sdg8.png")


# ---------------------------------------------------------------------------
# 5. Category illustrations (440x300)
# ---------------------------------------------------------------------------
CATEGORIES = [
    ("analytics", "Analytics", "chartline", (PURPLE, BLUE)),
    ("software", "Software", "code", (INDIGO, TEAL)),
    ("marketing", "Marketing", "megaphone", (ORANGE, PINK)),
    ("hr", "HR", "people", (GREEN, BLUE)),
    ("sales", "Sales", "target", (AMBER, ORANGE)),
]


def make_category(key, label, icon, colors):
    w, h = 440, 300
    img = gradient((w, h), LIGHT, (226, 232, 240))
    d = ImageDraw.Draw(img)
    # header band
    fill_gradient(img, [0, 0, w, 130], *colors)
    draw_icon(d, icon, w // 2, 65, 80, WHITE)
    # label
    f = load_font(34)
    d.text((w // 2, 190), label, font=f, fill=DARK, anchor="mm")
    f2 = load_font(20)
    d.text((w // 2, 235), "SAMPLE CATEGORY", font=f2, fill=(107, 114, 128), anchor="mm")
    # decorative dots
    for i in range(5):
        circle(d, w // 2 - 60 + i * 30, 270, 5, fill=lerp(colors[0], colors[1], i / 4))
    save(img, f"category-{key}.png")


# ---------------------------------------------------------------------------
# 6. Company logos (200x200)
# ---------------------------------------------------------------------------
def make_company(idx, name, colors):
    size = (200, 200)
    img = gradient(size, *colors)
    d = ImageDraw.Draw(img)
    # inner card with a lighter tint of the same gradient
    inner = gradient((184, 184),
                     lerp(colors[0], WHITE, 0.18),
                     lerp(colors[1], WHITE, 0.18))
    img.paste(inner, (8, 8))
    # rounded mask border effect: redraw rounded outline
    d.rounded_rectangle([8, 8, 192, 192], radius=40,
                        outline=lerp(colors[1], WHITE, 0.35), width=3)
    # initial letter
    f = load_font(96)
    d.text((100, 100), name[0], font=f, fill=WHITE, anchor="mm")
    save(img, f"company-{idx}.png")


# ---------------------------------------------------------------------------
# 7. Role illustrations (480x260) for job details
# ---------------------------------------------------------------------------
def make_role(idx, name, icon, colors):
    w, h = 480, 260
    img = gradient((w, h), *colors)
    d = ImageDraw.Draw(img)
    for (cx, cy, r) in [(50, 50, 45), (w - 60, 60, 55), (70, h - 50, 40)]:
        d.ellipse([cx - r, cy - r, cx + r, cy + r],
                  fill=lerp(colors[0], WHITE, 22))
    draw_icon(d, icon, w // 2, h // 2 - 20, 110, WHITE)
    f = load_font(30)
    d.text((w // 2, h - 38), name, font=f, fill=WHITE, anchor="mm")
    save(img, f"role-{idx}.png")


# ---------------------------------------------------------------------------
# 8. Tool illustrations (440x300)
# ---------------------------------------------------------------------------
TOOLS = [
    ("wage", "Fair Wage", "coins", (GREEN, TEAL)),
    ("roadmap", "Roadmap", "map", (PURPLE, BLUE)),
    ("interview", "Interview", "mic", (INDIGO, PINK)),
]


def make_tool(key, label, icon, colors):
    w, h = 440, 300
    img = gradient((w, h), LIGHT, (226, 232, 240))
    d = ImageDraw.Draw(img)
    fill_gradient(img, [0, 0, w, 150], *colors)
    draw_icon(d, icon, w // 2, 75, 90, WHITE)
    f = load_font(30)
    d.text((w // 2, 215), label, font=f, fill=DARK, anchor="mm")
    save(img, f"tool-{key}.png")


# ---------------------------------------------------------------------------
# 9. How-it-works steps (260x260)
# ---------------------------------------------------------------------------
STEPS = [
    ("profile", "Build profile", "doc", (PURPLE, BLUE)),
    ("match", "AI matching", "search", (INDIGO, TEAL)),
    ("gap", "Close skill gap", "brain", (BLUE, GREEN)),
    ("apply", "Apply & track", "rocket", (ORANGE, PINK)),
]


def make_step(idx, key, label, icon, colors):
    size = (260, 260)
    img = gradient(size, *colors)
    d = ImageDraw.Draw(img)
    circle(d, 130, 110, 78, fill=lerp(colors[0], WHITE, 20))
    draw_icon(d, icon, 130, 110, 80, WHITE)
    f = load_font(24)
    d.text((130, 220), label, font=f, fill=WHITE, anchor="mm")
    save(img, f"step-{idx}.png")


def main():
    print("Generating WorkWise AI images into", OUT)
    make_logo()
    make_hero()
    make_avatar()
    make_sdg()
    for key, label, icon, colors in CATEGORIES:
        make_category(key, label, icon, colors)
    for i, (name, colors) in enumerate(zip(COMPANIES, COMPANY_COLORS), start=1):
        make_company(i, name, colors)
    for i, (name, icon, colors) in enumerate(ROLES, start=1):
        make_role(i, name, icon, colors)
    for key, label, icon, colors in TOOLS:
        make_tool(key, label, icon, colors)
    for i, (key, label, icon, colors) in enumerate(STEPS, start=1):
        make_step(i, key, label, icon, colors)
    print("Done. Total images:", len(os.listdir(OUT)))


if __name__ == "__main__":
    main()
