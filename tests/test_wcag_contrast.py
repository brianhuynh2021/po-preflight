"""
WCAG 2.1 AA Contrast Automation Test Suite.
Verifies color contrast ratios for light and dark theme tokens across UI elements.
WCAG 2.1 AA Requirements:
- Normal text: >= 4.5:1
- Large text / UI components: >= 3.0:1
"""

import unittest
import math


def hex_to_rgb(hex_color: str) -> tuple[float, float, float]:
    hex_color = hex_color.strip().lstrip("#")
    if len(hex_color) == 3:
        hex_color = "".join(c * 2 for c in hex_color)
    r = int(hex_color[0:2], 16) / 255.0
    g = int(hex_color[2:4], 16) / 255.0
    b = int(hex_color[4:6], 16) / 255.0
    return r, g, b


def relative_luminance(r: float, g: float, b: float) -> float:
    def adjust(c: float) -> float:
        return c / 12.92 if c <= 0.04045 else math.pow((c + 0.055) / 1.055, 2.4)

    return 0.2126 * adjust(r) + 0.7152 * adjust(g) + 0.0722 * adjust(b)


def contrast_ratio(hex1: str, hex2: str) -> float:
    l1 = relative_luminance(*hex_to_rgb(hex1))
    l2 = relative_luminance(*hex_to_rgb(hex2))
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


class TestWCAGContrastCompliance(unittest.TestCase):
    def test_light_theme_text_contrast(self):
        # Light theme background: paper (#ffffff) and canvas (#f4f5f1)
        paper = "#ffffff"
        canvas = "#f4f5f1"
        ink = "#14231f"
        green = "#19704c"
        red = "#a5453c"
        blue = "#386b8e"

        # Primary ink text on white paper >= 7.0:1 (AAA standard)
        cr_ink_paper = contrast_ratio(ink, paper)
        self.assertGreaterEqual(cr_ink_paper, 7.0, f"Ink on paper ratio {cr_ink_paper:.2f} < 7.0")

        # Primary ink text on canvas >= 4.5:1 (AA standard)
        cr_ink_canvas = contrast_ratio(ink, canvas)
        self.assertGreaterEqual(cr_ink_canvas, 4.5, f"Ink on canvas ratio {cr_ink_canvas:.2f} < 4.5")

        # Semantic status text on white paper
        self.assertGreaterEqual(contrast_ratio(green, paper), 4.5, "Green status text failed AA")
        self.assertGreaterEqual(contrast_ratio(red, paper), 4.5, "Red status text failed AA")
        self.assertGreaterEqual(contrast_ratio(blue, paper), 4.5, "Blue status text failed AA")

    def test_dark_theme_text_contrast(self):
        # Dark theme background: paper (#1a1f1d) and canvas (#131715)
        paper = "#1a1f1d"
        canvas = "#131715"
        ink = "#e2e8e5"
        green = "#4ade80"
        amber = "#fbbf24"
        red = "#f87171"

        # Primary ink text on dark paper >= 7.0:1
        cr_ink_paper = contrast_ratio(ink, paper)
        self.assertGreaterEqual(cr_ink_paper, 7.0, f"Dark ink on paper ratio {cr_ink_paper:.2f} < 7.0")

        # Primary ink text on dark canvas >= 7.0:1
        cr_ink_canvas = contrast_ratio(ink, canvas)
        self.assertGreaterEqual(cr_ink_canvas, 7.0, f"Dark ink on canvas ratio {cr_ink_canvas:.2f} < 7.0")

        # Semantic status text on dark paper >= 4.5:1
        self.assertGreaterEqual(contrast_ratio(green, paper), 4.5, "Dark green status text failed AA")
        self.assertGreaterEqual(contrast_ratio(amber, paper), 4.5, "Dark amber status text failed AA")
        self.assertGreaterEqual(contrast_ratio(red, paper), 4.5, "Dark red status text failed AA")


if __name__ == "__main__":
    unittest.main()
