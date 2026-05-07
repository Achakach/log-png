import glob
from putpnginword import find_best_match

png_files = glob.glob('screenshots/*.png')

print("=== Case 1: Standalone display current-configuration (no SSH, no username) ===")
print("DOCX commands: ['display current-configuration']")
standalone_pngs = [p for p in png_files if 'TUCxx01' in p and 'username' not in p]
if standalone_pngs:
    for p in standalone_pngs:
        result = find_best_match('TUCxx01', ['display current-configuration'], [p])
        print(f"  ✓{'MATCH' if result else 'NO MATCH'}: {p.split('/')[-1]}")
else:
    print("  (No standalone PNG found)")

print("\n=== Case 2: SSH merge with username ===")
print("DOCX commands: ['username kacha1', 'display current-configuration']")
ssh_pngs = [p for p in png_files if 'TUCxx01' in p and 'username' in p]
for p in ssh_pngs:
    result = find_best_match('TUCxx01', ['username kacha1', 'display current-configuration'], [p])
    print(f"  ✓{'MATCH' if result else 'NO MATCH'}: {p.split('/')[-1]}")

print("\n=== Case 3: DOCX without username, PNG has username (should NOT match) ===")
print("DOCX commands: ['display current-configuration']")
for p in ssh_pngs:
    result = find_best_match('TUCxx01', ['display current-configuration'], [p])
    print(f"  ✓{'MATCH (BUG!)' if result else 'NO MATCH (Correct)'}: {p.split('/')[-1]}")

print("\n=== Available TUCxx01 PNGs ===")
for p in sorted(glob.glob('screenshots/TUCxx01*.png')):
    parts = p.split('/')[-1].replace('.png', '').split()
    print(f"  {p.split('/')[-1]}")
