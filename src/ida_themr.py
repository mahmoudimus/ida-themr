#!/usr/bin/env python3
"""
Color conversion & theme remapping for VSCode → IDA Pro.

This module provides:
- RGB and RGBA color types
- Parsing from CSS hex strings (#RGB[A], #RRGGBB[AA])
- CSS RGB(A) string generation
- Three-way color remapping for themes
- Instance class to remap CSS theme files

Includes doctests and a top-level unittest suite. Run `python idathemr.py [test|convert]`.
"""

import argparse
import colorsys
import doctest
import enum
import json
import logging
import math
import os
import pathlib
import re
import sys
import unittest
from dataclasses import dataclass, field
from typing import Any, Dict, List, NamedTuple, Tuple, Union
from unittest import mock

CSS_HEX_REGEX = re.compile(r"#[0-9A-Fa-f]{3,8};")


# -- Data types --------------------------------------------------------------
class RGB(NamedTuple):
    r: float
    g: float
    b: float

    def __repr__(self) -> str:
        r8, g8, b8 = int(self.r * 255), int(self.g * 255), int(self.b * 255)
        return f"RGB(r={r8}/255, g={g8}/255, b={b8}/255)"

    def Hsl(self) -> Tuple[float, float, float]:
        """Convert RGB to HSL: returns (h, s, l) in [0,1]."""
        h, l, s = colorsys.rgb_to_hls(self.r, self.g, self.b)
        return h, s, l

    @classmethod
    def from_hsl(cls, h: float, s: float, l: float) -> "RGB":
        """Convert HSL (h,s,l) to RGB."""
        r, g, b = colorsys.hls_to_rgb(h, l, s)
        return cls(r, g, b)


@dataclass
class RGBA:
    """RGBA color, wraps an RGB plus alpha in [0.0, 1.0]."""

    rgb: RGB
    alpha: float

    def __repr__(self) -> str:
        rgb_repr = repr(self.rgb)
        if self.alpha == 1.0:
            alpha_repr = "1.0"
        else:
            a8 = int(self.alpha * 255)
            alpha_repr = f"{a8}/255"
        return f"RGBA(rgb={rgb_repr}, alpha={alpha_repr})"

    def to_css_rgb(self) -> str:
        """
        Return the CSS-style #RRGGBB string.

        >>> RGBA(RGB(1, 0.5, 0), 1.0).to_css_rgb()
        '#FF7F00'
        """
        return rgb_to_hex(self.rgb)

    def to_css_rgba(self) -> str:
        """
        Return #RRGGBB if alpha ≈ 1.0, else #RRGGBBAA with alpha byte.

        >>> RGBA(RGB(1,1,1), 1.0).to_css_rgba()
        '#FFFFFF'
        >>> RGBA(RGB(1,0,0), 0.5).to_css_rgba()
        '#FF00007F'
        """
        hex_rgb = rgb_to_hex(self.rgb)
        if self.alpha >= 254 / 255:
            return hex_rgb
        alpha_byte = int(self.alpha * 255) & 0xFF
        return f"{hex_rgb}{alpha_byte:02X}"

    def distance(self, other: "RGBA") -> float:
        """
        Euclidean distance in RGB space. Alpha is ignored.

        >>> RGBA(RGB(0,0,0),1.0).distance(RGBA(RGB(1,1,1),1.0))
        1.7320508075688772
        """
        dr = self.rgb.r - other.rgb.r
        dg = self.rgb.g - other.rgb.g
        db = self.rgb.b - other.rgb.b
        return math.sqrt(dr * dr + dg * dg + db * db)


# -- Parsing utilities -------------------------------------------------------
def u4parse(byte_val: int) -> int:
    """
    Parse a single hex digit (0-9, A-F, a-f) to its integer value.

    >>> u4parse(ord('0'))
    0
    >>> u4parse(ord('9'))
    9
    >>> u4parse(ord('A'))
    10
    >>> u4parse(ord('f'))
    15
    """
    if 0x30 <= byte_val <= 0x39:
        return byte_val - 0x30
    if 0x41 <= byte_val <= 0x46:
        return byte_val - 0x41 + 10
    if 0x61 <= byte_val <= 0x66:
        return byte_val - 0x61 + 10
    raise ValueError(f"Invalid hex digit: {chr(byte_val)!r}")


