"""Test extraction with first 10 records"""
import sys
import os
import sqlite3
from pathlib import Path
from datetime import datetime

import pandas as pd
from pypdf import PdfReader
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv()

# Read Excel
df = pd.read_excel('ai-ml-enabled-devices-excel.xlsx')
df.columns = ['decision_date', 'submission_number', 'device_name', 'company', 'panel', 'product_code']

# Test first 10
print("=== Testing first 10 records ===\n")

for idx in range(min(10, len(df))):
    row = df.iloc[idx]
    submission_num = row['submission_number']
    pdf_path = Path('summaries') / f"{submission_num}.pdf"

    if pdf_path.exists():
        try:
            reader = PdfReader(pdf_path)
            num_pages = len(reader.pages)
            text_len = len(reader.pages[0].extract_text())
            print(f"[{idx+1}] {submission_num}: {num_pages} pages, first page {text_len} chars - OK")
        except Exception as e:
            print(f"[{idx+1}] {submission_num}: ERROR - {e}")
    else:
        print(f"[{idx+1}] {submission_num}: PDF NOT FOUND")

print("\nTest complete.")
