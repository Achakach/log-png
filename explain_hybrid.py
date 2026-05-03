import sys, os
sys.path.insert(0, '.')
from putpnginword import parse_paragraphs_detailed

class MP:
    def __init__(self, t): self.text = t

print("=== EXPLANATION: What I meant by the hybrid approach ===\n")

print("YOUR ORIGINAL GOAL:")
print("  CEx01 => display cpu-usage (good for TUC01)")
print("  CEx02 => display cpu (good for TUC02)")
print("  Then all devices: TUC01, TUC02, TUC03\n")

print("CURRENT BEHAVIOR (what we implemented = Option B):")
print("  If document structure is:")
print("    \u003cHUAWEI\u003edisplay cpu-usage")
print("    \u003cHUAWEI\u003edisplay cpu")
print("    \u003cTUC-TEST01\u003e")
print("    \u003cTUC-TEST02\u003e")
print("    \u003cTUC-TEST03\u003e")
print("  => ALL TUC01/02/03 are in Block 1 (last block: display cpu)")
print("  => Block 0 (display cpu-usage) has NO nodes!")
print("  => TUC01 never gets cpu-usage image\n")

paragraphs = [
    MP('\u003cHUAWEI\u003edisplay cpu-usage'),
    MP('\u003cHUAWEI\u003edisplay cpu'),
    MP('\u003cTUC-TEST01\u003e'),
    MP('\u003cTUC-TEST02\u003e'),
    MP('\u003cTUC-TEST03\u003e'),
]

blocks = parse_paragraphs_detailed(paragraphs)
for bi, (cmds, nodes) in enumerate(blocks):
    print(f"  Block {bi}: {cmds} -> nodes={[n for n,_ in nodes]}")

print("\n" + "="*60)
print("THE HYBRID APPROACH I WAS ASKING ABOUT:")
print("="*60)
print("""
What if when ALL nodes are at the end (like your modified Case 12),
the code does THIS instead:

1. For each node, try ALL blocks (not just its assigned block)
2. For each block, get the match
3. Prefer non-error over error
4. If all are error, skip

This would work like:
  TUC-TEST01: Block 0 (cpu-usage) matches?  -> YES, non-error -> INSERT
              Block 1 (cpu) matches?        -> maybe, but block 0 was OK so ignore
  
  TUC-TEST02: Block 0 (cpu-usage) matches?  -> maybe error -> FALLBACK to block 1
              Block 1 (cpu) matches?        -> YES, non-error -> INSERT
  
  TUC-TEST03: same as TUC01 or TUC02 depending on which command is correct
""")

print("BUT WAIT - the problem is: the code doesn't know WHICH device should use WHICH command!")
print("Unless you explicitly say in the document: TUC01 uses cpu-usage, TUC02 uses cpu")
print()
print("That's why I'm asking: do you want:")
print()
print("  A) Document structure shows order:")
print("       command-A, device-X, command-B, device-Y")
print("     => Each device naturally matches its preceding command")
print()
print("  B) All devices at bottom:")
print("       command-A, command-B, device-X, device-Y")
print("     => All devices currently go to last block")
print("     => If you change to 'try all blocks per device', EVERY device gets images from EVERY block")
print("     => 2 devices × 2 blocks = 4 images in 1 cell!")
print()
print("  C) ??? Something I haven't thought of")
print()
