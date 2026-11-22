#!/usr/bin/env python3
"""The picture that tastes of one ingredient.

A program that paints one delicious food picture: a tall stack of golden
pancakes drowned in glossy maple syrup, a pat of butter melting on top,
fresh blueberries and a strawberry, on a ceramic plate in warm morning
light. Everything is drawn procedurally with Pillow + numpy -- no network,
no external assets, fully deterministic.

Writes /output/entry.png (or $MAKEFUN_OUTPUT_DIR/entry.png):
a 1024x1024 PNG, well under the 1 MiB gate.
"""

import math
import os
import random

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

W = H = 1024
OUT_DIR = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
RNG = random.Random(20261122)


# ---------------------------------------------------------------- helpers

def vertical_gradient(size, top, bottom):
    """Smooth top->bottom RGB gradient as an RGB image."""
    w, h = size
    t = np.linspace(0.0, 1.0, h, dtype=np.float64)[:, None, None]
    top_a = np.array(top, dtype=np.float64)[None, None, :]
    bot_a = np.array(bottom, dtype=np.float64)[None, None, :]
    arr = top_a * (1.0 - t) + bot_a * t
    arr = np.repeat(arr, w, axis=1)
    return Image.fromarray(arr.astype(np.uint8), "RGB")


def radial_glow(size, center, radius, color, peak_alpha):
    """Soft radial glow: an RGBA layer, brightest at center."""
    w, h = size
    yy, xx = np.mgrid[0:h, 0:w]
    d = np.sqrt((xx - center[0]) ** 2 + (yy - center[1]) ** 2) / radius
    a = np.clip(1.0 - d, 0.0, 1.0) ** 2.2 * peak_alpha
    layer = np.zeros((h, w, 4), dtype=np.uint8)
    layer[..., 0] = color[0]
    layer[..., 1] = color[1]
    layer[..., 2] = color[2]
    layer[..., 3] = a.astype(np.uint8)
    return Image.fromarray(layer, "RGBA")


def soft_ellipse(layer, box, fill, blur):
    """Draw a filled ellipse on its own layer, blur it, return the layer."""
    tmp = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    ImageDraw.Draw(tmp).ellipse(box, fill=fill)
    return Image.alpha_composite(layer, tmp.filter(ImageFilter.GaussianBlur(blur)))


def ellipse_top(draw, cx, cy, rx, ry, colors):
    """A pancake top face: concentric ellipses, light centre -> toasted rim."""
    steps = 26
    for i in range(steps, 0, -1):
        f = i / steps
        r = int(colors[0][0] + (colors[1][0] - colors[0][0]) * (1 - f))
        g = int(colors[0][1] + (colors[1][1] - colors[0][1]) * (1 - f))
        b = int(colors[0][2] + (colors[1][2] - colors[0][2]) * (1 - f))
        draw.ellipse(
            [cx - rx * f, cy - ry * f, cx + rx * f, cy + ry * f],
            fill=(r, g, b, 255),
        )
    # toasted speckles: tiny darker dots, denser near the rim
    for _ in range(120):
        ang = RNG.uniform(0, 2 * math.pi)
        rr = math.sqrt(RNG.uniform(0.6, 1.0))
        x = cx + math.cos(ang) * rx * rr
        y = cy + math.sin(ang) * ry * rr
        s = RNG.uniform(1.5, 4.0)
        shade = RNG.choice([(146, 84, 22, 70), (120, 62, 14, 55), (214, 150, 70, 55)])
        draw.ellipse([x - s, y - s * 0.6, x + s, y + s * 0.6], fill=shade)


