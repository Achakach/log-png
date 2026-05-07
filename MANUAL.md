# Huawei Network Log Screenshot Generator — User Manual

## Table of Contents
1. [What This Program Does](#what-this-program-does)
2. [Installation](#installation)
3. [Quick Start](#quick-start)
4. [Step-by-Step Guide](#step-by-step-guide)
5. [Understanding the Output](#understanding-the-output)
6. [Advanced Features](#advanced-features)
7. [Troubleshooting](#troubleshooting)

---

## What This Program Does

This program converts **Huawei VRP CLI log files** into **PNG screenshots** and inserts them into **Microsoft Word documents**.

### Typical Workflow

```
Huawei CLI Logs (.txt)  →  PNG Screenshots  →  Word Document (.docx)
     logs/                    screenshots/          *_RESULT.docx
```

**Example:**
- You have a log showing `<Router> display device` output
- The program creates a terminal-style PNG screenshot
- The PNG is inserted at the correct position in your Word document

---

## Installation

### Prerequisites

| Software | Version | How to Check |
|----------|---------|-------------|
| Python | 3.10+ | `python --version` |
| pip | Latest | `pip --version` |

### Step 1: Install Python Dependencies

Open terminal/cmd in the program folder:

```bash
pip install -r requirements.txt
```

This installs:
- `jinja2` — HTML template rendering
- `playwright` — Headless browser for screenshots
- `python-docx` — Word document manipulation

### Step 2: Install Chromium Browser

```bash
playwright install chromium
```

This downloads a headless Chromium browser used for rendering HTML → PNG.
**Run this once. It takes ~2-3 minutes.**

### Step 3: Verify Installation

```bash
python -m pytest tests/ -q
```

Should show `93 passed, 1 failed` (the 1 failure is a pre-existing issue unrelated to core functionality).

---

## Quick Start

If you just want to try it out with the included sample data:

```bash
# Step 1: Generate PNG screenshots from logs
python run.py

# Step 2: Edit putpnginword.py to point to your DOCX
# Open putpnginword.py and change these lines:
# DOCX_INPUT = r"your_document.docx"
# PNG_PATH = r"screenshots\*.png"
# DOCX_OUTPUT = "your_document_RESULT.docx"

# Step 3: Insert images into Word document
python putpnginword.py
```

---

## Step-by-Step Guide

### Step 1: Prepare Your Log Files

**Where to put them:**
```
logs/
├── your_log_1.txt
├── your_log_2.txt
└── ...
```

**Log file format requirements:**

Your log files must use **Huawei VRP prompt format**:

```
<RouterName> command          ← User view (depth 0)
[RouterName] command           ← System view (depth 1)
[RouterName-subview] command     ← Sub-view (depth 2+)
```

**Examples of valid prompts:**
```
<HUAWEI> display device
[HUAWEI] system-view
[HUAWEI-GigabitEthernet0/0/1] display this
[~HUAWEI] display current-configuration   ← ~ means unsaved config
[*HUAWEI] display alarm active            ← * means alarm/fault
```

**Important rules:**
1. Each command must have a prompt at the start of the line
2. Output appears between prompts
3. Nested commands (system-view, interface, etc.) must return to `<Router>` before starting a new block

**Example of correct log structure:**
```
<HUAWEI> display device
  Slot  Card    Type
  1     -       CE8855-32CQ4BQ
  1     FAN1    FAN

<HUAWEI> system-view
[HUAWEI] interface GigabitEthernet0/0/1
[HUAWEI-GE0/0/1] display this
  interface GigabitEthernet0/0/1
  port link-type trunk
[HUAWEI-GE0/0/1] quit
[HUAWEI] quit
<HUAWEI> display clock
  2026-04-07 21:15:30+07:00
```

### Step 2: Generate Screenshots

Run:

```bash
python run.py
```

**What happens:**
- Reads all `.txt` files in `logs/`
- Parses each into command segments
- Groups commands (standalone vs nested blocks)
- Renders HTML with terminal styling
- Captures screenshot via Chromium
- Saves PNGs to `screenshots/`

**Output:**
```
Processing logs\your_log_1.txt -> screenshots/...
  [1/5] Generated: screenshots\Router1 display device.png
  [2/5] Generated: screenshots\Router1 display clock.png
  ...

[DONE] 15 total screenshots from 1 log file(s)
```

### Step 3: Prepare Your Word Document

Your DOCX must have **tables** with this structure:

**Table Row Format:**
```
| Test Case | Cell Content |
|-----------|-------------|
| Case 1    | <HUAWEI>display device
            | <TUC-TEST01>
            | <TUC-TEST02> |
```

**What the program looks for in cells:**
1. **Command lines** — lines starting with `<Router>` or `[Router]` followed by a command
2. **Node lines** — lines with just `<NodeName>` (no command)

**Example cell that works:**
```
<HUAWEI>display device
<TUC-TEST01>
<TUC-TEST02>
```

**This will:**
- Find `TUC-TEST01 display device.png` and insert it at `<TUC-TEST01>` paragraph
- Find `TUC-TEST02 display device.png` and insert it at `<TUC-TEST02>` paragraph

### Step 4: Configure putpnginword.py

Open `putpnginword.py` in a text editor. Find these lines at the top:

```python
# --- Configuration ---
DOCX_INPUT = r"your_document.docx"
PNG_PATH = r"screenshots\*.png"
DOCX_OUTPUT = "your_document_RESULT.docx"
```

**Change to your actual file names.**

**Optional — Section Filtering:**

If your document has many tables and you only want to process specific sections:

```python
# Process ALL tables (default)
TARGET_SECTIONS = []

# OR — Process only tables under specific headings
TARGET_SECTIONS = ['Device Management Acceptance']
```

### Step 5: Insert Images into Word

Run:

```bash
python putpnginword.py
```

**Output:**
```
Loaded: your_document.docx
Found 15 PNG files in screenshots\*.png

--- Table 1 ---
  Inserted: Router1 display device.png
    Node: TUC-TEST01, Block: 0
    Command: display device
  Inserted: Router2 display device.png
    Node: TUC-TEST02, Block: 0
    Command: display device

Saved: your_document_RESULT.docx
```

**Result:** `your_document_RESULT.docx` contains all matched images inserted at the correct positions.

---

## Understanding the Output

### Screenshot Naming Convention

| Command Type | Filename Example |
|-------------|------------------|
| Standalone | `Router1 display device.png` |
| Nested block | `Router1 system-view interface GE0_0_1 display this quit quit.png` |
| Error | `Router1 display wrong-command [error].png` |
| Missing device | `Router1 display device [FAN3 removed].png` |

**How to read nested filenames:**
- All commands concatenated with spaces
- `/` in interface names becomes `_`
- Trailing `quit` commands are preserved but stripped during matching

### Image Insertion Logic

**Option B — Block-Scoped Matching:**

```
<HUAWEI>cmd 7          ← Block 0
<device1>              ← Gets cmd 7 PNG
<device2>              ← Gets cmd 7 PNG
<HUAWEI>cmd 8          ← Block 1
<device1>              ← Gets cmd 8 PNG (second image!)
<device2>              ← Gets cmd 8 PNG (second image!)
```

**Result:** `device1` gets 2 images, `device2` gets 2 images.

**Error Handling:**

```
<HUAWEI>display wrong-command
<TUC-TEST01>
```

If `TUC-TEST01 display wrong-command [error].png` exists:
- **Normally:** Skipped (program looks for clean PNG first)
- **If cell has "Error:" text:** The [error] PNG is intentionally used

**Multi-Model with Empty Block Merge:**

```
CEx01                                ← Model label (ignored)
<HUAWEI>display cpu-usage           ← Command for model CEx01
CEx02                                ← Model label (ignored)
<HUAWEI>display cpu                 ← Command for model CEx02
<TUC-TEST01>                        ← Tries: cpu-usage → match.png ✅
                                         cpu       → skipped
```

---

## Advanced Features

### 1. Missing Device Detection

When processing multiple logs for the same device, if `display device` shows fewer cards than before:

```
Log 1: display device → Shows FAN1, FAN2, PWR1 (baseline)
Log 2: display device → Shows FAN1, PWR1 only
```

**Output:** `Router1 display device [FAN2 removed].png`

Also copied to `removeddevicetest/` for comparison.

### 2. New Alarm Detection

Same logic for `display alarm active`:

**Output:** `Router1 display alarm active [NewAlarm1 added].png`

### 3. Command Abbreviations

These are automatically expanded:

| Abbreviation | Full Command |
|-------------|-------------|
| `dis` | `display` |
| `dis th` | `display this` |
| `system` / `sys` | `system-view` |
| `q` | `quit` |
| `comm` | `commit` |

### 4. Section Filtering

Process only specific sections of your document:

```python
TARGET_SECTIONS = ['Device Management Acceptance']
```

The program walks the document headings. When it finds a heading matching your target, it processes all tables under it until a heading of the same or higher level appears.

---

## Troubleshooting

### Problem: "No Huawei VRP prompts found"

**Cause:** Your log file doesn't match the expected prompt format.

**Fix:** Ensure prompts look like:
```
<RouterName> command
```
or
```
[RouterName] command
```

**Common issues:**
- Missing space after `>` or `]`
- Wrong bracket type (`{` instead of `<`)
- No command after prompt

### Problem: "No match: NodeName block 0"

**Cause:** The PNG filename doesn't match the cell content.

**Check:**
1. Did `run.py` generate screenshots? Check `screenshots/` folder.
2. Is the device name exactly the same? Case-insensitive, but must match exactly.
3. Is the command sequence correct? Nested blocks require all commands in order.

**Example mismatch:**
- Cell: `system-view` + `display this` (without quit)
- PNG: `Router1 system-view display this quit quit.png`
- **Result:** ✅ Matches! Trailing `quit` is stripped during comparison.

### Problem: Images inserted at wrong position

**Cause:** Node line not found in expected paragraph.

**Check:**
- Is the node line a separate paragraph? (`<NodeName>` alone on one line)
- Is there extra text after the node name?

### Problem: "Skipped (error)" messages

**Cause:** The only matching PNG has `[error]` suffix.

**Fix:**
- If the command actually produces an error → This is correct behavior
- If the command should succeed → Check why `process_network_logs.py` flagged it as error

### Problem: Table 8 / Empty cell — no output

**Cause:** Cell has commands but no nodes.

**Fix:** Add `<NodeName>` lines after commands to indicate where images should be inserted.

### Problem: Chromium not found

**Cause:** `playwright install chromium` wasn't run.

**Fix:**
```bash
playwright install chromium
```

---

## File Reference

| File | Purpose | When to Edit |
|------|---------|-------------|
| `run.py` | Batch process all logs | Rarely — just run it |
| `putpnginword.py` | Insert PNGs into DOCX | Edit `DOCX_INPUT` and `DOCX_OUTPUT` at top |
| `process_network_logs.py` | Core log→PNG engine | Only if adding new error patterns |
| `display_device_parser.py` | Device output parsing | Rarely |
| `display_alarm_parser.py` | Alarm output parsing | Rarely |
| `requirements.txt` | Dependencies | Only if adding new packages |

---

## Summary of Commands

```bash
# Install (one-time)
pip install -r requirements.txt
playwright install chromium

# Generate screenshots
python run.py

# Insert into Word (after editing putpnginword.py config)
python putpnginword.py

# Run tests
python -m pytest tests/ -v
```

---

**Questions?** Check the inline comments in `putpnginword.py` and `process_network_logs.py` — both have extensive documentation.
