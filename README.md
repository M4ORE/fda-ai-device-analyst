# FDA AI Device Analyst

Comprehensive data platform for analyzing FDA-approved AI/ML-enabled medical devices with visualization dashboard and RAG-powered chatbot.

## Data Source

- **Excel File:** [FDA AI/ML-Enabled Device List](https://www.fda.gov/media/178540/download?attachment)
- **Source Page:** [FDA - Artificial Intelligence-Enabled Medical Devices](https://www.fda.gov/medical-devices/software-medical-device-samd/artificial-intelligence-enabled-medical-devices)
- **Last Updated:** Check FDA website for latest version

## Features

- **Data Extraction**: Parse Excel metadata and PDF approval documents (1247 devices)
- **Vector Database**: ChromaDB with Ollama embeddings for semantic search
- **Visualization Dashboard**: Interactive Streamlit dashboard with filtering and charts
- **RAG Chatbot**: Question-answering system using Ollama LLM

## Data Update

To update with the latest FDA data:

```bash
run_update.bat
```

Or manually:

```bash
venv\Scripts\python.exe src\update.py
```

This will:
1. Download latest Excel from FDA website
2. Compare with existing data to find new devices
3. Check for missing or corrupted PDFs in existing data
4. Download new PDFs from FDA servers
5. Extract text and update SQLite database
6. Backup old Excel and replace with new version

After update, rebuild vector database:

```bash
venv\Scripts\python.exe src\embed.py
```

## Setup

### 1. Install Dependencies

```bash
# Activate virtual environment (already created)
venv\Scripts\activate

# Dependencies already installed:
# - pandas, openpyxl (Excel)
# - pypdf (PDF parsing)
# - chromadb (vector DB)
# - streamlit, plotly (dashboard)
# - requests (API calls)
# - python-dotenv (config)
```

### 2. Configuration

Edit `.env` file to configure Ollama endpoint and models:

```env
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=gpt-oss:latest
EMBEDDING_MODEL=nomic-embed-text:latest
```

### 3. Extract Data

Run PDF extraction pipeline:

```bash
venv\Scripts\python.exe src\extract.py
```

This creates `data/devices.db` SQLite database with all device metadata and PDF content.

### 4. Build Vector Database

Generate embeddings and build ChromaDB:

```bash
venv\Scripts\python.exe src\embed.py
```

This creates `data/chroma/` vector store for RAG retrieval.

## Usage

### Launch Application

```bash
run_app.bat
```

Or:

```bash
venv\Scripts\streamlit.exe run src\dashboard.py
```

This launches a unified web interface with two pages:

**Dashboard (Main Page)**
- Timeline of device approvals
- Company and panel distribution
- Product code analysis
- Search and filter

**Chatbot (Secondary Page)**
- RAG-powered Q&A using Ollama LLM
- Semantic search through ChromaDB
- Source citations from FDA documents

Ask questions like:
- "What AI/ML devices were approved for radiology?"
- "Tell me about BriefCase-Triage device"
- "Which companies have the most AI/ML device approvals?"

## Data Structure

### SQLite Database (`data/devices.db`)

Table: `devices`
- submission_number (PK)
- decision_date
- device_name
- company
- panel
- product_code
- pdf_path
- pdf_pages
- extracted_text
- created_at

### Vector Database (`data/chroma/`)

Collection: `fda_devices`
- Document chunks (1000 chars, 200 overlap)
- Embeddings: nomic-embed-text (137M, F16)
- Metadata: submission_number, device_name, company, panel, date, product_code, chunk_index

## Architecture

```
Excel + PDFs -> extract.py -> SQLite (metadata + full text)
                               |
                               v
                          embed.py -> ChromaDB (vector embeddings)
                               |
                    +----------+----------+
                    |                     |
                dashboard.py          chatbot.py
                (Streamlit)           (RAG + Ollama)
```

## Models

- **LLM**: gpt-oss:latest (20.9B, MXFP4)
- **Embedding**: nomic-embed-text:latest (137M, F16)
- **Endpoint**: http://localhost:11434

## File Structure

```
fda-ai-device-analyst/
├── .env                    # Configuration
├── .gitignore
├── README.md
├── ARCHITECTURE.md         # Detailed design doc
├── venv/                   # Python virtual environment
├── data/
│   ├── devices.db         # SQLite database
│   └── chroma/            # ChromaDB vector store
├── src/
│   ├── extract.py         # PDF extraction pipeline
│   ├── embed.py           # Vector embedding builder
│   ├── update.py          # Auto-update from FDA
│   ├── dashboard.py       # Main page (visualization)
│   └── pages/
│       └── chatbot.py     # Secondary page (RAG chatbot)
├── summaries/             # PDF files (1241)
├── ai-ml-enabled-devices-excel.xlsx
├── run_app.bat            # Launch web interface
└── run_update.bat         # Update data from FDA
```

## Development Notes

- All code uses UTF-8 encoding to avoid cp950 issues
- Parameters stored in `.env` file
- Git commits after major milestones
- ChromaDB uses persistent storage
- Ollama API for both embedding and generation
