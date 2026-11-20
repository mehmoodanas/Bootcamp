"""Step 1 check: compare pypdf default vs layout mode on a page with a table.

Run:  uv run python parse_check.py
"""
from pypdf import PdfReader

reader = PdfReader("documents/quarterly_report_q1_2026.pdf")
page = reader.pages[1]  # page 2: Revenue Overview table

print("=" * 60)
print("DEFAULT extract_text()")
print("=" * 60)
print(page.extract_text()[:1200])

print("\n" + "=" * 60)
print('LAYOUT extract_text(extraction_mode="layout")')
print("=" * 60)
print(page.extract_text(extraction_mode="layout")[:1800])
