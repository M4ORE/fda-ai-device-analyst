# Usage Guide

## Data Update

### Auto-Update from FDA Website

```bash
run_update.bat
```

This script will:
- Download latest Excel file from FDA
- Compare with existing data
- Download new PDFs (510(k) and De Novo only)
- Re-download missing or corrupted PDFs
- Update SQLite database
- Create backup of old Excel file

**Note:** PMA (P-prefix) PDFs cannot be auto-downloaded as they use different URL patterns.

After update:
```bash
venv\Scripts\python.exe src\embed.py
```

## Quick Start

### 1. Check Extraction Status

Data extraction is currently running in the background. Check progress:

```bash
venv\Scripts\python.exe check_progress.py
```

Expected output when complete:
```
Total devices: 1247
With text: ~1241
Progress: 99.x%
```

(Some PDFs may be corrupted and will be skipped)

### 2. Build Vector Database

After extraction completes, build embeddings:

```bash
venv\Scripts\python.exe src\embed.py
```

This will:
- Read all extracted text from SQLite
- Chunk into 1000-char pieces with 200-char overlap
- Generate embeddings via Ollama (nomic-embed-text)
- Store in ChromaDB at `data/chroma/`

**Note**: With 1241 documents averaging ~10 pages each, expect:
- ~12,000-15,000 chunks total
- Processing time: 10-30 minutes (depends on Ollama server)

### 3. Launch Application

```bash
run_app.bat
```

Or manually:
```bash
venv\Scripts\streamlit.exe run src\dashboard.py
```

Access at: http://localhost:8501

This launches a unified web interface with two pages accessible via the sidebar:

**Dashboard (Main Page)**
- Timeline of device approvals over time
- Top companies by device count
- Panel distribution pie chart
- Product code analysis
- Search by device name, company, or submission number
- Interactive filtering by panel and year

**Chatbot (Secondary Page)**
- RAG-powered question answering
- Semantic search through device documents
- Source citations with metadata

Example questions:
- "What are the most common types of AI/ML devices in radiology?"
- "Tell me about devices from Aidoc Medical"
- "What is BriefCase-Triage used for?"
- "Which companies have the most approvals in 2024?"
- "What are the typical uses of QAS product code devices?"

## Data Pipeline Flow

```
Step 1: Extract
  Excel + PDFs → src/extract.py → data/devices.db
  Status: Currently running (check with check_progress.py)

Step 2: Embed
  data/devices.db → src/embed.py → data/chroma/
  Status: Run after extraction completes

Step 3: Launch App
  run_app.bat → Streamlit multipage interface
  - Dashboard: data/devices.db → visualization
  - Chatbot: data/chroma/ + Ollama → RAG Q&A
  Status: Dashboard ready anytime, Chatbot after embedding
```

## Configuration

Edit `.env` to change settings:

```env
# Ollama endpoint
OLLAMA_BASE_URL=http://m.m4ore.com:11436

# Models
OLLAMA_MODEL=gpt-oss:latest           # LLM for chatbot
EMBEDDING_MODEL=nomic-embed-text:latest  # Embedding model

# Chunking strategy
CHUNK_SIZE=1000
CHUNK_OVERLAP=200

# Storage paths
CHROMA_PERSIST_DIR=./data/chroma
SQLITE_DB_PATH=./data/devices.db
```

## Troubleshooting

### Extraction stuck or slow
- Check background process: Use Task Manager to see if python.exe is running
- Some PDFs may fail (corrupted files) - this is normal
- Expected final count: ~1241 devices (6 may be missing due to corrupt PDFs)

### Embedding fails
- Check Ollama endpoint: `curl http://m.m4ore.com:11436/api/tags`
- Verify model exists: Look for `nomic-embed-text:latest` in response
- Network timeout: Increase timeout in src/embed.py if needed

### Dashboard shows no data
- Run extraction first: `venv\Scripts\python.exe src\extract.py`
- Check database exists: `data\devices.db` should be present
- Verify data: `venv\Scripts\python.exe check_progress.py`

### Chatbot has no sources
- Run embedding first: `venv\Scripts\python.exe src\embed.py`
- Check vector DB exists: `data\chroma\` directory should contain files
- Verify collection: ChromaDB should show "fda_devices" collection

### Encoding errors (cp950)
- All scripts use UTF-8 encoding via `sys.stdout.reconfigure(encoding='utf-8')`
- If issues persist, set environment variable: `set PYTHONIOENCODING=utf-8`

## Performance Notes

### Extraction (src/extract.py)
- Processing: ~1 device/second
- Total time: ~20-30 minutes for 1247 devices
- Database size: ~500MB-1GB (depends on PDF text content)

### Embedding (src/embed.py)
- Processing: ~2-5 chunks/second (network dependent)
- Total chunks: ~12,000-15,000
- Total time: 10-30 minutes
- Vector DB size: ~500MB-1GB

### Dashboard
- Load time: <2 seconds (SQLite queries are fast)
- Memory: ~200MB

### Chatbot
- Query time: 2-5 seconds per question
  - Embedding: ~0.5s
  - Retrieval: ~0.5s
  - Generation: 1-4s (model dependent)
- Memory: ~300MB + model memory on Ollama server

## Data Quality

### PDF Extraction Issues
Some PDFs may fail due to:
- Invalid PDF headers (corrupted files)
- Missing EOF markers
- Encrypted/protected PDFs

These are skipped automatically with error messages in extraction log.

### Expected Statistics
Based on Excel metadata:
- Total devices in Excel: 1247
- Devices with PDFs: ~1241
- Date range: 2003-2025
- Top panels: Radiology, Cardiovascular, Clinical Chemistry
- Top product codes: QAS, LNH, QIH, etc.

## Next Steps

1. Wait for extraction to complete (monitor with check_progress.py)
2. Run embedding: `venv\Scripts\python.exe src\embed.py`
3. Launch dashboard: `run_dashboard.bat`
4. Launch chatbot: `run_chatbot.bat`
5. Explore the data and ask questions!

## Git Workflow

```bash
# Check status
git status

# View log
git log --oneline

# Create new feature
git checkout -b feature/your-feature
git add .
git commit -m "description"

# Rollback if needed
git reset --hard HEAD~1
```

## Development

### Add New Features to Dashboard
Edit `src/dashboard.py` - it's the main page in the multipage app:
- Add new charts in main()
- Use plotly for interactive visualizations
- Access data via load_data() function

### Modify RAG Behavior
Edit `src/pages/chatbot.py` - it's the secondary page:
- Change retrieval: modify retrieve_context() top_k parameter
- Adjust prompt: edit prompt template in generate_response()
- Add chat features: Streamlit session state in st.session_state

### Add New Pages
Create new files in `src/pages/`:
- Files are auto-detected by Streamlit
- Use numeric prefix for ordering (e.g., `3_Analysis.py`)
- Each page is independent with its own session state

### Optimize Chunking
Edit `.env`:
- Smaller chunks (500): More precise but more API calls
- Larger chunks (2000): Fewer calls but less precise
- Overlap (200): Context continuity between chunks
