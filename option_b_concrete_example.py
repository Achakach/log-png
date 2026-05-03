import sys, os
sys.path.insert(0, '.')
from putpnginword import find_best_match, expand_abbreviations

class MP:
    def __init__(self, t): self.text = t

print("=== CONCRETE EXAMPLE: Option B (Hybrid) ===\n")

# Create mock PNG files that WOULD exist in real scenario
# Imagine these PNG files are in screenshots/:
mock_pngs = [
    'TUC-TEST01 display cpu-usage.png',           # clean: CEx01 can run this
    'TUC-TEST02 display cpu.png',                  # clean: CEx02 can run this
    'TUC-TEST01 display cpu [error].png',          # error: CEx01 can't run cpu properly
    'TUC-TEST02 display cpu-usage [error].png',    # error: CEx02 can't run cpu-usage properly
]

print("PNG files (mock):")
for p in mock_pngs:
    print(f"  {p}")

print("\nScenario: 2 commands, 2 devices")
print("="*60)

# Original approach (Option A - strict block-scoped):
# Block 0: ['display cpu-usage'] -> nodes = []  (NO nodes assigned!)
# Block 1: ['display cpu']       -> nodes = [TUC01, TUC02]
# Result: Everyone only tries 'display cpu'

print("\n❌ OPTION A (current code):")
print("   Block 0: display cpu-usage -> no nodes")
print("   Block 1: display cpu        -> TUC01, TUC02")
print("   Result:")

for node in ['TUC-TEST01', 'TUC-TEST02']:
    match = find_best_match(node, ['display', 'cpu'], mock_pngs)
    if match:
        has_error = '[error]' in os.path.basename(match).lower()
        status = '❌ [ERROR] SKIPPED' if has_error else '✅ Inserted'
        print(f"     {node}: {os.path.basename(match)} {status}")
    else:
        print(f"     {node}: NO MATCH")

# Hyrbid approach (Option B):
# TUC01 tries ALL blocks that came before it:
#   Block 0 (cpu-usage): TUC01 display cpu-usage.png ✅ non-error → INSERT
#   Block 1 (cpu): skipped because already found

print("\n✅ OPTION B (hybrid - what I proposed):")
print("   Rule: Each device scans ALL previous blocks until first non-error match")
print("   Result:")

for node in ['TUC-TEST01', 'TUC-TEST02']:
    inserted = False
    for block_idx, commands in enumerate([['display', 'cpu-usage'], ['display', 'cpu']]):
        match = find_best_match(node, commands, mock_pngs)
        if match and '[error]' not in os.path.basename(match).lower():
            print(f"     {node}: Block {block_idx} {os.path.basename(match)} ✅ Inserted")
            inserted = True
            break
    if not inserted:
        print(f"     {node}: ALL BLOCKS SKIPPED (all error or no match)")

print("\n" + "="*60)
print("EXPLANATION:")
print("="*60)
print("""
Option B (hybrid) means:

Current code (Option A) - STRICT block-scoped:
  Each node goes to exactly ONE block (nearest preceding command)
  If that block's command is wrong for device's model = no image for that device

Hybrid approach (Option B):
  If a device's assigned block has no match / error:
  → Go back and try earlier blocks
  → Pick first non-error match found

Why it works with [ERROR] PNGs:
  CEx01's correct command (cpu-usage) → clean PNG  ✅
  CEx01's wrong command (cpu)         → error PNG  ❌
  CEx02's correct command (cpu)       → clean PNG  ✅
  CEx02's wrong command (cpu-usage)   → error PNG  ❌
  
  TUC01 scans: cpu-usage first → finds clean PNG → INSERT
  TUC02 scans: cpu-usage first → finds error PNG → skip
              cpu second → finds clean PNG → INSERT
""")
