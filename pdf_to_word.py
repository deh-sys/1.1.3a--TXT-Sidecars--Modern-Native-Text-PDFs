#!/usr/bin/env python3
"""
Stage 1: The Acrobat Bridge
Converts PDFs to Word (.docx) using Adobe Acrobat's AppleScript interface.

Uses external acrobat_export.scpt which invokes Acrobat's JavaScript saveAs()
for synchronous (blocking) file writes.

Usage:
    python3 pdf_to_word.py --input /path/to/pdf/folder
"""

import argparse
import subprocess
import time
from datetime import timedelta
from pathlib import Path

# Directory configuration
SCRIPT_DIR = Path(__file__).parent
APPLESCRIPT_FILE = SCRIPT_DIR / "acrobat_export.scpt"

# Delay between files to prevent Acrobat from freezing
DELAY_SECONDS = 5

# Abort after this many consecutive failures (indicates systemic issue)
MAX_CONSECUTIVE_FAILURES = 5


def force_kill_acrobat():
    """Force-kill Adobe Acrobat (handles modal dialog states like JS debugger)."""
    print("  >> Force-killing Adobe Acrobat...")
    subprocess.run(["pkill", "-9", "-f", "Adobe Acrobat"], capture_output=True)
    time.sleep(5)
    print("  >> Acrobat terminated.")


def convert_pdf_to_word(pdf_path: Path, output_path: Path) -> bool:
    """
    Convert a PDF to Word using Adobe Acrobat via external AppleScript.
    Uses JavaScript saveAs() for synchronous saving.
    Returns True on success, False on failure.
    """
    try:
        result = subprocess.run(
            ["osascript", str(APPLESCRIPT_FILE), str(pdf_path), str(output_path)],
            capture_output=True,
            text=True,
            timeout=180
        )
        if result.returncode != 0:
            print(f"  ERROR: {result.stderr.strip()}")
            return False
        return True
    except subprocess.TimeoutExpired:
        print("  ERROR: Conversion timed out (180s)")
        return False
    except Exception as e:
        print(f"  ERROR: {e}")
        return False


def run(input_dir: Path) -> dict:
    """
    Run Stage 1: PDF to Word conversion.

    Args:
        input_dir: Path to folder containing PDF files

    Returns:
        dict with counts: {'converted': N, 'skipped': N, 'failed': N}
    """
    output_dir = input_dir / "_stage1_docx"

    print("=" * 60)
    print("STAGE 1: PDF → Word (Adobe Acrobat)")
    print("=" * 60)
    print(f"Input:  {input_dir}")
    print(f"Output: {output_dir}")

    # Ensure output directory exists
    output_dir.mkdir(exist_ok=True)

    # Get list of PDFs
    pdf_files = sorted(input_dir.glob("*.pdf"))

    if not pdf_files:
        print(f"\nNo PDF files found in {input_dir}")
        return {'converted': 0, 'skipped': 0, 'failed': 0}

    print(f"\nFound {len(pdf_files)} PDF file(s) to process.\n")

    success_count = 0
    skip_count = 0
    fail_count = 0
    start_time = time.time()
    processed_count = 0  # Track actually processed files for ETA
    consecutive_failures = 0  # Circuit breaker for systemic issues
    failed_files = []  # Log of failed file names

    for i, pdf_path in enumerate(pdf_files, 1):
        output_path = output_dir / f"{pdf_path.stem}.docx"

        # Calculate ETA based on processed files
        eta_str = ""
        if processed_count > 0:
            elapsed = time.time() - start_time
            avg_per_file = elapsed / processed_count
            remaining_files = len(pdf_files) - i + 1
            remaining_time = remaining_files * avg_per_file
            eta_str = f" | ETA: {str(timedelta(seconds=int(remaining_time)))}"

        print(f"[{i}/{len(pdf_files)}] {pdf_path.name}{eta_str}")

        # Check if output already exists
        if output_path.exists():
            print(f"  Skipping... (output already exists)")
            skip_count += 1
            continue

        print(f"  Converting to Word...")
        conversion_success = False

        if convert_pdf_to_word(pdf_path, output_path):
            print(f"  Success: {output_path.name}")
            conversion_success = True
        else:
            # Retry 1: wait 10 seconds
            print(f"  Retry 1 in 10 seconds...")
            time.sleep(10)
            if convert_pdf_to_word(pdf_path, output_path):
                print(f"  Success on retry 1: {output_path.name}")
                conversion_success = True
            else:
                # Retry 2: wait 15 seconds
                print(f"  Retry 2 in 15 seconds...")
                time.sleep(15)
                if convert_pdf_to_word(pdf_path, output_path):
                    print(f"  Success on retry 2: {output_path.name}")
                    conversion_success = True
                else:
                    # All retries failed - force-kill Acrobat and try once more
                    print(f"  All retries failed. Force-killing Acrobat...")
                    force_kill_acrobat()
                    if convert_pdf_to_word(pdf_path, output_path):
                        print(f"  Success after restart: {output_path.name}")
                        conversion_success = True

        # Track success/failure for circuit breaker
        if conversion_success:
            success_count += 1
            consecutive_failures = 0  # Reset circuit breaker
        else:
            fail_count += 1
            failed_files.append(pdf_path.name)
            consecutive_failures += 1

            # Circuit breaker: abort if too many consecutive failures
            if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                print(f"\n{'='*60}")
                print(f"ABORTING: {consecutive_failures} consecutive failures detected.")
                print("Acrobat may be stuck in a modal state (dialog, debugger, etc.)")
                print("Close any Acrobat dialogs and re-run to resume from where you left off.")
                print(f"{'='*60}\n")
                break

        processed_count += 1

        # Delay between files to prevent Acrobat from freezing
        if i < len(pdf_files):
            print(f"  Waiting {DELAY_SECONDS} seconds...")
            time.sleep(DELAY_SECONDS)

    # Summary
    print("\n" + "-" * 40)
    print(f"Stage 1 Complete: {success_count} converted, {skip_count} skipped, {fail_count} failed")

    # Log failed files to manifest
    if failed_files:
        failed_log = output_dir / "_failed_pdfs.txt"
        with open(failed_log, "w", encoding="utf-8") as f:
            f.write("\n".join(failed_files))
        print(f"Failed files logged to: {failed_log}")

    return {'converted': success_count, 'skipped': skip_count, 'failed': fail_count}


def main():
    parser = argparse.ArgumentParser(
        description="Stage 1: Convert PDFs to Word using Adobe Acrobat"
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
