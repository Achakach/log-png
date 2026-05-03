"""Helper script to understand and test the merge logic before implementing."""
import sys
sys.path.insert(0, '.')
from putpnginword import parse_paragraphs_detailed, expand_abbreviations, find_best_match
import os

class MP:
    def __init__(self, t): self.text = t

def merge_empty_blocks(blocks):
    """Merge empty standalone blocks into the next block with nodes.
    
    Rule: If a block has commands but NO nodes, prepend its commands to the NEXT block.
    Skip blocks that already have nodes (don't touch them).
    """
    if not blocks:
        return blocks
    
    merged = []
    pending_commands = []  # Commands from empty blocks waiting to be merged
    
    for bi, (commands, nodes) in enumerate(blocks):
        if not commands:
            continue
            
        if nodes:
            # This block has nodes - prepend any pending commands
            if pending_commands:
                merged_commands = pending_commands + commands
                merged.append((merged_commands, nodes))
                pending_commands = []
            else:
                merged.append((commands, nodes))
        else:
            # No nodes - save commands to prepend to next block
            pending_commands.extend(commands)
    
    # If last block had no nodes and no subsequent block, commands are lost
    # (which is correct - no nodes to match against)
    
    return merged

# Test cases
print("=== Test 1: Case 12 (empty block followed by block with nodes) ===")
blocks1 = [
    (['display', 'cpu-usage'], []),
    (['display', 'cpu'], [('TUC-TEST01', 4), ('TUC-TEST02', 5)]),
]
print(f"Before: {blocks1}")
merged1 = merge_empty_blocks(blocks1)
print(f"After:  {merged1}")

print("\n=== Test 2: Case 6 (both blocks have nodes, no merge) ===")
blocks2 = [
    (['display', 'device'], [('TUC-TEST01', 1)]),
    (['display', 'clock'], [('TUC-TEST01', 3)]),
]
print(f"Before: {blocks2}")
merged2 = merge_empty_blocks(blocks2)
print(f"After:  {merged2}")

print("\n=== Test 3: Case 10 (nested + standalone, all have nodes) ===")
blocks3 = [
    (['system-view', 'interface', 'display', 'this', 'quit', 'quit'], [('TUC-TEST01', 5)]),
    (['display', 'device'], [('TUC-TEST01', 9)]),
    (['display', 'clock'], [('TUC-TEST01', 13)]),
]
print(f"Before: {blocks3}")
merged3 = merge_empty_blocks(blocks3)
print(f"After:  {merged3}")

print("\n=== Test 4: Multiple empty blocks ===")
blocks4 = [
    (['cmd', '1'], []),
    (['cmd', '2'], []),
    (['cmd', '3'], [('TUC-TEST01', 2)]),
]
print(f"Before: {blocks4}")
merged4 = merge_empty_blocks(blocks4)
print(f"After:  {merged4}")

print("\n=== Test 5: Empty block at end (no merge possible) ===")
blocks5 = [
    (['display', 'device'], [('TUC-TEST01', 1)]),
    (['display', 'clock'], []),
]
print(f"Before: {blocks5}")
merged5 = merge_empty_blocks(blocks5)
print(f"After:  {merged5}")

print("\n" + "="*60)
print("VERIFICATION:")
print("="*60)
assert merged1 == [(['display', 'cpu-usage', 'display', 'cpu'], [('TUC-TEST01', 4), ('TUC-TEST02', 5)])]
assert merged2 == blocks2
assert merged3 == blocks3
assert merged4 == [(['cmd', '1', 'cmd', '2', 'cmd', '3'], [('TUC-TEST01', 2)])]
assert merged5 == [(['display', 'device'], [('TUC-TEST01', 1)])]
print("✅ All assertions pass!")
