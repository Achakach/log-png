import sys
sys.path.insert(0, '.')
from putpnginword import parse_paragraphs_detailed

class MP:
    def __init__(self, t): self.text = t

print("=== CLARIFICATION: How Standalone Blocks Merge ===\n")

print("EXAMPLE 1: Case 12 (your scenario)")
paragraphs1 = [
    MP('CEx01'),
    MP('<HUAWEI>display cpu-usage'),
    MP('CEx02'),
    MP('<HUAWEI>display cpu'),
    MP('<TUC-TEST01>'),
    MP('<TUC-TEST02>'),
]

blocks1 = parse_paragraphs_detailed(paragraphs1)
print("Parsed:")
for bi, (cmds, nodes) in enumerate(blocks1):
    print(f"  Block {bi}: {cmds} -> nodes={[n for n,_ in nodes]}")

print("\nYour understanding:")
print("  'standalone block that don't have node under it will be merge into next standalone'")
print("\nALMOST correct, but more precisely:")
print("  'If ANY standalone block has NO nodes, MERGE ALL standalone blocks into ONE pool'")
print("\nSo it's not Block 0 merging into Block 1.")
print("It's ALL standalone blocks becoming ONE big block:")
print("  [display cpu-usage, display cpu] -> nodes=[TUC01, TUC02]")

print("\n" + "="*60)
print("\nEXAMPLE 2: Multiple standalone blocks with inline nodes")
paragraphs2 = [
    MP('<HUAWEI>display device'),
    MP('<TUC-TEST01>'),
    MP('<HUAWEI>display clock'),
    MP('<TUC-TEST02>'),
]

blocks2 = parse_paragraphs_detailed(paragraphs2)
print("Parsed:")
for bi, (cmds, nodes) in enumerate(blocks2):
    print(f"  Block {bi}: {cmds} -> nodes={[n for n,_ in nodes]}")

print("\nHere, ALL blocks have nodes (inline).")
print("Rule: DON'T merge because every block has its own nodes.")
print("Result: TUC01 matches device, TUC02 matches clock (same as current)")

print("\n" + "="*60)
print("\nEXAMPLE 3: Mix of empty and filled blocks")
paragraphs3 = [
    MP('<HUAWEI>display device'),
    MP('<HUAWEI>display clock'),
    MP('<TUC-TEST01>'),
    MP('<TUC-TEST02>'),
]

blocks3 = parse_paragraphs_detailed(paragraphs3)
print("Parsed:")
for bi, (cmds, nodes) in enumerate(blocks3):
    print(f"  Block {bi}: {cmds} -> nodes={[n for n,_ in nodes]}")

print("\nHere, Block 0 has NO nodes, Block 1 has ALL nodes.")
print("Rule: MERGE because some blocks are empty -> nodes at bottom.")
print("Merged: [display device, display clock] -> nodes=[TUC01, TUC02]")
print("Result: TUC01 tries device first -> match -> INSERT")
print("        TUC02 tries device first -> match -> INSERT (if not error)")
print("        (clock might never be tried if device matches first)")

print("\n" + "="*60)
print("\nCORRECT UNDERSTANDING:")
print("="*60)
print("1. Separate NESTED zone (system-view) from STANDALONE zone")
print("2. In STANDALONE zone, check if ANY block has ZERO nodes")
print("3. If YES -> MERGE ALL standalone blocks into ONE pool")
print("4. All bottom nodes try ALL commands in the pool")
print("5. If NO (all blocks have nodes) -> keep separate, works as before")
