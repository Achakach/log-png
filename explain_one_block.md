# Case 12: Simple Explanation

## Your Input (as you modified it)

```
CEx01
<HUAWEI>display cpu-usage
CEx02
<HUAWEI>display cpu
<TUC-TEST01>
<TUC-TEST02>
<TUC-TEST03>
```

## What Happens Now

The code sees TWO commands and nodes at bottom:
```
Block 0: display cpu-usage  ← NO nodes (all nodes came later)
Block 1: display cpu      ← nodes=[TUC01, TUC02, TUC03]
```

Result: Everyone ONLY tries `display cpu`
- TUC01: tries `display cpu` → gets error → SKIP ❌
- TUC02: tries `display cpu` → no error → INSERT ✅

**TUC01 never tries `display cpu-usage`!**

## What You Want (I think)

For each device, try ALL commands until finding one that works:
```
TUC-TEST01:
  Try "display cpu-usage" → "TUC01 display cpu-usage.png" ✅ → INSERT
  
TUC-TEST02:
  Try "display cpu-usage" → "TUC02 display cpu-usage [ERROR].png" ❌
  Try "display cpu"      → "TUC02 display cpu.png" ✅ → INSERT
  
TUC-TEST03:
  Try "display cpu-usage" → "TUC03 display cpu-usage.png" ✅ → INSERT
```

## Simple Solution

**Rule:** If all commands are standalone (no nested `system-view`), put them in ONE block.
Then for each device, try every command until finding a match.

**This is a small change** - only affects cells with multiple standalone commands.

## The Key Question

Do you want this behavior JUST for Case 12? Or for ALL cells with multiple commands?

Example: Row 7 in testthisplease.docx
```
<HUAWEI>system-view...quit quit
<TUC-TEST01>
<HUAWEI>display device
<TUC-TEST01>
<HUAWEI>display clock
<TUC-TEST01>
```

Should TUC01:
- Get 3 images (one per command)? ← What you wanted originally (Option B)
- Or try all 3 commands and pick the best one? ← What you're asking now

**Which one do you want?**
