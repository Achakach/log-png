# Impact Analysis: Treat All Standalone Commands As One Block

## Rule Change

**Current:** Each standalone `<Router>cmd` starts a new block
**Proposed:** If cell has only standalone commands (no `[Router-subview]`), treat ALL commands as ONE block

## Case-by-Case Impact

### Case 1: Basic single block
```
<HUAWEI>display device
<TUC-TEST01>
```
**Current:** Block 0: display device → 1 block
**Proposed:** Same
**Impact:** NONE ✅

---

### Case 2: Nested command block
```
<HUAWEI>system-view
[HW]interface GigabitEthernet0/0/1
[HW-GigabitEthernet0/0/1]display this
[HW]quit
<HUAWEI>quit
<TUC-TEST01>
```
**Current:** Block 0: [system-view, interface, display, quit, quit] → 1 block
**Proposed:** Same (has nested command, so NOT treated as standalone)
**Impact:** NONE ✅

---

### Case 3: Multiple standalone commands (Option B test)
```
<HUAWEI>display device
<TUC-TEST01>
<HUAWEI>display clock
<TUC-TEST02>
```
**Current:** Block 0: display device → nodes=[TUC01]
          Block 1: display clock → nodes=[TUC02]
          Result: 2 images
**Proposed:** Block 0: [display device, display clock] → nodes=[TUC01, TUC02]
          TUC01 tries both, picks first non-error
          TUC02 tries both, picks first non-error
          Result: 2 images (same)
**Impact:** NONE ✅

---

### Case 4: Multi-model scenario
```
<TUC-TEST01>display device
<TUC-TEST02>
<TUC-TEST01>display clock
<TUC-TEST01>
```
**Current:** Block 0: display device → nodes=[TUC02]
          Block 1: display clock → nodes=[TUC01]
**Proposed:** Block 0: [display device, display clock] → nodes=[TUC02, TUC01]
          TUC02 tries device first → match
          TUC01 tries device first → match
          Result: Same 2 images
**Impact:** NONE ✅

---

### Case 5: Error preference
```
<TUC-TEST01>display cpu-usage
<TUC-TEST01>
```
**Current:** Block 0: display cpu-usage → no match/error
**Proposed:** Same
**Impact:** NONE ✅

---

### Case 6: Block isolation
```
<HUAWEI>display device
<TUC-TEST01>
<HUAWEI>display clock
<TUC-TEST01>
```
**Current:** 2 blocks, TUC01 gets 2 images (1 per block)
**Proposed:** 1 block [device, clock], TUC01 tries both
          First non-error wins (device)
          Second try skipped
          Result: 1 image instead of 2!
**Impact:** ❌ BREAKS - TUC01 gets 1 image instead of 2

---

### Case 7: Cell without quit
```
<HUAWEI>system-view
[HW]interface GigabitEthernet0/0/1
[HW-GigabitEthernet0/0/1]display this
<TUC-TEST01>
```
**Current:** 1 block (nested)
**Proposed:** Same
**Impact:** NONE ✅

---

### Case 8: No nodes
```
<HUAWEI>display device
```
**Current:** 1 block, no nodes
**Proposed:** Same
**Impact:** NONE ✅

---

### Case 9: Wrong command
```
<HUAWEI>display wrong-command
<TUC-TEST01>
```
**Current:** 1 block, no match
**Proposed:** Same
**Impact:** NONE ✅

---

### Case 10: Real multi-block (3 blocks)
```
<HUAWEI>system-view...quit quit
<TUC-TEST01>
<HUAWEI>display device
<TUC-TEST01>
<HUAWEI>display clock
<TUC-TEST01>
```
**Current:** Block 0: nested → nodes=[TUC01]
          Block 1: device → nodes=[TUC01]
          Block 2: clock → nodes=[TUC01]
          Result: 3 images for TUC01
**Proposed:** Block 0: nested → nodes=[TUC01] (first command)
          Block 1: [device, clock] → nodes=[TUC01] (second and third)
          TUC01 in Block 0: matches nested → insert
          TUC01 in Block 1: tries device → match, insert
                          tries clock → match, but node already has image → skip
          Result: 2 images instead of 3!
**Impact:** ❌ BREAKS - TUC01 gets 2 images instead of 3

---

### Case 11: Error + OK blocks
```
<HUAWEI>display wrong-command
<TUC-TEST01>
<HUAWEI>display device
<TUC-TEST01>
```
**Current:** Block 0: wrong-command → no match
          Block 1: device → match
          TUC01 gets 1 image (from block 1)
**Proposed:** Block 0: [wrong-command, device] → nodes=[TUC01]
          TUC01 tries wrong-command → no match
          TUC01 tries device → match → insert
          Result: 1 image (same)
**Impact:** NONE ✅

---

### Case 12: Multi-model (the one you want fixed)
```
CEx01
<HUAWEI>display cpu-usage
CEx02
<HUAWEI>display cpu
<TUC-TEST01>
<TUC-TEST02>
```
**Current:** Block 0: cpu-usage → nodes=[]
          Block 1: cpu → nodes=[TUC01, TUC02]
          Result: Everyone tries cpu only
          TUC01 gets error/skipped, TUC02 gets image
**Proposed:** Block 0: [cpu-usage, cpu] → nodes=[TUC01, TUC02]
          TUC01 tries cpu-usage → match → insert
          TUC02 tries cpu-usage → error → skip
                    tries cpu → match → insert
          Result: Both TUC01 and TUC02 get images ✅
**Impact:** FIXES Case 12 ✅

---

## Summary

| Case | Status | Change |
|------|--------|--------|
| 1 | ✅ No impact | None |
| 2 | ✅ No impact | None |
| 3 | ✅ No impact | Same images |
| 4 | ✅ No impact | Same images |
| 5 | ✅ No impact | None |
| 6 | ❌ BREAKS | TUC01 gets 1 image instead of 2 |
| 7 | ✅ No impact | None |
| 8 | ✅ No impact | None |
| 9 | ✅ No impact | None |
| 10 | ❌ BREAKS | TUC01 gets 2 images instead of 3 |
| 11 | ✅ No impact | Same |
| 12 | ✅ FIXES | Now works |

## Conclusion

**BREAKS Case 6 and Case 10** - cells where same device appears after multiple standalone commands will get FEWER images.

**Solution:** Only apply "one block" when there are UNMATCHED nodes at the end (nodes not assigned to any block).

**Better Rule:**
1. Parse normally into multiple blocks
2. If last block has nodes but first block doesn't → merge ALL blocks into one
3. Then do per-node per-command matching

This only affects Case 12 (your scenario) without breaking Cases 6 and 10.