def u8parse(pair: bytes) -> int:
    """
    Parse two hex digits (big-endian) to a byte value 0–255.

    >>> u8parse(b'FF')
    255
    >>> u8parse(b'0A')
    10
    """
    return (u4parse(pair[0]) << 4) + u4parse(pair[1])


def u8vparse(hex_str: str) -> Tuple[int, int, int, int]:
    """
    Parse #RRGGBB or #RRGGBBAA to (r,g,b,a) each 0–255.

    >>> u8vparse('#112233')
    (17, 34, 51, 255)
    >>> u8vparse('#11223344')
    (17, 34, 51, 68)
    """
    r = u8parse(hex_str[1:3].encode())
    g = u8parse(hex_str[3:5].encode())
    b = u8parse(hex_str[5:7].encode())
    a = u8parse(hex_str[7:9].encode()) if len(hex_str) == 9 else 0xFF
    return r, g, b, a


def u4vparse(hex_str: str) -> Tuple[int, int, int, int]:
    """
    Parse #RGB or #RGBA to (r,g,b,a) with each nibble expanded (0xX → 0xXX).

    >>> u4vparse('#FAB')
    (255, 170, 187, 255)
    >>> u4vparse('#FAB7')
    (255, 170, 187, 119)
    """
    r = u4parse(ord(hex_str[1])) * 0x11
    g = u4parse(ord(hex_str[2])) * 0x11
    b = u4parse(ord(hex_str[3])) * 0x11
    a = u4parse(ord(hex_str[4])) * 0x11 if len(hex_str) == 5 else 0xFF
    return r, g, b, a


def new_css_color(hex_str: str) -> RGBA:
    """
    Construct an RGBA from any valid CSS hex string.

    Supports #RGB, #RGBA, #RRGGBB, #RRGGBBAA.

    >>> new_css_color('#123')
    RGBA(rgb=RGB(r=17/255, g=34/255, b=51/255), alpha=1.0)
    >>> new_css_color('#11223344')
    RGBA(rgb=RGB(r=17/255, g=34/255, b=51/255), alpha=68/255)
    """
    hex_str = hex_str.strip()
    if not re.fullmatch(
        r"#(?:[0-9A-Fa-f]{3,4}|[0-9A-Fa-f]{6}(?:[0-9A-Fa-f]{2})?)", hex_str
    ):
        raise ValueError(f"invalid hex color: {hex_str!r}")
    length = len(hex_str)
    if length in (4, 5):
        r8, g8, b8, a8 = u4vparse(hex_str)
    else:
        r8, g8, b8, a8 = u8vparse(hex_str)
    return RGBA(rgb=RGB(r8 / 255, g8 / 255, b8 / 255), alpha=a8 / 255)


# -- Helpers ---------------------------------------------------------------
def rgb_to_hex(rgb: RGB) -> str:
    """
    Convert an RGB to a #RRGGBB string.

    >>> rgb_to_hex(RGB(1, 0.5, 0))
    '#FF7F00'
    """
    r = int(rgb.r * 255) & 0xFF
    g = int(rgb.g * 255) & 0xFF
    b = int(rgb.b * 255) & 0xFF
    return f"#{r:02X}{g:02X}{b:02X}"


def pretty_color(rgb: RGB, text: str) -> str:
    """
    Render `text` in a foreground color matching `rgb` via ANSI escape.

    # NB: will actually print RED, in the color RED with the ANSI escape code
    # in a ANSI-escape capable terminal, but for the sake of the tests, we'll
    # just check the output is encoded correctly.
    >>> out = pretty_color(RGB(1,0,0), 'RED')
    >>> print(out == '\x1b[38;2;255;0;0mRED\x1b[0m')
    True
    """
    r = int(rgb.r * 255)
    g = int(rgb.g * 255)
    b = int(rgb.b * 255)
    return f"\x1b[38;2;{r};{g};{b}m{text}\x1b[0m"


