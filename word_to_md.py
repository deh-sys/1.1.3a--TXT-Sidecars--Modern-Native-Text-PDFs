#!/usr/bin/env python3
"""
Stage 2: The Converter
Converts Word (.docx) files to Markdown using Pandoc.
CRITICAL: Uses --wrap=none to preserve tables for NotebookLM.

Supports parallel processing for large batches.

Usage:
    python3 word_to_md.py --input /path/to/pdf/folder
    python3 word_to_md.py --input /path/to/folder --workers 8
"""

import argparse
import subprocess
from multiprocessing import Pool, cpu_count
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
            return False
        return True
    except subprocess.TimeoutExpired:
        return False
    except FileNotFoundError:
        return False
    except Exception:
        return False


def _convert_single_file(args: tuple) -> tuple:
    """
    Worker function for parallel processing.
    Args: (docx_path, output_path) tuple
    Returns: (status, filename) tuple where status is 'success', 'skipped', or 'failed'
    """
    docx_path, output_path = args

    # Skip if output already exists
    if output_path.exists():
        return ('skipped', docx_path.name)

    # Convert
    if convert_word_to_markdown(docx_path, output_path):
        return ('success', docx_path.name)
    return ('failed', docx_path.name)


def run(input_dir: Path, workers: int = None) -> dict:
    """
    Run Stage 2: Word to Markdown conversion.

    Args:
        input_dir: Path to folder containing PDF files (reads from _stage1_docx subfolder)
        workers: Number of parallel workers (default: CPU cores - 1)

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

    # Determine worker count
    if workers is None:
        workers = max(1, cpu_count() - 1)

    print(f"\nFound {len(docx_files)} Word file(s) to process.")
    print(f"Using {workers} parallel worker(s).\n")

    # Build work items
    work_items = [
        (docx_path, output_dir / f"{docx_path.stem}.md")
        for docx_path in docx_files
    ]

    # Process files
    if workers == 1:
        # Sequential processing (preserves detailed output)
        results = []
        for i, (docx_path, output_path) in enumerate(work_items, 1):
            print(f"[{i}/{len(work_items)}] {docx_path.name}")
            if output_path.exists():
                print(f"  Skipping... (output already exists)")
                results.append(('skipped', docx_path.name))
            else:
                print(f"  Converting to Markdown...")
                if convert_word_to_markdown(docx_path, output_path):
                    print(f"  Success: {output_path.name}")
                    results.append(('success', docx_path.name))
                else:
                    print(f"  Failed: {docx_path.name}")
                    results.append(('failed', docx_path.name))
    else:
        # Parallel processing
        print("Processing files in parallel...")
        with Pool(workers) as pool:
            results = pool.map(_convert_single_file, work_items)

        # Print summary of results
        for status, filename in results:
            if status == 'success':
                print(f"  ✓ {filename}")
            elif status == 'failed':
                print(f"  ✗ {filename}")

    # Count results
    success_count = sum(1 for r in results if r[0] == 'success')
    skip_count = sum(1 for r in results if r[0] == 'skipped')
    fail_count = sum(1 for r in results if r[0] == 'failed')

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
    parser.add_argument(
        "-w", "--workers",
        type=int,
        default=None,
        help=f"Number of parallel workers (default: {max(1, cpu_count() - 1)})"
    )
    args = parser.parse_args()

    if not args.input.is_dir():
        print(f"Error: {args.input} is not a valid directory")
        return

    run(args.input, workers=args.workers)


if __name__ == "__main__":
    main()
