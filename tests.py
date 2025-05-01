import math
import unittest
from typing import Any
from unittest import mock

from ida_themr import (
    RGB,
    RGBA,
    Instance,
    new_css_color,
    parse,
    strip_jsonc_comments,
    three_way_adjustment,
    u4parse,
    u4vparse,
    u8parse,
    u8vparse,
)


class TestSuiteRegistry:
    """
    Decorate TestCase subclasses with @test_suite to register them.
    Use test_suite.run() to execute all registered tests.
    """

    test_classes: list[type] = []

    def __call__(self, cls: type) -> type:
        # Register the TestCase subclass
        self.test_classes.append(cls)
        return cls

    @classmethod
    def run(cls, runner_options: dict[str, Any] = None) -> unittest.result.TestResult:
        """
        Load and run all registered TestCase classes. Returns TestResult.
        """
        runner_options = runner_options or {}
        suite = unittest.TestSuite()
        loader = unittest.defaultTestLoader
        for tc in cls.test_classes:
            suite.addTests(loader.loadTestsFromTestCase(tc))
        runner = unittest.TextTestRunner(**runner_options)
        return runner.run(suite)


# Create decorator instance
test_suite = TestSuiteRegistry()


@test_suite
class TestColorConversion(unittest.TestCase):
    def test_u4parse(self):
        self.assertEqual(u4parse(ord("0")), 0)
        self.assertEqual(u4parse(ord("A")), 10)

    def test_u8parse(self):
        self.assertEqual(u8parse(b"FF"), 255)

    def test_u8vparse(self):
        self.assertEqual(u8vparse("#112233"), (17, 34, 51, 255))

    def test_u4vparse(self):
        self.assertEqual(u4vparse("#FAB7"), (255, 170, 187, 119))

    def test_new_css_color(self):
        c = new_css_color("#123")
        self.assertEqual(
            repr(c), "RGBA(rgb=RGB(r=17/255, g=34/255, b=51/255), alpha=1.0)"
        )

    def test_to_css_rgba(self):
        c = RGBA(RGB(1, 0, 0), 0.5)
        self.assertEqual(c.to_css_rgba(), "#FF00007F")

    def test_distance(self):
        d = RGBA(RGB(0, 0, 0), 1.0).distance(RGBA(RGB(1, 1, 1), 1.0))
        self.assertAlmostEqual(d, math.sqrt(3))


@test_suite
class TestThreeWayAdjustment(unittest.TestCase):
    def test_placeholder_adjustment(self):
        with mock.patch.object(RGB, "Hsl", return_value=(0.1, 0.2, 0.3)):
            with mock.patch.object(RGB, "from_hsl", return_value=RGB(0.4, 0.5, 0.6)):
                out = three_way_adjustment(RGB(0, 0, 0), RGB(0, 0, 0), RGB(0, 0, 0))
                self.assertEqual(out, RGB(0.4, 0.5, 0.6))


@test_suite
class TestInstance(unittest.TestCase):
    def test_add_color_and_inversion(self):
        inst = Instance(data=None)
        inst.add_color("foo", "#336699")
        self.assertIn("foo", inst.colors)
        key_list = inst.inverted_colors.get(inst.colors["foo"].rgb)
        self.assertIsInstance(key_list, list)
        self.assertIn("foo", key_list)

    def test_add_color_invalid(self):
        inst = Instance(data=None)
        inst.add_color("bad", "zzz")
        self.assertNotIn("bad", inst.colors)

    def test_remap_color_rgb_direct_match(self):
        p = Instance(data=None)
        q = Instance(data=None)
        p.add_color("k", "#112233")
        q.add_color("k", "#112233")
        r = p.remap_color_rgb(p.colors["k"].rgb, q, False)
        self.assertEqual(r, p.colors["k"].rgb)


