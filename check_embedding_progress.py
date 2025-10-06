"""Check embedding progress by monitoring ChromaDB size"""
import sys
import os
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

chroma_db = Path('./data/chroma/chroma.sqlite3')

if not chroma_db.exists():
    print("ChromaDB not created yet. Embedding not started.")
    exit(0)

size_mb = chroma_db.stat().st_size / (1024 * 1024)

print(f"ChromaDB size: {size_mb:.1f} MB")

# Rough estimate: ~500-800MB when complete (based on 1228 devices)
estimated_progress = min(100, (size_mb / 600) * 100)

print(f"Estimated progress: ~{estimated_progress:.1f}%")
print(f"\nNote: This is rough estimate. Actual completion will be shown in embed.py output.")
