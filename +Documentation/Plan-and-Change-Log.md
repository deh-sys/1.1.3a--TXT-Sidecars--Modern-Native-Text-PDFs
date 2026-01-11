# Project Plan and Change Log

## Project Overview

**Project Name:** PDF-to-Markdown Pipeline
**Purpose:** Convert complex PDF medical records into clean, structured Markdown for RAG (Retrieval-Augmented Generation) systems, specifically optimized for NotebookLM timeline generation.

**Problem Solved:** Medical records in PDF format are difficult to process for AI systems. This pipeline leverages Adobe Acrobat's superior PDF parsing (especially for complex layouts and tables) combined with Pandoc's Markdown conversion to produce clean, AI-ready text.

## Architecture

### Design Philosophy
- **Modular:** Three independent scripts that can be run separately or in sequence
- **Resumable:** Each script skips files that already have output, allowing safe re-runs
- **Configurable:** Regex cleanup rules are externalized to YAML for easy customization
- **Safe:** Built-in delays prevent Adobe Acrobat from freezing during batch processing

### Pipeline Stages

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  01_input_pdfs  │────▶│ 02_stage1_docx  │────▶│ 03_stage2_raw_md│
│     (PDFs)      │     │    (Word)       │     │   (Markdown)    │
└─────────────────┘     └─────────────────┘     └─────────────────┘
        │                       │                       │
        ▼                       ▼                       ▼
   pdf_to_word.py         word_to_md.py           clean_md.py
   (AppleScript/          (Pandoc with            (Regex from
    Acrobat)              --wrap=none)             YAML config)
                                                        │
                                                        ▼
                                                ┌─────────────────┐
                                                │04_stage3_clean_md│
                                                │ (Final Output)  │
                                                └─────────────────┘
```

### File Descriptions

| File | Technology | Purpose |
|------|------------|---------|
| `run_pipeline.py` | Python | Router script to run all stages in sequence |
| `pdf_to_word.py` | Python + AppleScript + Adobe Acrobat | Converts PDFs to Word using Acrobat's high-quality export |
| `word_to_md.py` | Python + Pandoc | Converts Word to Markdown with `--wrap=none` to preserve tables |
| `clean_md.py` | Python + PyYAML + regex | Applies configurable regex transformations |
| `config_regex.yaml` | YAML | External configuration for regex rules |

### Key Technical Decisions

1. **Adobe Acrobat via AppleScript:** Acrobat provides superior PDF parsing compared to open-source alternatives, especially for scanned documents and complex tables.

2. **Word as intermediate format:** The PDF→Word→Markdown path preserves more structure than direct PDF→Markdown conversion.

3. **Pandoc with `--wrap=none`:** This flag is critical—it prevents Pandoc from wrapping lines, which would break table formatting for NotebookLM.

4. **External YAML config:** Regex rules can be modified without touching Python code, enabling non-developers to customize cleanup.

5. **Delays between files:** Prevents Adobe Acrobat from becoming unresponsive during batch processing.

6. **JavaScript saveAs() for synchronous saving:** Acrobat's native AppleScript `save` command returns before the file is fully written. Using `do script` with JavaScript ensures the save completes before proceeding.

7. **Periodic Acrobat restart:** Acrobat's AppleScript interface degrades over time. Restarting every N files prevents accumulating instability.

## Current Status

**Version:** 1.3
**Status:** Complete and production-ready for large batches

### Implemented Features
- [x] PDF to Word conversion via Adobe Acrobat
- [x] Word to Markdown conversion via Pandoc
- [x] Regex-based Markdown cleanup
- [x] External YAML configuration for regex rules
- [x] Skip-if-exists logic for all scripts (resumable)
- [x] Progress reporting and summaries
- [x] Default date-to-header regex rule for timeline generation
- [x] Synchronous file saving via JavaScript `saveAs()`
- [x] Auto-retry with escalating delays (10s, 15s)
- [x] Periodic Acrobat restart every 10 files
- [x] Emergency restart after consecutive failures
- [x] Pipeline router script (`run_pipeline.py`) with stage selection
- [x] Flexible input folder via `--input` argument
- [x] Output to `Sidecar Files/` subfolder
- [x] Green Finder tags on final .md files

### Known Limitations
- Requires macOS (AppleScript dependency)
- Requires licensed Adobe Acrobat Pro
- First run requires manual approval of automation permissions

---

## Change Log

### v1.3 — 2026-01-10
**Flexible Input + Sidecar Output + Finder Tags**

- All scripts now accept `--input` argument for specifying any folder
- Intermediate files stored in `_stage1_docx/` and `_stage2_raw_md/` subfolders
- Final output goes to `Sidecar Files/` subfolder
- Green Finder tags automatically applied to final .md files
- Updated documentation with new usage instructions

### v1.2 — 2026-01-10
**Pipeline Router**

- Added `run_pipeline.py` to run all stages with a single command
- Supports `--stage` flag to run specific stages only
- Updated documentation with new usage options

### v1.1 — 2026-01-10
**Robustness Update for Large Batches**

- Fixed corrupted .docx files by using JavaScript `saveAs()` for synchronous saving
- Added auto-retry logic (retry 1: 10s, retry 2: 15s)
- Added periodic Acrobat restart every 10 files to prevent degradation
- Added emergency Acrobat restart after all retries fail
- Added external `acrobat_export.scpt` for reliable AppleScript execution
- Increased timeout to 180s for large files

### v1.0 — 2026-01-10
**Initial Release**

- Created modular 3-script pipeline architecture
- Implemented `pdf_to_word.py` with AppleScript/Acrobat integration
- Implemented `word_to_md.py` with Pandoc and `--wrap=none` flag
- Implemented `clean_md.py` with YAML-configurable regex rules
- Created `config_regex.yaml` with default date-to-header rule
- Created folder structure for pipeline stages
- Added documentation
