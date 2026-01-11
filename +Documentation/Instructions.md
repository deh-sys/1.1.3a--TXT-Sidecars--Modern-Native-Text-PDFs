# PDF-to-Markdown Pipeline

A modular document ingestion pipeline that converts PDF medical records into clean, structured Markdown optimized for RAG systems like NotebookLM.

## Requirements

- macOS with Adobe Acrobat Pro installed
- Python 3 with PyYAML (`pip install pyyaml`)
- Pandoc (`brew install pandoc`)

## Setup

**First run only:** Grant Terminal automation permissions for Adobe Acrobat:
1. Run `python3 pdf_to_word.py --input /path/to/folder` — macOS will prompt for permission
2. Click **OK** to allow Terminal to control Adobe Acrobat
3. (Or pre-authorize via **System Settings > Privacy & Security > Automation**)

## Usage

### Step 1: Prepare Your Folder
Create a folder with your source PDF files (or use an existing folder).

### Step 2: Run the Pipeline

**Option A: Run all stages at once**
```bash
python3 run_pipeline.py --input /path/to/your/pdf/folder
```

**Option B: Run stages individually**
```bash
python3 pdf_to_word.py --input /path/to/folder    # Stage 1: PDF → Word
python3 word_to_md.py --input /path/to/folder     # Stage 2: Word → Markdown
python3 clean_md.py --input /path/to/folder       # Stage 3: Regex cleanup + green tags
```

**Option C: Run specific stages**
```bash
python3 run_pipeline.py -i /path/to/folder --stage 2 --stage 3  # Skip Stage 1
```

### Step 3: Retrieve Output
Cleaned Markdown files are in `Sidecar Files/` subfolder within your input folder.
Files are tagged with a green Finder tag for easy identification.

## Folder Structure

After running the pipeline on `/path/to/folder/`, the structure will be:

```
/path/to/folder/
├── file1.pdf              # Your original PDFs
├── file2.pdf
├── _stage1_docx/          # Intermediate: Word files
│   ├── file1.docx
│   └── file2.docx
├── _stage2_raw_md/        # Intermediate: Raw Markdown
│   ├── file1.md
│   └── file2.md
└── Sidecar Files/         # Final output (with green Finder tags)
    ├── file1.md
    └── file2.md
```

## Batch Processing (Large Folders)

The pipeline is designed for large batches (1000+ files):

- **Auto-retry:** Failed conversions retry up to 2 times with increasing delays
- **Periodic restart:** Acrobat restarts every 10 files to prevent degradation
- **Emergency recovery:** Full Acrobat restart after consecutive failures
- **Resumable:** Re-running skips already-converted files

## Customizing Regex Rules

Edit `config_regex.yaml` to add or modify cleanup rules. Each rule has:
- `name`: Description of the rule
- `find`: Regex pattern to match
- `replace`: Replacement string (use `\1`, `\2` for capture groups)

Default rule converts dates (e.g., "12/05/2023") into Markdown headers for timeline generation.
