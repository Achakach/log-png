"""Add 'Expected Result' column to comprehensive_test_cases.docx"""
from docx import Document
from docx.shared import Pt, RGBColor

doc = Document('comprehensive_test_cases.docx')

# Expected results for each test case
expected = [
    # Table 1
    "TUC-TEST01 display device.png\nTUC-TEST02 display device.png\nTUC-TEST03 display device.png",
    # Table 2
    "TUC-TEST01 system-view interface GigabitEthernet0_0_1 display this quit quit.png",
    # Table 3
    "TUC-TEST01 display device.png\nTUC-TEST02 display device.png\nTUC-TEST03 display device.png\nTUC-TEST01 display clock.png\nTUC-TEST02 display clock.png\nTUC-TEST03 display clock.png",
    # Table 4
    "TUC-TEST02 display device.png\nTUC-TEST01 display clock.png",
    # Table 5
    "No match (no PNG for display cpu-usage)",
    # Table 6
    "TUC-TEST01 display device.png\nTUC-TEST01 display clock.png",
    # Table 7
    "TUC-TEST01 system-view interface GigabitEthernet0_0_1 display this quit quit.png",
    # Table 8
    "No match (no nodes to insert)",
    # Table 9
    "Skipped (error PNG but no error text in DOCX)",
    # Table 10
    "TUC-TEST01/02/03 system-view interface GigabitEthernet0_0_1 display this quit quit.png\n" +
    "TUC-TEST01/02/03 display device.png\n" +
    "TUC-TEST01/02/03 display clock.png",
    # Table 11
    "Skipped error (wrong-command)\nTUC-TEST01/02/03 display device.png",
    # Table 12
    "TUC-TEST01/02/03 display device.png\nTUC-TEST01/02/03 display clock.png",
    # Table 13
    "TUC-TEST01/02/03 display current-configutation [error].png",
    # Table 14
    "TUC-TEST01/02/03 startup saved-configuration backup.zip.png\n" +
    "TUC-TEST01/02/03 startup saved-configuration test.cfg.png\n" +
    "TUC-TEST01/02/03 startup saved-configuration file.hi.png",
    # Table 15
    "TUC-TEST01/02/03 display current-configuration.png",
    # Table 16
    "TUC-TEST01/02/03 system-view [error].png",
    # Table 17
    "TUC-TEST01/02/03 display current-configuration [error].png",
    # Table 18
    "TUC-TEST01/02/03 display current-configuration username kacha1.png",
    # Table 19
    "TUC-TEST01/02/03 display current-configuration.png + OLE .txt",
]

for ti, table in enumerate(doc.tables):
    # Get header row
    header_row = table.rows[0]
    data_row = table.rows[1]
    
    # Add header cell
    new_header_cell = header_row.cells[-1]  # Last cell
    new_data_cell = data_row.cells[-1]  # Last cell
    
    # Check if we need to add a new column
    if len(header_row.cells) < 3:
        # Add new column by adding cells
        new_header = table.rows[0].cells[-1]._element.addnext(new_header_cell._element)
        new_data = table.rows[1].cells[-1]._element.addnext(new_data_cell._element)
        
        # Actually, python-docx doesn't support adding columns easily
        # Let me insert a new cell properly
        new_header = table.rows[0].cells[-1]._element.addnext(new_header_cell._element)
        new_data = table.rows[1].cells[-1]._element.addnext(new_data_cell._element)

print("Done - please check the output")
