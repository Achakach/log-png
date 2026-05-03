import sys, os
sys.path.insert(0, '.')
from putpnginword import parse_paragraphs_detailed, match_cell_blocks

class MockParagraph:
    def __init__(self, text):
        self.text = text

# Real PNG files from screenshots directory
real_png_files = [os.path.join('screenshots', f) for f in os.listdir('screenshots') if f.endswith('.png')]

def test_case(name, paragraphs, png_files, expected_results):
    """expected_results: list of (node, block_idx, should_match) tuples"""
    print(f"\n{'='*60}")
    print(f"CASE: {name}")
    print(f"{'='*60}")
    
    print("Input:")
    for i, p in enumerate(paragraphs):
        print(f"  {i}: {p.text}")
    
    results = match_cell_blocks(paragraphs, png_files)
    
    print("\nParsed blocks:")
    blocks = parse_paragraphs_detailed(paragraphs)
    for bi, (cmds, nodes) in enumerate(blocks):
        print(f"  Block {bi}: {cmds} -> nodes={nodes}")
    
    print("\nMatch results:")
    all_pass = True
    for r in results:
        match_name = os.path.basename(r['match_path']) if r['match_path'] else 'NO MATCH'
        print(f"  {r['node']} (block {r['block_idx']}): {match_name} [{r['action']}]")
    
    for node, block_idx, should_match in expected_results:
        found = [r for r in results if r['node'] == node and r['block_idx'] == block_idx]
        if should_match:
            if not found:
                print(f"  FAIL: {node} block {block_idx} should match but didn't")
                all_pass = False
            elif found[0]['action'] != 'inserted':
                print(f"  FAIL: {node} block {block_idx} matched but action={found[0]['action']}")
                all_pass = False
            else:
                print(f"  PASS: {node} block {block_idx} inserted")
        else:
            if found and found[0]['action'] == 'inserted':
                print(f"  FAIL: {node} block {block_idx} should NOT match but did")
                all_pass = False
            else:
                print(f"  PASS: {node} block {block_idx} not inserted (correct)")
    
    return all_pass

all_pass = True

# Case 1: Basic single block (real commands)
all_pass &= test_case(
    "Basic single block",
    [
        MockParagraph('<HUAWEI>display device'),
        MockParagraph('<TUC-TEST01>'),
        MockParagraph('<TUC-TEST02>'),
    ],
    real_png_files,
    [('TUC-TEST01', 0, True), ('TUC-TEST02', 0, True)]
)

# Case 2: Nested command block (real commands)
all_pass &= test_case(
    "Nested command block",
    [
        MockParagraph('<HUAWEI>system-view'),
        MockParagraph('[HW]interface GigabitEthernet0/0/1'),
        MockParagraph('[HW-GigabitEthernet0/0/1]display this'),
        MockParagraph('[HW-GigabitEthernet0/0/1]quit'),
        MockParagraph('[HW]quit'),
        MockParagraph('<TUC-TEST01>'),
    ],
    real_png_files,
    [('TUC-TEST01', 0, True)]
)

# Case 3: Multiple blocks per cell (Option B - THE KEY CASE)
all_pass &= test_case(
    "Multiple blocks per cell (Option B)",
    [
        MockParagraph('<HUAWEI>display device'),
        MockParagraph('<TUC-TEST01>'),
        MockParagraph('<TUC-TEST02>'),
        MockParagraph('<HUAWEI>display clock'),
        MockParagraph('<TUC-TEST01>'),
        MockParagraph('<TUC-TEST02>'),
    ],
    real_png_files,
    [
        ('TUC-TEST01', 0, True), ('TUC-TEST02', 0, True),
        ('TUC-TEST01', 1, True), ('TUC-TEST02', 1, True),
    ]
)

# Case 4: Multi-model scenario (user's case)
all_pass &= test_case(
    "Multi-model: different NEs with devices",
    [
        MockParagraph('<TUC-TEST01>display device'),
        MockParagraph('<TUC-TEST02>'),
        MockParagraph('<TUC-TEST01>display clock'),
        MockParagraph('<TUC-TEST01>'),
    ],
    real_png_files,
    [('TUC-TEST02', 0, True), ('TUC-TEST01', 1, True)]
)

