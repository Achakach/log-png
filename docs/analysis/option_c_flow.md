# Option C Flow: Step-by-Step Explanation

## The Big Picture

**Goal:** Handle cells that have BOTH nested commands AND standalone commands with nodes at the bottom.

**Solution:** Split the cell into **zones** based on command type.

---

## Step 1: Detect Zones (Parsing)

Read the cell paragraphs and categorize commands:

```
Input cell:
  <HUAWEI>system-view              ← DETECTED: 'system-view' present
  [HW]interface GE0/0/1            ← Part of nested zone
  [HW-GE0/0/1]display this           ← Part of nested zone
  [HW-GE0/0/1]quit                   ← Part of nested zone
  [HW]quit                            ← Part of nested zone
  <TUC-TEST01>                        ← Inline node (belongs to nested zone)
  
  <HUAWEI>display cpu-usage          ← Standalone command
  <HUAWEI>display cpu                ← Standalone command
  <TUC-TEST02>                        ← Bottom node (belongs to standalone zone)
  <TUC-TEST03>                        ← Bottom node (belongs to standalone zone)
```

**Detection rule:**
- Find first `system-view` → marks start of **Nested Zone**
- Find first standalone `<Router>cmd` after nested zone ends → marks start of **Standalone Zone**
- Nodes after nested zone commands → **Nested Zone**
- Nodes after standalone commands → **Standalone Zone**

---

## Step 2: Build Blocks Per Zone

### Nested Zone
```
Commands: [system-view, interface GE0/0/1, display this, quit, quit]
Nodes:    [(TUC-TEST01, para_idx=5)]
```

### Standalone Zone
```
Block 0: [display cpu-usage]         ← nodes=[] (empty!)
Block 1: [display cpu]               ← nodes=[(TUC-TEST02, 8), (TUC-TEST03, 9)]
```

**Decision:** Since Standalone Zone has empty blocks → **MERGE all standalone blocks**

Merged Standalone Zone:
```
Commands: [display cpu-usage, display cpu]
Nodes:    [(TUC-TEST02, 8), (TUC-TEST03, 9)]
```

---

## Step 3: Match PNGs Per Zone

### Nested Zone Matching
```
TUC-TEST01 tries:
  Command: system-view interface GE0/0/1 display this quit quit
  Match: TUC-TEST01 system-view interface GE0_0_1 display this quit quit.png
  Check: [error] in filename? → NO → INSERT ✅
```

### Standalone Zone Matching (merged)
```
TUC-TEST02 tries:
  Command 1: display cpu-usage
    Match: TUC-TEST02 display cpu-usage [ERROR].png → ERROR → SKIP ❌
  Command 2: display cpu
    Match: TUC-TEST02 display cpu.png → NO ERROR → INSERT ✅

TUC-TEST03 tries:
  Command 1: display cpu-usage
    Match: TUC-TEST03 display cpu-usage.png → NO ERROR → INSERT ✅
  Command 2: display cpu
    Skipped because already found
```

---

## Step 4: Insert Images

**Nested Zone:**
- Insert at para_idx=5 (where TUC-TEST01 is)
- Image: TUC-TEST01 system-view interface GE0_0_1 display this quit quit.png

**Standalone Zone:**
- Insert at para_idx=8 (where TUC-TEST02 is)
- Image: TUC-TEST02 display cpu.png
- Insert at para_idx=9 (where TUC-TEST03 is)
- Image: TUC-TEST03 display cpu-usage.png

---

## Final Result

| Device | Images | From |
|--------|--------|------|
| TUC-TEST01 | 1 | Nested command block |
| TUC-TEST02 | 1 | Standalone: display cpu |
| TUC-TEST03 | 1 | Standalone: display cpu-usage |

**Total: 3 images** — each device gets the RIGHT image.

---

## Comparison with Current Code

| Approach | TUC01 | TUC02 | TUC03 | Total |
|----------|-------|-------|-------|-------|
| Current (Option A) | 1 (nested) | 0 (cpu error) | 0 (cpu error) | 1 |
| Option C | 1 (nested) | 1 (cpu) | 1 (cpu-usage) | 3 |

**Option C fixes the problem:**
- Nested zone works as before
- Standalone zone merges empty blocks so all bottom nodes can try all commands
- Error detection via [ERROR] suffix ensures wrong matches are skipped
