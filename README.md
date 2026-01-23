# legos
building blocks - rip wrap and ship

## Google OSS License Page Architecture + LLM-Powered RAG System

This project reverse-engineers Google's OSS license page architecture using the "Blob+Map" pattern for efficient lazy-loading of license data, enhanced with an **Active RAG (Retrieval-Augmented Generation) system** for AI-powered license analysis.

### Architecture Overview

The system consists of **two layers**:

#### Layer 1: Static Archive (Blob+Map Pattern)
1. **ingest.py**: Playwright-based scraper that extracts license data
2. **build.py**: Converter that implements the Blob+Map pattern

#### Layer 2: Active RAG System (LLM Integration)
3. **server.py**: FastAPI backend with ChromaDB vector storage
4. **index.html**: Dual-pane UI (Google-style list + AI Analyst chat)

### The Blob+Map Pattern

This pattern enables efficient lazy-loading:
- **licenses.txt** (The Blob): Monolithic file containing all license text
- **index.json** (The Map): Lightweight index with byte offsets for O(1) lookups

Benefits:
- Load only small index initially (~few KB)
- Fetch individual licenses on-demand using byte-range requests
- Efficient memory usage and fast lookups

### The RAG System

The RAG layer adds intelligent analysis capabilities:
- **Vector Search**: ChromaDB indexes license text for semantic search
- **LLM Analysis**: GPT-4 provides compliance insights and risk assessment
- **Dual Interface**: Browse licenses (left) + Chat with AI analyst (right)

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers (for scraping)
playwright install chromium

# Set OpenAI API key (for RAG features)
export OPENAI_API_KEY="sk-..."

# Optional: Configure CORS for production
export ALLOWED_ORIGINS="https://yourdomain.com,https://app.yourdomain.com"

# Optional: Use different models
export MODEL_CHAT="gpt-4o"        # For interactive chat
export MODEL_AUDIT="gpt-4o-mini"  # For bulk analysis
```

### Configuration

The RAG system supports the following environment variables:

- `OPENAI_API_KEY` - OpenAI API key (required for LLM features)
- `ALLOWED_ORIGINS` - Comma-separated list of allowed CORS origins (default: `*`)
- `MODEL_CHAT` - Model for interactive chat (default: `gpt-4o`)
- `MODEL_AUDIT` - Model for risk audits (default: `gpt-4o-mini`)

Data persistence:
- ChromaDB stores vectors in `./chroma_db/` for persistence across restarts
- Add to `.gitignore` to avoid committing large vector databases


### Usage

#### Workflow 1: Static Archive (Blob+Map)

##### Step 1: Scrape License Data

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

##### Step 2: Build Blob+Map

```bash
# Convert JSONL to Blob+Map pattern
python build.py licenses.jsonl output/

# This creates:
#   output/licenses.txt - The monolithic blob
#   output/index.json   - The byte offset index
```

##### Step 3: Demonstrate Lazy Loading

```bash
# Lookup a specific license by ID
python build.py --demo output/index.json output/licenses.txt 0
```

#### Workflow 2: Active RAG System

##### Step 1: Scrape and prepare data

```bash
# Scrape licenses (same as above)
python ingest.py https://opensource.google/projects licenses.jsonl
```

##### Step 2: Start the RAG server

```bash
# The server will automatically ingest licenses.jsonl on startup
export OPENAI_API_KEY="sk-..."
python server.py
```

The server provides:
- `GET /` - Health check and status
- `GET /licenses` - List all licenses (for UI)
- `POST /chat` - Ask questions about licenses
- `POST /generate_ideas` - Generate comprehensive risk audit

##### Step 3: Open the UI

```bash
# Open index.html in your browser
open index.html
# Or navigate to file:///path/to/index.html
```

The UI features:
- **Left Panel**: Google-style license list with lazy loading
- **Right Panel**: AI Compliance Analyst chat interface
- **Audit Button**: One-click comprehensive risk assessment

### Example Questions for the AI Analyst

```
- "Which libraries have viral licenses?"
- "Show me all MIT licensed packages"
- "Are there any GPL dependencies?"
- "What are the compliance requirements for commercial use?"
- "Which licenses require attribution?"
- "Identify any security risks in our dependencies"
```

### Complete Example Workflow

```bash
# 1. Scrape licenses from Google's OSS page
python ingest.py https://opensource.google/projects licenses.jsonl

# 2. (Optional) Build static Blob+Map for serving
python build.py licenses.jsonl output/

# 3. Start the RAG server
export OPENAI_API_KEY="sk-..."
python server.py

# 4. Open index.html in browser and start chatting!
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

### API Endpoints

#### `GET /`
Health check and system status.

**Response:**
```json
{
  "status": "ok",
  "service": "License RAG API",
  "openai_enabled": true,
  "indexed_licenses": 42
}
```

#### `GET /licenses`
Returns list of all licenses for the UI.

**Response:**
```json
[
  {
    "library": "requests",
    "preview": "Apache License\nVersion 2.0..."
  }
]
```

#### `POST /chat`
Ask questions about licenses using RAG.

**Request:**
```json
{
  "message": "Which libraries use GPL licenses?"
}
```

**Response:**
```json
{
  "reply": "Based on the license data, the following libraries use GPL licenses: ..."
}
```

#### `POST /generate_ideas`
Generate comprehensive risk audit.

**Response:**
```json
{
  "analysis": "<html>Detailed risk assessment...</html>"
}
```

### Features

**Static Archive (Blob+Map):**
- ✅ Production-ready error handling
- ✅ Authentication support
- ✅ Flexible scraping with multiple selector patterns
- ✅ UTF-8 encoding for international characters
- ✅ Lazy-loading demo
- ✅ Minimal dependencies

**RAG System:**
- ✅ Vector search with ChromaDB
- ✅ Semantic similarity matching
- ✅ GPT-4 powered analysis
- ✅ Proactive risk auditing
- ✅ Reactive Q&A system
- ✅ Beautiful dual-pane UI
- ✅ Real-time chat interface

### Architecture Benefits

1. **Separation of Concerns**: Static archive can be used independently
2. **Scalability**: Vector DB handles large license datasets efficiently
3. **Intelligence**: LLM provides insights beyond simple keyword search
4. **User Experience**: Combines Google's UX patterns with modern AI
5. **Flexibility**: Easy to swap LLM providers (OpenAI → Ollama/Local)

### Requirements

- Python 3.8+
- OpenAI API key (for RAG features)
- Modern web browser (for UI)

### License

This is a demonstration project for reverse-engineering Google's architecture patterns. 
