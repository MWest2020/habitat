# SPDX-License-Identifier: MIT
"""Fixtures for the design-check tests (change add-designer-role): a valid
delivery built with the standard library, and a TestCase that copies it."""
import json
import math
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import check  # noqa: E402
import gates  # noqa: E402
import png  # noqa: E402

GROUP = {"accent": "#2a8f88", "tint": "#e6f3f1", "text": "#28245c"}
TOKENS = {
    "color": {"base": "#fbf7f0", "ink": "#28245c", "ink-soft": "#5a5585",
              "brand": "#4f43c4", "on-brand": "#ffffff",
              "groups": {g: dict(GROUP) for g in gates.GROUPS}},
    "type": {"families": {"heading": "Fredoka", "body": "Nunito"},
             "scale_px": [16, 20, 28, 40], "weights": [400, 700]},
}
RATIONALE = "# Bazibo\n\n## Direction A Paper\n\nx\n\n## Direction B Polder\n\ny\n\n## Recommendation\n\nA\n"
LICENSES = "Nunito, Fredoka: SIL Open Font License 1.1 (OFL-1.1).\nArtwork: CC0-1.0.\n"


def svg(ident, extra=""):
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10">'
            f'<path id="{ident}" d="M0 0h10v10z" fill="#28245c"/>{extra}</svg>')


def disc(size, r, fg, bg=(0, 0, 0, 0), cx=None):
    cx = size / 2 if cx is None else cx
    return lambda x, y: fg if math.hypot(x + .5 - cx, y + .5 - size / 2) <= r else bg


def build(out):
    def w(rel, text):
        os.makedirs(os.path.dirname(os.path.join(out, rel)), exist_ok=True)
        with open(os.path.join(out, rel), "w") as fh:
            fh.write(text)
    for sub in ("logo", "icon", "adaptive", "store"):
        os.makedirs(os.path.join(out, sub), exist_ok=True)
    w("rationale.md", RATIONALE)
    w("LICENSES.md", LICENSES)
    w("tokens.json", json.dumps(TOKENS))
    w("tokens.css", ":root { --base: #fbf7f0; }\n")
    for d in ("a", "b"):
        w(f"directions/{d}/mark.svg", svg(f"dir-{d}"))
        w(f"directions/{d}/tokens.json", json.dumps(TOKENS))
        png.write(os.path.join(out, f"directions/{d}/preview.png"), 4, 4, (255, 255, 255, 255))
    for rel in check.REQUIRED:
        if rel.endswith(".svg") and not os.path.exists(os.path.join(out, rel)):
            w(rel, svg(rel.replace("/", "-").replace(".svg", "")))
    ink = (40, 36, 92, 255)
    pngs = {
        "logo/mark-24.png": (24, 24, disc(24, 9, ink), True),
        "logo/mark-96.png": (96, 96, disc(96, 36, ink), True),
        "icon/play-512.png": (512, 512, disc(512, 150, ink, (251, 247, 240, 255)), True),
        "icon/appstore-1024.png": (1024, 1024, (251, 247, 240, 255), False),
        "adaptive/foreground.png": (432, 432, disc(432, 100, ink), True),
        "adaptive/background.png": (432, 432, (251, 247, 240, 255), True),
        "adaptive/monochrome.png": (432, 432, disc(432, 100, (0, 0, 0, 255)), True),
        "store/feature-graphic.png": (1024, 500, (251, 247, 240, 255), False),
        "store/screenshot-frame-nl.png": (1080, 1920, (251, 247, 240, 255), False),
        "store/screenshot-frame-en.png": (1080, 1920, (251, 247, 240, 255), False),
    }
    for rel in check.REQUIRED:
        if rel.endswith(".png") and rel not in pngs:
            pngs[rel] = (8, 8, (40, 36, 92, 255), True)
    for rel, (wd, ht, px, alpha) in pngs.items():
        png.write(os.path.join(out, rel), wd, ht, px, alpha)


class DeliveryCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = tempfile.mkdtemp()
        build(cls.base)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.base)

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.out = os.path.join(self.tmp, "brand")
        shutil.copytree(self.base, self.out)

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def failed(self):
        return sorted(g for g, f in check.run(self.out).items() if f)

    def put(self, rel, text):
        with open(os.path.join(self.out, rel), "w") as fh:
            fh.write(text)

