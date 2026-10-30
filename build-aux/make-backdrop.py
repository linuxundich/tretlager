#!/usr/bin/env python3
"""Hintergrund für den Seitenkopf aus einem Foto: Tonwert-Silhouette als Alphamaske.

    build-aux/make-backdrop.py foto.jpg [tretlager/data/backdrop.png] [--preview ordner]

Die Ausgabe ist weiß mit Alphakanal: dunkle Bildteile (Fahrer, Schatten, Bäume) werden deckend,
der helle Himmel durchsichtig. Die Oberfläche färbt sie mit der Textfarbe des Farbschemas ein und
zeigt sie mit geringer Deckkraft (PageHero.qml), so passt sie zu Hell und Dunkel. Drei Tonstufen,
Medianfilter und weiche Ränder machen aus dem Foto eine ruhige Grafik; Schrift und Gesichter verschwinden.
"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageFilter, ImageOps

WIDTH = 1400  # reicht für die Kopfbreite (gridUnit * 62) auch bei 2× Skalierung im Ausschnitt
LEVELS = 3
FLOOR = 110  # hellere Töne (Himmel, sonnige Straße) bleiben ganz durchsichtig


def backdrop(src: Path) -> Image.Image:
    im = Image.open(src).convert("L")
    w, h = im.size
    # Ausschnitt: Gruppe bis zu den Rädern, wenig Himmel; Seitenverhältnis ≈ 3:1 wie der Seitenkopf,
    # damit die Oberfläche kaum beschneiden muss und die weichen Ränder sichtbar bleiben
    im = im.crop((0, int(h * 0.06), w, int(h * 0.64)))
    im = im.resize((WIDTH, round(WIDTH * im.height / im.width)), Image.LANCZOS)
    im = ImageOps.autocontrast(im, cutoff=2)
    # Medianfilter glättet Asphalt- und Graskörnung; drei Tonstufen wie eine Illustration
    dark = ImageOps.invert(im.filter(ImageFilter.MedianFilter(7)))
    step = 256 // LEVELS
    dark = dark.point(lambda v: 0 if v < FLOOR else min(255, (v // step) * step + step // 2))
    dark = dark.filter(ImageFilter.GaussianBlur(1.5))
    # Weiche Ränder an allen Seiten, unten am längsten
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
    """So sieht es in Breeze hell und dunkel aus (Deckkraft wie in PageHero.qml)."""
    folder.mkdir(parents=True, exist_ok=True)
    for name, bg, fg, opacity in (("hell", "#eff0f1", "#232629", 0.09), ("dunkel", "#202326", "#fcfcfc", 0.07),
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
