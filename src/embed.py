"""
Build vector database from extracted PDF content using Ollama embeddings
"""
import sys
import os
import sqlite3
import requests
from pathlib import Path
from typing import List, Dict

import chromadb
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv()

class VectorDBBuilder:
    def __init__(self, db_path: str, chroma_path: str, ollama_url: str, model: str):
        self.db_path = db_path
        self.chroma_path = chroma_path
        self.ollama_url = ollama_url
        self.embedding_model = model

        # Initialize ChromaDB
        self.chroma_client = chromadb.PersistentClient(path=chroma_path)

        # Get or create collection
        self.collection = self.chroma_client.get_or_create_collection(
            name="fda_devices",
            metadata={"description": "FDA AI/ML medical device documents"}
        )

    def get_ollama_embedding(self, text: str) -> List[float]:
        """Get embedding from Ollama API"""
        url = f"{self.ollama_url}/api/embed"
        payload = {
            "model": self.embedding_model,
            "input": text
        }

        try:
            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()
            result = response.json()

            # Handle different response formats
            if 'embeddings' in result:
                return result['embeddings'][0]
            elif 'embedding' in result:
                return result['embedding']
            else:
                raise ValueError(f"Unexpected response format: {result.keys()}")

        except Exception as e:
            print(f"Error getting embedding: {e}")
            raise

    def chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """Split text into overlapping chunks"""
        chunks = []
        start = 0
        text_len = len(text)

        while start < text_len:
            end = min(start + chunk_size, text_len)
            chunk = text[start:end]

            # Only add non-empty chunks
            if chunk.strip():
                chunks.append(chunk)

            start += (chunk_size - overlap)

        return chunks

    def process_all_documents(self):
        """Process all documents from SQLite and add to vector DB"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get all devices with extracted text
        cursor.execute("""
            SELECT submission_number, device_name, company, panel,
                   decision_date, product_code, extracted_text
            FROM devices
            WHERE extracted_text IS NOT NULL AND extracted_text != ''
        """)

        devices = cursor.fetchall()
        conn.close()

        print(f"Processing {len(devices)} documents...")

        chunk_size = int(os.getenv('CHUNK_SIZE', 1000))
        chunk_overlap = int(os.getenv('CHUNK_OVERLAP', 200))

        total_chunks = 0

        for idx, device in enumerate(devices):
            submission_num, device_name, company, panel, date, prod_code, text = device

            # Split into chunks
            chunks = self.chunk_text(text, chunk_size, chunk_overlap)

            print(f"[{idx+1}/{len(devices)}] {submission_num}: {len(chunks)} chunks")

            # Process each chunk
            for chunk_idx, chunk in enumerate(chunks):
                chunk_id = f"{submission_num}_{chunk_idx}"

                try:
                    # Get embedding
                    embedding = self.get_ollama_embedding(chunk)

                    # Add to ChromaDB
                    self.collection.add(
                        ids=[chunk_id],
                        embeddings=[embedding],
                        documents=[chunk],
                        metadatas=[{
                            "submission_number": submission_num,
                            "device_name": device_name,
                            "company": company,
                            "panel": panel,
                            "decision_date": date,
                            "product_code": prod_code,
                            "chunk_index": chunk_idx
                        }]
                    )

                    total_chunks += 1

                except Exception as e:
                    print(f"  Error processing chunk {chunk_idx}: {e}")
                    continue

            # Commit every 10 devices
            if (idx + 1) % 10 == 0:
                print(f"  Committed {total_chunks} chunks so far...")

        print(f"\n=== EMBEDDING COMPLETE ===")
        print(f"Total chunks: {total_chunks}")
        print(f"Vector DB: {self.chroma_path}")

def main():
    db_path = os.getenv('SQLITE_DB_PATH', './data/devices.db')
    chroma_path = os.getenv('CHROMA_PERSIST_DIR', './data/chroma')
    ollama_url = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
    embedding_model = os.getenv('EMBEDDING_MODEL', 'nomic-embed-text:latest')

    os.makedirs(chroma_path, exist_ok=True)

    builder = VectorDBBuilder(db_path, chroma_path, ollama_url, embedding_model)
    builder.process_all_documents()

if __name__ == "__main__":
    main()