# Case 5: Error preference - should skip
all_pass &= test_case(
    "Error preference: skip error block",
    [
        MockParagraph('<TUC-TEST01>display cpu-usage'),
        MockParagraph('<TUC-TEST01>'),
    ],
    real_png_files,
    [('TUC-TEST01', 0, False)]
)

# Case 6: Block isolation
all_pass &= test_case(
    "Block isolation",
    [
        MockParagraph('<HUAWEI>display device'),
        MockParagraph('<TUC-TEST01>'),
        MockParagraph('<HUAWEI>display clock'),
        MockParagraph('<TUC-TEST01>'),
    ],
    real_png_files,
    [('TUC-TEST01', 0, True), ('TUC-TEST01', 1, True)]
)

# Case 7: Missing quit
all_pass &= test_case(
    "Cell without quit",
    [
        MockParagraph('<HUAWEI>system-view'),
        MockParagraph('[HW]interface GigabitEthernet0/0/1'),
        MockParagraph('[HW-GigabitEthernet0/0/1]display this'),
        MockParagraph('<TUC-TEST01>'),
    ],
    real_png_files,
    [('TUC-TEST01', 0, True)]
)

# Case 8: Empty nodes
all_pass &= test_case(
    "Cell with no nodes",
    [
        MockParagraph('<HUAWEI>display device'),
    ],
    real_png_files,
    []
)

# Case 9: Wrong command
all_pass &= test_case(
    "Wrong command - no PNG",
    [
        MockParagraph('<HUAWEI>display wrong-command'),
        MockParagraph('<TUC-TEST01>'),
    ],
    real_png_files,
    [('TUC-TEST01', 0, False)]
)

# Case 10: Real multi-block from testthisplease.docx Row 7
all_pass &= test_case(
    "Real multi-block from testthisplease.docx Row 7",
    [
        MockParagraph('<HUAWEI>system-view'),
        MockParagraph('[HW]interface GigabitEthernet0/0/1'),
        MockParagraph('[HW-GigabitEthernet0/0/1]display this'),
        MockParagraph('[HW-GigabitEthernet0/0/1]quit'),
        MockParagraph('[HW]quit'),
        MockParagraph('<TUC-TEST01>'),
        MockParagraph('<TUC-TEST02>'),
        MockParagraph('<TUC-TEST03>'),
        MockParagraph('<HUAWEI>display device'),
        MockParagraph('<TUC-TEST01>'),
        MockParagraph('<TUC-TEST02>'),
        MockParagraph('<TUC-TEST03>'),
        MockParagraph('<HUAWEI>display clock'),
        MockParagraph('<TUC-TEST01>'),
        MockParagraph('<TUC-TEST02>'),
        MockParagraph('<TUC-TEST03>'),
    ],
    real_png_files,
    [
        ('TUC-TEST01', 0, True), ('TUC-TEST02', 0, True), ('TUC-TEST03', 0, True),
        ('TUC-TEST01', 1, True), ('TUC-TEST02', 1, True), ('TUC-TEST03', 1, True),
        ('TUC-TEST01', 2, True), ('TUC-TEST02', 2, True), ('TUC-TEST03', 2, True),
    ]
)

# Case 11: Error + OK blocks from testthisplease.docx Row 8
all_pass &= test_case(
    "Error block + OK block",
    [
        MockParagraph('<HUAWEI>display wrong-command'),
        MockParagraph('<TUC-TEST01>'),
        MockParagraph('<TUC-TEST02>'),
        MockParagraph('<TUC-TEST03>'),
        MockParagraph('<HUAWEI>display device'),
        MockParagraph('<TUC-TEST01>'),
        MockParagraph('<TUC-TEST02>'),
        MockParagraph('<TUC-TEST03>'),
    ],
    real_png_files,
    [
        ('TUC-TEST01', 0, False), ('TUC-TEST02', 0, False), ('TUC-TEST03', 0, False),
        ('TUC-TEST01', 1, True), ('TUC-TEST02', 1, True), ('TUC-TEST03', 1, True),
    ]
)

print(f"\n{'='*60}")
print(f"OVERALL: {'ALL PASS' if all_pass else 'SOME FAILED'}")
print(f"{'='*60}")
