"""Check data extraction progress"""
import sys
import os
import sqlite3

sys.stdout.reconfigure(encoding='utf-8')

db_path = './data/devices.db'

if not os.path.exists(db_path):
    print("Database not found. Extraction not started.")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get counts
cursor.execute("SELECT COUNT(*) FROM devices")
total = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM devices WHERE extracted_text IS NOT NULL AND extracted_text != ''")
with_text = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM devices WHERE extracted_text IS NULL OR extracted_text = ''")
without_text = cursor.fetchone()[0]

conn.close()

print(f"=== EXTRACTION PROGRESS ===")
print(f"Total devices: {total}")
print(f"With text: {with_text}")
print(f"Without text: {without_text}")
print(f"Progress: {with_text}/{total} ({100*with_text/total:.1f}%)")
