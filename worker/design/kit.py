#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""design-kit: the designer's deterministic tools (change add-designer-role).

  design-kit render IN.svg OUT.png --width W [--height H] [--opaque]
  design-kit text2path TEXT --family Nunito [--weight 800] [--size 72] [--x 0] [--y 0]
  design-kit contrast FG BG
  design-kit fonts

render  uses rsvg-convert (librsvg, from Debian) and, with --opaque, flattens
        the result to an RGB PNG without alpha (App Store icon, feature graphic,
        screenshot frames).
text2path turns text set in a baked OFL font into one SVG <path> (logos and
        store captions carry no <text> and no web fonts); prints the element
        and the advance width.
Runs in /opt/habitat/design-venv (Pillow, fontTools). No network.
"""
import argparse
import glob
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gates  # noqa: E402

FONTS = os.environ.get("HABITAT_FONTS_DIR", "/opt/habitat/fonts")


def render(a):
    if not a.svg.endswith(".svg") or not a.png.endswith(".png"):
        sys.exit("render: IN must be .svg and OUT .png")
    cmd = ["rsvg-convert", "--width", str(a.width)]
    cmd += ["--height", str(a.height)] if a.height else ["--keep-aspect-ratio"]
    cmd += ["--output", a.png, a.svg]
    subprocess.run(cmd, check=True, timeout=120)
    from PIL import Image
    im = Image.open(a.png)
    if a.height and im.size != (a.width, a.height):
        sys.exit(f"render: got {im.size}, wanted {a.width}x{a.height}; fix the viewBox ratio")
    if a.opaque:
        flat = Image.new("RGB", im.size, (255, 255, 255))
        flat.paste(im.convert("RGBA"), mask=im.convert("RGBA").split()[3])
        flat.save(a.png, optimize=True)
    else:
        im.convert("RGBA").save(a.png, optimize=True)
    print(f"{a.png} {im.size[0]}x{im.size[1]} {'RGB' if a.opaque else 'RGBA'}")


def _font_file(family, weight):
    d = os.path.join(FONTS, family.lower().replace(" ", ""))
    files = sorted(glob.glob(os.path.join(d, "*.ttf")))
    files = [f for f in files if "Italic" not in f]
    if not files:
        sys.exit(f"text2path: no font {family!r}; see `design-kit fonts`")
    if len(files) == 1:
        return files[0], True
    want = "Bold" if weight >= 600 else "Regular"
    return next((f for f in files if want in f), files[0]), False


def text2path(a):
    from fontTools.pens.svgPathPen import SVGPathPen
    from fontTools.pens.transformPen import TransformPen
    from fontTools.ttLib import TTFont
    path, variable = _font_file(a.family, a.weight)
    font = TTFont(path)
    if variable and "fvar" in font:
        from fontTools.varLib import instancer
        axes = {ax.axisTag: ax for ax in font["fvar"].axes}
        loc = {"wght": max(axes["wght"].minValue, min(axes["wght"].maxValue, a.weight))}
        font = instancer.instantiateVariableFont(font, loc)
    scale = a.size / font["head"].unitsPerEm
    cmap, glyphs, hmtx = font.getBestCmap(), font.getGlyphSet(), font["hmtx"]
    pen = SVGPathPen(glyphs)
    x = 0.0
    for ch in a.text:
        name = cmap.get(ord(ch))
        if name is None:
            sys.exit(f"text2path: {a.family} has no glyph for {ch!r}")
        t = TransformPen(pen, (scale, 0, 0, -scale, a.x + x, a.y))
        glyphs[name].draw(t)
        x += hmtx[name][0] * scale + a.tracking
    print(f'<path d="{pen.getCommands()}"/>')
    print(f"<!-- advance {x - a.tracking:.2f} -->", file=sys.stderr)


def contrast(a):
    r = gates.contrast(a.fg, a.bg)
    verdict = "AA text" if r >= 4.5 else ("AA shapes/large" if r >= 3 else "fails AA")
    print(f"{a.fg} on {a.bg}: {r:.2f}:1 ({verdict})")


def fonts(_a):
    for d in sorted(glob.glob(os.path.join(FONTS, "*"))):
        if os.path.isdir(d):
            names = [os.path.basename(f) for f in sorted(glob.glob(os.path.join(d, "*.ttf")))]
            print(f"{os.path.basename(d)}: {', '.join(names)} (licence: {d}/OFL.txt)")


def main():
    ap = argparse.ArgumentParser(prog="design-kit")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("render")
    r.add_argument("svg"), r.add_argument("png")
    r.add_argument("--width", type=int, required=True)
    r.add_argument("--height", type=int)
    r.add_argument("--opaque", action="store_true")
    t = sub.add_parser("text2path")
    t.add_argument("text")
    t.add_argument("--family", required=True)
    t.add_argument("--weight", type=int, default=400)
    t.add_argument("--size", type=float, default=72)
    t.add_argument("--x", type=float, default=0)
    t.add_argument("--y", type=float, default=0)
    t.add_argument("--tracking", type=float, default=0)
    c = sub.add_parser("contrast")
    c.add_argument("fg"), c.add_argument("bg")
    sub.add_parser("fonts")
    a = ap.parse_args()
    {"render": render, "text2path": text2path, "contrast": contrast, "fonts": fonts}[a.cmd](a)


if __name__ == "__main__":
    main()
