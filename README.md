# ida-themr 🎨

A pure Python IDA Pro theme porter from VS Code. Transform your reversing environment with ease! 🚀

![CI Status](https://github.com/mahmoudimus/ida-themr/actions/workflows/python.yml/badge.svg)

## Overview 🌟

`ida-themr` is a powerful tool designed to convert VS Code themes to IDA Pro color schemes, allowing you to bring your favorite VS Code aesthetics into IDA Pro. Whether you're a reverse engineer, a security researcher, or a developer, this plugin ensures the IDA Pro workspace matches your style with intelligent color mapping and theme preservation. 🖌️

Beyond theme conversion, `ida-themr` also simplifies CSS theme files by resolving variable references and functions, making themes easier to maintain and debug. There is a dearth of information regarding how to make themes etc and I am hoping to consolidate it here for others to benefit! 🛠️

### Features ✨

- **Theme Conversion**: Convert individual VS Code themes to IDA Pro effortlessly. 🎭
- **Batch Processing**: Convert all installed VS Code extension themes in one go. 📦
- **Intelligent Color Mapping**: Maps colors between VS Code and IDA Pro using theme keys and nearest-color matching with HSL adjustments. 🌈
- **Theme Semantics Preservation**: Maintains the visual intent of the original theme during conversion. 🖼️
- **Variable Resolution**: Replaces `${variable}` references with their defined values in CSS files. 🔄
- **Function Simplification**: Converts complex functions like `@lighten()` to base colors for clarity. 🧹
- **Error Logging**: Provides warnings for undefined variables or malformed function calls. ⚠️
- **Custom Output**: Generates new theme files in a specified output directory for easy integration. 📁
- **Well-Tested**: Comprehensive unit tests ensure reliability and accuracy in color conversion and CSS processing. ✅

## How It Works 🛠️

`ida-themr` operates by parsing VS Code theme files (JSONC format), mapping colors to an existing IDA Pro theme, and generating compatible CSS files for IDA Pro. Here's the breakdown:

1. **Color Parsing**: Supports CSS hex formats (`#RGB`, `#RGBA`, `#RRGGBB`, `#RRGGBBAA`) and converts them to normalized RGB/RGBA values. 🎨
2. **Theme Mapping**: Uses theme keys to match colors directly or falls back to nearest-color matching with Euclidean distance and HSL adjustments. 📏
3. **CSS Processing**: Resolves variables and simplifies functions in CSS, ensuring clean and maintainable output. 🧑‍💻
4. **Output Generation**: Creates new theme directories with remapped CSS files ready for IDA Pro. 📤

## IDA supports some `SASS` directives

- `@def`
- `@lighten`
- `@darken`
- `@importtheme`
- `@ifdef/@ifndef` -> optional `@else` -> `@endif`

## Installation 📥

Get started with `ida-themr` in just a few steps! 🚀

1. **Clone the Repository**:

   ```bash
   git clone https://github.com/mahmoudimus/ida-themr.git
   cd ida-themr
   ```

2. **Ensure Python 3 is Installed**:
   Make sure you have Python 3 installed on your system. You can check with:

   ```bash
   python3 --version
   ```

3. **No Additional Dependencies Needed**:
   `ida-themr` is a pure Python tool with no external dependencies beyond the standard library. You're ready to go! 👍

## Usage 🖥️

Run `ida-themr` to convert themes with the following commands. Make sure you're in the project directory. 📂

### Convert a Single Theme 🎯

To convert a specific VS Code theme to IDA Pro:

```bash
python3 src/ida_themr.py /path/to/vscode/theme.json /path/to/output/directory
```

### Batch Convert All Installed Themes 🌍

To convert all themes from your VS Code extensions directory:

```bash
python3 src/ida_themr.py "*" /path/to/output/directory
```

**Note**: If the VS Code extensions directory isn't automatically detected, set the `--ext-root` flag or the `VSCODE_DATA` environment variable to point to your VS Code data directory. 🔍

```bash
python3 src/ida_themr.py "*" /path/to/output/directory --ext-root /path/to/vscode/extensions
```

### Applying the Theme to IDA Pro 🖌️

1. Locate the generated theme folder in your output directory (named after the theme). 📁
2. Copy the `theme.css` file from the folder to your IDA Pro themes directory (usually found in IDA's installation directory under `themes/`). 📋
3. Restart IDA Pro, and select the new theme from the options menu under `View > Themes`. 🎉

## Examples 📸

### Before Conversion 📝

Here's a sample CSS snippet with variables and functions from a VS Code theme:

```css
@def color-primary #ff5733;
@def color-background @lighten(#ff5733, 20);

.button {
  color: ${color-primary};
  background-color: ${color-background};
}
```

### After Conversion 🎨

After processing with `ida-themr`, the CSS is simplified and colors are remapped for IDA Pro:

```css
.button {
  color: #ff5733;
  background-color: #ff5733; /* simplified */
}
```

## Testing 🧪

`ida-themr` is thoroughly tested to ensure reliability. The test suite covers color conversion, JSONC parsing, HSL adjustments, variable expansion, and more. To run the tests:

```bash
python3 tests.py
```

You'll see detailed output confirming the functionality of each component. ✅

## Contributing 🤝

We welcome contributions to `ida-themr`! Whether it's bug fixes, new features, or documentation improvements, your help is appreciated. Here's how to contribute:

1. **Fork the Repository** and clone it locally. 🍴
2. **Make Your Changes** in a new branch. 🌿
3. **Run Tests** to ensure everything works (`python3 tests.py`). 🧪
4. **Submit a Pull Request** with a clear description of your changes. 📬

Please follow the coding style and include tests for new functionality. Let's make `ida-themr` even better together! 💪

## License 📜

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details. 📄

## Contact 📧

Have questions, suggestions, or need support? Open an issue on GitHub or reach out to [mahmoudimus](https://github.com/mahmoudimus). I'm happy to help! 😊

## Acknowledgments 🙏

[@SmugNugg](github.com/SmugNugg) for the idea about resolving inlined css functions.
[@can1357](github.com/can1357) for his [IdaThemer](https://github.com/can1357/IdaThemer) from which this is shamelessly ported and enhanced.

Happy theming with `ida-themr`! Let's make IDA Pro as colorful as your imagination! 🎨🚀
