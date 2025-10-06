"""
Extract and process FDA AI/ML device data from Excel and PDF files
"""
import sys
import os
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Optional

import pandas as pd
from pypdf import PdfReader
from dotenv import load_dotenv

# Force UTF-8 encoding
sys.stdout.reconfigure(encoding='utf-8')

# Load environment variables
load_dotenv()

class DataExtractor:
    def __init__(self, excel_path: str, pdf_dir: str, db_path: str):
        self.excel_path = excel_path
        self.pdf_dir = Path(pdf_dir)
        self.db_path = db_path

    def init_database(self):
        """Initialize SQLite database with schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create devices table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS devices (
                submission_number TEXT PRIMARY KEY,
                decision_date TEXT,
                device_name TEXT,
                company TEXT,
                panel TEXT,
                product_code TEXT,
                pdf_path TEXT,
                pdf_pages INTEGER,
                extracted_text TEXT,
                created_at TEXT,
                imaging_modality TEXT,
                body_region TEXT,
                clinical_application TEXT,
                ai_tags_version TEXT
            )
        ''')

        # Create indexes for competitive analysis
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_panel ON devices(panel)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_product_code ON devices(product_code)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_company ON devices(company)')

        conn.commit()
        conn.close()
        print(f"Database initialized: {self.db_path}")

    def extract_excel(self) -> pd.DataFrame:
        """Extract metadata from Excel file"""
        print(f"Reading Excel: {self.excel_path}")
        df = pd.read_excel(self.excel_path)

        # Normalize column names
        df.columns = [
            'decision_date',
            'submission_number',
            'device_name',
            'company',
            'panel',
            'product_code'
        ]

        print(f"Loaded {len(df)} device records")
        return df

    def extract_pdf(self, pdf_path: Path) -> tuple[Optional[str], int]:
        """Extract text from PDF file"""
        try:
            reader = PdfReader(pdf_path)
            num_pages = len(reader.pages)

            # Extract all text
            text_parts = []
            for page in reader.pages:
                text_parts.append(page.extract_text())

            full_text = "\n\n".join(text_parts)
            return full_text, num_pages

        except Exception as e:
            print(f"Error extracting {pdf_path.name}: {e}")
            return None, 0

    def process_all(self):
        """Main processing pipeline"""
        # Initialize database
        self.init_database()

        # Extract Excel metadata
        df = self.extract_excel()

        # Process each device
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        processed = 0
        skipped = 0

        for idx, row in df.iterrows():
            submission_num = row['submission_number']
            pdf_path = self.pdf_dir / f"{submission_num}.pdf"

            # Check if PDF exists
            if not pdf_path.exists():
                print(f"[{idx+1}/{len(df)}] SKIP: {submission_num} - PDF not found")
                skipped += 1
                continue

            # Extract PDF text
            text, num_pages = self.extract_pdf(pdf_path)

            if text is None:
                skipped += 1
                continue

            # Insert into database
            cursor.execute('''
                INSERT OR REPLACE INTO devices (
                    submission_number, decision_date, device_name, company,
                    panel, product_code, pdf_path, pdf_pages, extracted_text, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                submission_num,
                row['decision_date'],
                row['device_name'],
                row['company'],
                row['panel'],
                row['product_code'],
                str(pdf_path),
                num_pages,
                text,
                datetime.now().isoformat()
            ))

            processed += 1
            if processed % 50 == 0:
                conn.commit()
                print(f"[{idx+1}/{len(df)}] Processed {processed} devices...")

        conn.commit()
        conn.close()

        print(f"\n=== EXTRACTION COMPLETE ===")
        print(f"Processed: {processed}")
        print(f"Skipped: {skipped}")
        print(f"Database: {self.db_path}")

def main():
    # Paths
    excel_path = "ai-ml-enabled-devices-excel.xlsx"
    pdf_dir = "summaries"
    db_path = os.getenv('SQLITE_DB_PATH', './data/devices.db')

    # Ensure data directory exists
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    # Run extraction
    extractor = DataExtractor(excel_path, pdf_dir, db_path)
    extractor.process_all()

if __name__ == "__main__":
    main()
