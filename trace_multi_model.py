from docx import Document
import sys
sys.path.insert(0, '.')
from putpnginword import parse_paragraphs_detailed

# Create a test specifically based on document structure example.docx Table 3
# User pattern: Cxx01,<HW>cmd1.1,Cxx02,<HW>cmd1.2 <device1(cmd1.2)>,<device2(cmd1.1)>

# Let's recreate what would be inside a Word cell

print("=== CASE: Multiple models, devices appearing after their specific blocks ===\n")

# Simulating Word paragraphs (each node on its own line in a paragraph)
class MockParagraph:
    def __init__(self, text):
        self.text = text

# This is your exact case
paragraphs = [
    MockParagraph('<Cxx01>cmd1.1'),
    MockParagraph('<Cxx02>cmd1.2'),
    MockParagraph('<device1>'),    # This should match cmd1.2 (block 1)
    MockParagraph('<device2>'),    # This should match cmd1.1 (block 0)
]

print("Input:")
for i, p in enumerate(paragraphs):
    print(f"  Para {i}: {p.text}")

print("\nParsed blocks:")
blocks = parse_paragraphs_detailed(paragraphs)
for bi, (cmds, nodes) in enumerate(blocks):
    print(f"  Block {bi}: cmds={cmds}, nodes={nodes}")
    # Expected:
    # Block 0: ['cmd1.1'], nodes=[('device2', 3?)]
    # Wait - device2 appears BEFORE device1 in the input...
    # But actually device1 is after block 1 (cmd1.2), device2 is after block 0 (cmd1.1)
    # Let's trace carefully.

# Actually wait - the parse_paragraphs_detailed logic:
# For each paragraph:
#   - If node: add to current block's nodes
#   - If prompt+cmd: add to current block's commands
#   - If standalone user-view AFTER existing commands: start NEW block

# Para 0: <Cxx01>cmd1.1 → current_commands = ['cmd1.1']
# Para 1: <Cxx02>cmd1.2 → standalone user-view after existing commands!
#         → blocks.append((['cmd1.1'], nodes_so_far))
#         → current_commands = ['cmd1.2']
#         → nodes = []
# Para 2: <device1> → nodes = [('device1', 2)]
# Para 3: <device2> → nodes = [('device1', 2), ('device2', 3)]  # BOTH in block 1!

print("\n*** ISSUE: With current logic, BOTH device1 and device2 end up in Block 1 ***")
print("Because the standalone user-view command at para 1 starts a new block,")
print("but all subsequent nodes go into THAT new block.")
print("\nCurrent result:")
for bi, (cmds, nodes) in enumerate(blocks):
    print(f"  Block {bi}: cmds={cmds}")
    for node, para_idx in nodes:
        print(f"    Node {node} at para {para_idx}")

print("\nExpected (your requirement):")
print("  Block 0: cmds=['cmd1.1'], nodes=[('device2', 3)]")
print("  Block 1: cmds=['cmd1.2'], nodes=[('device1', 2)]")
print("\n=> The current parse_paragraphs_detailed() does NOT handle 'nodes BEFORE block start' correctly!")
