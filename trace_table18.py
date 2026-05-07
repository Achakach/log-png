from putpnginword import parse_paragraphs_detailed, _merge_empty_blocks, find_best_match, expand_abbreviations
import glob

# Simulate Table 18 cell
class FakePara:
    def __init__(self, text):
        self._text = text
    @property
    def text(self):
        return self._text

paras = [FakePara(t) for t in [
    '<HUAWEI>display current-configuration',
    '<HUAWEI>username kacha1',
    '<TUC-TEST01>',
    '<TUC-TEST02>', 
    '<TUC-TEST03>',
]]

blocks = parse_paragraphs_detailed(paras)
merged = _merge_empty_blocks(blocks)

print('=== Parsed Blocks ===')
for i, (cmds, nodes, err) in enumerate(merged):
    print(f'Block {i}: cmds={cmds}, nodes={[n[0] for n in nodes]}, error={err}')

# Simulate matching for non-merged block
png_files = glob.glob('screenshots/TUC-TEST01*.png')

for block_idx, (commands, block_nodes, expect_error) in enumerate(merged):
    if not commands or not block_nodes:
        continue
        
    expanded_commands = expand_abbreviations(commands)
    print(f'\n=== Matching Block {block_idx} ===')
    print(f'Commands: {commands}')
    print(f'Expanded: {expanded_commands}')
    print(f'Nodes: {[n[0] for n in block_nodes]}')
    
    # This matches the actual logic in match_cell_blocks
    for node, para_idx in block_nodes:
        print(f'\n  Node: {node}')
        
        # For non-merged block, try full command sequence
        match_result = find_best_match(
            node, expanded_commands, png_files, prefer_error=expect_error
        )
        if match_result:
            print(f'  -> MATCH: {match_result.split(chr(92))[-1]}')
        else:
            print(f'  -> NO MATCH')
