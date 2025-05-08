#!/usr/bin/env python3
"""
QSS Formatter - Post-processing script for QSS files
Fixes variable interpolation formatting in QSS files after VS Code formatting
"""

import argparse
import re
import sys
import tempfile  # Import tempfile
import unittest
from pathlib import Path  # Import Path


def fix_qss_formatting(file_path: Path):  # Type hint for Path
    """Fix QSS formatting for variable interpolation and pseudo-class spacing."""
    try:
        # Read the file using Path.read_text()
        content = file_path.read_text(encoding="utf-8")

        # Fix variable interpolation formatting
        # Replace multiline/spaced variable interpolations like $ { varname } with ${varname}
        # This handles different contexts like ending with ;, ), ,, etc.
        content = re.sub(r"\$\s*{\s*(\w+)\s*}\s*", r"${\1}", content)

        # Fix spacing after colon in pseudo-class selectors
        # Replace ': !' with ':!' to collapse the space
        content = re.sub(r":\s*!", r":!", content)

        # Write the file back using Path.write_text()
        file_path.write_text(content, encoding="utf-8")

        print(f"Successfully processed: {file_path}")  # Path objects stringify nicely
        return True
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False


def main():
    """Main function that processes arguments and starts fixing files."""
    parser = argparse.ArgumentParser(
        description="Fix CSS/QSS file formatting for variable interpolation"
    )
    parser.add_argument(
        "paths",
        nargs="*",
        default=["."],
        help="Paths to QSS files or directories containing QSS files",
    )
    parser.add_argument(
        "-e", "--extension", type=str, default=".css", help="File extension to process"
    )
    parser.add_argument(
        "-r", "--recursive", action="store_true", help="Process directories recursively"
    )

    args = parser.parse_args()

    # Process all provided paths
    for path_str in args.paths:
        path = Path(path_str)  # Convert string path to Path object
        if path.is_file() and path.suffix == args.extension:
            # Process single file
            fix_qss_formatting(path)
        elif path.is_dir():
            # Process directory
            if args.recursive:
                # Recursively find all QSS files using Path.rglob()
                qss_files = list(path.rglob(args.extension))
            else:
                # Only find QSS files in the top directory using Path.glob()
                qss_files = list(path.glob(args.extension))

            # Process each QSS file
            success_count = 0
            for qss_file in qss_files:
                if fix_qss_formatting(qss_file):
                    success_count += 1

            if qss_files:  # Avoid division by zero if no files found
                print(
                    f"Processed {success_count} of {len(qss_files)} QSS files in {path}"
                )
            else:
                print(f"No QSS files found in {path}")
        else:
            print(f"Warning: Path not found or not a QSS file/directory: {path}")


# --- Unit Tests ---


class TestQssFormatter(unittest.TestCase):
    def test_variable_interpolation_formatting_semicolon(self):  # Renamed for clarity
        """Test fixing variable interpolation ending with semicolon."""
        input_qss = """
DockWidgetTitle[os-dark-theme="true"][active="true"] QPushButton:hover {

    /* Dark */
    background: $ {
        clr_blue
    }

    ;
}
"""
        # Expected output after the updated regex (no trailing space before ;)
        expected_qss = """
DockWidgetTitle[os-dark-theme="true"][active="true"] QPushButton:hover {

    /* Dark */
    background: ${clr_blue};
}
"""
        # Use a temporary file for testing
        with tempfile.NamedTemporaryFile(
            mode="w+", delete=False, suffix=".css", encoding="utf-8"
        ) as tmp_file:
            tmp_file_path = Path(tmp_file.name)
            tmp_file.write(input_qss)
            tmp_file.flush()  # Ensure content is written before closing handle implicitly or explicitly
            tmp_file.close()  # Close the file handle to allow fix_qss_formatting to open it

        try:
            # Run the function on the temporary file
            result = fix_qss_formatting(tmp_file_path)
            self.assertTrue(result, "fix_qss_formatting should return True on success")

            # Read the content after processing
            actual_qss = tmp_file_path.read_text(encoding="utf-8")

            # Assert the content matches the expected output
            self.assertEqual(actual_qss, expected_qss)
        finally:
            # Clean up the temporary file
            if tmp_file_path.exists():
                tmp_file_path.unlink()

    def test_def_lighten_formatting(self):
        """Test fixing multiple interpolations in @def/@lighten context."""
        input_qss = """
@def diff_region_pick_l @lighten($ {

        diff_region_pick

    }

    , $ {

        lightening

    });
"""
        # Note: The regex only collapses the ${...}, it doesn't fix surrounding whitespace like extra spaces after @def
        # Adjusting expected output based *only* on what the regex does.
        expected_qss = """
@def diff_region_pick_l @lighten(${diff_region_pick}, ${lightening});
"""
        # Use a temporary file for testing
        with tempfile.NamedTemporaryFile(
            mode="w+", delete=False, suffix=".css", encoding="utf-8"
        ) as tmp_file:
            tmp_file_path = Path(tmp_file.name)
            tmp_file.write(input_qss)
            tmp_file.flush()
            tmp_file.close()

        try:
            # Run the function on the temporary file
            result = fix_qss_formatting(tmp_file_path)
            self.assertTrue(result, "fix_qss_formatting should return True on success")

            # Read the content after processing
            actual_qss = tmp_file_path.read_text(encoding="utf-8")

            # Assert the content matches the expected output
            self.assertEqual(actual_qss, expected_qss)
        finally:
            # Clean up the temporary file
            if tmp_file_path.exists():
                tmp_file_path.unlink()

    def test_pseudo_class_spacing(self):
        """Test fixing spacing after colon in pseudo-class selectors."""
        input_qss = """
QPushButton[os-dark-theme="true"]: !enabled {
    background: ${clr_background};
}
"""
        expected_qss = """
QPushButton[os-dark-theme="true"]:!enabled {
    background: ${clr_background};
}
"""
        # Use a temporary file for testing
        with tempfile.NamedTemporaryFile(
            mode="w+", delete=False, suffix=".css", encoding="utf-8"
        ) as tmp_file:
            tmp_file_path = Path(tmp_file.name)
            tmp_file.write(input_qss)
            tmp_file.flush()
            tmp_file.close()

        try:
            # Run the function on the temporary file
            result = fix_qss_formatting(tmp_file_path)
            self.assertTrue(result, "fix_qss_formatting should return True on success")

            # Read the content after processing
            actual_qss = tmp_file_path.read_text(encoding="utf-8")

            # Assert the content matches the expected output
            self.assertEqual(actual_qss, expected_qss)
        finally:
            # Clean up the temporary file
            if tmp_file_path.exists():
                tmp_file_path.unlink()


if __name__ == "__main__":
    # Run tests if the script is executed directly
    # Note: This will run tests instead of the main() function when run directly
    # To run the main logic, execute without specific test flags.
    # Consider using separate files or a test runner for more complex scenarios.
    if len(sys.argv) > 1 and sys.argv[1] not in ("-r", "--recursive"):
        # Allow running the main script functionality if paths are provided
        # and they are not the recursive flag.
        # This is a simple way to distinguish between running tests and the script's main purpose.
        main()
    else:
        # Default to running tests if no specific file/dir paths are given
        # or if only the recursive flag is present (which doesn't make sense alone).
        # We need to remove our script name from argv for unittest.main
        test_argv = [sys.argv[0]]
        unittest.main(argv=test_argv)
