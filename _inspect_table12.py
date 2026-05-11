"""Show full content of Table 12."""
from docx import Document

doc = Document('comprehensive_test_cases_updated.docx')
table = doc.tables[11]  # Table 12 (0-indexed)

for ri, row in enumerate(table.rows):
    for ci, cell in enumerate(row.cells):
        text = cell.text.strip()
        if text:
            print(f"Row {ri+1}, Col {ci+1}:")
            for line in text.split('\n'):
                print(f"  | {line}")
            print()
