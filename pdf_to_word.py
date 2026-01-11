#!/usr/bin/env python3
"""
Script 1: The Acrobat Bridge
Converts PDFs to Word (.docx) using Adobe Acrobat's AppleScript interface.

Uses external acrobat_export.scpt which invokes Acrobat's JavaScript saveAs()
for synchronous (blocking) file writes.
"""

import subprocess
import time
from pathlib import Path

# Directory configuration
SCRIPT_DIR = Path(__file__).parent
INPUT_DIR = SCRIPT_DIR / "01_input_pdfs"
OUTPUT_DIR = SCRIPT_DIR / "02_stage1_docx"
APPLESCRIPT_FILE = SCRIPT_DIR / "acrobat_export.scpt"

# Delay between files to prevent Acrobat from freezing
DELAY_SECONDS = 5

# Restart Acrobat every N files to prevent degradation
RESTART_EVERY = 10


def restart_acrobat():
    """Quit and restart Adobe Acrobat to reset its state."""
    print("  >> Restarting Adobe Acrobat...")
    # Quit Acrobat
    subprocess.run(
        ["osascript", "-e", 'tell application "Adobe Acrobat" to quit'],
        capture_output=True,
        timeout=30
    )
    time.sleep(5)
    # Activate will relaunch it on next conversion
    print("  >> Acrobat restarted.")


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
            timeout=180  # 3 minutes for large files
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


def main():
    print("=" * 60)
    print("PDF to Word Converter (Adobe Acrobat)")
    print("=" * 60)

    # Ensure directories exist
    INPUT_DIR.mkdir(exist_ok=True)
    OUTPUT_DIR.mkdir(exist_ok=True)

    # Get list of PDFs
    pdf_files = sorted(INPUT_DIR.glob("*.pdf"))

    if not pdf_files:
        print(f"\nNo PDF files found in {INPUT_DIR}")
        print("Place PDF files in the 01_input_pdfs folder and run again.")
        return

    print(f"\nFound {len(pdf_files)} PDF file(s) to process.\n")

    success_count = 0
    skip_count = 0
    fail_count = 0
    files_since_restart = 0

    for i, pdf_path in enumerate(pdf_files, 1):
        output_path = OUTPUT_DIR / f"{pdf_path.stem}.docx"

        print(f"[{i}/{len(pdf_files)}] {pdf_path.name}")

        # Check if output already exists
        if output_path.exists():
            print(f"  Skipping... (output already exists)")
            skip_count += 1
            continue

        # Periodic restart to prevent Acrobat degradation
        if files_since_restart >= RESTART_EVERY:
            restart_acrobat()
            files_since_restart = 0

        print(f"  Converting to Word...")
        if convert_pdf_to_word(pdf_path, output_path):
            print(f"  Success: {output_path.name}")
            success_count += 1
            files_since_restart += 1
        else:
            # Retry 1: wait 10 seconds
            print(f"  Retry 1 in 10 seconds...")
            time.sleep(10)
            if convert_pdf_to_word(pdf_path, output_path):
                print(f"  Success on retry 1: {output_path.name}")
                success_count += 1
                files_since_restart += 1
            else:
                # Retry 2: wait 15 seconds
                print(f"  Retry 2 in 15 seconds...")
                time.sleep(15)
                if convert_pdf_to_word(pdf_path, output_path):
                    print(f"  Success on retry 2: {output_path.name}")
                    success_count += 1
                    files_since_restart += 1
                else:
                    # All retries failed - restart Acrobat and try once more
                    print(f"  All retries failed. Restarting Acrobat...")
                    restart_acrobat()
                    files_since_restart = 0
                    if convert_pdf_to_word(pdf_path, output_path):
                        print(f"  Success after restart: {output_path.name}")
                        success_count += 1
                        files_since_restart += 1
                    else:
                        fail_count += 1

        # Delay between files to prevent Acrobat from freezing
        if i < len(pdf_files):
            print(f"  Waiting {DELAY_SECONDS} seconds...")
            time.sleep(DELAY_SECONDS)

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
