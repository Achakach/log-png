import sys, os
sys.path.insert(0, '.')
from putpnginword import parse_paragraphs_detailed, match_cell_blocks, _merge_empty_blocks

class MP:
    def __init__(self, t): self.text = t

print("=== Test: Case 12 (empty block merge) ===\n")

# Case 12: Empty block followed by block with nodes
paragraphs = [
    MP('CEx01'),
    MP('<HUAWEI>display cpu-usage'),
    MP('CEx02'),
    MP('<HUAWEI>display cpu'),
    MP('<TUC-TEST01>'),
    MP('<TUC-TEST02>'),
]

blocks = parse_paragraphs_detailed(paragraphs)
print("Before merge:")
for bi, (cmds, nodes) in enumerate(blocks):
    print(f"  Block {bi}: {cmds} -> nodes={[n for n,_ in nodes]}")

merged = _merge_empty_blocks(blocks)
print("\nAfter merge:")
for bi, (cmds, nodes) in enumerate(merged):
    print(f"  Block {bi}: {cmds} -> nodes={[n for n,_ in nodes]}")

# Verify
assert len(merged) == 1
assert merged[0][0] == ['display cpu-usage', 'display cpu']
assert [n for n,_ in merged[0][1]] == ['TUC-TEST01', 'TUC-TEST02']
print("\n✅ Merge correct: ['display', 'cpu-usage', 'display', 'cpu'] -> [TUC01, TUC02]")

# Now test matching (with mock PNGs)
png_files = [
    'TUC-TEST01 display cpu-usage.png',
    'TUC-TEST02 display cpu.png',
    'TUC-TEST01 display cpu [error].png',
    'TUC-TEST02 display cpu-usage [error].png',
]

results = match_cell_blocks(paragraphs, png_files)
print("\nMatch results:")
for r in results:
    match_name = os.path.basename(r['match_path']) if r['match_path'] else 'NO MATCH'
    print(f"  {r['node']}: {match_name} [{r['action']}]")

# Verify TUC01 gets cpu-usage, TUC02 gets cpu
tuc01_result = [r for r in results if r['node'] == 'TUC-TEST01'][0]
tuc02_result = [r for r in results if r['node'] == 'TUC-TEST02'][0]

assert 'cpu-usage' in tuc01_result['match_path']
assert 'cpu' in tuc02_result['match_path']
assert '[error]' not in tuc01_result['match_path'], "TUC01 should not get error"
assert '[error]' not in tuc02_result['match_path'], "TUC02 should not get error"

print("\n✅ CORRECT:")
print("  TUC01 gets cpu-usage (correct for its model)")
print("  TUC02 gets cpu (correct for its model)")
print("  Both skip error PNGs!")
