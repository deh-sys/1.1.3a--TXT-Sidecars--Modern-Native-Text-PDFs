#!/usr/bin/env python3
"""
Stage 3: The Optimizer
Applies regex transformations to Markdown files for NotebookLM optimization.
Loads rules from config_regex.yaml.
Outputs to "Sidecar Files" folder with green Finder tags.

Supports parallel processing for large batches.

Usage:
    python3 clean_md.py --input /path/to/pdf/folder
    python3 clean_md.py --input /path/to/folder --workers 8
"""

import argparse
import plistlib
import re
import subprocess
from multiprocessing import Pool, cpu_count
from pathlib import Path

import yaml

# Directory configuration
SCRIPT_DIR = Path(__file__).parent
CONFIG_FILE = SCRIPT_DIR / "config_regex.yaml"

# Global rules variable for multiprocessing workers
_GLOBAL_RULES = []


def load_regex_rules() -> list:
    """Load regex rules from the YAML config file."""
    if not CONFIG_FILE.exists():
        print(f"WARNING: Config file not found: {CONFIG_FILE}")
        print("Creating default config file...")
        create_default_config()

    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    return config.get("rules", [])


def create_default_config():
    """Create a default config file with sample rules."""
    default_config = {
        "rules": [
            {
                "name": "Convert dates to headers",
                "description": "Add ### before dates for NotebookLM timeline generation",
                "find": r"(\d{1,2}/\d{1,2}/\d{4})",
                "replace": r"### \1"
            }
        ]
    }
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        yaml.dump(default_config, f, default_flow_style=False, sort_keys=False)
    print(f"Created: {CONFIG_FILE}")


def apply_rules(content: str, rules: list) -> str:
    """Apply all regex rules to the content."""
    for rule in rules:
        find_pattern = rule.get("find", "")
        replace_pattern = rule.get("replace", "")

        if not find_pattern:
            continue

        try:
            content = re.sub(find_pattern, replace_pattern, content)
        except re.error:
            pass

    return content


def mark_medical_headings(content: str) -> str:
    """
    Detect and mark medical document headings as Markdown headers.
    Uses line-by-line processing with priority ordering.

    Handles: Academic papers (IMRAD), clinical guidelines, patient education,
    Q&A formats, and case reports.
    """
    lines = content.split('\n')
    new_lines = []

    # 1. IMRAD structure (standard journal format)
    p_structure = re.compile(
        r'^\s*(?:\d+\.|[IVX]+\.)?\s*'
        r'(Abstract|Summary|Introduction|Background|Objectives?|Aims?|'
        r'Methods?|Materials\s+and\s+Methods|Patients\s+and\s+Methods|'
        r'Study\s+Design|Results?|Findings?|Discussion|Comments?|'
        r'Conclusion.*|Future\s+Directions)\s*$',
        re.IGNORECASE
    )

    # 2. Clinical & Causation headings (crucial for malpractice analysis)
    p_clinical = re.compile(
        r'^\s*(?:\d+\.|[IVX]+\.)?\s*'
        r'(Epidemiology|Etiology|Pathophysiology|Pathogenesis|'
        r'Clinical\s+Presentation|Diagnosis|Evaluation|Investigations|'
        r'Management|Treatment|Therapy|Prognosis|Complications|'
        r'Prevention|Recommendations?|Key\s+Points?)\s*$',
        re.IGNORECASE
    )

    # 3. Patient Education / MedlinePlus style
    p_patient_ed = re.compile(
        r'^\s*(Start\s+Here|Diagnosis\s+and\s+Tests?|Related\s+Issues|'
        r'Genetics|Clinical\s+Trials?|Journal\s+Articles?|'
        r'Find\s+an\s+Expert|Patient\s+Handouts?|Medical\s+Encyclopedia)\s*$',
        re.IGNORECASE
    )

    # 4. Q&A / Definition headers (e.g., "What are Fats?", "Types of fat")
    p_qa = re.compile(
        r'^\s*(What\s+are\s+.+\??|What\s+is\s+.+\??|How\s+does\s+.+\??|'
        r'Types\s+of\s+.+|Alternative\s+Names?)\s*$',
        re.IGNORECASE
    )

    # 5. Case reports
    p_case = re.compile(
        r'^\s*(Case\s+Report[s]?|Case\s+Presentation|Case\s+\d+(?:-\d+)?)\s*$',
        re.IGNORECASE
    )

    # 6. Back matter (meta-data to separate from clinical content)
    p_meta = re.compile(
        r'^\s*(References|Bibliography|Literature\s+Cited|'
        r'Abbreviations?|Key\s*words?|'
        r'Acknowledgments?|Disclosures?|Conflicts?\s+of\s+Interest|'
        r'Funding|Financial\s+Support|Author\s+Contributions)\s*$',
        re.IGNORECASE
    )

    # 7. ALL CAPS heuristic (with noise filtering)
    p_caps = re.compile(
        r'^(?!.*\b(Copyright|DOI|ISSN|Vol\.|Page)\b)[A-Z][A-Z0-9\s\-\(\):]{3,80}$'
    )

    for line in lines:
        clean = line.strip()
        if not clean:
            new_lines.append(line)
            continue

        # Skip lines that are already headers
        if clean.startswith('#'):
            new_lines.append(line)
            continue

        # Priority 1: High-confidence named sections → ## heading
        if (p_structure.match(clean) or p_clinical.match(clean) or
            p_patient_ed.match(clean) or p_case.match(clean) or p_qa.match(clean)):
            new_lines.append(f"\n## {clean}\n")

        # Priority 2: Back matter → --- separator + ### heading
        elif p_meta.match(clean):
            new_lines.append(f"\n---\n### {clean}\n")

        # Priority 3: ALL CAPS fallback (with sentence filtering)
        elif p_caps.match(clean) and not clean.replace('.', '').replace(' ', '').isdigit():
            # Sanity check: headers are typically short and don't end with period
            if len(clean.split()) < 12 and not clean.endswith('.'):
                new_lines.append(f"\n## {clean}\n")
            else:
                new_lines.append(line)

        else:
            new_lines.append(line)

    return '\n'.join(new_lines)


