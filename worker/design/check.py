#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""design-check <dir>: the designer's delivery gate (change add-designer-role).

Checks a brand delivery (default layout: design/brand/ in the target repo, see
docs/reference/roles.md#designer) and prints one line per gate plus a JSON
summary. Exit 0 only when every gate passes. The worker entrypoint runs it after
the designer's run, from the image, so a PASS the agent claims without passing
these gates fails the run.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gates  # noqa: E402
import png  # noqa: E402
import svggate  # noqa: E402

REQUIRED = [
    "rationale.md", "LICENSES.md", "tokens.json", "tokens.css",
    "logo/full-light.svg", "logo/full-dark.svg", "logo/mark.svg", "logo/wordmark.svg",
    "logo/full-light.png", "logo/full-dark.png", "logo/mark.png", "logo/wordmark.png",
    "logo/mark-24.png", "logo/mark-96.png",
    "icon/play-512.png", "icon/appstore-1024.png",
    "adaptive/foreground.svg", "adaptive/background.svg", "adaptive/monochrome.svg",
    "adaptive/foreground.png", "adaptive/background.png", "adaptive/monochrome.png",
    "store/feature-graphic.svg", "store/feature-graphic.png",
    "store/screenshot-frame-nl.svg", "store/screenshot-frame-nl.png",
    "store/screenshot-frame-en.svg", "store/screenshot-frame-en.png",
]
# path, width, height, alpha
SIZES = [
    ("logo/mark-24.png", 24, 24, True), ("logo/mark-96.png", 96, 96, True),
    ("icon/play-512.png", 512, 512, True), ("icon/appstore-1024.png", 1024, 1024, False),
    ("adaptive/foreground.png", 432, 432, True), ("adaptive/background.png", 432, 432, True),
    ("adaptive/monochrome.png", 432, 432, True),
    ("store/feature-graphic.png", 1024, 500, False),
    ("store/screenshot-frame-nl.png", 1080, 1920, False),
    ("store/screenshot-frame-en.png", 1080, 1920, False),
]
DIRECTION_FILES = ("mark.svg", "tokens.json", "preview.png")


def _text(path):
    if not os.path.isfile(path):
        return ""
    with open(path, encoding="utf-8", errors="replace") as fh:
        return fh.read()


def _load_tokens(path, rel):
    try:
        return json.loads(_text(path)), []
    except (OSError, ValueError) as exc:
        return None, [f"{rel}: unreadable ({exc})"]


def run(out):
    res = {}
    p = lambda rel: os.path.join(out, rel)  # noqa: E731
    res["layout"] = [f"missing: {r}" for r in REQUIRED if not os.path.isfile(p(r))]

    # Directions: 2-3 in rationale.md, each with its own folder.
    found = []
    rat = _text(p("rationale.md"))
    heads = re.findall(r"^## (?:Direction|Richting) ([A-Za-z0-9-]+)", rat, re.M)
    if not 2 <= len(heads) <= 3:
        found.append(f"rationale.md: {len(heads)} '## Direction <id>' sections, need 2 or 3")
    if rat and not re.search(r"^## (Recommendation|Aanbeveling)", rat, re.M):
        found.append("rationale.md: no '## Recommendation' section")
    for d in heads:
        for f in DIRECTION_FILES:
            if not os.path.isfile(p(f"directions/{d.lower()}/{f}")):
                found.append(f"direction {d}: missing directions/{d.lower()}/{f}")
    res["directions"] = found

    # Palette: WCAG AA on the delivered tokens and on every direction's tokens.
    found = []
    tok_files = ["tokens.json"] + [f"directions/{d.lower()}/tokens.json" for d in heads]
    families = set()
    for rel in tok_files:
        if os.path.isfile(p(rel)):
            tok, errs = _load_tokens(p(rel), rel)
            found += errs or gates.tokens(tok, rel)
            if tok and isinstance(tok.get("type", {}).get("families"), dict):
                families |= set(tok["type"]["families"].values())
    res["contrast"] = found

    # SVG hygiene; ids unique across logo/ and adaptive/ (they may be inlined together).
    found, seen = [], {}
    for root, _dirs, files in os.walk(out):
        for f in sorted(files):
            if not f.endswith(".svg") or os.path.islink(os.path.join(root, f)):
                continue
            rel = os.path.relpath(os.path.join(root, f), out)
            errs, ids = svggate.check(os.path.join(root, f), rel)
            found += errs
            if rel.startswith(("logo/", "adaptive/")):
                for i in ids:
                    if i in seen and seen[i] != rel:
                        found.append(f"{rel}: id {i!r} also used in {seen[i]}")
                    seen[i] = rel
    res["svg"] = found
    res["files"] = svggate.files(out)

    found = []
    for rel, w, h, alpha in SIZES:
        if os.path.isfile(p(rel)):
            found += gates.png_spec(p(rel), rel, w, h, alpha)
    res["png-sizes"] = found

    found = []
    try:
        for layer in ("foreground", "background", "monochrome"):
            rel = f"adaptive/{layer}.png"
            if os.path.isfile(p(rel)):
                found += gates.adaptive(png.read(p(rel)), rel, layer)
        if os.path.isfile(p("icon/play-512.png")):
            found += gates.play_icon(png.read(p("icon/play-512.png")), "icon/play-512.png")
    except png.PngError as exc:
        found.append(str(exc))
    res["safe-zone"] = found

    found = []
    if os.path.isfile(p("logo/mark-96.png")) and os.path.isfile(p("logo/mark-24.png")):
        try:
            found = gates.legibility(png.read(p("logo/mark-96.png")),
                                     png.read(p("logo/mark-24.png")), "logo/mark")
        except png.PngError as exc:
            found = [str(exc)]
    res["legibility-24px"] = found

    found = []
    lic = _text(p("LICENSES.md"))
    for fam in sorted(families):
        if fam not in lic:
            found.append(f"LICENSES.md: font {fam!r} is used but not listed")
    if families and not re.search(r"OFL-1\.1|Open Font License", lic):
        found.append("LICENSES.md: fonts are used but the SIL OFL 1.1 is not named")
    if lic and not re.search(r"CC0-1\.0|\bMIT\b", lic):
        found.append("LICENSES.md: no licence (CC0-1.0 or MIT) for the artwork itself")
    res["licences"] = found
    return res


def main(argv):
    out = argv[1] if len(argv) > 1 else "design/brand"
    if not os.path.isdir(out):
        print(f"design-check: FAIL, no delivery directory {out!r}")
        return 1
    res = run(out)
    for gate, found in res.items():
        print(f"design-check: {'ok  ' if not found else 'FAIL'} {gate}")
        for f in found[:20]:
            print(f"    - {f}")
    failed = sorted(g for g, f in res.items() if f)
    print(json.dumps({"dir": out, "passed": not failed, "failed": failed}))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
