#!/usr/bin/env python3
"""
Pipeline Router: Runs all conversion stages in sequence.

Supports parallel processing for Stages 2 and 3, and sleep prevention
via macOS caffeinate.

Usage:
    python3 run_pipeline.py --input /path/to/pdf/folder
    python3 run_pipeline.py -i /path/to/folder --stage 2 --stage 3
    python3 run_pipeline.py -i /path/to/folder --workers 8
"""

import argparse
import os
import subprocess
import sys
from multiprocessing import cpu_count
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


def start_caffeinate():
    """
    Start caffeinate to prevent system sleep during long runs.
    Returns the process handle (or None if caffeinate is unavailable).
    """
    try:
        # -i: Prevent idle sleep
        # -w: Wait for the specified process (this script) to exit
        proc = subprocess.Popen(
            ["caffeinate", "-i", "-w", str(os.getpid())],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        return proc
    except FileNotFoundError:
        # caffeinate not available (non-macOS)
        return None
    except Exception:
        return None


def stop_caffeinate(proc):
    """Stop the caffeinate process if it's running."""
    if proc is not None:
        try:
            proc.terminate()
            proc.wait(timeout=5)
        except Exception:
            pass


def main():
    parser = argparse.ArgumentParser(
        description="PDF-to-Markdown Pipeline Router",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Stages:
  1  PDF → Word     (uses Adobe Acrobat, sequential only)
  2  Word → Markdown (uses Pandoc, parallelizable)
  3  Clean Markdown  (uses regex rules, parallelizable)

Examples:
  python3 run_pipeline.py --input /path/to/folder
  python3 run_pipeline.py -i /path/to/folder --stage 2 --stage 3
  python3 run_pipeline.py -i /path/to/folder --workers 8
  python3 run_pipeline.py -i /path/to/folder --no-caffeinate
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
    parser.add_argument(
        "-w", "--workers",
        type=int,
        default=None,
        help=f"Number of parallel workers for Stages 2 and 3 (default: {max(1, cpu_count() - 1)})"
    )
    parser.add_argument(
        "--no-caffeinate",
        action="store_true",
        help="Disable sleep prevention (caffeinate) during run"
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

    # Determine worker count
    workers = args.workers if args.workers else max(1, cpu_count() - 1)

    # Start caffeinate to prevent sleep
    caffeinate_proc = None
    if not args.no_caffeinate:
        caffeinate_proc = start_caffeinate()

    try:
        print_banner("PDF-TO-MARKDOWN PIPELINE")
        print(f"Input folder: {input_dir}")
        print(f"Stages to run: {stages_to_run}")
        print(f"Parallel workers: {workers} (for Stages 2 and 3)")
        if caffeinate_proc:
            print(f"Sleep prevention: ENABLED (caffeinate)")
        else:
            print(f"Sleep prevention: disabled")
        print()

        results = {}

        # Run selected stages
        if 1 in stages_to_run:
            results[1] = pdf_to_word.run(input_dir)

        if 2 in stages_to_run:
            results[2] = word_to_md.run(input_dir, workers=workers)

        if 3 in stages_to_run:
            results[3] = clean_md.run(input_dir, workers=workers)

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

    finally:
        # Always stop caffeinate when done
        stop_caffeinate(caffeinate_proc)


if __name__ == "__main__":
    main()
