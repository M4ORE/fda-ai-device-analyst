"""
Automatic device classification using LLM
Extracts imaging modality, body region, and clinical application
"""
import sys
import os
import json
import sqlite3
from datetime import datetime
from typing import Dict, Optional

import requests
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv()

CLASSIFICATION_VERSION = "v1.0"

CLASSIFICATION_PROMPT = """You are a medical device classification expert. Analyze this FDA-approved AI/ML medical device and extract structured information.

Device Information:
- Name: {device_name}
- Panel: {panel}
- Product Code: {product_code}

Extract the following categories (use "Unknown" if not determinable):

1. **Imaging Modality** (select ONE most relevant):
   - CT
   - MRI
   - X-ray
   - Ultrasound
   - Endoscopy
   - ECG
   - EEG
   - PET
   - Mammography
   - Fluoroscopy
   - OCT
   - Non-imaging
   - Unknown

2. **Body Region** (select ONE primary region):
   - Brain
   - Heart
   - Chest/Lung
   - Breast
   - Abdomen
   - Liver
   - Kidney
   - Bone/Musculoskeletal
   - Eye/Retina
   - Vascular
   - Multi-organ
   - Not applicable
   - Unknown

3. **Clinical Application** (select ONE primary purpose):
   - Screening
   - Diagnosis
   - Treatment Planning
   - Monitoring
   - Risk Assessment
   - Image Enhancement
   - Workflow Optimization
   - Detection/Segmentation
   - Unknown

Respond ONLY with valid JSON in this exact format:
{{
  "imaging_modality": "...",
  "body_region": "...",
  "clinical_application": "..."
}}

No explanations, no additional text, only the JSON object."""

