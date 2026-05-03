import sys
import os
sys.path.insert(0, '.')

from putpnginword import parse_paragraphs_detailed, match_cell_blocks

class MockParagraph:
    def __init__(self, text):
        self.text = text

# Scenario: Multiple models (Cxx01, Cxx02) each with their own command,
# then devices appear after specific blocks

# Test case from user:
# Cxx01,<HW>cmd1.1,Cxx02,<HW>cmd1.2
# <device1(cmd1.2)>,<device2(cmd1.1)>

# This means:
# Block 0: Cxx01 runs cmd1.1
# Block 1: Cxx02 runs cmd1.2
# Then: device1 should show cmd1.2 (block 1)
#       device2 should show cmd1.1 (block 0)

paragraphs = [
    MockParagraph('<Cxx01>cmd1.1'),
    MockParagraph('<device2>'),       # belongs to block 0
    MockParagraph('<Cxx02>cmd1.2'),
    MockParagraph('<device1>'),       # belongs to block 1
]

print("=== Parsing Result ===")
blocks = parse_paragraphs_detailed(paragraphs)
for bi, (cmds, nodes) in enumerate(blocks):
    print(f"Block {bi}: commands={cmds}, nodes={nodes}")

print("\n=== Matching with PNGs ===")
png_files = [
    'device1 cmd1.2.png',
    'device2 cmd1.1.png',
]

results = match_cell_blocks(paragraphs, png_files)
for r in results:
    print(f"Block {r['block_idx']}: {r['node']} -> {os.path.basename(r['match_path']) if r['match_path'] else 'NO MATCH'} [{r['action']}]")

# Verify
print("\n=== Verification ===")
device2_result = [r for r in results if r['node'] == 'device2']
device1_result = [r for r in results if r['node'] == 'device1']

if device2_result:
    r = device2_result[0]
    assert r['block_idx'] == 0, f"device2 should be in block 0, got {r['block_idx']}"
    assert 'cmd1.1' in (r['match_path'] or ''), f"device2 should match cmd1.1"
    print("PASS: device2 matched cmd1.1 in block 0")
else:
    print("FAIL: device2 not found")

if device1_result:
    r = device1_result[0]
    assert r['block_idx'] == 1, f"device1 should be in block 1, got {r['block_idx']}"
    assert 'cmd1.2' in (r['match_path'] or ''), f"device1 should match cmd1.2"
    print("PASS: device1 matched cmd1.2 in block 1")
else:
    print("FAIL: device1 not found")
