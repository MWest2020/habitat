# SPDX-License-Identifier: MIT
"""Tests for design-check (change add-designer-role): a valid delivery passes,
and each gate catches the fault it is there for. Standard library only."""
import copy
import io
import json
import math
import os
import shutil
import sys
import tempfile
import unittest
from contextlib import redirect_stdout

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


class DesignCheck(unittest.TestCase):
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

    def test_valid_delivery_passes(self):
        with redirect_stdout(io.StringIO()) as buf:
            self.assertEqual(check.main(["design-check", self.out]), 0, buf.getvalue())

    def test_contrast_ratio(self):
        self.assertAlmostEqual(gates.contrast("#000000", "#ffffff"), 21.0)

    def test_low_contrast_text_fails(self):
        tok = copy.deepcopy(TOKENS)
        tok["color"]["ink-soft"] = "#b0aac8"
        self.put("tokens.json", json.dumps(tok))
        self.assertEqual(self.failed(), ["contrast"])

    def test_weak_accent_and_non_ofl_font_fail(self):
        tok = copy.deepcopy(TOKENS)
        tok["color"]["groups"]["action"]["accent"] = "#f2d27a"
        tok["type"]["families"]["body"] = "Inter"
        self.put("directions/b/tokens.json", json.dumps(tok))
        found = check.run(self.out)["contrast"]
        self.assertTrue(any("action accent" in f for f in found), found)
        self.assertTrue(any("'Inter'" in f for f in found), found)

    def test_svg_external_ref_text_style_and_id_clash_fail(self):
        for extra in ('<image href="https://example.org/a.png"/>', "<text>bazibo</text>",
                      '<rect width="1" height="1" style="fill:red"/>'):
            self.put("logo/mark.svg", svg("logo-mark", extra))
            self.assertEqual(self.failed(), ["svg"], extra)
        self.put("logo/mark.svg", svg("adaptive-foreground"))
        self.assertEqual(self.failed(), ["svg"])

    def test_alpha_on_store_asset_and_wrong_size_fail(self):
        png.write(os.path.join(self.out, "icon/appstore-1024.png"), 1024, 1024, (1, 2, 3, 255), True)
        png.write(os.path.join(self.out, "store/feature-graphic.png"), 1024, 512, (1, 2, 3, 255), False)
        self.assertEqual(self.failed(), ["png-sizes"])

    def test_art_outside_safe_zones_fails(self):
        png.write(os.path.join(self.out, "adaptive/foreground.png"), 432, 432,
                  disc(432, 150, (40, 36, 92, 255)), True)
        self.assertEqual(self.failed(), ["safe-zone"])
        self.setUp()
        png.write(os.path.join(self.out, "icon/play-512.png"), 512, 512,
                  disc(512, 60, (40, 36, 92, 255), (251, 247, 240, 255), cx=70), True)
        self.assertEqual(self.failed(), ["safe-zone"])

    def test_hairline_mark_is_not_legible_at_24px(self):
        hair = lambda x, y: (40, 36, 92, 255) if x % 8 == 0 or y % 8 == 0 else (0, 0, 0, 0)  # noqa: E731
        png.write(os.path.join(self.out, "logo/mark-96.png"), 96, 96, hair, True)
        self.assertEqual(self.failed(), ["legibility-24px"])

    def test_licences_must_name_fonts_and_artwork_licence(self):
        self.put("LICENSES.md", "Nunito: SIL Open Font License.\n")
        found = check.run(self.out)["licences"]
        self.assertEqual(len(found), 2, found)

    def test_directions_need_two_or_three_with_folders(self):
        self.put("rationale.md", "## Direction A\n\n## Recommendation\n")
        self.assertEqual(self.failed(), ["directions"])
        self.put("rationale.md", RATIONALE.replace("Direction B", "Direction C"))
        self.assertIn("directions", self.failed())

    def test_missing_file_fails_layout(self):
        os.remove(os.path.join(self.out, "store/screenshot-frame-en.svg"))
        self.assertEqual(self.failed(), ["layout"])


if __name__ == "__main__":
    unittest.main(verbosity=1)
