#!/usr/bin/env python3
"""
Script 3: The Optimizer
Applies regex transformations to Markdown files for NotebookLM optimization.
Loads rules from config_regex.yaml.
"""

import re
from pathlib import Path

import yaml

# Directory configuration
SCRIPT_DIR = Path(__file__).parent
INPUT_DIR = SCRIPT_DIR / "03_stage2_raw_md"
OUTPUT_DIR = SCRIPT_DIR / "04_stage3_clean_md"
CONFIG_FILE = SCRIPT_DIR / "config_regex.yaml"


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
        name = rule.get("name", "Unnamed rule")
        find_pattern = rule.get("find", "")
        replace_pattern = rule.get("replace", "")

        if not find_pattern:
            print(f"  Skipping rule '{name}': no 'find' pattern")
            continue

        try:
            content = re.sub(find_pattern, replace_pattern, content)
        except re.error as e:
            print(f"  ERROR in rule '{name}': {e}")

    return content


def clean_markdown(input_path: Path, output_path: Path, rules: list) -> bool:
    """
    Apply regex rules to a Markdown file.
    Returns True on success, False on failure.
    """
    try:
        with open(input_path, "r", encoding="utf-8") as f:
            content = f.read()

        cleaned_content = apply_rules(content, rules)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(cleaned_content)

        return True
    except Exception as e:
        print(f"  ERROR: {e}")
        return False


def main():
    print("=" * 60)
    print("Markdown Cleaner (Regex Optimizer)")
    print("=" * 60)

    # Ensure directories exist
    INPUT_DIR.mkdir(exist_ok=True)
    OUTPUT_DIR.mkdir(exist_ok=True)

    # Load regex rules
    rules = load_regex_rules()
    print(f"\nLoaded {len(rules)} regex rule(s) from config.")
    for rule in rules:
        print(f"  - {rule.get('name', 'Unnamed')}: {rule.get('description', '')}")

    # Get list of Markdown files
    md_files = sorted(INPUT_DIR.glob("*.md"))

    if not md_files:
        print(f"\nNo Markdown files found in {INPUT_DIR}")
        print("Run word_to_md.py first to generate Markdown files.")
        return

    print(f"\nFound {len(md_files)} Markdown file(s) to process.\n")

    success_count = 0
    skip_count = 0
    fail_count = 0

    for i, md_path in enumerate(md_files, 1):
        output_path = OUTPUT_DIR / md_path.name

        print(f"[{i}/{len(md_files)}] {md_path.name}")

        # Check if output already exists
        if output_path.exists():
            print(f"  Skipping... (output already exists)")
            skip_count += 1
            continue

        print(f"  Applying regex rules...")
        if clean_markdown(md_path, output_path, rules):
            print(f"  Success: {output_path.name}")
            success_count += 1
        else:
            fail_count += 1

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  Cleaned:  {success_count}")
    print(f"  Skipped:  {skip_count}")
    print(f"  Failed:   {fail_count}")
    print(f"\nOutput folder: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
