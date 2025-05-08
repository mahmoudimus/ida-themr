import argparse
import pathlib
import re
from xml.etree import ElementTree as ET


def patch_fill(element, color):
    """Patch fill or style attributes with the given color."""
    if "fill" in element.attrib:
        if element.attrib["fill"] in ("currentColor", "#000", "#000000"):
            element.attrib["fill"] = color
    if "style" in element.attrib:
        style = element.attrib["style"]
        if "fill:" in style:
            style = re.sub(r"fill:\s*[^;]+", f"fill:{color}", style)
        else:
            style += f";fill:{color}"
        element.attrib["style"] = style


def generate_svg_variant(input_path, output_path, color):
    ET.register_namespace("", "http://www.w3.org/2000/svg")  # keep clean xmlns
    tree = ET.parse(input_path)
    root = tree.getroot()

    for elem in root.iter():
        patch_fill(elem, color)

    tree.write(output_path)
    print(f"Saved {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate SVG icon variants with different colors."
    )
    parser.add_argument(
        "theme_path", type=str, help="Path to the directory containing SVG files."
    )
    args = parser.parse_args()

    theme_dir = pathlib.Path(args.theme_path)
    if not theme_dir.is_dir():
        print(f"Error: Theme path '{args.theme_path}' is not a valid directory.")
        exit(1)

    variants = {"hover": "#f0a500", "pressed": "#d97706", "disabled": "#888888"}

    svg_files_found = False
    for base_svg_path in theme_dir.glob("*.svg"):
        # Skip already processed variants if they are in the same directory
        if any(f"-{state}.svg" in base_svg_path.name for state in variants):
            continue

        svg_files_found = True
        print(f"Processing {base_svg_path}...")
        for state, color in variants.items():
            out_svg_name = f"{base_svg_path.stem}-{state}{base_svg_path.suffix}"
            out_svg_path = base_svg_path.with_name(out_svg_name)
            generate_svg_variant(base_svg_path, out_svg_path, color)

    if not svg_files_found:
        print(f"No SVG files found in '{args.theme_path}'.")
