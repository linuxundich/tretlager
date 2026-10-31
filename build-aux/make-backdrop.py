#!/usr/bin/env python3
"""Page header background from a photo: tonal silhouette as an alpha mask.

    build-aux/make-backdrop.py photo.jpg [tretlager/data/backdrop.png] [--preview folder]

The output is white with an alpha channel: dark parts of the image (riders, shadows, trees) become opaque,
the bright sky transparent. The UI tints it with the text colour of the colour scheme and shows it at
low opacity (PageHero.qml), so it fits both light and dark. Three tone levels, a median filter and soft
edges turn the photo into a calm graphic; lettering and faces disappear.
"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageFilter, ImageOps

WIDTH = 1400  # enough for the header width (gridUnit * 62) even at 2x scaling of the crop
LEVELS = 3
FLOOR = 110  # brighter tones (sky, sunny road) stay fully transparent


def backdrop(src: Path) -> Image.Image:
    im = Image.open(src).convert("L")
    w, h = im.size
    # Crop: the group down to the wheels, little sky; aspect ratio about 3:1 like the page header,
    # so the UI hardly has to crop and the soft edges stay visible
    im = im.crop((0, int(h * 0.06), w, int(h * 0.64)))
    im = im.resize((WIDTH, round(WIDTH * im.height / im.width)), Image.LANCZOS)
    im = ImageOps.autocontrast(im, cutoff=2)
    # Median filter smooths asphalt and grass grain; three tone levels like an illustration
    dark = ImageOps.invert(im.filter(ImageFilter.MedianFilter(7)))
    step = 256 // LEVELS
    dark = dark.point(lambda v: 0 if v < FLOOR else min(255, (v // step) * step + step // 2))
    dark = dark.filter(ImageFilter.GaussianBlur(1.5))
    # Soft edges on all sides, longest at the bottom
    fade = Image.new("L", dark.size, 0)
    fw, fh = dark.size
    px = fade.load()
    for x in range(fw):
        edge_x = min(x, fw - 1 - x) / (fw * 0.25)
        for y in range(fh):
            edge_y = min((fh - 1 - y) / (fh * 0.40), y / (fh * 0.30))
            px[x, y] = int(255 * max(0.0, min(1.0, edge_x, edge_y)) ** 1.5)
    alpha = ImageChops.multiply(dark, fade)
    out = Image.new("RGBA", dark.size, (255, 255, 255, 0))
    out.putalpha(alpha)
    return out


def preview(img: Image.Image, folder: Path) -> None:
    """How it looks in Breeze light and dark (opacity as in PageHero.qml)."""
    folder.mkdir(parents=True, exist_ok=True)
    for name, bg, fg, opacity in (("light", "#eff0f1", "#232629", 0.09), ("dark", "#202326", "#fcfcfc", 0.07),
                                  ("form", "#ffffff", "#000000", 0.6)):
        base = Image.new("RGBA", img.size, bg)
        ink = Image.new("RGBA", img.size, fg)
        ink.putalpha(img.getchannel("A").point(lambda a: int(a * opacity)))
        Image.alpha_composite(base, ink).convert("RGB").save(folder / f"backdrop-{name}.png")


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        print(__doc__)
        return 2
    src = Path(args[0])
    dest = Path(args[1]) if len(args) > 1 else Path(__file__).resolve().parent.parent / "tretlager/data/backdrop.png"
    img = backdrop(src)
    img.save(dest, optimize=True)
    print(dest, img.size, f"{dest.stat().st_size // 1024} kB")
    if "--preview" in sys.argv:
        preview(img, Path(sys.argv[sys.argv.index("--preview") + 1]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
