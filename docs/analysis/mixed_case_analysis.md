## What If Case 10 + Case 12 Mixed Together?

### Example you might mean:

```
<HUAWEI>system-view
[HW]interface GE0/0/1
[HW-GE0/0/1]display this
[HW-GE0/0/1]quit
[HW]quit
<TUC-TEST01>              ← Block 0: nested command

<HUAWEI>display cpu-usage  
<HUAWEI>display cpu        
<TUC-TEST01>              ← Block 2: standalone commands
<TUC-TEST02>
```

**Current parsing:**
```
Block 0: system-view...>quit quit → nodes=[TUC01]
Block 1: display cpu-usage → nodes=[]  ← EMPTY
Block 2: display cpu → nodes=[TUC01, TUC02]  ← all at bottom
```

### Under "Safer Solution"

**IF we detect nested commands → DON'T merge anything**

Result:
- TUC01 (Block 0): gets nested image ✅
- TUC01 (Block 2): gets display cpu image ✅  
- TUC02 (Block 2): gets display cpu image ✅
- TUC01 never tries cpu-usage ❌

**IF we allow merge (merge Blocks 1+2 since Block 1 empty):**

Result:
- TUC01 (Block 0): gets nested image ✅
- TUC01 (at bottom): tries system-view first → matches → INSERT (wrong image!) ❌
- TUC02 tries system-view first → no match → tries cpu-usage → error → tries cpu → match → INSERT ✅

**Problem:** TUC01 at bottom would get nested image instead of cpu!

### Safer Rule Refined

**DON'T merge if:**
1. ANY block is a nested block (has system-view/sub-views)
2. OR any block has inline nodes AND we have bottom nodes

**Only merge when:**
1. ALL commands are standalone (no system-view)
2. AND some blocks have zero nodes
3. AND all nodes are at the bottom

### Your Specific Case

If you truly have this mixed scenario, the safest thing is: **don't merge at all**. Each device inline with its command uses that command; devices at bottom only use the last block.

But if you want devices at bottom to try ALL standalone commands (ignoring nested), we need a third approach:

**Option C: Treat nested blocks separately, merge standalone blocks only**

```
Nested part:     system-view...>quit quit → nodes=[TUC01] → TUC01 gets nested image ✅
Standalone part:  cpu-usage, cpu → nodes=[TUC01, TUC02] → each tries both commands ✅
```

**This is more complex but possible.** Do you want this, or is the "don't merge if nested" rule good enough?
