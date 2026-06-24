"""Generate Android launcher icon assets from imgs/logo.png.

Run from the repo root with the project env:
    uv run python android/tools/gen_launcher_icons.py
"""
from __future__ import annotations

import os

from PIL import Image, ImageDraw

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(REPO_ROOT, "imgs", "logo.png")
RES = os.path.join(REPO_ROOT, "android", "app", "src", "main", "res")

# Legacy square launcher sizes (px) and adaptive foreground sizes (px).
LEGACY = {"mdpi": 48, "hdpi": 72, "xhdpi": 96, "xxhdpi": 144, "xxxhdpi": 192}
FOREGROUND = {"mdpi": 108, "hdpi": 162, "xhdpi": 216, "xxhdpi": 324, "xxxhdpi": 432}
BG = (255, 255, 255, 255)  # matches @color/ic_launcher_background


def load_emblem() -> Image.Image:
    """Load the logo and tightly crop to the non-white/non-transparent emblem."""
    img = Image.open(SRC).convert("RGBA")
    # Build a mask of "ink" pixels (not near-white, not transparent).
    px = img.load()
    w, h = img.size
    mask = Image.new("L", (w, h), 0)
    mdraw = mask.load()
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a > 20 and not (r > 245 and g > 245 and b > 245):
                mdraw[x, y] = 255
    bbox = mask.getbbox()
    return img.crop(bbox) if bbox else img


def square_canvas(emblem: Image.Image, size: int, scale: float, bg) -> Image.Image:
    """Center the emblem on a square RGBA canvas at the given fractional scale."""
    canvas = Image.new("RGBA", (size, size), bg)
    target = int(size * scale)
    e = emblem.copy()
    e.thumbnail((target, target), Image.LANCZOS)
    ox = (size - e.width) // 2
    oy = (size - e.height) // 2
    canvas.alpha_composite(e, (ox, oy))
    return canvas


def round_mask(size: int) -> Image.Image:
    m = Image.new("L", (size, size), 0)
    ImageDraw.Draw(m).ellipse((0, 0, size - 1, size - 1), fill=255)
    return m


def write(img: Image.Image, folder: str, name: str) -> None:
    d = os.path.join(RES, folder)
    os.makedirs(d, exist_ok=True)
    img.save(os.path.join(d, name))


def main() -> None:
    emblem = load_emblem()
    for dens, size in LEGACY.items():
        sq = square_canvas(emblem, size, 0.82, BG)
        write(sq, f"mipmap-{dens}", "ic_launcher.png")
        rnd = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        rnd.paste(sq, (0, 0), round_mask(size))
        write(rnd, f"mipmap-{dens}", "ic_launcher_round.png")
    for dens, size in FOREGROUND.items():
        # Transparent foreground; emblem within the ~66% adaptive safe zone.
        fg = square_canvas(emblem, size, 0.60, (0, 0, 0, 0))
        write(fg, f"drawable-{dens}", "ic_launcher_foreground.png")
    print("Launcher icons generated under", RES)


if __name__ == "__main__":
    main()
