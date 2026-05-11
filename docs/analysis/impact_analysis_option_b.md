# Impact Analysis: Option B (Hybrid Approach)

## What Would Change

### 1. `match_cell_blocks()` function
**Current:** Each node only matches against its assigned block's commands  
**New:** Each node scans ALL blocks, tries to find first non-error match

**Code change:** ~20 lines in `putpnginword.py`

### 2. No Change To
- `parse_paragraphs()` - still works same way
- `parse_paragraphs_detailed()` - still works same way  
- `find_best_match()` - no changes needed
- `expand_abbreviations()` - no changes needed
- Main loop insertion logic - mostly same

## What Would Break (Regressions)

### Risk 1: Devices Get Multiple Images
If a device matches MULTIPLE blocks cleanly, it gets MULTIPLE images:
```
Block 0: display device → matches TUC01 ✅
Block 1: display clock → matches TUC01 ✅
Result: TUC01 gets 2 images!
```
**Mitigation:** Add dedup logic (only insert first non-error match per device per cell)

### Risk 2: Wrong Block Matching
A node that should be in Block 1 might match Block 0's PNG:
```
Block 0: system-view interface display this → long command
Block 1: display device → short command
Node TUC01 (from Block 1) → scans Block 0 first → might match!
```
**Mitigation:** Only scan blocks that come BEFORE the node's position

### Risk 3: Cell-Wide Deduplication Returns
With Option A (current): `inserted_paragraphs` prevents double-insert at same paragraph  
With Option B: Need `inserted_nodes` to prevent multiple images per device across blocks
**This reintroduces the old limitation!**

## Affected Test Cases

| Test | Impact |
|------|--------|
| `test_option_b_integration.py` | Needs rewrite - tests assume 1 node per block |
| `test_multi_block_preference.py` | Needs rewrite - error preference logic changes |
| `test_putpnginword.py` | Some tests may fail |
| `comprehensive_test.py` | Cases 3, 4, 10, 11 need updates |

## Backward Compatibility

| Scenario | Current (Option A) | Option B |
|----------|---------------------|----------|
| Simple single block | Works | Works |
| Multiple blocks, inline nodes | Works | Works |
| Multiple blocks, nodes at bottom | ❌ Broken | ✅ Works |
| Same node in multiple blocks | Gets 1 image | Gets 1 image |

## Conclusion

**Option B is a MEDIUM-sized change:**
- ~20 lines of core logic change
- ~5-8 test files need updates
- 1 new dedup mechanism needed
- Risk of unintended multi-image insertion

**Alternative: Just fix Case 12 document structure**
Instead of changing code, put nodes next to their correct command:
```
CEx01
<HUAWEI>display cpu-usage
<TUC-TEST01>
CEx02
<HUAWEI>display cpu
<TUC-TEST02>
```
This requires ZERO code changes and works immediately.

**My recommendation:** Fix the document structure for now. Option B adds complexity that might introduce bugs for a single edge case.