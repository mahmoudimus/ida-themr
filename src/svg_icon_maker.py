"""
Generate complete icon families:

    base-light.svg
    base-light-hover.svg
    base-light-pressed.svg
    base-light-disabled.svg
    base-dark.svg
    base-dark-hover.svg
    base-dark-pressed.svg
    base-dark-disabled.svg
"""

import argparse
import colorsys
import pathlib
import re
import sys
from xml.etree import ElementTree as ET

HEX = re.compile(r"#([0-9a-fA-F]{3,6})\b")
SKIP = {"none", "currentColor"}


# ───────────────────────── color helpers ───────────────────────── #
def normalize(hexcode: str) -> str:
    hexcode = hexcode.lower()
    if len(hexcode) == 4:  # #rgb → #rrggbb
        hexcode = "#" + "".join(c * 2 for c in hexcode[1:])
    return hexcode


def hex_to_rgb(hexcode: str) -> tuple[int, int, int]:
    return tuple(int(hexcode[i : i + 2], 16) for i in (1, 3, 5))


def rgb_to_hex(rgb: tuple[int, int, int]) -> str:
    return "#{:02x}{:02x}{:02x}".format(*rgb)


def adjust_lightness(hexcode: str, factor: float) -> str:
    """factor > 1 → lighter, factor < 1 → darker."""
    r, g, b = [c / 255.0 for c in hex_to_rgb(hexcode)]
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    l = max(0.0, min(1.0, l * factor))
    r2, g2, b2 = colorsys.hls_to_rgb(h, l, s)
    return rgb_to_hex((int(r2 * 255), int(g2 * 255), int(b2 * 255)))


def desaturate(hexcode: str, sat_factor: float = 0.2, lum_factor: float = 0.6) -> str:
    """Gray-out for disabled state."""
    r, g, b = [c / 255.0 for c in hex_to_rgb(hexcode)]
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    r2, g2, b2 = colorsys.hls_to_rgb(h, l * lum_factor, s * sat_factor)
    return rgb_to_hex((int(r2 * 255), int(g2 * 255), int(b2 * 255)))


# ───────────────────────── SVG helpers ───────────────────────── #
def extract_colors(root):
    colors = []
    for el in root.iter():
        for attr in ("fill", "stroke"):
            if attr in el.attrib and el.attrib[attr] not in SKIP:
                if el.attrib[attr].startswith("#"):
                    colors.append(normalize(el.attrib[attr]))
        if "style" in el.attrib:
            colors += [
                normalize("#" + m.group(1)) for m in HEX.finditer(el.attrib["style"])
            ]
    return list({*colors})  # unique list


def darkest_lightest(colors):
    colors.sort(key=lambda c: sum(hex_to_rgb(c)))  # crude luminance
    return colors[0], colors[-1]


def swap_in_string(text, a, b):
    def repl(m):
        col = normalize("#" + m.group(1))
        return b if col == a else a if col == b else col

    return HEX.sub(repl, text)


def patch_el(el, old, new):
    for attr in ("fill", "stroke"):
        if attr in el.attrib and el.attrib[attr] not in SKIP:
            if el.attrib[attr].startswith("#"):
                el.attrib[attr] = swap_in_string(el.attrib[attr], old, new)
    if "style" in el.attrib:
        el.attrib["style"] = swap_in_string(el.attrib["style"], old, new)


def recolor_inner(root, original, replacement):
    for el in root.iter():
        patch_el(el, original, replacement)


# ───────────────────────── generator ───────────────────────── #
def generate_icon_family(svg_path: pathlib.Path):
    ET.register_namespace("", "http://www.w3.org/2000/svg")
    tree = ET.parse(svg_path)
    root = tree.getroot()

    colors = extract_colors(root)
    if len(colors) < 2:
        raise ValueError("Fewer than two colors found")

    outer, inner = darkest_lightest(colors)  # crude but practical

    family = {
        "light": inner,  # unchanged
        "hover": adjust_lightness(inner, 1.25),  # lighter 25 %
        "pressed": adjust_lightness(inner, 0.75),  # darker 25 %
        "disabled": desaturate(inner),
    }

    for theme in ("light", "dark"):
        # make a copy of the parsed tree each time so we start fresh
        for state, new_color in family.items():
            themed_tree = ET.ElementTree(ET.fromstring(ET.tostring(root)))
            themed_root = themed_tree.getroot()

            if theme == "dark":  # swap outer ↔ inner first
                for el in themed_root.iter():
                    patch_el(el, outer, inner)

            if state != "light":  # recolor “inner” for UI state
                recolor_inner(themed_root, inner, new_color)

            out_name = f"{svg_path.stem}-{theme}"
            if state != "light":
                out_name += f"-{state}"
            out_svg = svg_path.with_name(out_name + svg_path.suffix)
            themed_tree.write(out_svg)
    print(f"✓  {svg_path.name} → full family written.")


# ───────────────────────── CLI ───────────────────────── #
def main():
    ap = argparse.ArgumentParser(
        description="Generate light/dark + UI-state SVG families."
    )
    ap.add_argument("folder", help="Directory with original SVGs")
    args = ap.parse_args()

    directory = pathlib.Path(args.folder)
    if not directory.is_dir():
        sys.exit(f"Error: {directory} is not a directory")

    originals = [
        p
        for p in directory.glob("*.svg")
        if not any(
            p.stem.endswith(suf)
            for suf in ("-light", "-hover", "-pressed", "-disabled", "-dark")
        )
    ]

    if not originals:
        sys.exit("No base SVGs found.")

    for svg in originals:
        try:
            generate_icon_family(svg)
        except Exception as e:
            print(f"⚠️  {svg.name}: {e}")


if __name__ == "__main__":
    main()
