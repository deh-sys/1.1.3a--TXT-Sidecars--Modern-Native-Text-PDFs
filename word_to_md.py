#!/usr/bin/env python3
"""
Script 2: The Converter
Converts Word (.docx) files to Markdown using Pandoc.
CRITICAL: Uses --wrap=none to preserve tables for NotebookLM.
"""

import subprocess
from pathlib import Path

# Directory configuration
SCRIPT_DIR = Path(__file__).parent
INPUT_DIR = SCRIPT_DIR / "02_stage1_docx"
OUTPUT_DIR = SCRIPT_DIR / "03_stage2_raw_md"


def convert_word_to_markdown(docx_path: Path, output_path: Path) -> bool:
    """
    Convert a Word document to Markdown using Pandoc.
    Returns True on success, False on failure.
    """
    cmd = [
        "pandoc",
        str(docx_path),
        "-f", "docx",
        "-t", "markdown",
        "-o", str(output_path),
        "--wrap=none"  # CRITICAL: Preserves tables for NotebookLM
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )
        if result.returncode != 0:
            print(f"  ERROR: {result.stderr.strip()}")
            return False
        return True
    except subprocess.TimeoutExpired:
        print("  ERROR: Conversion timed out")
        return False
    except FileNotFoundError:
        print("  ERROR: Pandoc not found. Install with: brew install pandoc")
        return False
    except Exception as e:
        print(f"  ERROR: {e}")
        return False


def main():
    print("=" * 60)
    print("Word to Markdown Converter (Pandoc)")
    print("=" * 60)

    # Ensure directories exist
    INPUT_DIR.mkdir(exist_ok=True)
    OUTPUT_DIR.mkdir(exist_ok=True)

    # Get list of Word files
    docx_files = sorted(INPUT_DIR.glob("*.docx"))

    if not docx_files:
        print(f"\nNo Word files found in {INPUT_DIR}")
        print("Run pdf_to_word.py first to generate Word files.")
        return

    print(f"\nFound {len(docx_files)} Word file(s) to process.\n")

    success_count = 0
    skip_count = 0
    fail_count = 0

    for i, docx_path in enumerate(docx_files, 1):
        output_path = OUTPUT_DIR / f"{docx_path.stem}.md"

        print(f"[{i}/{len(docx_files)}] {docx_path.name}")

        # Check if output already exists
        if output_path.exists():
            print(f"  Skipping... (output already exists)")
            skip_count += 1
            continue

        print(f"  Converting to Markdown...")
        if convert_word_to_markdown(docx_path, output_path):
            print(f"  Success: {output_path.name}")
            success_count += 1
        else:
            fail_count += 1

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  Converted: {success_count}")
    print(f"  Skipped:   {skip_count}")
    print(f"  Failed:    {fail_count}")
    print(f"\nOutput folder: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
