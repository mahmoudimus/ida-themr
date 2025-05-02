import re
from typing import Dict

from ida_themr import RGB, RGBA, new_css_color


def load_variables(content: str) -> Dict[str, str]:
    variables = {}
    var_pattern = re.compile(r"@def\s+(\S+)\s+(.+?);")

    # Collect variables in definition order
    defined_order = []
    for match in var_pattern.finditer(content):
        var_name = match.group(1)
        variables[var_name] = match.group(2)
        defined_order.append(var_name)

    var_usage_pattern = re.compile(r"\$\{(\S+?)\}")

    # Process variables in definition order, only resolving previous variables
    for var_name in defined_order:
        value = variables[var_name]
        while True:
            match = var_usage_pattern.search(value)
            if not match:
                break

            ref_name = match.group(1)
            if ref_name in variables and defined_order.index(
                ref_name
            ) < defined_order.index(var_name):
                value = value.replace(match.group(0), variables[ref_name])
                variables[var_name] = value
            else:
                if ref_name not in variables:
                    print(
                        f"Warning: Variable {ref_name} referenced in {var_name} is undefined."
                    )
                break  # Stop processing this variable

    return variables


def remove_functions(content: str) -> str:
    """
    Remove function calls like @lighten or @darken and evaluate them if possible.
    If a function is recognized, it will be replaced with the transformed color.
    """

    def evaluate_function(match: re.Match) -> str:
        func_name = match.group(1)
        color_hex = match.group(2)
        params = match.group(3).strip() if match.group(3) else ""

        try:
            # Parse the color
            rgba = new_css_color(color_hex)
            rgb = rgba.rgb

            # Handle lighten and darken functions
            if func_name.lower() == "lighten" and params:
                factor = (
                    float(params.split(",")[1].strip()) / 100.0
                    if "," in params
                    else float(params) / 100.0
                )
                return rgb.lighten(factor).to_css_rgba()
            elif func_name.lower() == "darken" and params:
                factor = (
                    float(params.split(",")[1].strip()) / 100.0
                    if "," in params
                    else float(params) / 100.0
                )
                return rgb.darken(factor).to_css_rgba()
            else:
                # Default to returning the color without transformation
                return color_hex
        except (ValueError, IndexError):
            return color_hex

    # Match function calls like @lighten(#FF0000, 20)
    return re.sub(
        r"@([A-Za-z_][A-Za-z0-9_]*)\(\s*(#[A-Fa-f0-9]{6})(?:([^)]*))?\)",
        evaluate_function,
        content,
    )


def replace_variables(content: str, variables: Dict[str, str]) -> str:
    result = content
    var_usage_pattern = re.compile(r"\$\{(\S+?)\}")

    while True:
        match = var_usage_pattern.search(result)
        if not match:
            break

        var_name = match.group(1)
        if var_name in variables:
            result = result.replace(match.group(0), variables[var_name])
        else:
            print(f"Warning: Variable {var_name} not defined. Skipping replacement.")
            break  # Break the loop to prevent infinite recursion

    result = remove_functions(result)
    return result


def parse_template(content: str) -> str:
    """
    Parse templated CSS content containing @def lines and a CSS block.
    Returns only the processed CSS block with variables expanded, functions removed,
    and any line originating from a function definition annotated with '/* simplified */'.
    """
    # Split into lines and find end of @def section (first blank line)
    lines = content.splitlines()
    split_idx = 0
    for idx, line in enumerate(lines):
        if not line.strip():
            split_idx = idx
            break

    # Everything after the blank line is the CSS block
    css_original = lines[split_idx + 1 :]

    # Build variables and detect which were defined via functions
    variables = load_variables(content)
    simplified_vars = {
        name for name, val in variables.items() if remove_functions(val) != val
    }

    # Prepare pattern to find ${var} in original CSS lines
    var_usage_pattern = re.compile(r"\$\{(\S+?)\}")

    # Process each CSS line: replace vars & remove functions, then annotate
    output_lines: list[str] = []
    for css_line in css_original:
        if not css_line.strip():
            continue
        replaced = replace_variables(css_line, variables)
        # If this line referenced a function‐defined var, append the comment
        for match in var_usage_pattern.finditer(css_line):
            if match.group(1) in simplified_vars:
                if replaced.rstrip().endswith(";"):
                    replaced = replaced.rstrip() + " /* simplified */"
                break
        output_lines.append(replaced)

    return "\n".join(output_lines)
