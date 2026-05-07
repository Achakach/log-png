# Analysis of Tables 15-19 matching results
import glob
from putpnginword import find_best_match, expand_abbreviations

print("=== AVAILABLE PNGS ===")
test01_pngs = sorted(glob.glob('screenshots/TUC-TEST01*.png'))
for p in test01_pngs:
    print(f"  {p.split('/')[-1]}")

print("\n=== TABLE 15: display current-configuration (clean, all 3 devices) ===")
print("DOCX: <HUAWEI>display current-configuration")
print("      <TUC-TEST01>")
print("      <TUC-TEST02>")
print("      <TUC-TEST03>")

for node in ['TUC-TEST01', 'TUC-TEST02', 'TUC-TEST03']:
    pngs = glob.glob(f'screenshots/{node}*display*.png')
    for p in pngs:
        result = find_best_match(node, ['display current-configuration'], [p])
        match = 'MATCH' if result else 'NO MATCH'
        print(f"  {node} -> {p.split('/')[-1]}: {match}")

print("\n=== TABLE 16: system-view with Error ===")
print("DOCX: <HUAWEI>system-view")
print("      Error: you have no right..")
print("      <TUC-TEST01>")
print("      <TUC-TEST02>")
print("      <TUC-TEST03>")

for node in ['TUC-TEST01', 'TUC-TEST02', 'TUC-TEST03']:
    pngs = glob.glob(f'screenshots/{node}*system-view*.png')
    for p in pngs:
        result = find_best_match(node, ['system-view'], [p])
        match = 'MATCH' if result else 'NO MATCH'
        print(f"  {node} -> {p.split('/')[-1]}: {match}")

print("\n=== TABLE 17: display current-configuration with Error ===")
print("DOCX: <HUAWEI>display current-configuration")
print("      Error: you have no right..")
print("      <TUC-TEST01>")
print("      <TUC-TEST02>")
print("      <TUC-TEST03>")

for node in ['TUC-TEST01', 'TUC-TEST02', 'TUC-TEST03']:
    pngs = glob.glob(f'screenshots/{node}*display*error*.png')
    for p in pngs:
        result = find_best_match(node, expand_abbreviations(['display current-configuration']), [p], prefer_error=True)
        match = 'MATCH' if result else 'NO MATCH'
        print(f"  {node} -> {p.split('/')[-1]}: {match}")

print("\n=== TABLE 18: display current-configuration with username kacha1 ===")
print("DOCX: <HUAWEI>display current-configuration")
print("      <HUAWEI>username kacha1")
print("      <TUC-TEST01>")
print("      <TUC-TEST02>")
print("      <TUC-TEST03>")

for node in ['TUC-TEST01', 'TUC-TEST02', 'TUC-TEST03']:
    print(f"\n  For {node}:")
    pngs = glob.glob(f'screenshots/{node}*display*.png')
    for p in pngs:
        # Without username in search
        result_clean = find_best_match(node, expand_abbreviations(['display current-configuration']), [p])
        # With username in search  
        result_user = find_best_match(node, expand_abbreviations(['username kacha1', 'display current-configuration']), [p])
        print(f"    {p.split('/')[-1]}:")
        print(f"      Without username search: {'MATCH' if result_clean else 'NO MATCH'}")
        print(f"      With username search: {'MATCH' if result_user else 'NO MATCH'}")