def pancake(base, cx, top_y, rx, ry, band_h, dx=0):
    """One pancake: side band + golden top face. Returns the new layer."""
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    cx += dx
    cy = top_y + ry
    # side band: vertical gradient baked as stacked thin ellipses
    for i in range(band_h):
        f = i / band_h
        r = int(176 + (122 - 176) * f)
        g = int(106 + (68 - 106) * f)
        b = int(36 + (19 - 36) * f)
        d.ellipse([cx - rx, cy + i - ry * 0.12, cx + rx, cy + i + ry * 0.12],
                  fill=(r, g, b, 255))
    # soft bottom shade of the band
    d.ellipse([cx - rx, cy + band_h - ry * 0.35, cx + rx, cy + band_h + ry * 0.15],
              fill=(96, 52, 12, 140))
    # top face
    ellipse_top(d, cx, cy, rx, ry, ((238, 178, 92), (196, 128, 48)))
    # crisp toasted rim
    d.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], outline=(150, 86, 20, 220), width=4)
    # warm light kiss on the upper-left of the top face
    layer = soft_ellipse(layer, [cx - rx * 0.75, cy - ry * 0.85,
                                  cx - rx * 0.05, cy - ry * 0.05],
                         (255, 224, 160, 70), 18)
    return Image.alpha_composite(base, layer)


def syrup_drip(base, x, y_top, y_bot, width, color=(168, 82, 8, 235)):
    """One glossy syrup drip running down the stack: a gently waving
    solid ribbon with a rounded end and a thin gloss line."""
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    steps = max(2, int((y_bot - y_top) / 6))
    pts = []
    for i in range(steps + 1):
        f = i / steps
        pts.append((x + math.sin(f * 5.0) * width * 0.22,
                    y_top + (y_bot - y_top) * f))
    d.line(pts, fill=color, width=int(width), joint="curve")
    ex, ey = pts[-1]
    d.ellipse([ex - width * 0.55, ey - width * 0.35,
               ex + width * 0.55, ey + width * 0.35], fill=color)
    # glossy highlight: a thinner wavy line down the left edge
    hpts = [(px - width * 0.22, py) for px, py in pts]
    d.line(hpts, fill=(240, 168, 50, 210),
           width=max(3, int(width * 0.28)), joint="curve")
    return Image.alpha_composite(base, layer)


def blueberry(base, cx, cy, r):
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(38, 48, 96, 255))
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(20, 26, 60, 255), width=2)
    # bloom + shine
    layer = soft_ellipse(layer, [cx - r * 0.7, cy - r * 0.75, cx + r * 0.1, cy + r * 0.1],
                         (150, 165, 225, 110), 8)
    d = ImageDraw.Draw(layer)
    d.ellipse([cx - r * 0.45, cy - r * 0.55, cx - r * 0.05, cy - r * 0.15],
              fill=(235, 240, 255, 235))
    # little crown star
    for k in range(5):
        ang = -math.pi / 2 + k * 2 * math.pi / 5
        x1 = cx + math.cos(ang) * r * 0.28
        y1 = cy + math.sin(ang) * r * 0.28
        x2 = cx + math.cos(ang) * r * 0.52
        y2 = cy + math.sin(ang) * r * 0.52
        d.line([x1, y1, x2, y2], fill=(74, 90, 154, 255), width=3)
    d.ellipse([cx - r * 0.14, cy - r * 0.14, cx + r * 0.14, cy + r * 0.14],
              fill=(74, 90, 154, 255))
    return Image.alpha_composite(base, layer)


