from putpnginword import parse_paragraphs_detailed, _merge_empty_blocks, find_best_match, expand_abbreviations
import glob

# Test Table 13 scenario
print("=== Table 13: Error + Username ===")
print("DOCX: display current-configutation + Error: + username xxuser")
print()

# Available PNGs
png_files = glob.glob('screenshots/TUC-TEST01*configutation*.png')
for p in sorted(png_files):
    print(f"  {p.split(chr(92))[-1]}")

print("\n--- Test 1: Current behavior (prefer_error=True, no username filter) ---")
result = find_best_match('TUC-TEST01', ['display current-configutation'], png_files, prefer_error=True)
print(f"Match: {result.split(chr(92))[-1] if result else 'None'}")

print("\n--- Test 2: With username (should require username tag) ---")
# This simulates what user wants: match should also consider username
result = find_best_match('TUC-TEST01', ['display current-configutation', 'username xxuser'], png_files, prefer_error=True)
print(f"Match: {result.split(chr(92))[-1] if result else 'None'}")

print("\n--- Test 3: No error preference, with username ---")
result = find_best_match('TUC-TEST01', ['display current-configutation', 'username xxuser'], png_files, prefer_error=False)
print(f"Match: {result.split(chr(92))[-1] if result else 'None'}")

print("\n--- Analysis ---")
print("Available TUC-TEST01 display current-configutation PNGs:")
for p in sorted(glob.glob('screenshots/TUC-TEST01*current*.png')):
    name = p.split(chr(92))[-1]
    has_error = '[error]' in name
    has_username = 'username' in name
    print(f"  {name:60s} error={has_error}, username={has_username}")
