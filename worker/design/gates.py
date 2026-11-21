# SPDX-License-Identifier: MIT
"""The designer's quality gates (change add-designer-role). Standard library only.

Every gate returns a list of findings; an empty list is a pass. The numbers come
from the sources named in docs/explanation/designer-agent.md: WCAG 2.2 (1.4.3,
1.4.11), Android adaptive icons (108 dp layer, 66 dp safe circle) and the Google
Play icon spec (512 px, 32-bit, Play masks with a 30 % corner radius; artwork
on the 75 % keyline grid).
"""
import math
import re
import xml.etree.ElementTree as ET

import png

# Fonts baked into the worker image (all SIL OFL 1.1). Nothing else may be named.
OFL_FAMILIES = {"Nunito", "Fredoka", "Baloo 2", "Lexend", "Andika"}
GROUPS = ("puzzles", "board", "creative", "learning", "action")


def _lum(hexcol):
    h = hexcol.lstrip("#")
    if not re.fullmatch(r"[0-9a-fA-F]{6}", h):
        raise ValueError(f"not a #rrggbb colour: {hexcol!r}")
    out = []
    for i in (0, 2, 4):
        c = int(h[i:i + 2], 16) / 255
        out.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return 0.2126 * out[0] + 0.7152 * out[1] + 0.0722 * out[2]


