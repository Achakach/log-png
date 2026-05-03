## Option B in My Explanation: "All nodes at bottom, try ALL blocks"

### The Scenario

Document cell:
```
<HUAWEI>display cpu-usage
<HUAWEI>display cpu
<TUC-TEST01>
<TUC-TEST02>
```

**Current behavior:** TUC01 and TUC02 are in **Block 1** only (the last block). They only try `display cpu`. `display cpu-usage` never matches.

### Option B (Hybrid): Try ALL blocks for each device

```
<TUC-TEST01>  should try: Block 0 (cpu-usage) AND Block 1 (cpu) ⬅️ BOTH
<TUC-TEST02>  should try: Block 0 (cpu-usage) AND Block 1 (cpu) ⬅️ BOTH
```

**Result:**
| Device | Block 0 (cpu-usage) match? | Block 1 (cpu) match? | Action |
|--------|----------------------------|----------------------|--------|
| TUC01  | ✅ YES (non-error)         | ❌ maybe but we skip | Insert cpu-usage PNG |
| TUC02  | ❌ error                   | ✅ YES (non-error)   | Insert cpu PNG |

**Where this breaks down:**

TUC01 tries BOTH blocks:
1. Block 0 `display cpu-usage` → `TUC01 display cpu-usage.png` ✅ non-error → INSERT
2. Block 1 `display cpu` → `TUC01 display cpu.png` → BUT we already inserted for this device!

So we need a rule: **For each device, pick ONE non-error match from any block** (not all blocks). This gives:
- TUC01 → `cpu-usage.png` (1 image)
- TUC02 → `cpu.png` (1 image)

Total: 2 images for 2 devices.

But **Problem:** All devices look the same to the code. It doesn't know TUC01 should prefer cpu-usage. It just picks whichever works. If BOTH blocks match for TUC01, how does it pick?

**Answer:** The code still picks **first non-error match** (block order). If `cpu-usage` matches for TUC01, block 0 wins and block 1 never considered.

### Simple Example

```
Blocks: [cpu-usage] [cpu]
Nodes:  [TUC01]     [TUC02]   
# BUT all nodes are at bottom, so parser sees:
# Block 0 nodes: [TUC01]     ← node after first command
# Block 1 nodes: [TUC02]     ← node after second command
```

If you could place nodes inline, no problem.

If all at bottom:
```
Blocks: [cpu-usage] [cpu]
# Both nodes get same block assignment (last block) unless we change parser
```

**I don't think Option B (hybrid) works without changing the parser** to understand which device belongs where.

**Question:** Can you just place devices after their correct command?

```
<HUAWEI>display cpu-usage
<TUC-TEST01>          ← belongs to cpu-usage
<HUAWEI>display cpu
<TUC-TEST02>          ← belongs to cpu
```

If yes, no code changes needed.
