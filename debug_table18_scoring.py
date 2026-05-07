import glob
from putpnginword import find_best_match, expand_abbreviations, sanitize_filename

png_files = glob.glob('screenshots/TUC-TEST01*display*current*.png')

# Trace find_best_match for Table 18 scenario
device = 'TUC-TEST01'
commands = expand_abbreviations(['display current-configuration', 'username kacha1'])

print(f'Device: {device}')
print(f'Commands: {commands}')
print(f'PNG files: {[p.split(chr(92))[-1] for p in png_files]}')
print()

# Manually call find_best_match with tracing
import os
import re

# Step 1: Build search tokens
search_tokens = sanitize_filename(device).lower().split()
for cmd in commands:
    search_tokens.extend(sanitize_filename(cmd).lower().split())

# Extract and remove "username VALUE" tag from search tokens
cell_username = None
for i in range(len(search_tokens) - 1):
    if search_tokens[i] == 'username':
        cell_username = search_tokens[i + 1]
        del search_tokens[i:i + 2]
        break

print(f'Search tokens after username strip: {search_tokens}')
print(f'Cell username: {cell_username}')

# Strip quit
while len(search_tokens) > 1 and search_tokens[-1] == 'quit':
    search_tokens.pop()

cmd_tokens = search_tokens[1:]
print(f'Command tokens: {cmd_tokens}')

# Canonicalize
if cmd_tokens:
    cmd_tokens = expand_abbreviations([' '.join(cmd_tokens)])[0].split()
    print(f'Canonicalized: {cmd_tokens}')

print()

# Now trace each PNG
for png_path in png_files:
    png_name = os.path.basename(png_path).replace('.png', '').lower()
    png_tokens = png_name.split()
    
    # Device match
    if not png_tokens or png_tokens[0] != search_tokens[0]:
        print(f'{png_name}: Device mismatch')
        continue
    
    # Strip quit
    png_cmd_tokens = png_tokens[1:]
    while png_cmd_tokens and png_cmd_tokens[-1] in ('quit', '[error]'):
        png_cmd_tokens.pop()
    
    # Extract username
    png_username = None
    for i in range(len(png_cmd_tokens) - 1):
        if png_cmd_tokens[i] == 'username':
            png_username = png_cmd_tokens[i + 1]
            del png_cmd_tokens[i:i + 2]
            break
    
    # Username filter
    if cell_username != png_username:
        print(f'{png_name}: USERNAME MISMATCH (cell={cell_username}, png={png_username})')
        continue
    else:
        print(f'{png_name}: Username OK (both={cell_username})')
    
    # Canonicalize
    if png_cmd_tokens:
        png_cmd_tokens = expand_abbreviations([' '.join(png_cmd_tokens)])[0].split()
    
    # Check token count
    if len(png_cmd_tokens) != len(cmd_tokens):
        print(f'  Token count mismatch: {len(png_cmd_tokens)} vs {len(cmd_tokens)}')
        continue
    
    # Compare tokens
    match = png_cmd_tokens == cmd_tokens
    print(f'  Final tokens: {png_cmd_tokens}')
    print(f'  Match: {match}')
    
    if match:
        print(f'  -> ** VALID MATCH **')