# -----------------------------------------------------------------------------
# JSONC parsing & theme remapping utilities
# -----------------------------------------------------------------------------


# Define states using an Enum
class State(enum.Enum):
    CODE = 1
    SINGLE_COMMENT = 2
    MULTI_COMMENT = 3
    STRING = 4


def strip_jsonc_comments(jsonc_string: str, preserve_newlines: bool = True) -> str:
    """
    Strips // and /* */ comments from a JSONC string using a state machine
    with Enum and match statements.

    Args:
        jsonc_string: The input string containing JSONC.

    Returns:
        A string with comments removed. The resulting string should be
        valid JSON if the original JSONC was valid after comment removal.

    Doctests:
        >>> strip_jsonc_comments('{"key": "value"}')
        '{"key": "value"}'
        >>> strip_jsonc_comments('{"key": "value" // comment}')
        '{"key": "value" }'
        >>> strip_jsonc_comments('{"key": "value" /* comment */}')
        '{"key": "value" }'
        >>> strip_jsonc_comments('{"key": /* block */ "value"}')
        '{"key":  "value"}'
        >>> strip_jsonc_comments('{"key": "value with // and /* in string"}')
        '{"key": "value with // and /* in string"}'
        >>> strip_jsonc_comments('/* block\\ncomment */{"key": "value"}')
        '{"key": "value"}'
        >>> strip_jsonc_comments('{"key": "value"}\\n// trailing comment')
        '{"key": "value"}\\n'
        >>> strip_jsonc_comments('')
        ''
        >>> strip_jsonc_comments('{"key": "value\\\\ // comment"}') # Escaped backslash near comment
        '{"key": "value\\\\ // comment"}'
    """
    output = []
    i = 0
    n = len(jsonc_string)
    state = State.CODE  # Start in CODE state

    def peek():
        return jsonc_string[i + 1] if i + 1 < n else None

    def consume():
        nonlocal i
        i += 1

    while i < n:
        char = jsonc_string[i]

        match state:
            case State.CODE:
                if char == '"':
                    state = State.STRING
                    output.append(char)
                elif char == "/":
                    if (p := peek()) is not None:
                        if p == "/":
                            state = State.SINGLE_COMMENT
                            consume()  # Consume the second '/'
                        elif p == "*":
                            state = State.MULTI_COMMENT
                            consume()  # Consume the '*'
                        else:
                            output.append(char)  # Just a regular slash
                    else:
                        output.append(char)  # Trailing slash
                else:
                    output.append(char)

            case State.SINGLE_COMMENT:
                match char:
                    case "}" | "{":
                        # Stay in single-line comment state until a newline or a start/end brace
                        state = State.CODE
                        output.append(char)
                    case "\\" if (p := peek()) in ("n", "r") and preserve_newlines:
                        output.append(char)
                        output.append(p)
                        consume()
                    case _:
                        # Discard other characters in this state
                        pass

            case State.MULTI_COMMENT:
                if char == "*":
                    if peek() == "/":
                        state = State.CODE
                        consume()
                    # Discard '*' if not followed by '/'
                # Discard other characters in this state

            case State.STRING:
                if char == "\\":
                    # Handle escape sequence: append the backslash
                    output.append(char)  # Append '\'
                    if (p := peek()) is not None:  # and the next character
                        output.append(p)
                        consume()
                    # Let the main loop's i += 1 move past the escaped character
                elif char == '"':
                    output.append(char)  # Append the closing quote
                    state = State.CODE
                else:
                    # Append regular character if it wasn't a backslash or quote
                    output.append(char)

            # No need for a default case if all states are covered

        consume()

    return "".join(output)