def strawberry(base, cx, cy, s):
    """A plump strawberry leaning at the plate's edge, seeds and leaves."""
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    # body: a wide heart-ish shape built from a polygon + circles
    pts = []
    for t in np.linspace(0, 1, 40):
        ang = math.pi * t  # upper half arc
        pts.append((cx + math.cos(ang) * s * 0.62, cy - s * 0.18 - math.sin(ang) * s * 0.30))
    d.polygon(pts, fill=(206, 32, 44, 255))
    d.ellipse([cx - s * 0.62, cy - s * 0.48, cx + s * 0.62, cy + s * 0.10],
              fill=(206, 32, 44, 255))
    d.polygon([(cx - s * 0.58, cy - s * 0.10), (cx + s * 0.58, cy - s * 0.10),
               (cx + s * 0.18, cy + s * 0.78), (cx - s * 0.18, cy + s * 0.78)],
              fill=(206, 32, 44, 255))
    d.ellipse([cx - s * 0.30, cy + s * 0.42, cx + s * 0.30, cy + s * 0.86],
              fill=(206, 32, 44, 255))
    # shading: darker right side, lit left side
    layer = soft_ellipse(layer, [cx + s * 0.05, cy - s * 0.45, cx + s * 0.65, cy + s * 0.8],
                         (120, 8, 18, 130), 14)
    layer = soft_ellipse(layer, [cx - s * 0.6, cy - s * 0.45, cx - s * 0.05, cy + s * 0.3],
                         (255, 120, 110, 110), 14)
    d = ImageDraw.Draw(layer)
    # seeds
    for row, yy in enumerate(np.linspace(-0.28, 0.62, 5)):
        n = 5 - abs(row - 2)
        for k in range(n):
            x = cx + (k - (n - 1) / 2) * s * 0.26
            y = cy + yy * s
            d.ellipse([x - 3, y - 5, x + 3, y + 5], fill=(255, 214, 150, 230))
    # glossy highlight
    d.ellipse([cx - s * 0.48, cy - s * 0.42, cx - s * 0.10, cy - s * 0.02],
              fill=(255, 150, 140, 160))
    # leafy top
    for k in range(5):
        ang = -math.pi / 2 + (k - 2) * 0.42
        x2 = cx + math.cos(ang) * s * 0.52
        y2 = cy - s * 0.42 + math.sin(ang) * s * 0.42
        d.line([cx, cy - s * 0.42, x2, y2], fill=(52, 110, 44, 255), width=9)
    d.ellipse([cx - s * 0.10, cy - s * 0.52, cx + s * 0.10, cy - s * 0.32],
              fill=(66, 128, 52, 255))
    return Image.alpha_composite(base, layer)


def butter(base, cx, cy, w, h):
    """A pat of butter, edges softening as it melts, with a drip."""
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    # slight perspective: a soft-edged slab
    d.rounded_rectangle([cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2],
                        radius=16, fill=(255, 222, 138, 255))
    d.rounded_rectangle([cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2],
                        radius=16, outline=(226, 190, 96, 255), width=3)
    # top face glow
    d.rounded_rectangle([cx - w / 2 + 10, cy - h / 2 + 8, cx + w / 2 - 14, cy - h / 2 + 26],
                        radius=9, fill=(255, 246, 207, 220))
    # melting drip off the front-right corner
    d.rounded_rectangle([cx + w * 0.18, cy + h / 2 - 6, cx + w * 0.34, cy + h / 2 + 34],
                        radius=8, fill=(255, 222, 138, 255))
    d.ellipse([cx + w * 0.18, cy + h / 2 + 22, cx + w * 0.34, cy + h / 2 + 40],
              fill=(255, 222, 138, 255))
    # melted pool spreading around the base of the slab
    layer = soft_ellipse(layer, [cx - w / 2 - 14, cy + h / 2 - 10,
                                  cx + w / 2 + 20, cy + h / 2 + 20],
                         (255, 226, 140, 175), 10)
    # soft shadow under the slab
    layer = soft_ellipse(layer, [cx - w / 2, cy + h / 2 - 8, cx + w / 2, cy + h / 2 + 16],
                         (120, 70, 10, 110), 8)
    return Image.alpha_composite(base, layer)


def steam(base, x, y_top, y_bot, amp, alpha):
    """One lazy wisp of steam, drawn as a blurred sine ribbon."""
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    pts = []
    for y in range(y_top, y_bot, 4):
        f = (y_bot - y) / max(1, y_bot - y_top)
        pts.append((x + math.sin(f * 5.2) * amp * f, y))
    d.line(pts, fill=(255, 250, 240, alpha), width=16, joint="curve")
    return Image.alpha_composite(base, layer.filter(ImageFilter.GaussianBlur(7)))


# ---------------------------------------------------------------- scene

