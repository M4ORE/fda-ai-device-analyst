"""
Auto-update script for FDA AI/ML devices data
Downloads latest Excel, compares changes, downloads new PDFs, and updates database
"""
import sys
import os
import sqlite3
import time
from pathlib import Path
from datetime import datetime
from typing import Set, List, Dict

import pandas as pd
import requests
from pypdf import PdfReader
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv()

# FDA URLs
FDA_EXCEL_URL = "https://www.fda.gov/media/178540/download?attachment"
FDA_510K_BASE = "https://www.accessdata.fda.gov/cdrh_docs/pdf"
FDA_DENOVO_BASE = "https://www.accessdata.fda.gov/cdrh_docs/reviews"

class DataUpdater:
    def __init__(self, excel_path: str, pdf_dir: str, db_path: str):
        self.excel_path = excel_path
        self.excel_new_path = excel_path.replace('.xlsx', '_new.xlsx')
        self.pdf_dir = Path(pdf_dir)
        self.db_path = db_path

    def download_excel(self) -> bool:
        """Download latest Excel file from FDA"""
        print(f"Downloading latest Excel from FDA...")

        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }

            response = requests.get(FDA_EXCEL_URL, headers=headers, timeout=30)
            response.raise_for_status()

            with open(self.excel_new_path, 'wb') as f:
                f.write(response.content)

            print(f"Downloaded to: {self.excel_new_path}")
            return True

        except Exception as e:
            print(f"Error downloading Excel: {e}")
            return False

    def compare_changes(self) -> Dict[str, List[str]]:
        """Compare old and new Excel files to find changes"""
        print("\nComparing old and new data...")

        # Read old file
        df_old = pd.read_excel(self.excel_path)
        df_old.columns = ['decision_date', 'submission_number', 'device_name', 'company', 'panel', 'product_code']

        # Read new file
        df_new = pd.read_excel(self.excel_new_path)
        df_new.columns = ['decision_date', 'submission_number', 'device_name', 'company', 'panel', 'product_code']

        # Find differences
        old_submissions = set(df_old['submission_number'])
        new_submissions = set(df_new['submission_number'])

        added = new_submissions - old_submissions
        removed = old_submissions - new_submissions

        print(f"Total devices (old): {len(df_old)}")
        print(f"Total devices (new): {len(df_new)}")
        print(f"Added: {len(added)}")
        print(f"Removed: {len(removed)}")

        # Get details of added devices
        added_devices = []
        if added:
            print("\n=== NEW DEVICES ===")
            for sub in sorted(added):
                row = df_new[df_new['submission_number'] == sub].iloc[0]
                added_devices.append({
                    'submission_number': sub,
                    'decision_date': row['decision_date'],
                    'device_name': row['device_name'],
                    'company': row['company'],
                    'panel': row['panel'],
                    'product_code': row['product_code']
                })
                print(f"  {sub}: {row['device_name']} - {row['company']}")

        return {
            'added': added_devices,
            'removed': list(removed),
            'df_new': df_new
        }

    def build_pdf_url(self, submission_number: str) -> str:
        """Construct PDF download URL based on submission type"""
        # Extract year and number from submission
        if submission_number.startswith('K'):
            # 510(k): K251406 -> 25/1406 -> https://...pdf25/K251406.pdf
            year = submission_number[1:3]
            num = submission_number[3:]
            return f"{FDA_510K_BASE}{year}/{submission_number}.pdf"

        elif submission_number.startswith('DEN'):
            # De Novo: DEN240047 -> 24/0047 -> https://...reviews/DEN240047.pdf
            year = submission_number[3:5]
            num = submission_number[5:].zfill(4)
            return f"{FDA_DENOVO_BASE}/DEN{year}{num}.pdf"

        else:
            # PMA or other - no direct URL pattern
            return None

    def download_pdf(self, submission_number: str, pdf_path: Path) -> bool:
        """Download PDF for a submission"""
        url = self.build_pdf_url(submission_number)

        if not url:
            print(f"  No URL pattern for {submission_number} (likely PMA)")
            return False

        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }

            response = requests.get(url, headers=headers, timeout=30)

            if response.status_code == 404:
                print(f"  PDF not found at: {url}")
                return False

            response.raise_for_status()

            with open(pdf_path, 'wb') as f:
                f.write(response.content)

            print(f"  Downloaded: {pdf_path.name}")
            time.sleep(1)  # Be nice to FDA servers
            return True

        except Exception as e:
            print(f"  Error downloading {submission_number}: {e}")
            return False

    def extract_pdf_text(self, pdf_path: Path) -> tuple[str, int]:
        """Extract text from PDF"""
        try:
            reader = PdfReader(pdf_path)
            num_pages = len(reader.pages)

            text_parts = []
            for page in reader.pages:
                text_parts.append(page.extract_text())

            return "\n\n".join(text_parts), num_pages

        except Exception as e:
            print(f"  Error extracting {pdf_path.name}: {e}")
            return None, 0

    def update_database(self, device_data: Dict, text: str, num_pages: int):
        """Insert or update device in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT OR REPLACE INTO devices (
                submission_number, decision_date, device_name, company,
                panel, product_code, pdf_path, pdf_pages, extracted_text, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            device_data['submission_number'],
            device_data['decision_date'],
            device_data['device_name'],
            device_data['company'],
            device_data['panel'],
            device_data['product_code'],
            str(self.pdf_dir / f"{device_data['submission_number']}.pdf"),
            num_pages,
            text,
            datetime.now().isoformat()
        ))

        conn.commit()
        conn.close()

    def check_missing_pdfs(self, df: pd.DataFrame) -> List[Dict]:
        """Check for devices without PDFs or corrupted PDFs"""
        print("\nChecking for missing or corrupted PDFs...")

        missing = []
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        for idx, row in df.iterrows():
            submission_num = row['submission_number']
            pdf_path = self.pdf_dir / f"{submission_num}.pdf"

            # Check if PDF exists
            if not pdf_path.exists():
                missing.append({
                    'submission_number': submission_num,
                    'decision_date': row['decision_date'],
                    'device_name': row['device_name'],
                    'company': row['company'],
                    'panel': row['panel'],
                    'product_code': row['product_code'],
                    'reason': 'PDF not found'
                })
                continue

            # Check if in database with valid text
            cursor.execute(
                "SELECT extracted_text FROM devices WHERE submission_number = ?",
                (submission_num,)
            )
            result = cursor.fetchone()

            if not result or not result[0] or len(result[0]) < 100:
                missing.append({
                    'submission_number': submission_num,
                    'decision_date': row['decision_date'],
                    'device_name': row['device_name'],
                    'company': row['company'],
                    'panel': row['panel'],
                    'product_code': row['product_code'],
                    'reason': 'PDF corrupted or extraction failed'
                })

        conn.close()

        if missing:
            print(f"Found {len(missing)} devices needing PDF download/re-extraction:")
            for item in missing[:10]:  # Show first 10
                print(f"  {item['submission_number']}: {item['reason']}")
            if len(missing) > 10:
                print(f"  ... and {len(missing) - 10} more")

        return missing

    def run_update(self):
        """Main update process"""
        print("=== FDA AI/ML DEVICES DATA UPDATE ===\n")

        # Step 1: Download latest Excel
        if not self.download_excel():
            print("Failed to download Excel. Aborting.")
            return

        # Step 2: Compare changes
        changes = self.compare_changes()

        # Step 3: Check for missing/corrupted PDFs
        missing_pdfs = self.check_missing_pdfs(changes['df_new'])

        # Combine new devices and missing PDFs
        all_to_process = changes['added'] + missing_pdfs

        if not all_to_process:
            print("\nNo new devices or missing PDFs. Data is up to date.")
            os.remove(self.excel_new_path)
            return

        print(f"\nTotal devices to process:")
        print(f"  New devices: {len(changes['added'])}")
        print(f"  Missing/corrupted PDFs: {len(missing_pdfs)}")
        print(f"  Total: {len(all_to_process)}")

        # Step 4: Download PDFs and update database
        print(f"\nProcessing {len(all_to_process)} devices...")

        success_count = 0
        skip_count = 0

        for device in all_to_process:
            submission_num = device['submission_number']
            pdf_path = self.pdf_dir / f"{submission_num}.pdf"

            print(f"\n[{success_count + skip_count + 1}/{len(all_to_process)}] {submission_num}")

            # Download PDF
            if pdf_path.exists():
                print(f"  PDF already exists")
            else:
                if not self.download_pdf(submission_num, pdf_path):
                    skip_count += 1
                    continue

            # Extract text
            text, num_pages = self.extract_pdf_text(pdf_path)

            if text:
                # Update database
                self.update_database(device, text, num_pages)
                success_count += 1
                print(f"  Added to database ({num_pages} pages)")
            else:
                skip_count += 1

        # Step 4: Replace old Excel with new one
        if success_count > 0:
            import shutil
            shutil.copy(self.excel_path, self.excel_path.replace('.xlsx', '_backup.xlsx'))
            shutil.move(self.excel_new_path, self.excel_path)
            print(f"\n=== UPDATE COMPLETE ===")
            print(f"Successfully added: {success_count}")
            print(f"Skipped: {skip_count}")
            print(f"Excel backup: {self.excel_path.replace('.xlsx', '_backup.xlsx')}")
            print(f"New Excel: {self.excel_path}")
        else:
            os.remove(self.excel_new_path)
            print("\nNo updates applied.")

def main():
    excel_path = "ai-ml-enabled-devices-excel.xlsx"
    pdf_dir = "summaries"
    db_path = os.getenv('SQLITE_DB_PATH', './data/devices.db')

    updater = DataUpdater(excel_path, pdf_dir, db_path)
    updater.run_update()

    print("\nTo rebuild vector database, run:")
    print("  venv\\Scripts\\python.exe src\\embed.py")

if __name__ == "__main__":
    main()
