# PDF-to-Markdown Pipeline

A modular document ingestion pipeline that converts PDF medical records into clean, structured Markdown optimized for RAG systems like NotebookLM.

## Requirements

- macOS with Adobe Acrobat Pro installed
- Python 3 with PyYAML (`pip install pyyaml`)
- Pandoc (`brew install pandoc`)

## Setup

**First run only:** Grant Terminal automation permissions for Adobe Acrobat:
1. Run `python3 pdf_to_word.py` — macOS will prompt for permission
2. Click **OK** to allow Terminal to control Adobe Acrobat
3. (Or pre-authorize via **System Settings > Privacy & Security > Automation**)

## Usage

### Step 1: Add PDFs
Place your source PDF files in the `01_input_pdfs/` folder.

### Step 2: Run the Pipeline

**Option A: Run all stages at once**
```bash
python3 run_pipeline.py
```

**Option B: Run stages individually**
```bash
python3 pdf_to_word.py    # Stage 1: PDF → Word via Adobe Acrobat
python3 word_to_md.py     # Stage 2: Word → Markdown via Pandoc
python3 clean_md.py       # Stage 3: Applies regex cleanup rules
```

**Option C: Run specific stages**
```bash
python3 run_pipeline.py --stage 2 --stage 3  # Skip Stage 1
```

### Step 3: Retrieve Output
Cleaned Markdown files are in `04_stage3_clean_md/`, ready for NotebookLM.

## Batch Processing (Large Folders)

The pipeline is designed for large batches (1000+ files):

- **Auto-retry:** Failed conversions retry up to 2 times with increasing delays
- **Periodic restart:** Acrobat restarts every 10 files to prevent degradation
- **Emergency recovery:** Full Acrobat restart after consecutive failures
- **Resumable:** Re-running skips already-converted files

## Folder Structure

| Folder | Contents |
|--------|----------|
| `01_input_pdfs/` | Source PDFs (input) |
| `02_stage1_docx/` | Word files from Acrobat |
| `03_stage2_raw_md/` | Raw Markdown from Pandoc |
| `04_stage3_clean_md/` | Final cleaned Markdown |

## Customizing Regex Rules

Edit `config_regex.yaml` to add or modify cleanup rules. Each rule has:
- `name`: Description of the rule
- `find`: Regex pattern to match
- `replace`: Replacement string (use `\1`, `\2` for capture groups)

Default rule converts dates (e.g., "12/05/2023") into Markdown headers for timeline generation.
