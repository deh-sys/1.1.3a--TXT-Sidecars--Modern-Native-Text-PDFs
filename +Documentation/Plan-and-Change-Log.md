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

7. **Background operation:** Uses `open -g` flag to prevent Acrobat from stealing focus during batch processing.

## Current Status

**Version:** 1.8.2
**Status:** Complete and production-ready for large batches (2000+ files)

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
- [x] Emergency force-kill after all retries fail (rare)
- [x] Pipeline router script (`run_pipeline.py`) with stage selection
- [x] Flexible input folder via `--input` argument
- [x] Output to `Sidecar Files/` subfolder
- [x] Green Finder tags on final .md files
- [x] Medical heading detection (IMRAD, clinical, patient education, Q&A, case reports, back matter, ALL CAPS)
- [x] Parallel processing for Stages 2 and 3 (configurable via `--workers`)
- [x] Sleep prevention via macOS `caffeinate` (auto-enabled, disable with `--no-caffeinate`)
- [x] ETA display during Stage 1 processing
- [x] Force-kill Acrobat to handle modal dialog states (JS debugger, etc.)
- [x] Circuit breaker: auto-abort after 5 consecutive failures
- [x] Failed files manifest (`_failed_pdfs.txt`) for review/retry
- [x] Background operation: Acrobat no longer steals focus during batch processing (uses `open -g`)

### Known Limitations
- Requires macOS (AppleScript dependency)
- Requires licensed Adobe Acrobat Pro
- First run requires manual approval of automation permissions

---

## Change Log

### v1.8.2 — 2026-01-11
**Fix System Events Error**

- Removed System Events hide command (was causing `-10006` errors)
- The `open -g` flag alone is sufficient for background operation
- Fixes spurious force-kills triggered by AppleScript errors

### v1.8.1 — 2026-01-11
**Remove Periodic Restart**

- Removed periodic Acrobat restart (was every 10 files, caused focus stealing on relaunch)
- Force-kill now only used for failure recovery (rare)
- Retry logic and circuit breaker provide sufficient protection without proactive restarts

### v1.8 — 2026-01-11
**Background Operation (No Focus Stealing)**

- Acrobat no longer steals focus when opening each PDF
- Replaced AppleScript `open` with `open -g` (background flag)
- Removed `activate` command from AppleScript
- Added System Events hide as fallback to prevent any focus flicker
- Computer now usable for other tasks during multi-hour batch runs

### v1.7 — 2026-01-11
**Acrobat Hang Recovery**

- **Force-kill Acrobat** using `pkill -9` instead of polite AppleScript quit (handles modal states like JS debugger)
- **Circuit breaker**: Auto-abort after 5 consecutive failures to prevent infinite loops
- **Failed files manifest**: Writes `_failed_pdfs.txt` to output folder for later review/retry
- Fixed issue where JavaScript Debugger popup would block all AppleScript commands indefinitely
- Recommendation: Disable Acrobat's JS debugger in Preferences → JavaScript

### v1.6 — 2026-01-11
**Large Batch Optimization**

- Added parallel processing for Stage 2 (Word→Markdown) and Stage 3 (Clean Markdown)
- New `--workers` flag to set number of parallel workers (default: CPU cores - 1)
- Added sleep prevention via macOS `caffeinate` (auto-enabled by default)
- New `--no-caffeinate` flag to disable sleep prevention
- Added ETA display during Stage 1 processing
- Stages 2 and 3 now show parallel processing status and worker count
- Sequential mode (workers=1) preserves detailed per-file output

### v1.5 — 2026-01-11
**Expanded Medical Heading Detection**

- Added patient education patterns (MedlinePlus/Mayo Clinic style): Start Here, Diagnosis and Tests, Related Issues, Genetics, Clinical Trials, Find an Expert, Patient Handouts, Medical Encyclopedia
- Added Q&A patterns: "What are X?", "What is X?", "How does X?", "Types of X", "Alternative Names"
- Added clinical terms: Pathogenesis, Complications
- Added structure terms: Summary, Future Directions
- Added back matter terms: Abbreviations, Keywords
- Improved ALL CAPS heuristic: filters out sentences (>12 words or ends with period)

### v1.4 — 2026-01-11
**Medical Heading Detection**

- Added built-in medical heading detection using line-by-line processing with priority ordering
- Detects IMRAD structure (Abstract, Introduction, Methods, Results, Discussion, Conclusions)
- Detects clinical headings (Diagnosis, Treatment, Management, Prognosis, etc.)
- Detects case reports (Case Report, Case 1, Case Presentation)
- Detects back matter with separator (References, Acknowledgments, Disclosures)
- ALL CAPS fallback heuristic with noise filtering (Copyright, DOI, ISSN excluded)
- Medical headings run before YAML regex rules, so custom rules still apply

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
