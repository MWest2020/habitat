# SPDX-License-Identifier: MIT
"""Tests for design-check (change add-designer-role): a valid delivery passes,
and each gate catches the fault it is there for. Standard library only."""
import copy
import io
import json
import os
import sys
import unittest
from contextlib import redirect_stdout

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import check  # noqa: E402
import gates  # noqa: E402
import png  # noqa: E402
from fixtures import RATIONALE, TOKENS, DeliveryCase, disc  # noqa: E402


class DesignCheck(DeliveryCase):
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

    def test_alpha_on_store_asset_and_wrong_size_fail(self):
        png.write(os.path.join(self.out, "icon/appstore-1024.png"), 1024, 1024, (1, 2, 3, 255), True)
        png.write(os.path.join(self.out, "store/feature-graphic.png"), 1024, 512, (1, 2, 3, 255), False)
        self.assertEqual(self.failed(), ["png-sizes"])

    def test_art_outside_safe_zones_fails(self):
        png.write(os.path.join(self.out, "adaptive/foreground.png"), 432, 432,
                  disc(432, 150, (40, 36, 92, 255)), True)
        self.assertEqual(self.failed(), ["safe-zone"])
        self.tearDown()
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