@dataclass
class Settings:
    font_style: str = ""
    foreground: str = ""


@dataclass
class TokenColors:
    name: str
    scope: Union[str, List[str], None]
    settings: Settings

    def get_scope(self) -> List[str]:
        """Return scope as a list of strings."""
        if isinstance(self.scope, str):
            return [self.scope]
        if isinstance(self.scope, list):
            return self.scope
        return []


@dataclass
class Data:
    name: str
    type: str
    colors: Dict[str, str]
    token_colors: List[TokenColors] = field(default_factory=list)


def parse(data: bytes) -> "Instance":
    """Parse JSONC bytes into an Instance."""
    text = strip_jsonc_comments(data.decode("utf-8"), preserve_newlines=False)
    obj = json.loads(text)
    d = Data(
        name=obj.get("name", ""),
        type=obj.get("type", ""),
        colors=obj.get("colors", {}),
        token_colors=[
            TokenColors(
                name=tc.get("name", ""),
                scope=tc.get("scope"),
                settings=Settings(
                    font_style=tc.get("settings", {}).get("fontStyle", ""),
                    foreground=tc.get("settings", {}).get("foreground", ""),
                ),
            )
            for tc in obj.get("tokenColors", [])
        ],
    )
    inst = Instance(data=d)
    for tc in d.token_colors:
        for scope in tc.get_scope():
            inst.add_color(scope, tc.settings.foreground)
    for k, v in d.colors.items():
        inst.add_color(k, v)
    return inst


def read_file(path: pathlib.Path) -> "Instance":
    """Read a theme file and parse into an Instance."""
    with path.open("rb") as f:
        data = f.read()
    return parse(data)


# -----------------------------------------------------------------------------
# Theme remapping utilities
# -----------------------------------------------------------------------------


def three_way_adjustment(src: RGB, dst: RGB, remapped: RGB) -> RGB:
    """
    Adjust HSL values across src, dst, remapped.
    """
    _, s1, l1 = src.Hsl()
    _, s2, l2 = dst.Hsl()
    h, s, l = remapped.Hsl()
    if s < s1:
        s1, s2 = s2, s1
    if l < l1:
        l1, l2 = l2, l1
    s += (s2 - s1) * 0.25
    l += (l2 - l1) * 0.25
    s = max(0, min(1, s))
    l = max(0, min(1, l))
    return RGB.from_hsl(h, s, l)


@dataclass
class Instance:
    """Holds theme data and remaps CSS hex colors."""

    data: Any
    colors: Dict[str, RGBA] = field(default_factory=dict)
    inverted_colors: Dict[RGB, List[str]] = field(default_factory=dict)

    def add_color(self, key: str, hex_str: str) -> None:
        """Add a hex color under a theme key."""
        try:
            col = new_css_color(hex_str)
        except ValueError:
            return
        self.colors[key] = col
        self.inverted_colors.setdefault(col.rgb, []).append(key)

    def remap_color_rgb(self, col: RGB, other: "Instance", internal: bool) -> RGB:
        """Remap a single RGB value."""
        if col in self.inverted_colors:
            keys = self.inverted_colors[col]
            options: Dict[RGB, List[str]] = {}
            for key in keys:
                cand = other.colors.get(key)
                if cand:
                    options.setdefault(cand.rgb, []).append(key)
            if options:
                best = next(iter(options))
                best_keys: List[str] = []
                for rgb_val, names in options.items():
                    if len(names) > len(best_keys):
                        best_keys = names
                        best = rgb_val
                return best
        else:
            closest = next(iter(self.inverted_colors))
            min_dist = math.inf
            for candidate in self.inverted_colors:
                dist = RGBA(candidate, 1.0).distance(RGBA(col, 1.0))
                if dist < min_dist:
                    min_dist = dist
                    closest = candidate
            remapped = self.remap_color_rgb(closest, other, True)
            return three_way_adjustment(closest, col, remapped)
        return col

    def remap_css(self, css: str, other: "Instance") -> str:
        """Remap all CSS hex tokens in stylesheet."""
        cache: Dict[RGB, RGB] = {}

        def repl(m: re.Match) -> str:
            token = m.group(0)
            hex_str = token[:-1]
            try:
                col = new_css_color(hex_str)
            except ValueError:
                return token
            prev = col.rgb
            if prev in cache:
                return RGBA(cache[prev], col.alpha).to_css_rgba() + ";"
            new_rgb = self.remap_color_rgb(prev, other, False)
            cache[prev] = new_rgb
            return RGBA(new_rgb, col.alpha).to_css_rgba() + ";"

        return CSS_HEX_REGEX.sub(repl, css)