class DeviceClassifier:
    def __init__(self, db_path: str, ollama_url: str, model: str):
        self.db_path = db_path
        self.ollama_url = ollama_url
        self.model = model

    def call_ollama(self, prompt: str) -> str:
        """Call Ollama LLM API"""
        url = f"{self.ollama_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.1,  # Low temperature for consistent classification
                "top_p": 0.9
            }
        }

        try:
            response = requests.post(url, json=payload, timeout=60)
            response.raise_for_status()
            result = response.json()
            return result.get('response', '').strip()
        except Exception as e:
            print(f"Ollama API error: {e}")
            return ""

    def parse_classification(self, llm_response: str) -> Optional[Dict[str, str]]:
        """Parse LLM response as JSON"""
        try:
            # Try to find JSON object in response
            start_idx = llm_response.find('{')
            end_idx = llm_response.rfind('}') + 1

            if start_idx == -1 or end_idx == 0:
                return None

            json_str = llm_response[start_idx:end_idx]
            data = json.loads(json_str)

            # Validate required fields
            required = ['imaging_modality', 'body_region', 'clinical_application']
            if all(k in data for k in required):
                return data
            else:
                return None

        except json.JSONDecodeError as e:
            print(f"JSON parse error: {e}")
            print(f"Response: {llm_response[:200]}")
            return None

    def classify_device(self, device_name: str, panel: str, product_code: str) -> Optional[Dict[str, str]]:
        """Classify a single device"""
        prompt = CLASSIFICATION_PROMPT.format(
            device_name=device_name,
            panel=panel,
            product_code=product_code
        )

        llm_response = self.call_ollama(prompt)
        if not llm_response:
            return None

        return self.parse_classification(llm_response)

    def classify_all_devices(self, batch_size: int = 10, limit: Optional[int] = None):
        """Classify all devices in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get unclassified devices
        query = """
            SELECT submission_number, device_name, panel, product_code
            FROM devices
            WHERE ai_tags_version IS NULL OR ai_tags_version != ?
            ORDER BY decision_date DESC
        """

        if limit:
            query += f" LIMIT {limit}"

        cursor.execute(query, (CLASSIFICATION_VERSION,))
        devices = cursor.fetchall()

        total = len(devices)
        print(f"Found {total} devices to classify")

        if total == 0:
            print("All devices already classified with current version")
            conn.close()
            return

        processed = 0
        failed = 0

        for idx, (sub_num, name, panel, code) in enumerate(devices, 1):
            print(f"\n[{idx}/{total}] {name[:50]}...")

            classification = self.classify_device(name, panel, code)

            if classification:
                cursor.execute("""
                    UPDATE devices
                    SET imaging_modality = ?,
                        body_region = ?,
                        clinical_application = ?,
                        ai_tags_version = ?
                    WHERE submission_number = ?
                """, (
                    classification['imaging_modality'],
                    classification['body_region'],
                    classification['clinical_application'],
                    CLASSIFICATION_VERSION,
                    sub_num
                ))

                print(f"  Modality: {classification['imaging_modality']}")
                print(f"  Region: {classification['body_region']}")
                print(f"  Application: {classification['clinical_application']}")

                processed += 1

                # Commit in batches
                if processed % batch_size == 0:
                    conn.commit()
                    print(f"\n--- Checkpoint: {processed}/{total} completed ---")

            else:
                print(f"  FAILED - Could not classify")
                failed += 1

        # Final commit
        conn.commit()
        conn.close()

        print(f"\n{'='*60}")
        print(f"Classification complete:")
        print(f"  Processed: {processed}")
        print(f"  Failed: {failed}")
        print(f"  Total: {total}")
        print(f"{'='*60}")

    def show_statistics(self):
        """Show classification statistics"""
        conn = sqlite3.connect(self.db_path)

        print("\n=== Classification Statistics ===\n")

        # Imaging modality distribution
        df = conn.execute("""
            SELECT imaging_modality, COUNT(*) as count
            FROM devices
            WHERE imaging_modality IS NOT NULL
            GROUP BY imaging_modality
            ORDER BY count DESC
        """).fetchall()

        print("Imaging Modality:")
        for mod, count in df:
            print(f"  {mod:<25} {count:>4}")

        # Body region distribution
        df = conn.execute("""
            SELECT body_region, COUNT(*) as count
            FROM devices
            WHERE body_region IS NOT NULL
            GROUP BY body_region
            ORDER BY count DESC
        """).fetchall()

        print("\nBody Region:")
        for region, count in df:
            print(f"  {region:<25} {count:>4}")

        # Clinical application distribution
        df = conn.execute("""
            SELECT clinical_application, COUNT(*) as count
            FROM devices
            WHERE clinical_application IS NOT NULL
            GROUP BY clinical_application
            ORDER BY count DESC
        """).fetchall()

        print("\nClinical Application:")
        for app, count in df:
            print(f"  {app:<25} {count:>4}")

        conn.close()

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Classify FDA AI/ML devices using LLM")
    parser.add_argument('--db', default='./data/devices.db', help='Database path')
    parser.add_argument('--ollama-url', default=None, help='Ollama API URL')
    parser.add_argument('--model', default=None, help='Ollama model name')
    parser.add_argument('--limit', type=int, default=None, help='Limit number of devices to classify')
    parser.add_argument('--batch-size', type=int, default=10, help='Commit batch size')
    parser.add_argument('--stats', action='store_true', help='Show statistics only')

    args = parser.parse_args()

    ollama_url = args.ollama_url or os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
    model = args.model or os.getenv('OLLAMA_MODEL', 'gpt-oss:latest')

    classifier = DeviceClassifier(args.db, ollama_url, model)

    if args.stats:
        classifier.show_statistics()
    else:
        print(f"Using model: {model}")
        print(f"Ollama URL: {ollama_url}")
        print(f"Database: {args.db}")
        if args.limit:
            print(f"Limit: {args.limit} devices")
        print()

        classifier.classify_all_devices(batch_size=args.batch_size, limit=args.limit)
        classifier.show_statistics()

if __name__ == "__main__":
    main()
