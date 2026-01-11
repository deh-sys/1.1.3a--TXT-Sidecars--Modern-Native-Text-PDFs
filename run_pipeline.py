#!/usr/bin/env python3
"""
Pipeline Router: Runs all conversion stages in sequence.

Usage:
    python3 run_pipeline.py           # Run all stages
    python3 run_pipeline.py --stage 1 # Run only Stage 1 (PDF → Word)
    python3 run_pipeline.py --stage 2 # Run only Stage 2 (Word → Markdown)
    python3 run_pipeline.py --stage 3 # Run only Stage 3 (Clean Markdown)
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


def run_stage_1():
    """Stage 1: PDF → Word via Adobe Acrobat"""
    print_banner("STAGE 1: PDF → Word (Adobe Acrobat)")
    pdf_to_word.main()


def run_stage_2():
    """Stage 2: Word → Markdown via Pandoc"""
    print_banner("STAGE 2: Word → Markdown (Pandoc)")
    word_to_md.main()


def run_stage_3():
    """Stage 3: Clean Markdown via regex rules"""
    print_banner("STAGE 3: Clean Markdown (Regex)")
    clean_md.main()


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
  python3 run_pipeline.py           # Run all stages
  python3 run_pipeline.py --stage 2 # Run only Stage 2
  python3 run_pipeline.py -s 2 -s 3 # Run Stages 2 and 3
        """
    )
    parser.add_argument(
        "-s", "--stage",
        type=int,
        choices=[1, 2, 3],
        action="append",
        help="Run specific stage(s). Can be used multiple times. Default: all stages."
    )
    args = parser.parse_args()

    # Determine which stages to run
    stages_to_run = args.stage if args.stage else [1, 2, 3]
    stages_to_run = sorted(set(stages_to_run))  # Remove duplicates, sort

    print_banner("PDF-TO-MARKDOWN PIPELINE")
    print(f"Stages to run: {stages_to_run}\n")

    # Run selected stages
    if 1 in stages_to_run:
        run_stage_1()

    if 2 in stages_to_run:
        run_stage_2()

    if 3 in stages_to_run:
        run_stage_3()

    # Final summary
    print_banner("PIPELINE COMPLETE")
    print("Output locations:")
    print(f"  Word files:     02_stage1_docx/")
    print(f"  Raw Markdown:   03_stage2_raw_md/")
    print(f"  Clean Markdown: 04_stage3_clean_md/")


if __name__ == "__main__":
    main()
