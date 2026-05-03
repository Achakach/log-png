import sys
sys.path.insert(0, '.')
from putpnginword import parse_paragraphs_detailed

class MockParagraph:
    def __init__(self, text):
        self.text = text

# User's exact scenario:
# Cxx01,<HW>cmd1.1,Cxx02,<HW>cmd1.2
# <device1(cmd1.2)>,<device2(cmd1.1)>

# This means the cell content is:
# <Cxx01>cmd1.1
# <device2>               ← should match cmd1.1 (block 0)
# <Cxx02>cmd1.2
# <device1>               ← should match cmd1.2 (block 1)

print("=== User's Multi-Model Scenario ===\n")

paragraphs = [
    MockParagraph('<Cxx01>cmd1.1'),
    MockParagraph('<device2>'),
    MockParagraph('<Cxx02>cmd1.2'),
    MockParagraph('<device1>'),
]

print("Input paragraphs:")
for i, p in enumerate(paragraphs):
    print(f"  {i}: {p.text}")

print("\nParsed blocks:")
blocks = parse_paragraphs_detailed(paragraphs)
for bi, (cmds, nodes) in enumerate(blocks):
    print(f"  Block {bi}: commands={cmds}")
    for node, para_idx in nodes:
        print(f"    - {node} (para {para_idx})")

# What actually happens:
# Para 0: <Cxx01>cmd1.1 → current_commands = ['cmd1.1'], nodes = []
# Para 1: <device2> → nodes = [('device2', 1)]
# Para 2: <Cxx02>cmd1.2 → standalone user-view after existing commands!
#         → blocks.append((['cmd1.1'], [('device2', 1)]))
#         → current_commands = ['cmd1.2'], nodes = []
# Para 3: <device1> → nodes = [('device1', 3)]
# End: blocks.append((['cmd1.2'], [('device1', 3)]))

print("\nExpected:")
print("  Block 0: ['cmd1.1'] with nodes=[('device2', 1)]")
print("  Block 1: ['cmd1.2'] with nodes=[('device1', 3)]")

print("\nActual:")
if len(blocks) == 2:
    print(f"  ✅ Block 0: {blocks[0][0]} with {blocks[0][1]}")
    print(f"  ✅ Block 1: {blocks[1][0]} with {blocks[1][1]}")
    
    # Verify
    assert blocks[0] == (['cmd1.1'], [('device2', 1)]), "Block 0 incorrect"
    assert blocks[1] == (['cmd1.2'], [('device1', 3)]), "Block 1 incorrect"
    print("\n  ✅ VERIFIED: Each node is correctly associated with its preceding command block!")
else:
    print(f"  ❌ Got {len(blocks)} blocks instead of 2:")
    for bi, (cmds, nodes) in enumerate(blocks):
        print(f"    Block {bi}: {cmds}, {nodes}")

# Now test with match_cell_blocks
from putpnginword import match_cell_blocks

png_files = [
    'device1 cmd1.2.png',
    'device2 cmd1.1.png',
]

print("\n=== Matching ===")
results = match_cell_blocks(paragraphs, png_files)
for r in results:
    if r['match_path']:
        import os
        print(f"  Block {r['block_idx']}: {r['node']} -> {os.path.basename(r['match_path'])} [{r['action']}]")
    else:
        print(f"  Block {r['block_idx']}: {r['node']} -> NO MATCH [{r['action']}]")

# Verify device2 matches cmd1.1 and device1 matches cmd1.2
device2_results = [r for r in results if r['node'] == 'device2']
device1_results = [r for r in results if r['node'] == 'device1']

print("\nVerification:")
if device2_results:
    r = device2_results[0]
    assert r['block_idx'] == 0, f"Expected block 0, got {r['block_idx']}"
    assert 'cmd1.1' in r['match_path'], f"Expected cmd1.1 match"
    print(f"  ✅ device2 -> block 0, cmd1.1")
else:
    print(f"  ❌ device2 not found")

if device1_results:
    r = device1_results[0]
    assert r['block_idx'] == 1, f"Expected block 1, got {r['block_idx']}"
    assert 'cmd1.2' in r['match_path'], f"Expected cmd1.2 match"
    print(f"  ✅ device1 -> block 1, cmd1.2")
else:
    print(f"  ❌ device1 not found")

print("\n=== Result: MULTI-MODEL CASE WORKS CORRECTLY ===")