@test_suite
class TestJSONCParsing(unittest.TestCase):
    def test_header_comment(self):
        jsonc_string = '// header comment\\n{"key": "value"}'
        expected = '\\n{"key": "value"}'
        self.assertEqual(strip_jsonc_comments(jsonc_string), expected)

    def test_no_comments(self):
        json_string = '{"name": "test", "value": 123}'
        self.assertEqual(strip_jsonc_comments(json_string), json_string)

    def test_single_line_comment_end_of_line(self):
        jsonc_string = '{"key": "value"} // comment here'
        expected = '{"key": "value"} '
        self.assertEqual(strip_jsonc_comments(jsonc_string), expected)

    def test_single_line_comment_on_its_own_line(self):
        jsonc_string = '// This is a comment\\n{"key": "value"}'
        expected = '\\n{"key": "value"}'
        self.assertEqual(strip_jsonc_comments(jsonc_string), expected)

    def test_multi_line_comment_inline(self):
        jsonc_string = '{"key": /* comment */ "value"}'
        expected = '{"key":  "value"}'  # Note: space preserved where comment was
        self.assertEqual(strip_jsonc_comments(jsonc_string), expected)

    def test_multi_line_comment_spanning_lines(self):
        jsonc_string = '/*\\nThis is a block comment\\n*/{"key": "value"}'
        expected = '{"key": "value"}'
        self.assertEqual(strip_jsonc_comments(jsonc_string), expected)

    def test_multi_line_comment_containing_stars_and_slashes(self):
        jsonc_string = '{"key": /* comment with * and / inside */ "value"}'
        expected = '{"key":  "value"}'
        self.assertEqual(strip_jsonc_comments(jsonc_string), expected)

    def test_mixed_comments(self):
        jsonc_string = (
            '// line 1\\n{"key1": 1, /* comment */ "key2": 2 // comment 2\\n}'
        )
        expected = '\\n{"key1": 1,  "key2": 2 \\n}'
        self.assertEqual(strip_jsonc_comments(jsonc_string), expected)

    def test_comments_inside_string(self):
        jsonc_string = '{"key": "value with // comment and /* block */ inside"}'
        expected = '{"key": "value with // comment and /* block */ inside"}'
        self.assertEqual(strip_jsonc_comments(jsonc_string), expected)

    def test_string_with_escaped_quote_near_comment(self):
        jsonc_string = '{"key": "value with \\" quote" // comment}'
        expected = '{"key": "value with \\" quote" }'
        self.assertEqual(strip_jsonc_comments(jsonc_string), expected)

    def test_string_with_escaped_backslash_near_comment(self):
        jsonc_string = '{"key": "value with \\\\ backslash" // comment}'
        expected = '{"key": "value with \\\\ backslash" }'
        self.assertEqual(strip_jsonc_comments(jsonc_string), expected)

    def test_empty_string(self):
        self.assertEqual(strip_jsonc_comments(""), "")

    def test_only_comments(self):
        jsonc_string = "// comment 1\\n/* comment 2 */\\n// comment 3"
        expected = "\\n\\n"  # Newlines are preserved
        self.assertEqual(strip_jsonc_comments(jsonc_string), expected)

    def test_comment_at_start_and_end(self):
        jsonc_string = '/* start */{"key": "value"}// end'
        expected = '{"key": "value"}'
        self.assertEqual(strip_jsonc_comments(jsonc_string), expected)

    def test_comment_adjacent_to_punctuation(self):
        jsonc_string = '{"key": 1 /* comment */, "key2": 2}'
        expected = '{"key": 1 , "key2": 2}'
        self.assertEqual(strip_jsonc_comments(jsonc_string), expected)

    def test_unclosed_multi_line_comment(self):
        # The function doesn't validate, just strips.
        # An unclosed comment means everything after /* is removed.
        jsonc_string = '{"key": /* unclosed comment'
        expected = '{"key": '
        self.assertEqual(strip_jsonc_comments(jsonc_string), expected)

    def test_unclosed_string_near_comment_like_chars(self):
        # The function doesn't validate, just strips.
        # An unclosed string means everything after the opening quote is kept.
        jsonc_string = '{"key": "unclosed string // /*'
        expected = '{"key": "unclosed string // /*'
        self.assertEqual(strip_jsonc_comments(jsonc_string), expected)

    def test_slashes_in_string_not_comment(self):
        jsonc_string = '{"url": "http://example.com", "path": "/path/to/file"}'
        expected = '{"url": "http://example.com", "path": "/path/to/file"}'
        self.assertEqual(strip_jsonc_comments(jsonc_string), expected)

    def test_string_with_escaped_quote_followed_by_comment(self):
        # Input literal represents the string: {"key": "value\" // comment"}
        jsonc_string = '{"key": "value\\" // comment"}'
        # Expected literal represents the string: {"key": "value\" // comment"}
        # The comment // comment should NOT be stripped as it's inside a string.
        expected = '{"key": "value\\" // comment"}'
        self.assertEqual(strip_jsonc_comments(jsonc_string), expected)

    def test_strip_jsonc(self):
        raw = b'{/*c*/"a":1//c\\n}'
        self.assertEqual(strip_jsonc_comments(raw.decode("utf-8")), '{"a":1\\n}')
        self.assertEqual(strip_jsonc_comments(raw.decode("utf-8"), False), '{"a":1}')

    def test_parse_and_read_file(self):
        sample = b"""
        {
          "name":"demo",
          "type":"test",
          "colors":{"x":"#000000"},
          "tokenColors":[
            {"name":"t","scope":"s","settings":{"foreground":"#FFFFFF"}}
          ]
        }
        """
        inst = parse(sample)
        self.assertIn("x", inst.colors)
        self.assertIn("s", inst.colors)


@test_suite
class TestHslConversion(unittest.TestCase):
    def test_red_hsl(self):
        h, s, l = RGB(1, 0, 0).Hsl()
        self.assertAlmostEqual(h, 0.0)
        self.assertAlmostEqual(s, 1.0)
        self.assertAlmostEqual(l, 0.5)

    def test_roundtrip(self):
        orig = RGB(0.3, 0.6, 0.9)
        h, s, l = orig.Hsl()
        recon = RGB.from_hsl(h, s, l)
        self.assertAlmostEqual(orig.r, recon.r, places=6)
        self.assertAlmostEqual(orig.g, recon.g, places=6)
        self.assertAlmostEqual(orig.b, recon.b, places=6)
