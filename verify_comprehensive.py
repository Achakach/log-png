from docx import Document
import re

result_doc = Document('comprehensive_test_cases_RESULT.docx')

print('=== COMPREHENSIVE TEST RESULTS ===\n')

total_expected = [3, 1, 6, 2, 0, 2, 1, 0, 0, 9, 3, 3]
total_actual = 0
total_expected_sum = sum(total_expected)

for ti, table in enumerate(result_doc.tables):
    case_num = ti + 1
    for ri, row in enumerate(table.rows):
        for ci, cell in enumerate(row.cells):
            if ci == 1:  # Content column
                text = cell.text.strip()
                if text and len(text) > 10:
                    img_count = len(cell._element.findall('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}drawing'))
                    expected = total_expected[ti] if ti < len(total_expected) else '?'
                    status = '✅' if img_count == expected else '❌'
                    
                    # Extract nodes
                    nodes = re.findall(r'<([A-Za-z][\w.\-]+)>', text)
                    
                    print(f'Case {case_num}: {img_count} image(s) / {expected} expected {status}')
                    if nodes:
                        print(f'  Nodes: {nodes}')
                    
                    total_actual += img_count
                    break  # Only check content column

print(f'\n{"="*50}')
print(f'Total images: {total_actual} / {total_expected_sum} expected')
print(f'{"="*50}')