def set_finder_tag_green(file_path: Path):
    """Set a green Finder tag on a file using xattr."""
    try:
        # Green tag in macOS Finder format
        tag_data = plistlib.dumps(["Green\n2"])
        subprocess.run(
            ["xattr", "-w", "com.apple.metadata:_kMDItemUserTags", tag_data, str(file_path)],
            capture_output=True,
            check=True
        )
    except Exception:
        pass  # Silent fail for tags (non-critical)


def clean_markdown(input_path: Path, output_path: Path, rules: list) -> bool:
    """
    Apply medical heading detection and regex rules to a Markdown file.
    Returns True on success, False on failure.
    """
    try:
        with open(input_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Apply medical heading detection first
        content = mark_medical_headings(content)

        # Then apply YAML regex rules (dates, etc.)
        cleaned_content = apply_rules(content, rules)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(cleaned_content)

        # Apply green Finder tag
        set_finder_tag_green(output_path)

        return True
    except Exception:
        return False


def _clean_single_file(args: tuple) -> tuple:
    """
    Worker function for parallel processing.
    Args: (input_path, output_path) tuple
    Returns: (status, filename) tuple where status is 'success', 'skipped', or 'failed'
    """
    input_path, output_path = args

    # Skip if output already exists
    if output_path.exists():
        return ('skipped', input_path.name)

    # Clean
    if clean_markdown(input_path, output_path, _GLOBAL_RULES):
        return ('success', input_path.name)
    return ('failed', input_path.name)


def _init_worker(rules: list):
    """Initialize worker with shared rules."""
    global _GLOBAL_RULES
    _GLOBAL_RULES = rules


def run(input_dir: Path, workers: int = None) -> dict:
    """
    Run Stage 3: Markdown cleanup and tagging.

    Args:
        input_dir: Path to folder containing PDF files (reads from _stage2_raw_md subfolder)
        workers: Number of parallel workers (default: CPU cores - 1)

    Returns:
        dict with counts: {'converted': N, 'skipped': N, 'failed': N}
    """
    raw_md_dir = input_dir / "_stage2_raw_md"
    output_dir = input_dir / "Sidecar Files"

    print("=" * 60)
    print("STAGE 3: Clean Markdown + Green Tags")
    print("=" * 60)
    print(f"Input:  {raw_md_dir}")
    print(f"Output: {output_dir}")

    # Ensure output directory exists
    output_dir.mkdir(exist_ok=True)

    # Load regex rules
    rules = load_regex_rules()
    print(f"\nLoaded {len(rules)} regex rule(s) from config.")
    for rule in rules:
        print(f"  - {rule.get('name', 'Unnamed')}: {rule.get('description', '')}")

    # Check if input directory exists
    if not raw_md_dir.exists():
        print(f"\nStage 2 output folder not found: {raw_md_dir}")
        print("Run Stage 2 first.")
        return {'converted': 0, 'skipped': 0, 'failed': 0}

    # Get list of Markdown files
    md_files = sorted(raw_md_dir.glob("*.md"))

    if not md_files:
        print(f"\nNo Markdown files found in {raw_md_dir}")
        return {'converted': 0, 'skipped': 0, 'failed': 0}

    # Determine worker count
    if workers is None:
        workers = max(1, cpu_count() - 1)

    print(f"\nFound {len(md_files)} Markdown file(s) to process.")
    print(f"Using {workers} parallel worker(s).\n")

    # Build work items
    work_items = [
        (md_path, output_dir / md_path.name)
        for md_path in md_files
    ]

    # Process files
    if workers == 1:
        # Sequential processing (preserves detailed output)
        results = []
        for i, (md_path, output_path) in enumerate(work_items, 1):
            print(f"[{i}/{len(work_items)}] {md_path.name}")
            if output_path.exists():
                print(f"  Skipping... (output already exists)")
                results.append(('skipped', md_path.name))
            else:
                print(f"  Applying regex rules + green tag...")
                if clean_markdown(md_path, output_path, rules):
                    print(f"  Success: {output_path.name}")
                    results.append(('success', md_path.name))
                else:
                    print(f"  Failed: {md_path.name}")
                    results.append(('failed', md_path.name))
    else:
        # Parallel processing
        print("Processing files in parallel...")
        with Pool(workers, initializer=_init_worker, initargs=(rules,)) as pool:
            results = pool.map(_clean_single_file, work_items)

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
    print(f"Stage 3 Complete: {success_count} cleaned, {skip_count} skipped, {fail_count} failed")
    print(f"Output: {output_dir}")

    return {'converted': success_count, 'skipped': skip_count, 'failed': fail_count}


def main():
    parser = argparse.ArgumentParser(
        description="Stage 3: Clean Markdown and apply green Finder tags"
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