def build():
    img = vertical_gradient((W, H), (38, 22, 10), (74, 44, 20)).convert("RGBA")
    # warm morning glow behind the plate
    img = Image.alpha_composite(img, radial_glow((W, H), (512, 430), 560,
                                                 (255, 190, 110), 150))
    img = Image.alpha_composite(img, radial_glow((W, H), (512, 760), 700,
                                                 (255, 170, 90), 60))
    d = ImageDraw.Draw(img)
    # wooden table: lower band + soft sheen
    d.rectangle([0, 800, W, H], fill=(58, 34, 16, 255))
    img = Image.alpha_composite(img, radial_glow((W, H), (512, 900), 620,
                                                 (150, 95, 45), 90))
    d = ImageDraw.Draw(img)
    for gx in (180, 512, 844):
        d.line([gx, 806, gx, H], fill=(40, 22, 10, 90), width=3)

    # plate shadow, then the plate
    img = soft_ellipse(img, [150, 800, 874, 940], (0, 0, 0, 150), 22)
    d = ImageDraw.Draw(img)
    d.ellipse([132, 690, 892, 918], fill=(244, 236, 220, 255))
    d.ellipse([132, 690, 892, 918], outline=(214, 200, 176, 255), width=3)
    d.ellipse([168, 712, 856, 894], outline=(226, 212, 188, 255), width=3)
    # syrup pool glistening on the plate, front-right
    img = soft_ellipse(img, [560, 830, 830, 892], (150, 74, 6, 235), 6)
    d = ImageDraw.Draw(img)
    d.ellipse([560, 830, 830, 892], fill=(168, 88, 10, 235))
    d.arc([590, 838, 800, 884], start=200, end=330, fill=(240, 168, 50, 220), width=6)

    # the stack: four pancakes, lowest first
    img = pancake(img, 512, 640, 292, 82, 58, dx=-10)
    img = pancake(img, 512, 578, 278, 78, 56, dx=8)
    img = pancake(img, 512, 516, 264, 74, 54, dx=-6)
    img = pancake(img, 512, 454, 248, 70, 52, dx=2)

    # maple syrup: glossy cap on the top pancake + drips down the stack
    syrup = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ds = ImageDraw.Draw(syrup)
    ds.ellipse([268, 448, 756, 588], fill=(146, 66, 4, 228))
    ds.ellipse([300, 458, 724, 566], fill=(172, 84, 8, 228))
    ds.arc([330, 466, 700, 556], start=195, end=335, fill=(250, 190, 80, 235), width=9)
    img = Image.alpha_composite(img, syrup.filter(ImageFilter.GaussianBlur(2)))
    img = syrup_drip(img, 352, 505, 668, 20)
    img = syrup_drip(img, 688, 512, 618, 18)
    img = syrup_drip(img, 742, 540, 700, 18)
    img = syrup_drip(img, 296, 545, 640, 18)

    # melting butter on top, slightly off-centre
    img = butter(img, 505, 462, 104, 60)

    # blueberries crowning the top
    img = blueberry(img, 640, 478, 34)
    img = blueberry(img, 392, 490, 30)
    img = blueberry(img, 596, 522, 26)

    # strawberry leaning on the plate's right edge, fully in view
    img = strawberry(img, 838, 772, 86)

    # powdered sugar dust over the top pancake
    d = ImageDraw.Draw(img)
    for _ in range(90):
        x = RNG.uniform(300, 720)
        y = RNG.uniform(470, 560)
        r = RNG.uniform(1.0, 2.6)
        d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 250, 240, 150))

    # steam rising off the hot stack
    img = steam(img, 430, 300, 470, 26, 90)
    img = steam(img, 560, 280, 470, 30, 80)
    img = steam(img, 650, 320, 480, 22, 70)

    # gentle vignette so the eye stays on the food
    vig = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dv = ImageDraw.Draw(vig)
    dv.rectangle([0, 0, W, H], outline=(20, 10, 4, 110), width=90)
    img = Image.alpha_composite(img, vig.filter(ImageFilter.GaussianBlur(60)))

    # a whisper of warmth + crispness
    img = img.convert("RGB").filter(ImageFilter.UnsharpMask(radius=2, percent=60,
                                                            threshold=3))
    return img


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    img = build()
    path = os.path.join(OUT_DIR, "entry.png")
    img.save(path, format="PNG", optimize=True)
    size = os.path.getsize(path)
    print(f"wrote {path}: {img.size[0]}x{img.size[1]}, {size} bytes")
    assert img.size == (1024, 1024), "must be 1024x1024"
    assert size <= 1_048_576, "must be at most 1 MiB"
    print("gate OK: 1024x1024 PNG under 1 MiB")


if __name__ == "__main__":
    main()
