# legos
building blocks - rip wrap and ship

## Google OSS License Page Architecture

This project reverse-engineers Google's OSS license page architecture using the "Blob+Map" pattern for efficient lazy-loading of license data.

### Architecture Overview

The system consists of two main components:

1. **ingest.py**: Playwright-based scraper that extracts license data
2. **build.py**: Converter that implements the Blob+Map pattern

#### The Blob+Map Pattern

This pattern enables efficient lazy-loading:
- **licenses.txt** (The Blob): Monolithic file containing all license text
- **index.json** (The Map): Lightweight index with byte offsets for O(1) lookups

Benefits:
- Load only small index initially (~few KB)
- Fetch individual licenses on-demand using byte-range requests
- Efficient memory usage and fast lookups

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
```

### Usage

#### Step 1: Scrape License Data

```bash
# Basic usage (with manual authentication)
python ingest.py https://example.com/licenses licenses.jsonl

# Headless mode (no GUI, for already-authenticated sources)
python ingest.py https://example.com/licenses licenses.jsonl --headless
```

The scraper will:
- Open a browser window
- Navigate to the target URL
- Pause for manual authentication if needed
- Extract all license list items
- Save to JSONL format

#### Step 2: Build Blob+Map

```bash
# Convert JSONL to Blob+Map pattern
python build.py licenses.jsonl output/

# This creates:
#   output/licenses.txt - The monolithic blob
#   output/index.json   - The byte offset index
```

#### Step 3: Demonstrate Lazy Loading

```bash
# Lookup a specific license by ID
python build.py --demo output/index.json output/licenses.txt 0
```

### Example Workflow

```bash
# 1. Scrape licenses
python ingest.py https://opensource.google/projects licenses.jsonl

# 2. Build the Blob+Map
python build.py licenses.jsonl output/

# 3. Demo lazy-loading
python build.py --demo output/index.json output/licenses.txt 0
```

### Output Format

**licenses.jsonl** (intermediate format):
```json
{"id": 0, "name": "Package Name", "content": "License text...", "license_type": "MIT"}
{"id": 1, "name": "Another Package", "content": "More license text...", "license_type": "Apache-2.0"}
```

**index.json** (map):
```json
{
  "version": "1.0",
  "total_licenses": 100,
  "blob_file": "licenses.txt",
  "encoding": "utf-8",
  "entries": [
    {
      "id": 0,
      "name": "Package Name",
      "offset": 0,
      "length": 1234,
      "license_type": "MIT"
    }
  ]
}
```

**licenses.txt** (blob):
```
License text for package 1...
================================================================================
License text for package 2...
```

### Features

- **Production-ready error handling**: Comprehensive try-catch blocks and error messages
- **Authentication support**: Pauses for manual login when needed
- **Flexible scraping**: Tries multiple selector patterns
- **UTF-8 encoding**: Proper handling of international characters
- **Lazy-loading demo**: Shows how to efficiently lookup licenses
- **Minimal dependencies**: Only requires Playwright 
