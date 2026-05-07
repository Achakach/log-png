# Comprehensive Test Result Explained - All 19 Tables

This document explains which PNG matched each DOCX cell and why.

---

## Table 1: Basic Single Command
**DOCX:** `<HUAWEI>display device` → nodes: TUC-TEST01, TUC-TEST02, TUC-TEST03
**Match:** `TUC-TEST01 display device.png`
**Why:** Basic standalone command. Simple device+command match.

---

## Table 2: Nested Block
**DOCX:** `<HUAWEI>system-view` → `[HW-GigabitEthernet0/0/1]display this` → quit → quit → node: TUC-TEST01  
**Match:** `TUC-TEST01 system-view interface GigabitEthernet0_0_1 display this quit quit.png`
**Why:** All commands in nested view are concatenated into filename. `quit`s are stripped during matching for flexibility.

---

## Table 3: Multiple Commands in Same Cell
**DOCX:** `<HUAWEI>display device` (nodes 1-3) then `<HUAWEI>display clock` (nodes 1-3)
**Match:** 
- Block 0: TUC-TEST01/02/03 `display device.png`
- Block 1: TUC-TEST01/02/03 `display clock.png`
**Why:** Two separate blocks parsed. Each block matches independently.

---

## Table 4: Different Devices for Different Nodes
**DOCX:** `<TUC-TEST01>display device` → `<TUC-TEST02>` then `<TUC-TEST01>display clock` → `<TUC-TEST01>`
**Match:** TUC-TEST02 `display device.png` + TUC-TEST01 `display clock.png`
**Why:** Device-specific matching. Commands only match their own node's PNGs.

---

## Table 5: Missing PNG (No Match)
**DOCX:** `<TUC-TEST01>display cpu-usage`
**Result:** No match
**Why:** No `TUC-TEST01 display cpu-usage.png` exists in screenshots folder.

---

## Table 6: Multiple Independent Commands
**DOCX:** `<HUAWEI>display device` → `<TUC-TEST01>` then `<HUAWEI>display clock` → `<TUC-TEST01>`
**Match:** `display device.png` + `display clock.png`
**Why:** Two separate standalone commands.

---

## Table 7: Nested Without Complete Quit Chain
**DOCX:** `<HUAWEI>system-view` → `[HW-GigabitEthernet0/0/1]display this` → `<TUC-TEST01>`
**Match:** `TUC-TEST01 system-view interface GigabitEthernet0_0_1 display this quit quit.png`
**Why:** Missing quit commands in DOCX, but `find_best_match` strips trailing `quit` from PNG before matching.

---

## Table 8: Empty Cell
**DOCX:** `<HUAWEI>display device` (no nodes)
**Result:** Nothing inserted
**Why:** Cell has commands but no node paragraphs → no place to insert images.

---

## Table 9: Nonexistent Command
**DOCX:** `<HUAWEI>display wrong-command` → `<TUC-TEST01>`
**Result:** No match
**Why:** No PNG for `display wrong-command` exists.

---

## Table 10: Mixed Nested + Standalone Commands
**DOCX:** Three full command blocks:
1. Nested: `system-view` → `interface GigabitEthernet0/0/1` → `display this` → `quit x2` → nodes 1-3
2. Standalone: `display device` → nodes 1-3
3. Standalone: `display clock` → nodes 1-3

**Match:** Mixed: nested block + standalone commands, each matched separately.
**Why:** Block-level matching isolates each command sequence.

---

## Table 11: Skip Error, Match Next
**DOCX:** Block 0: `display wrong-command` (Error: ...) → nodes 1-3 → **No match**  
Block 1: `display device` → nodes 1-3 → Match
**Result:** First block skipped (no such PNG). Second block matched.
**Why:** Block-scoped matching. One block fails but next block succeeds independently.

---

## Table 12: Model Labels (Empty Block Merge)
**DOCX:** `CEx01` label → `<HUAWEI>display device` → `CEx02` label → `<HUAWEI>display clock` → nodes 1-3
**Match:** `display device.png` + `display clock.png` for all nodes
**Why:** Empty block merge.
- `CEx01` (no commands) → empty block merged with `display device` block
- `CEx02` (no commands) → empty block merged with `display clock` block

---

## Table 13: Error Detection + Username Present
**DOCX:** `display current-configutation` → `Error: Do not have permission` → `username xxuser` → nodes 1-3
**Match:** `display current-configutation [error].png`
**Why:** Error detection marks block as `expect_error=True`. Matches `[error]` PNG.
`username xxuser` is in the block but is ignored because it's a documentation command.

---

## Table 14: Placeholder Matching (3 blocks)
**DOCX:** Three blocks: `startup saved-configuration xxx.zip` / `xxx.cfg` / `xxx.hi` → nodes 1-3
**Match:** `startup saved-configuration xxx.zip.png` matches with `xxx.zip` in DOCX
**Why:** Placeholder extension matching. `xxx.*` in DOCX matches any value in PNG, but extension must match exactly.
- `xxx.zip` → `xxx.zip.png` ✅
- `xxx.cfg` → `xxx.cfg.png` ✅
- `xxx.hi` → `xxx.hi.png` ✅

---

## Table 15: Basic Display Current-Configuration
**DOCX:** `display current-configuration` → nodes 1-3
**Match:** `TUC-TEST01/02/03 display current-configuration.png`
**Why:** Clean command. No username, no error.

---

## Table 16: Error with System-View
**DOCX:** `system-view` + `Error: you have no right..` → nodes 1-3
**Match:** `system-view [error].png`
**Why:** Error text triggers `expect_error=True`. Prefers `[error]` tagged PNG.

---

## Table 17: Error with Display Current-Configuration
**DOCX:** `display current-configuration` + `Error: you have no right..` → nodes 1-3
**Match:** `display current-configuration [error].png`
**Why:** Same as Table 16 - error text in DOCX pairs with `[error]` PNG.

---

## Table 18: Username Kacha1 (SSH Session)
**DOCX:** `display current-configuration` + `username kacha1` → nodes 1-3
**Match:** `display current-configuration username kacha1.png`
**Why:** Username filter + scoring. Both DOCX and PNG have `username kacha1`, so they match.
**Merge logic:** Empty-block-merge detected. Individual matching tried `display current-configuration` first (matched clean PNG), then full sequence tried `display current-configuration username kacha1` (matched username-tagged PNG). Scoring prefers username-tagged when DOCX has username.

---

## Table 19: Clean Display Current-Configuration (No Username)
**DOCX:** `display current-configuration` → nodes 1-3
**Match:** `display current-configuration.png`
**Why:** Clean command. No username in DOCX, no username in PNG.

---

## Summary of Matching Logic

| Scenario | How It Works |
|---|---|
| Basic command | Device + command exact match |
| Nested block | All commands concatenated into filename |
| Multiple blocks | Each block matched independently |
| Missing PNG | "No match" if no file |
| Error DOCX | `expect_error=True` → prefers `[error]` PNG |
| Clean DOCX | Skips `[error]` PNGs |
| Placeholder | `xxx.*` matches extension, ignores prefix |
| Username tag | DOCX and PNG username must match (both present or both absent) |
| Empty block merge | `CEx01` label merges into next block |
| Abbreviation | `dis cur` ↔ `display current-configuration` (bidirectional) |
| Quit stripping | Trailing `quit` removed from both sides before matching |
