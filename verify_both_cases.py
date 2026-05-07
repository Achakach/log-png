import glob
from putpnginword import find_best_match

png_files = glob.glob('screenshots/*.png')

print("=== Case 1: Standalone dis cur (no SSH, no username) ===")
print("DOCX: <TUCxx01>display current-configuration")
target1 = ['TUCxx01 display current-configuration.png', 'TUCxx01 dis cur.png']
# Find matching PNGs
for png_name in target1:
    full_path = f'screenshots/{png_name}'
    if full_path in png_files:
        result = find_best_match('TUCxx01', ['display current-configuration'], [full_path])
        print(f"  Match {png_name}: {'YES' if result else 'NO'}")

print("\n=== Case 2: SSH with username ===")
print("DOCX: <TUCxx01>display current-configuration + username kacha1")
target2 = [
    'TUCxx01 display current-configuration username kacha1.png',
    'TUCxx01 dis cur username kacha1.png'
]
for png_name in target2:
    full_path = f'screenshots/{png_name}'
    if full_path in png_files:
        result = find_best_match('TUCxx01', ['username kacha1', 'display current-configuration'], [full_path])
        print(f"  Match {png_name}: {'YES' if result else 'NO'}")

print("\n=== Case 3: DOCX without username, PNG has username (should NOT match) ===")
print("DOCX: <TUCxx01>display current-configuration")  
png_with_user = [p for p in png_files if 'username kacha1' in p and 'TUCxx01' in p]
for p in png_with_user:
    result = find_best_match('TUCxx01', ['display current-configuration'], [p])
    print(f"  Match {p}: {'YES (BUG!)' if result else 'NO (Correct - skipped)'}")

print("\n=== Available TUCxx01 PNGs ===")
for p in sorted(glob.glob('screenshots/TUCxx01*.png')):
    print(f"  {p}")
