from putpnginword import find_best_match, expand_abbreviations
import glob

# Test strict username + error matching for Table 13
png_files = glob.glob('screenshots/TUC-TEST01*current*.png')
print("Available PNGs:")
for p in sorted(png_files):
    print(f"  {p.split(chr(92))[-1]}")

print("\n=== Test 1: Error + username (DOCX has both) ===")
# This simulates the merged block from Table 13
cmds = expand_abbreviations(['display current-configutation', 'username xxuser'])
print(f"Commands: {cmds}")

result = find_best_match('TUC-TEST01', cmds, png_files, prefer_error=True)
print(f"Match with prefer_error=True: {result.split(chr(92))[-1] if result else 'None'}")

# Try without prefer_error
result = find_best_match('TUC-TEST01', cmds, png_files, prefer_error=False)
print(f"Match with prefer_error=False: {result.split(chr(92))[-1] if result else 'None'}")

print("\n=== Test 2: Error only (no username in DOCX) ===")
cmds_no_user = ['display current-configutation']
result = find_best_match('TUC-TEST01', cmds_no_user, png_files, prefer_error=True)
print(f"Match: {result.split(chr(92))[-1] if result else 'None'}")

print("\n=== What we need ===")
print("Need: TUC-TEST01 display current-configutation username xxuser [error].png")
print("But available:")
for p in sorted(png_files):
    name = p.split(chr(92))[-1]
    has_error = '[error]' in name
    has_user = 'username' in name
    print(f"  {name:60s} error={has_error}, username={has_user}")
