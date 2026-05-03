# Mismatch Risk Analysis

## Your Concern Is Valid

If we merge all standalone blocks, EVERY device tries EVERY command. This CAN cause mismatches.

## Scenario Where It Goes Wrong

**Input:**
```
<HUAWEI>display device
<HUAWEI>display clock
<TUC-TEST01>
<TUC-TEST02>
```

**PNG files:**
```
TUC-TEST01 display device.png      ← clean
TUC-TEST01 display clock.png       ← clean (NOT marked as error!)
TUC-TEST02 display device.png      ← clean
TUC-TEST02 display clock.png       ← clean (NOT marked as error!)
```

**Merged pool:** [display device, display clock]

**Matching:**
```
TUC-TEST01:
  Try display device -> match.png ✅ clean -> INSERT
  (skips display clock)
  
TUC-TEST02:
  Try display device -> match.png ✅ clean -> INSERT
  (skips display clock)
```

**Result:** Both TUC01 and TUC02 get `display device` image.
**TUC02 never gets `display clock` even though it should!** ❌

## Why It Currently Works (Option A)

With current code (no merge):
```
Block 0: [display device] -> nodes=[]
Block 1: [display clock]   -> nodes=[TUC01, TUC02]
```

TUC01 and TUC02 BOTH try `display clock`.
If `display clock` is correct for them, they get it. ✅

## When Is It Safe?

**Option C (merge) is ONLY safe when:**

1. **Wrong command produces [ERROR] PNG** — code skips it
   ```
   TUC01 display cpu-usage.png         ✅ clean
   TUC01 display cpu [ERROR].png       ❌ skipped
   ```

2. **Or: wrong command produces NO PNG at all** — code skips it
   ```
   TUC01 display cpu-usage.png         ✅ match
   TUC01 display cpu.png             ❌ no such file
   ```

**NOT safe when:**
- Both commands produce clean PNGs for the same device
- Code can't tell which is "correct"

## The Real Problem

**We don't know which command belongs to which device.**

The ONLY signals we have:
- [ERROR] suffix → wrong command
- No PNG file → wrong command
- If both match → code picks first one (arbitrary)

## Solutions

### Option 1: Trust [ERROR] marker (your current approach)
**Assumption:** Wrong command always generates [ERROR] PNG.
**Risk:** If someone forgets to mark errors, mismatches happen.

### Option 2: Model annotation in document
```
CEx01                    ← model label
<HUAWEI>display cpu-usage  ← command for CEx01
<TUC-TEST01>             ← device

CEx02                    ← model label
<HUAWEI>display cpu      ← command for CEx02
<TUC-TEST02>             ← device
```
**Would need:** Parser to understand "lines between model label and device belong together"

### Option 3: Don't merge, keep current behavior
**Accept:** Case 12 doesn't work with current document structure.
**Fix:** Change document to put devices next to commands.

## My Recommendation

**Option 1 is risky** — depends on perfect [ERROR] marking.
**Option 2 is complex** — needs parser changes + document convention.
**Option 3 is safest** — but requires document changes.

**Question for you:** 
In your real documents, does `display cpu` for the wrong model ALWAYS produce an `[ERROR]` PNG? If yes, Option 1 works. If not, we have a bigger problem.
