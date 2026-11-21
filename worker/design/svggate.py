# SPDX-License-Identifier: MIT
"""SVG hygiene for the designer's delivery (change add-designer-role).

An allowlist, judged on PARSED values (entities decoded), not on raw text:
static drawing elements and presentation attributes only. Rejected: DOCTYPE and
entity declarations, processing instructions (`<?xml-stylesheet?>`), event
attributes (`on*`), animation (`<set>`, `<animate*>`), scripts, foreign
content, images, text and styles, any href that is not `#id`, and any `url()`
that is not `url(#id)`. Files: no symlinks, and an SVG is `*.svg` exactly
(no `.SVG`, no `.svgz`). Standard library only.
"""
import os
import re
import xml.etree.ElementTree as ET

SVG = "http://www.w3.org/2000/svg"
XLINK = "http://www.w3.org/1999/xlink"
XML = "http://www.w3.org/XML/1998/namespace"
ELEMENTS = {
    "svg", "g", "defs", "symbol", "use", "title", "desc", "path", "rect", "circle",
    "ellipse", "line", "polyline", "polygon", "linearGradient", "radialGradient",
    "stop", "clipPath", "mask",
}
ATTRS = {
    "id", "class", "version", "viewBox", "preserveAspectRatio", "width", "height",
    "x", "y", "x1", "y1", "x2", "y2", "cx", "cy", "r", "rx", "ry", "fx", "fy", "fr",
    "d", "points", "pathLength", "transform", "opacity", "fill", "fill-opacity",
    "fill-rule", "stroke", "stroke-width", "stroke-linecap", "stroke-linejoin",
    "stroke-miterlimit", "stroke-dasharray", "stroke-dashoffset", "stroke-opacity",
    "clip-path", "clip-rule", "clipPathUnits", "mask", "maskUnits",
    "maskContentUnits", "gradientUnits", "gradientTransform", "spreadMethod",
    "offset", "stop-color", "stop-opacity", "href", "role", "aria-label",
    "aria-labelledby", "aria-describedby", "aria-hidden", "focusable",
    "shape-rendering", "vector-effect", "paint-order",
}
LOCAL_URL = re.compile(r"""\s*(['"]?)#[A-Za-z_][\w.:-]*\1\s*""")
LOCAL_HREF = re.compile(r"#[A-Za-z_][\w.:-]*")


def _attr_findings(rel, tag, key, value):
    ns, name = (key[1:].split("}", 1) if key.startswith("{") else ("", key))
    if ns not in ("", XLINK, XML) or (ns == XLINK and name != "href") \
            or (ns == XML and name not in ("space", "lang")):
        return [f"{rel}: <{tag}> attribute {key!r} not allowed"]
    if ns == "" and name not in ATTRS:
        return [f"{rel}: <{tag}> attribute {name!r} not allowed"]
    out = []
    if "\\" in value:
        out.append(f"{rel}: <{tag}> {name} contains a backslash (CSS escapes not allowed)")
    if name == "href" and not LOCAL_HREF.fullmatch(value):
        out.append(f"{rel}: <{tag}> href {value[:60]!r} is not a local #id")
    for inner in re.findall(r"url\(([^)]*)\)", value, re.I):
        if not LOCAL_URL.fullmatch(inner):
            out.append(f"{rel}: <{tag}> {name}=url({inner[:60]}) is not url(#id)")
    if re.search(r"url\(", value, re.I) and not re.search(r"url\([^)]*\)", value, re.I):
        out.append(f"{rel}: <{tag}> {name} has an unclosed url(")
    if re.search(r"javascript:|data:|@import|expression\(", value, re.I):
        out.append(f"{rel}: <{tag}> {name} carries a script or data URL")
    return out


def check(path, rel):
    """(findings, ids) for one SVG file."""
    with open(path, encoding="utf-8", errors="replace") as fh:
        raw = fh.read()
    if re.search(r"<!(DOCTYPE|ENTITY)", raw, re.I):
        return [f"{rel}: DOCTYPE/ENTITY declarations are not allowed"], set()
    out, ids, root = [], set(), None
    parser = ET.XMLPullParser(events=("start", "pi"))
    try:
        parser.feed(raw)
        parser.close()
        for event, el in parser.read_events():
            if event == "pi":
                out.append(f"{rel}: processing instruction {el.text[:40]!r} not allowed")
                continue
            root = el if root is None else root
            ns, tag = (el.tag[1:].split("}", 1) if el.tag.startswith("{") else ("", el.tag))
            if ns != SVG or tag not in ELEMENTS:
                out.append(f"{rel}: element <{tag}> not allowed (static shapes only)")
            for k, v in el.attrib.items():
                out += _attr_findings(rel, tag, k, v)
                if k == "id":
                    if v in ids:
                        out.append(f"{rel}: duplicate id {v!r}")
                    ids.add(v)
    except ET.ParseError as exc:
        return [f"{rel}: not well-formed XML ({exc})"], set()
    if root is None or root.tag != f"{{{SVG}}}svg" or "viewBox" not in root.attrib:
        out.append(f"{rel}: root must be <svg> in the SVG namespace with a viewBox")
    return out, ids


def files(out_dir):
    """No symlinks anywhere under the delivery; SVGs only as lower-case *.svg."""
    found = []
    for root, dirs, names in os.walk(out_dir):
        for n in dirs + names:
            full = os.path.join(root, n)
            rel = os.path.relpath(full, out_dir)
            if os.path.islink(full):
                found.append(f"{rel}: symlinks are not allowed in the delivery")
            low = n.lower()
            if (low.endswith(".svg") and not n.endswith(".svg")) or low.endswith(".svgz"):
                found.append(f"{rel}: SVGs must be plain files named *.svg")
    return found
