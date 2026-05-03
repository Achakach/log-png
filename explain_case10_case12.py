import sys
sys.path.insert(0, '.')
from putpnginword import parse_paragraphs_detailed

class MP:
    def __init__(self, t): self.text = t

print("=== Case 10: Nested + Standalone Commands ===\n")

paragraphs = [
    MP('<HUAWEI>system-view'),
    MP('[HW]interface GigabitEthernet0/0/1'),
    MP('[HW-GigabitEthernet0/0/1]display this'),
    MP('[HW-GigabitEthernet0/0/1]quit'),
    MP('[HW]quit'),
    MP('<TUC-TEST01>'),
    MP('<TUC-TEST02>'),
    MP('<TUC-TEST03>'),
    MP('<HUAWEI>display device'),
    MP('<TUC-TEST01>'),
    MP('<TUC-TEST02>'),
    MP('<TUC-TEST03>'),
    MP('<HUAWEI>display clock'),
    MP('<TUC-TEST01>'),
    MP('<TUC-TEST02>'),
    MP('<TUC-TEST03>'),
]

blocks = parse_paragraphs_detailed(paragraphs)
print('Parsed blocks:')
for bi, (cmds, nodes) in enumerate(blocks):
    node_list = [n for n,_ in nodes]
    print(f'  Block {bi}: {cmds}')
    print(f'    nodes={node_list} at para_idx={nodes}')

print(f'\n✅ Current Result: {len(blocks)} blocks × 3 nodes = {len(blocks)*3} images')
print('   (TUC01 gets 3 images, TUC02 gets 3, TUC03 gets 3)')

print('\n---\n')

print('❌ If we MERGE all blocks:')
print('   Block 0: ALL commands = [<system-view...>, display device, display clock]')
print('   nodes = ALL TUCs')
print('   TUC01 tries system-view... first → matches → INSERT')
print('   Skips display device and display clock')
print('   => TUC01 only gets 1 image instead of 3!')
print('   => Total: 3 images instead of 9')

print('\n---\n')

print('✅ SAFER SOLUTION:')
print('   DON\'T merge when nodes are inline with their commands!')
print('   Only merge when ALL nodes are at the BOTTOM (no inline nodes).')

# Simulate what we want for Case 12
print('\n=== Case 12: What You Want ===')

paragraphs2 = [
    MP('CEx01'),
    MP('<HUAWEI>display cpu-usage'),
    MP('CEx02'),
    MP('<HUAWEI>display cpu'),
    MP('<TUC-TEST01>'),
    MP('<TUC-TEST02>'),
]

blocks2 = parse_paragraphs_detailed(paragraphs2)
print('Parsed blocks:')
for bi, (cmds, nodes) in enumerate(blocks2):
    node_list = [n for n,_ in nodes]
    print(f'  Block {bi}: {cmds}')
    print(f'    nodes={node_list}')

print('\n  Problem: Block 0 has no nodes!')
print('  All nodes go to Block 1 (last block)')
print('  => TUC01 never tries display cpu-usage')

print('\n  SOLUTION: Merge blocks because ALL nodes are at the END')
print('  Merged block: [display cpu-usage, display cpu]')
print('  nodes: [TUC01, TUC02]')
print('  TUC01 tries cpu-usage → match → INSERT')
print('  TUC02 tries cpu-usage → error → skip → tries cpu → match → INSERT')
print('  => Both TUC01 and TUC02 get images! ✅')
