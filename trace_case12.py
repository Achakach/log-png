import sys, os
sys.path.insert(0, '.')
from putpnginword import parse_paragraphs_detailed, match_cell_blocks

class MP:
    def __init__(self, t): self.text = t

paragraphs = [
    MP('CEx01'),
    MP('<HUAWEI>display cpu-usage'),
    MP('CEx02'),
    MP('<HUAWEI>display cpu'),
    MP('<TUC-TEST01>'),
    MP('<TUC-TEST02>'),
    MP('<TUC-TEST03>'),
]

print('=== Case 12 as Modified by User ===')
print('Input:')
for i, p in enumerate(paragraphs):
    print(f'  {i}: {p.text}')

blocks = parse_paragraphs_detailed(paragraphs)
print(f'\nParsed blocks ({len(blocks)}):')
for bi, (cmds, nodes) in enumerate(blocks):
    print(f'  Block {bi}: cmds={cmds}, nodes={nodes}')

png_files = [os.path.join('screenshots', f) for f in os.listdir('screenshots') if f.endswith('.png')]
results = match_cell_blocks(paragraphs, png_files)
print(f'\nMatch results ({len(results)}):')
for r in results:
    match_name = os.path.basename(r['match_path']) if r['match_path'] else 'NO MATCH'
    print(f"  {r['node']} (block {r['block_idx']}): {match_name} [{r['action']}]")

# Check if first block non-error match exists
first_block_results = [r for r in results if r['block_idx'] == 0]
second_block_results = [r for r in results if r['block_idx'] == 1]

print(f'\nAnalysis:')
print(f'  Block 0 results: {len(first_block_results)}')
print(f'  Block 1 results: {len(second_block_results)}')

if first_block_results:
    print(f"  First block nodes: {[r['node'] for r in first_block_results]}")
    print("  => Nodes would match 'display cpu-usage' (first command)")
else:
    print("  First block has NO nodes!")
    print("  => All nodes go to block 1 'display cpu' (last command)")
    if second_block_results:
        for r in second_block_results:
            match_name = os.path.basename(r['match_path']) if r['match_path'] else 'NO MATCH'
            has_error = '[error]' in match_name
            print(f"    {r['node']} matches {match_name} (error={has_error})")
            if has_error:
                print(f"    -> SKIPPED (as intended by user)")
            else:
                print(f"    -> Would insert")
