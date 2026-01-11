#!/usr/bin/env python3
"""
Stage 2: The Converter
Converts Word (.docx) files to Markdown using Pandoc.
CRITICAL: Uses --wrap=none to preserve tables for NotebookLM.

Usage:
    python3 word_to_md.py --input /path/to/pdf/folder
"""

import argparse
import subprocess
from pathlib import Path


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


def run(input_dir: Path) -> dict:
    """
    Run Stage 2: Word to Markdown conversion.

    Args:
        input_dir: Path to folder containing PDF files (reads from _stage1_docx subfolder)

    Returns:
        dict with counts: {'converted': N, 'skipped': N, 'failed': N}
    """
    docx_dir = input_dir / "_stage1_docx"
    output_dir = input_dir / "_stage2_raw_md"

    print("=" * 60)
    print("STAGE 2: Word → Markdown (Pandoc)")
    print("=" * 60)
    print(f"Input:  {docx_dir}")
    print(f"Output: {output_dir}")

    # Ensure output directory exists
    output_dir.mkdir(exist_ok=True)

    # Get list of Word files
    if not docx_dir.exists():
        print(f"\nStage 1 output folder not found: {docx_dir}")
        print("Run Stage 1 first.")
        return {'converted': 0, 'skipped': 0, 'failed': 0}

    docx_files = sorted(docx_dir.glob("*.docx"))

    if not docx_files:
        print(f"\nNo Word files found in {docx_dir}")
        return {'converted': 0, 'skipped': 0, 'failed': 0}

    print(f"\nFound {len(docx_files)} Word file(s) to process.\n")

    success_count = 0
    skip_count = 0
    fail_count = 0

    for i, docx_path in enumerate(docx_files, 1):
        output_path = output_dir / f"{docx_path.stem}.md"

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
    print("\n" + "-" * 40)
    print(f"Stage 2 Complete: {success_count} converted, {skip_count} skipped, {fail_count} failed")

    return {'converted': success_count, 'skipped': skip_count, 'failed': fail_count}


def main():
    parser = argparse.ArgumentParser(
        description="Stage 2: Convert Word files to Markdown using Pandoc"
    )
    parser.add_argument(
        "-i", "--input",
        type=Path,
        required=True,
        help="Path to folder containing PDF files"
    )
    args = parser.parse_args()

    if not args.input.is_dir():
        print(f"Error: {args.input} is not a valid directory")
        return

    run(args.input)


if __name__ == "__main__":
    main()
