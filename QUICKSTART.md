# Huawei Log Screenshot Generator — Quick Reference

## 1. Prerequisites
- Python 3.10+ installed
- Huawei VRP CLI log files (.txt) with prompts like `<Router>` or `[Router]`

## 2. Install (One Time)
```bash
pip install -r requirements.txt
playwright install chromium
```

## 3. Workflow

### Step A: Put Logs
Place `.txt` log files in the `logs/` folder.

**Required log format:**
```
<RouterName> command              ← User view
[RouterName] command            ← System view
[RouterName-subview] command      ← Sub-view
```

**Example valid log:**
```
<HUAWEI> display device
  Slot 1   FAN1   Present
<HUAWEI> system-view
[HUAWEI] interface GE0/0/1
[HUAWEI-GE0/0/1] display this
[HUAWEI-GE0/0/1] quit
[HUAWEI] quit
<HUAWEI> display clock
```

### Step B: Generate Screenshots
```bash
python run.py
```
- Reads all `.txt` files in `logs/`
- Saves PNG screenshots to `screenshots/`
- Also saves removed-device cases to `removeddevicetest/` (if any)

### Step C: Insert into Word

**1. Prepare your DOCX table cell:**
```
<HUAWEI>display device       ← Command line
<TUC-TEST01>                 ← Node line (image inserted HERE)
<TUC-TEST02>                 ← Node line (image inserted HERE)
```

**2. Edit `putpnginword.py` (top 3 lines):**
```python
DOCX_INPUT  = r"your_input.docx"      # Your source Word file
PNG_PATH    = r"screenshots\*.png"    # Where PNGs are
DOCX_OUTPUT = "your_output.docx"      # Result file name
```

**3. Run:**
```bash
python putpnginword.py
```

## 4. Naming Rules

| What You See | PNG Filename |
|---|---|
| `<R> display device` | `R display device.png` |
| `<R> system-view` → `[R] interface GE0/0/1` → `[R-GE0/0/1] display this` | `R system-view interface GE0_0_1 display this quit quit.png` |
| Command with error output | `R display wrong [error].png` |

## 5. Key Features

| Feature | How It Works |
|---|---|
| **Block-scoped matching** | Same node after multiple command blocks gets multiple images |
| **Empty block merge** | Commands without nodes merge forward to the next block |
| **Error preference** | `[error]` PNGs are skipped unless the block is explicitly error-marked |
| **Missing device** | Second `display device` missing cards → `[FAN3 removed].png` |
| **Abbreviations** | `dis`→`display`, `sys`→`system-view`, `q`→`quit` (auto-expanded) |
| **Noise filtering** | `username` commands are ignored (not treated as real commands) |

## 6. Troubleshooting

| Problem | Cause | Fix |
|---|---|---|
| "No match: Node block 0" | No PNG filename matches the command sequence | Check `screenshots/` exists and filenames match exactly |
| "Skipped (error)" | Only an `[error]` PNG exists for this command | Either the command actually fails, or no clean PNG was generated |
| Table empty / no images | Cell has commands but no `<NodeName>` lines | Add node lines after commands to mark insertion points |
| "No Huawei VRP prompts found" | Log format is wrong | Ensure prompts start with `<` or `[` and have a space before the command |

## 7. Useful Commands

```bash
python run.py                          # Generate all screenshots
python putpnginword.py                 # Insert images into DOCX
python -m pytest tests/ -q             # Run test suite
```

---

**For full documentation, see `MANUAL.md`**
