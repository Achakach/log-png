"""Show full content of specific cells from comprehensive_test_cases_updated.docx"""
from docx import Document

doc = Document('comprehensive_test_cases_updated.docx')

for ti in range(7):
    table = doc.tables[ti]
    for row in table.rows:
        for cell in row.cells:
            text = cell.text.strip()
            if text and 'TUC' in text and 'HUAWEI' in text:
                print(f"=== Table {ti+1}, Row ===")
                lines = [l.strip() for l in text.split('\n') if l.strip()]
                for line in lines:
                    print(f"    {line}")
                print()
