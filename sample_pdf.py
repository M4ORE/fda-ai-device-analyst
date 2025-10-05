import sys
from pypdf import PdfReader

sys.stdout.reconfigure(encoding='utf-8')

# Read sample PDF
pdf_path = 'summaries/K251406.pdf'
reader = PdfReader(pdf_path)

print(f"=== PDF: {pdf_path} ===")
print(f"Total pages: {len(reader.pages)}")
print("\n=== FIRST 2 PAGES CONTENT ===\n")

for i in range(min(2, len(reader.pages))):
    print(f"--- Page {i+1} ---")
    print(reader.pages[i].extract_text())
    print("\n")
