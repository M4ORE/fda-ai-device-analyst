# FDA AI/ML Medical Devices Data Platform Architecture

## Data Structure

### Source Data
- **Excel**: 1247 FDA AI/ML-enabled device records
  - Columns: Date, Submission Number, Device, Company, Panel, Product Code
- **PDFs**: 1241 510(k) approval letters in `summaries/`
  - Filename format: `{Submission_Number}.pdf` (e.g., K251406.pdf)

### Data Pipeline

```
Excel + PDFs -> Extract & Parse -> SQLite + Vector DB -> Dashboard + RAG Chatbot
```

## Architecture Components

### 1. Data Extraction Layer
- Parse Excel metadata
- Extract PDF text content
- Normalize and clean data
- Store in SQLite for structured queries

### 2. Vector Database Layer
- Embedding model: via Ollama API (http://m.m4ore.com:11436)
- Vector store: ChromaDB (local, persistent)
- Chunking strategy: paragraph-based with metadata
- Metadata: submission_number, company, device, date, panel

### 3. Visualization Dashboard
- Framework: Streamlit (simple, fast)
- Features:
  - Timeline view (approval trends)
  - Company/Panel distribution
  - Device category analysis
  - Search and filter

### 4. RAG Chatbot
- LLM: Ollama API endpoint
- Retrieval: ChromaDB similarity search
- Context window: top-k relevant chunks
- Chat history management

## Tech Stack

- **Python 3.12** + venv
- **Data Processing**: pandas, pypdf
- **Database**: SQLite (metadata), ChromaDB (vectors)
- **Embeddings**: Ollama API
- **LLM**: Ollama API (gpt-oss model)
- **UI**: Streamlit
- **Config**: python-dotenv (.env file)

## Project Structure

```
cch-20250929/
├── .env                    # Configuration (Ollama endpoint, etc.)
├── data/
│   ├── devices.db         # SQLite database
│   └── chroma/            # ChromaDB vector store
├── src/
│   ├── extract.py         # PDF extraction
│   ├── embed.py           # Vector embedding pipeline
│   ├── dashboard.py       # Streamlit dashboard
│   └── chatbot.py         # RAG chatbot
├── summaries/             # PDF files (1241)
└── ai-ml-enabled-devices-excel.xlsx
```

## Implementation Priority

1. Data extraction (Excel + PDF -> SQLite)
2. Vector embedding (PDF chunks -> ChromaDB)
3. Dashboard (basic visualization)
4. RAG chatbot (Q&A interface)
5. Integration and testing
