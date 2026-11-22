#!/usr/bin/env python3
"""The picture that tastes of one ingredient.

A program that paints one hero food picture: a tall stack of golden
pancakes drowned in glossy maple syrup, a melting slab of butter,
blueberries, and a strawberry on a cream plate. One ingredient --
maple syrup -- carries the whole picture.

Pure Pillow + numpy, no network, no external assets, fully
deterministic (fixed seed). Writes entry.png, 1024x1024, <= 1 MiB.
"""

import math
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

W = H = 1024
MAX_BYTES = 1_048_576
RNG = np.random.default_rng(20261122)


# ---------------------------------------------------------------- helpers
def lerp(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def radial_glow(arr, cx, cy, radius, color, strength):
    """Add a soft radial glow centred at (cx, cy) into a float array."""
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / radius
    fall = np.clip(1.0 - d, 0.0, 1.0) ** 2
    for i in range(3):
        arr[:, :, i] += fall * color[i] * strength


def draw_ellipse_outline(draw, box, width, color):
    for i in range(width):
        draw.ellipse(
            [box[0] + i, box[1] + i, box[2] - i, box[3] - i], outline=color
        )


# ---------------------------------------------------------------- background
def background():
    """Warm dark-brown vertical gradient + amber glow + table band."""
    top = np.array([46, 26, 14], dtype=np.float32)
    mid = np.array([74, 44, 22], dtype=np.float32)
    bot = np.array([58, 34, 18], dtype=np.float32)
    t = np.linspace(0.0, 1.0, H, dtype=np.float32)[:, None, None]
    arr = np.zeros((H, W, 3), dtype=np.float32)
    upper = top[None, None, :] * (1 - t * 2) + mid[None, None, :] * (t * 2)
    lower = mid[None, None, :] * (2 - t * 2) + bot[None, None, :] * (t * 2 - 1)
    arr[: H // 2] = upper[: H // 2]
    arr[H // 2 :] = lower[H // 2 :]
    # Soft radial amber glow behind the plate.
    radial_glow(arr, 512, 640, 560, (255, 170, 60), 0.55)
    radial_glow(arr, 512, 640, 300, (255, 205, 110), 0.35)
    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB")
    d = ImageDraw.Draw(img, "RGBA")
    # Wooden table band at the bottom.
    d.rectangle([0, 918, W, H], fill=(58, 34, 16, 255))
    d.rectangle([0, 918, W, 924], fill=(96, 58, 28, 255))
    for y, tone in ((946, (70, 42, 20)), (978, (48, 28, 14))):
        d.line([0, y, W, y], fill=tone + (255,), width=3)
    # Faint wood grain.
    for _ in range(26):
        y = int(RNG.integers(928, 1018))
        x0 = int(RNG.integers(0, 500))
        x1 = x0 + int(RNG.integers(200, 1024))
        d.line([x0, y, x1, y + int(RNG.integers(-2, 3))],
               fill=(88, 52, 24, 70), width=2)
    return img


# ---------------------------------------------------------------- plate
def plate(d):
    box = [132, 690, 892, 918]
    # Drop shadow under the plate.
    d.ellipse([148, 884, 876, 934], fill=(0, 0, 0, 90))
    # Plate body: cream with a warm rim.
    d.ellipse(box, fill=(246, 236, 214, 255))
    d.ellipse([150, 700, 874, 908], fill=(250, 243, 226, 255))
    draw_ellipse_outline(d, [168, 712, 856, 896], 5, (214, 186, 148, 255))
    draw_ellipse_outline(d, [188, 724, 836, 884], 2, (226, 200, 164, 255))
    # Glossy amber syrup pool, front-right of the plate.
    d.ellipse([600, 800, 830, 888], fill=(176, 96, 12, 255))
    d.ellipse([612, 808, 818, 880], fill=(206, 122, 22, 255))
    d.ellipse([640, 816, 780, 856], fill=(232, 152, 40, 255))
    d.arc([648, 818, 772, 852], start=200, end=330,
          fill=(255, 214, 130, 220), width=7)


# ---------------------------------------------------------------- pancakes
def pancake(d, cx, top_y, width, height):
    """One pancake: darker side band + golden radial top + speckles."""
    x0, x1 = cx - width // 2, cx + width // 2
    # Side band (the cooked edge you see from the front).
    d.ellipse([x0, top_y, x1, top_y + height], fill=(178, 112, 46, 255))
    d.ellipse([x0, top_y, x1, top_y + height - 14],
              fill=(198, 132, 58, 255))
    # Golden top, slightly inset so the toasted rim shows.
    d.ellipse([x0 + 4, top_y - 6, x1 - 4, top_y + height - 22],
              fill=(232, 178, 84, 255))
    d.ellipse([x0 + 14, top_y - 2, x1 - 14, top_y + height - 26],
              fill=(244, 196, 106, 255))
    d.ellipse([x0 + 34, top_y + 2, x1 - 34, top_y + height - 32],
              fill=(250, 208, 128, 255))
    # Toasted rim.
    draw_ellipse_outline(d, [x0 + 4, top_y - 6, x1 - 4, top_y + height - 22],
                         4, (190, 122, 44, 255))
    # Light golden speckles on the top (kept inside the top ellipse).
    for _ in range(46):
        sx = int(RNG.normal(cx, width * 0.22))
        sy = int(RNG.normal(top_y + height * 0.28, height * 0.14))
        sx = max(x0 + 18, min(x1 - 18, sx))
        sy = max(top_y + 2, min(top_y + height - 30, sy))
        r = int(RNG.integers(2, 6))
        tone = int(RNG.integers(200, 235))
        d.ellipse([sx - r, sy - r, sx + r, sy + r],
                  fill=(tone, 150, 60, 110))
    # A few darker toast spots.
    for _ in range(12):
        sx = int(RNG.normal(cx, width * 0.26))
        sy = int(RNG.normal(top_y + height * 0.30, height * 0.16))
        sx = max(x0 + 18, min(x1 - 18, sx))
        sy = max(top_y + 2, min(top_y + height - 30, sy))
        r = int(RNG.integers(2, 5))
        d.ellipse([sx - r, sy - r, sx + r, sy + r],
                  fill=(170, 104, 36, 120))


def syrup_cap(d, cx, top_y, width):
    """Dark glossy maple-syrup cap pooling on the top pancake."""
    x0, x1 = cx - width // 2, cx + width // 2
    d.ellipse([x0 + 6, top_y - 14, x1 - 6, top_y + 26],
              fill=(120, 58, 8, 255))
    d.ellipse([x0 + 16, top_y - 10, x1 - 16, top_y + 18],
              fill=(146, 74, 12, 255))
    d.ellipse([x0 + 34, top_y - 6, x1 - 34, top_y + 10],
              fill=(176, 98, 20, 255))
    # Bright highlight arc on the cap.
    d.arc([x0 + 30, top_y - 8, x1 - 30, top_y + 12], start=195, end=335,
          fill=(255, 216, 130, 235), width=8)
    d.arc([x0 + 52, top_y - 2, x1 - 52, top_y + 6], start=200, end=330,
          fill=(255, 232, 170, 200), width=4)


def syrup_drip(d, x, y0, length, width):
    """One wavy solid syrup drip running down the stack side."""
    pts = []
    steps = 14
    for i in range(steps + 1):
        t = i / steps
        y = y0 + length * t
        wob = math.sin(t * math.pi * 2.2 + x * 0.05) * 5
        pts.append((x + wob - width / 2, y))
    for i in range(steps, -1, -1):
        t = i / steps
        y = y0 + length * t
        wob = math.sin(t * math.pi * 2.2 + x * 0.05) * 5
        pts.append((x + wob + width / 2, y))
    d.polygon(pts, fill=(146, 74, 12, 255))
    # Rounded bulb at the end.
    d.ellipse([x - width / 2 - 2, y0 + length - 6,
               x + width / 2 + 2, y0 + length + 10],
              fill=(146, 74, 12, 255))
    d.ellipse([x - width / 2, y0 + length - 2,
               x + width / 2, y0 + length + 6],
              fill=(176, 98, 20, 255))
    # Thin shine down the drip.
    shine = []
    for i in range(steps + 1):
        t = i / steps
        y = y0 + length * t
        wob = math.sin(t * math.pi * 2.2 + x * 0.05) * 5
        shine.append((x + wob - 3, y))
    d.line(shine, fill=(255, 210, 120, 160), width=3)


# ---------------------------------------------------------------- toppings
def butter(d, cx, cy):
    """Warm-yellow butter slab, slightly tilted, with a melted pool."""
    # Melted pool spreading under the slab.
    d.ellipse([cx - 78, cy + 18, cx + 82, cy + 44],
              fill=(250, 214, 110, 255))
    d.ellipse([cx - 60, cy + 22, cx + 64, cy + 40],
              fill=(255, 226, 140, 255))
    # Slab body (rotated rectangle via polygon).
    ang = math.radians(-7)
    hw, hh = 52, 30
    corners = [(-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh)]
    pts = [(cx + x * math.cos(ang) - y * math.sin(ang),
            cy + x * math.sin(ang) + y * math.cos(ang))
           for x, y in corners]
    d.polygon(pts, fill=(255, 214, 96, 255))
    # Top face, a touch lighter.
    top = [(cx + x * math.cos(ang) - y * math.sin(ang),
            cy + x * math.sin(ang) + y * math.cos(ang))
           for x, y in [(-hw, -hh), (hw, -hh), (hw, -hh + 12), (-hw, -hh + 12)]]
    d.polygon(top, fill=(255, 228, 138, 255))
    # Gloss highlight on the top face.
    d.line([(cx - 38, cy - 26), (cx + 34, cy - 33)],
           fill=(255, 244, 190, 230), width=5)
    # Melt drip off the slab's right edge.
    d.ellipse([cx + 40, cy + 6, cx + 56, cy + 40],
              fill=(250, 210, 100, 255))
    d.ellipse([cx + 42, cy + 30, cx + 54, cy + 46],
              fill=(250, 210, 100, 255))


def blueberry(d, cx, cy, r=26):
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(38, 48, 110, 255))
    d.ellipse([cx - r + 4, cy - r + 3, cx + r - 5, cy + r - 8],
              fill=(58, 72, 148, 255))
    d.ellipse([cx - r + 8, cy - r + 6, cx + r - 10, cy + r - 12],
              fill=(74, 92, 172, 255))
    # Crown star.
    for k in range(5):
        a = math.radians(-90 + k * 72)
        d.line([(cx, cy - r + 6),
                (cx + math.cos(a) * 8, cy - r + 6 + math.sin(a) * 8)],
               fill=(24, 30, 70, 255), width=3)
    # Bloom + highlight.
    d.ellipse([cx - r + 5, cy - r + 4, cx - r + 16, cy - r + 15],
              fill=(200, 205, 235, 160))
    d.ellipse([cx - 9, cy - 12, cx + 3, cy - 1],
              fill=(255, 255, 255, 210))


def strawberry(d, cx, cy):
    """One strawberry leaning on the plate's right edge."""
    d = d  # draw on the same layer
    # Body: plump red heart shape.
    body = [(cx - 52, cy - 30), (cx + 52, cy - 30),
            (cx + 46, cy + 26), (cx + 18, cy + 66),
            (cx, cy + 78), (cx - 18, cy + 66), (cx - 46, cy + 26)]
    d.polygon(body, fill=(198, 32, 44, 255))
    d.ellipse([cx - 52, cy - 44, cx + 52, cy + 10],
              fill=(214, 44, 54, 255))
    d.ellipse([cx - 40, cy - 40, cx + 40, cy - 6],
              fill=(228, 62, 70, 255))
    # Seeds.
    for _ in range(26):
        sx = int(RNG.normal(cx, 30))
        sy = int(RNG.normal(cy + 12, 26))
        d.ellipse([sx - 2, sy - 4, sx + 2, sy + 4],
                  fill=(255, 226, 150, 230))
    # Shine.
    d.ellipse([cx - 34, cy - 34, cx - 8, cy - 8],
              fill=(255, 140, 140, 170))
    # Green calyx leaves.
    for ang in (-150, -110, -70, -30):
        a = math.radians(ang)
        x2 = cx + math.cos(a) * 46
        y2 = cy - 34 + math.sin(a) * 30
        d.line([(cx, cy - 36), (x2, y2)], fill=(46, 120, 52, 255), width=9)
        d.line([(cx, cy - 36), (x2, y2)], fill=(74, 160, 76, 255), width=4)
    d.ellipse([cx - 14, cy - 46, cx + 14, cy - 24],
              fill=(58, 138, 60, 255))


def powdered_sugar(d, cx, top_y, width):
    """Fine white dust scattered over the top pancake."""
    for _ in range(240):
        sx = int(RNG.normal(cx, width * 0.20))
        sy = int(RNG.normal(top_y + 8, 7))
        if ((sx - cx) / (width / 2 - 12)) ** 2 + ((sy - top_y - 8) / 15) ** 2 > 1:
            continue
        r = int(RNG.integers(1, 3))
        d.ellipse([sx - r, sy - r, sx + r, sy + r],
                  fill=(255, 255, 255, int(RNG.integers(120, 210))))


def steam(img):
    """Three soft steam wisps rising above the stack."""
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for cx, phase in ((452, 0.0), (512, 1.4), (572, 2.6)):
        pts = []
        for i in range(40):
            t = i / 39
            y = 452 - t * 165
            x = cx + math.sin(t * 5.0 + phase) * 22 * (0.4 + t)
            pts.append((x, y))
        d.line(pts, fill=(255, 255, 255, 90), width=16)
        d.line(pts, fill=(255, 255, 255, 70), width=8)
    layer = layer.filter(ImageFilter.GaussianBlur(7))
    img.alpha_composite(layer)


def vignette(img):
    arr = np.asarray(img.convert("RGB")).astype(np.float32)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.sqrt(((xx - 512) / 620) ** 2 + ((yy - 512) / 620) ** 2)
    fall = np.clip(1.0 - 0.22 * np.clip(d - 0.55, 0, None) ** 2, 0.78, 1.0)
    arr *= fall[:, :, None]
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB")


# ---------------------------------------------------------------- main
def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    out_path = os.path.join(out_dir, "entry.png")

    img = background().convert("RGBA")
    d = ImageDraw.Draw(img, "RGBA")

    plate(d)

    # Four stacked pancakes, widest at the bottom.
    cx = 512
    layers = [(292, 668), (278, 620), (264, 574), (248, 528)]
    for width, top_y in layers:
        pancake(d, cx, top_y, width, 60)

    # Maple-syrup cap on the top pancake + drips down the stack.
    syrup_cap(d, cx, 528, 248)
    for x, length, width in ((398, 150, 20), (466, 190, 18),
                             (556, 170, 19), (628, 130, 18)):
        syrup_drip(d, x, 540, length, width)

    # Butter slab melting on top, blueberries around it.
    butter(d, 512, 490)
    blueberry(d, 424, 524, 25)
    blueberry(d, 606, 526, 24)
    blueberry(d, 566, 506, 21)

    # Powdered sugar dust on the top pancake.
    powdered_sugar(d, cx, 528, 248)

    # Strawberry leaning on the plate's right edge.
    strawberry(d, 812, 742)

    steam(img)
    img = vignette(img).convert("RGB")

    os.makedirs(out_dir, exist_ok=True)
    img.save(out_path, "PNG", optimize=True)
    assert img.size == (1024, 1024), img.size
    size = os.path.getsize(out_path)
    assert size <= MAX_BYTES, f"{size} bytes > {MAX_BYTES}"
    print(f"wrote {out_path} {img.size[0]}x{img.size[1]} {size} bytes")


if __name__ == "__main__":
    main()