def create_theme(
    ref_json: bytes,
    ref_css: str,
    tgt_json: pathlib.Path,
    out_dir: pathlib.Path,
    name_alt: str,
):
    src = Instance(data=None)
    # parse ref theme JSON/CSS
    src = parse(ref_json)
    dst = read_file(tgt_json)
    css = src.remap_css(ref_css, dst)
    if dst.data.type == "light":
        css = css.replace('@importtheme "dark";', '@importtheme "_base";')
    nm = dst.data.name.replace("/", "_").replace("\\", "_") or name_alt or "theme"
    od = out_dir / nm
    od.mkdir(parents=True, exist_ok=True)
    with (od / "theme.css").open("w+") as f:
        f.write(css)


def create_themes_from_extension(
    ref_json: bytes, ref_css: str, ext_path: pathlib.Path, out_dir: pathlib.Path
):
    pkg_path = ext_path / "package.json"
    if not pkg_path.exists():
        raise FileNotFoundError(pkg_path)
    with pkg_path.open("r") as f:
        pkg = json.load(f)
    for t in pkg.get("contributes", {}).get("themes", []):
        p = ext_path / t.get("path", "")
        create_theme(ref_json, ref_css, p, out_dir, ext_path.name)


## Tests


class TestSuiteRegistry:
    """
    Registry for TestCase subclasses and runner.

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


# -- Test runners & CLI -----------------------------------------------------


def main():
    parser = argparse.ArgumentParser(description="Theme tool: test or convert")
    subs = parser.add_subparsers(dest="cmd")
    subs.add_parser("test", help="run tests")
    conv = subs.add_parser("convert", help="convert themes")
    conv.add_argument(
        "target",
        type=pathlib.Path,
        help="theme to convert or pass '*' for all themes in a directory",
    )
    conv.add_argument("outdir", type=pathlib.Path)
    conv.add_argument(
        "--ext-root",
        type=pathlib.Path,
        default=None,
        help="VSCode extensions directory",
    )
    args = parser.parse_args()

    if args.cmd == "convert":
        base = pathlib.Path(__file__).parent
        rj = (base / "rsrc" / "theme.json").read_bytes()
        rc = (base / "rsrc" / "theme.css").read_text()
        if args.target == "*":
            # Use provided ext_root or compute it
            ext_root = None if args.ext_root is None else args.ext_root
            if ext_root is None:
                for d in ("vscode", "vscode-insiders", ".cursor"):
                    if (
                        p := pathlib.Path(os.getenv("VSCODE_DATA")) / d / "extensions"
                    ).exists():
                        ext_root = p
                        break
                else:
                    raise ValueError(
                        "No VSCode extensions directory found! "
                        "Set --ext-root or VSCODE_DATA"
                    )
            for fd in ext_root.iterdir():
                try:
                    create_themes_from_extension(rj, rc, fd, args.outdir)
                    logging.info("Created themes from %s", fd.name)
                except Exception as e:
                    logging.info("Failed %s: %s", fd.name, e)
        else:
            create_theme(rj, rc, args.target, args.outdir, "")
    else:

        failures, _ = doctest.testmod()
        result = test_suite.run()
        sys.exit(0 if (result.wasSuccessful() or failures) else 1)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    main()