def contrast(a, b):
    la, lb = sorted((_lum(a), _lum(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def tokens(tok, where):
    """WCAG AA on the palette: text 4.5:1, accents (shapes) 3:1 on the base."""
    out = []
    try:
        c = tok["color"]
        pairs = [("ink", "base", 4.5), ("ink-soft", "base", 4.5), ("on-brand", "brand", 4.5)]
        for fg, bg, need in pairs:
            r = contrast(c[fg], c[bg])
            if r < need:
                out.append(f"{where}: {fg} on {bg} is {r:.2f}:1, needs {need}:1")
        for g in GROUPS:
            grp = c["groups"][g]
            r = contrast(grp["accent"], c["base"])
            if r < 3.0:
                out.append(f"{where}: {g} accent on base is {r:.2f}:1, needs 3:1")
            r = contrast(grp["text"], grp["tint"])
            if r < 4.5:
                out.append(f"{where}: {g} text on its tint is {r:.2f}:1, needs 4.5:1")
        fams = set(tok["type"]["families"].values())
        for f in sorted(fams - OFL_FAMILIES):
            out.append(f"{where}: font {f!r} is not one of the OFL fonts in the image")
        if min(tok["type"]["scale_px"]) < 16:
            out.append(f"{where}: type scale goes below 16 px")
    except (KeyError, TypeError, ValueError) as exc:
        out.append(f"{where}: tokens incomplete or malformed ({exc!r})")
    return out


SVG_NS = "{http://www.w3.org/2000/svg}"
BANNED = {"image", "script", "foreignObject", "text", "tspan", "style"}


def svg(path, rel):
    """No external refs, no fonts or text, no inline styles; returns (findings, ids)."""
    with open(path, encoding="utf-8", errors="replace") as fh:
        raw = fh.read()
    if re.search(r"<!(DOCTYPE|ENTITY)", raw):
        return [f"{rel}: DOCTYPE/ENTITY declarations are not allowed"], set()
    for pat in (r"@import", r"@font-face", r"url\(\s*['\"]?(https?:|data:|//)"):
        if re.search(pat, raw, re.I):
            return [f"{rel}: external reference ({pat})"], set()
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as exc:
        return [f"{rel}: not well-formed XML ({exc})"], set()
    out, ids = [], set()
    if root.tag != SVG_NS + "svg" or "viewBox" not in root.attrib:
        out.append(f"{rel}: root must be <svg> with a viewBox")
    for el in root.iter():
        tag = el.tag.split("}")[-1]
        if tag in BANNED:
            out.append(f"{rel}: <{tag}> not allowed (text as paths, no images/styles)")
        for k, v in el.attrib.items():
            name = k.split("}")[-1]
            if name == "href" and not v.startswith("#"):
                out.append(f"{rel}: external href {v[:60]!r}")
            if name == "style":
                out.append(f"{rel}: inline style attribute (strict CSP: use attributes)")
            if name == "id":
                if v in ids:
                    out.append(f"{rel}: duplicate id {v!r}")
                ids.add(v)
    return out, ids


def png_spec(path, rel, w, h, alpha):
    """Exact size; alpha=True needs 32-bit RGBA, alpha=False needs no alpha channel."""
    try:
        pw, ph, depth, ctype, _ = png.header(path)
    except (OSError, png.PngError) as exc:
        return [f"{rel}: unreadable PNG ({exc})"]
    out = []
    if (pw, ph) != (w, h):
        out.append(f"{rel}: is {pw}x{ph}, must be {w}x{h}")
    if alpha and (ctype, depth) != (6, 8):
        out.append(f"{rel}: must be a 32-bit RGBA PNG (colour type {ctype}, depth {depth})")
    if not alpha and ctype in (4, 6):
        out.append(f"{rel}: must have no alpha channel (colour type {ctype})")
    return out


def _inside_circle(x, y, size, ratio):
    c = size / 2
    return math.hypot(x + 0.5 - c, y + 0.5 - c) <= ratio * size / 2 + 1


def adaptive(img, rel, layer):
    """Foreground/monochrome inside the 66/108 safe circle; background opaque."""
    out, colours = [], set()
    for y in range(img.height):
        for x in range(img.width):
            r, g, b, a = img.px(x, y)
            if layer == "background":
                if a < 255:
                    return [f"{rel}: background layer must be fully opaque"]
                continue
            if a > 16 and not _inside_circle(x, y, img.width, 66 / 108):
                return [f"{rel}: art outside the 66 dp safe circle at ({x},{y})"]
            if layer == "monochrome" and a > 200:
                colours.add((r // 32, g // 32, b // 32))
    if layer == "monochrome" and len(colours) > 1:
        out.append(f"{rel}: monochrome layer uses more than one colour")
    return out


def play_icon(img, rel):
    """Opaque; everything that differs from the corner colour sits on the 75 %
    keyline square with Play's 30 % corner radius."""
    s, bg = img.width, img.px(0, 0)
    k0, k1 = s * 0.125, s * 0.875
    rad = 0.3 * (k1 - k0)
    for y in range(s):
        for x in range(s):
            p = img.px(x, y)
            if p[3] < 255:
                return [f"{rel}: must be opaque (Play shows transparency as its own UI colour)"]
            if sum(abs(p[i] - bg[i]) for i in range(3)) <= 48:
                continue
            cx = min(max(x + 0.5, k0 + rad), k1 - rad)
            cy = min(max(y + 0.5, k0 + rad), k1 - rad)
            if math.hypot(x + 0.5 - cx, y + 0.5 - cy) > rad + 1:
                return [f"{rel}: key shape outside the Play keyline at ({x},{y})"]
    return []


def legibility(img96, img24, rel):
    """Heuristic for 24 px: the 96 px mark loses <10 % of its ink under a
    3 px morphological opening (features thinner than ~0.75 px at 24 px), and the
    24 px render is not empty."""
    w, h = img96.width, img96.height
    ink = [[img96.px(x, y)[3] > 127 for x in range(w)] for y in range(h)]

    def morph(m, op):
        return [[op(m[j][i] for j in range(max(0, y - 1), min(h, y + 2))
                 for i in range(max(0, x - 1), min(w, x + 2))) for x in range(w)] for y in range(h)]
    opened = morph(morph(ink, all), any)
    total = sum(map(sum, ink))
    lost = sum(1 for y in range(h) for x in range(w) if ink[y][x] and not opened[y][x])
    out = []
    if total == 0:
        return [f"{rel}: mark-96.png is empty"]
    if lost / total > 0.10:
        out.append(f"{rel}: {lost / total:.0%} of the mark is thinner than ~1 px at 24 px")
    cov = sum(img24.px(x, y)[3] > 127 for y in range(img24.height) for x in range(img24.width))
    if cov < 0.08 * img24.width * img24.height:
        out.append(f"{rel}: mark-24.png is nearly empty ({cov} px of ink)")
    return out
