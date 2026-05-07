from putpnginword import find_best_match

print("=== Test: Username Filter Logic ===\n")

# Case 1: DOCX no username, PNG has username → SKIP
print("Case 1: DOCX no username vs PNG with username → SKIP")
png1 = ['screenshots/TUCxx01 dis cur username kacha1.png']
result = find_best_match('TUCxx01', ['dis cur'], png1)
print(f"  Result: {result}")
print(f"  Expected: None (username mismatch)")

# Case 2: DOCX no username, PNG no username → MATCH
print("\nCase 2: DOCX no username vs PNG no username → MATCH")
png2 = ['screenshots/TUCxx01 dis cur.png']
result = find_best_match('TUCxx01', ['dis cur'], png2)
print(f"  Result: {result}")
print(f"  Expected: screenshots/TUCxx01 dis cur.png")

# Case 3: DOCX has username, PNG has same username → MATCH
print("\nCase 3: DOCX username=kacha1 vs PNG username=kacha1 → MATCH")
png3 = ['screenshots/TUCxx01 display current-configuration username kacha1.png']
result = find_best_match('TUCxx01', ['username kacha1', 'display current-configuration'], png3)
print(f"  Result: {result}")
print(f"  Expected: screenshots/TUCxx01 display current-configuration username kacha1.png")

# Case 4: DOCX has username, PNG has different username → SKIP
print("\nCase 4: DOCX username=admin vs PNG username=kacha1 → SKIP")
result = find_best_match('TUCxx01', ['username admin', 'display current-configuration'], png3)
print(f"  Result: {result}")
print(f"  Expected: None (username mismatch)")
