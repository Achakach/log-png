from docx import Document

doc = Document(r"C:\Users\kacha\OneDrive\Desktop\test\comprehensive_test_cases.docx")

table14 = doc.tables[13]  # Table 14 (0-indexed = 13)
cell = table14.rows[1].cells[1]  # Cell content

print("Table 14 full content:")
for i, line in enumerate(cell.text.split('\n')):
    if line.strip():
        print(f"  Line {i}: '{line.strip()}'")
