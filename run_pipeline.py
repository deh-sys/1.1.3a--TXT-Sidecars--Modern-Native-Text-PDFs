#!/usr/bin/env python3
"""
Pipeline Router: Runs all conversion stages in sequence.

Usage:
    python3 run_pipeline.py --input /path/to/pdf/folder
    python3 run_pipeline.py -i /path/to/folder --stage 2 --stage 3
"""

import argparse
import sys
from pathlib import Path

# Add script directory to path for imports
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))

import pdf_to_word
import word_to_md
import clean_md


def print_banner(text: str):
    """Print a prominent stage banner."""
    width = 60
    print("\n" + "=" * width)
    print(f"  {text}")
    print("=" * width + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="PDF-to-Markdown Pipeline Router",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Stages:
  1  PDF → Word     (uses Adobe Acrobat)
  2  Word → Markdown (uses Pandoc)
  3  Clean Markdown  (uses regex rules from config_regex.yaml)

Examples:
  python3 run_pipeline.py --input /path/to/folder
  python3 run_pipeline.py -i /path/to/folder --stage 2 --stage 3
        """
    )
    parser.add_argument(
        "-i", "--input",
        type=Path,
        required=True,
        help="Path to folder containing PDF files"
    )
    parser.add_argument(
        "-s", "--stage",
        type=int,
        choices=[1, 2, 3],
        action="append",
        help="Run specific stage(s). Can be used multiple times. Default: all stages."
    )
    args = parser.parse_args()

    # Validate input directory
    if not args.input.is_dir():
        print(f"Error: {args.input} is not a valid directory")
        sys.exit(1)

    input_dir = args.input.resolve()

    # Determine which stages to run
    stages_to_run = args.stage if args.stage else [1, 2, 3]
    stages_to_run = sorted(set(stages_to_run))  # Remove duplicates, sort

    print_banner("PDF-TO-MARKDOWN PIPELINE")
    print(f"Input folder: {input_dir}")
    print(f"Stages to run: {stages_to_run}\n")

    results = {}

    # Run selected stages
    if 1 in stages_to_run:
        results[1] = pdf_to_word.run(input_dir)

    if 2 in stages_to_run:
        results[2] = word_to_md.run(input_dir)

    if 3 in stages_to_run:
        results[3] = clean_md.run(input_dir)

    # Final summary
    print_banner("PIPELINE COMPLETE")
    print(f"Input folder: {input_dir}")
    print("\nOutput locations:")
    print(f"  Word files:     {input_dir}/_stage1_docx/")
    print(f"  Raw Markdown:   {input_dir}/_stage2_raw_md/")
    print(f"  Final output:   {input_dir}/Sidecar Files/")

    # Print combined results
    total_converted = sum(r.get('converted', 0) for r in results.values())
    total_skipped = sum(r.get('skipped', 0) for r in results.values())
    total_failed = sum(r.get('failed', 0) for r in results.values())

    print(f"\nTotal: {total_converted} converted, {total_skipped} skipped, {total_failed} failed")


if __name__ == "__main__":
    main()
