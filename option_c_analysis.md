# Option C: Mixed Nested + Standalone Handling

## What It Means

**Current (Option A):**
- One flat list of blocks
- Nested commands + standalone commands all treated equally
- Nodes assigned to nearest preceding block

**Option C:**
- **Split cell into two zones:**
  1. **Nested zone:** Any `system-view` + subview commands + their inline nodes
  2. **Standalone zone:** All standalone `<Router>cmd` commands + bottom nodes
- **Each zone processed separately**

## How It Works

### Parsing Logic Change

```python
# Step 1: Detect nested commands
# If block contains system-view + subview → mark as "nested zone"
# All blocks after nested zone = "standalone zone"

# Step 2: Process nested zone
# Each inline node matches against the nested block

# Step 3: Process standalone zone  
# If empty blocks exist → merge all standalone blocks
# All bottom nodes try each standalone command
```

### Example

**Input:**
```
<HUAWEI>system-view
[HW]interface GE0/0/1
[HW-GE0/0/1]display this
[HW-GE0/0/1]quit
[HW]quit
<TUC-TEST01>              ← Zone 1: Nested, inline node

<HUAWEI>display cpu-usage
CEx02
<HUAWEI>display cpu
<TUC-TEST02>              ← Zone 2: Standalone, bottom nodes
<TUC-TEST03>
```

**Processing:**
```
Zone 1 (Nested):
  Block: [system-view, interface, display this, quit, quit]
  Nodes: [TUC-TEST01]
  Result: TUC01 gets nested image ✅

Zone 2 (Standalone):
  Commands: [display cpu-usage, display cpu]
  Nodes: [TUC-TEST02, TUC-TEST03]
  TUC02 tries cpu-usage → match/error? → insert/skip
  TUC03 tries cpu-usage → match/error? → insert/skip
          tries cpu → match/error? → insert/skip
  Result: Both TUC02 and TUC03 get images ✅
```

## Impact on All Cases

| Case | Structure | Current Result | Option C Result | Change |
|------|-----------|----------------|-----------------|--------|
| 1 | Single standalone | 3 images | 3 images | ✅ None |
| 2 | Single nested | 1 image | 1 image | ✅ None |
| 3 | Multiple standalone, inline nodes | 6 images | 6 images | ✅ None |
| 4 | Multi-model inline | 2 images | 2 images | ✅ None |
| 5 | Error (single) | 0 images | 0 images | ✅ None |
| 6 | Multiple standalone, inline nodes | 2 images | 2 images | ✅ None |
| 7 | Nested without quit | 1 image | 1 image | ✅ None |
| 8 | No nodes | 0 images | 0 images | ✅ None |
| 9 | Wrong command | 0 images | 0 images | ✅ None |
| 10 | Nested + standalone, all inline | 9 images | 9 images | ✅ None |
| 11 | Error + OK blocks | 3 images | 3 images | ✅ None |
| 12 | Standalone, bottom nodes | **BROKEN** (0-3 images) | **FIXED** (all get images) | ✅ **FIXES** |
| **NEW** | Nested + standalone, mixed nodes | TUC01 gets nested, bottom nodes get last block only | TUC01 gets nested, bottom nodes try all standalone | ✅ **IMPROVES** |

## Code Changes Required

### 1. `parse_paragraphs_detailed()` — Modified

Add zone detection:
```python
def parse_paragraphs_detailed(paragraphs):
    # ... existing logic ...
    
    # Detect zones
    nested_zone = None
    standalone_blocks = []
    
    for bi, (cmds, nodes) in enumerate(blocks):
        if 'system-view' in cmds:
            nested_zone = (cmds, nodes)
        else:
            standalone_blocks.append((cmds, nodes))
    
    return {
        'nested': nested_zone,
        'standalone': standalone_blocks
    }
```

### 2. New `match_cell_zones()` function

```python
def match_cell_zones(paragraphs, png_files):
    zones = parse_paragraphs_detailed(paragraphs)
    results = []
    
    # Process nested zone
    if zones['nested']:
        cmds, nodes = zones['nested']
        for node, para_idx in nodes:
            match = find_best_match(node, cmds, png_files)
            # ... add to results ...
    
    # Process standalone zone
    if zones['standalone']:
        # Merge if needed
        all_cmds = []
        all_nodes = []
        for cmds, nodes in zones['standalone']:
            all_cmds.extend(cmds)
            all_nodes.extend(nodes)
        
        for node, para_idx in all_nodes:
            # Try each command
            for cmd in all_cmds:
                match = find_best_match(node, [cmd], png_files)
                if match and not error:
                    # insert
                    break
    
    return results
```

### 3. Main Loop — Minor Update

Replace `match_cell_blocks()` with `match_cell_zones()`

## Pros and Cons

**Pros:**
- Fixes Case 12 without breaking anything
- Handles mixed nested+standalone scenarios
- More flexible for future edge cases
- Backward compatible with all existing tests

**Cons:**
- More complex code (~50 lines new logic)
- `parse_paragraphs_detailed()` return format changes
- Need to update all test files
- Risk of new edge cases in zone detection
- Takes more time to implement + test

## My Recommendation

**Option C is the RIGHT solution** but it's more work.

**If you need it now:** I can implement it.
**If Case 12 is the only problem:** Use the simpler "don't merge if nested" rule (covers 99% of cases).

**Question:** Do you actually have cells with mixed nested+standalone+bottom_nodes? Or is Case 12 always standalone-only?
