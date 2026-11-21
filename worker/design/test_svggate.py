# SPDX-License-Identifier: MIT
"""Tests for the SVG and file gates of design-check (change add-designer-role):
every unsafe construct the review found, and a few more, fails on its own."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fixtures import DeliveryCase, svg  # noqa: E402


class SvgGate(DeliveryCase):
    def test_svg_local_gradient_passes(self):
        self.put("logo/mark.svg", svg("logo-mark", '<defs><linearGradient id="logo-g">'
                 '<stop offset="0" stop-color="#fff"/></linearGradient></defs>'
                 '<rect width="1" height="1" fill="url(#logo-g)"/>'))
        self.assertEqual(self.failed(), [])

    def test_unsafe_svgs_fail(self):
        bad = {
            "external href": '<use href="https://example.org/a.svg#x"/>',
            "image": '<image href="#x"/>',
            "text": "<text>bazibo</text>",
            "style attribute": '<rect width="1" height="1" style="fill:red"/>',
            "style element": "<style>rect{fill:red}</style>",
            "script": "<script>alert(1)</script>",
            "foreignObject": "<foreignObject><div/></foreignObject>",
            "event attribute": '<rect width="1" height="1" onclick="alert(1)"/>',
            "entity-encoded url": '<rect width="1" height="1" fill="&#117;rl(https://e.org/x)"/>',
            "CSS escape": '<rect width="1" height="1" fill="u\\72 l(https://e.org/x)"/>',
            "relative url": '<rect width="1" height="1" fill="url(other.svg#f)"/>',
            "set href": '<set attributeName="href" to="javascript:alert(1)"/>',
            "animate": '<animate attributeName="fill" to="red"/>',
            "foreign attribute": '<rect xmlns:x="urn:x" x:y="1" width="1" height="1"/>',
        }
        for name, extra in bad.items():
            self.put("logo/mark.svg", svg("logo-mark", extra))
            self.assertEqual(self.failed(), ["svg"], name)
        variants = {
            "onload on root": svg("logo-mark").replace("<svg ", '<svg onload="alert(1)" '),
            "stylesheet PI": '<?xml-stylesheet href="https://e.org/a.css"?>' + svg("logo-mark"),
            "DOCTYPE": '<!DOCTYPE svg [<!ENTITY x "y">]>' + svg("logo-mark"),
            "no namespace": svg("logo-mark").replace(' xmlns="http://www.w3.org/2000/svg"', ""),
        }
        for name, text in variants.items():
            self.put("logo/mark.svg", text)
            self.assertEqual(self.failed(), ["svg"], name)
        self.put("logo/mark.svg", svg("adaptive-foreground"))
        self.assertEqual(self.failed(), ["svg"], "id clash across files")

    def test_symlinks_and_odd_svg_names_fail(self):
        mark = os.path.join(self.out, "logo/mark.svg")
        os.remove(mark)
        os.symlink(os.path.join(self.out, "directions/a/mark.svg"), mark)
        self.assertEqual(self.failed(), ["files"])
        self.tearDown()
        self.setUp()
        for name in ("extra.SVG", "extra.svgz"):
            self.put(name, svg("extra"))
            self.assertEqual(self.failed(), ["files"], name)
            os.remove(os.path.join(self.out, name))


if __name__ == "__main__":
    unittest.main(verbosity=1)
