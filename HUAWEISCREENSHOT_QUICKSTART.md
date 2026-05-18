# Huawei Screenshot Tool - Complete User Guide

## Version 1.2.1 | 2026-05-18

---

## 1. QUICK START (5 Minutes)

### What You Need
- Windows 10/11 PC
- This ZIP file extracted to any folder
- Huawei VRP log files (`.txt` or `.log`)

### 3-Step Workflow
```
Step 1: Copy your log files → logs/
Step 2: Double-click run.exe → generates screenshots
Step 3: Double-click putpnginword.exe → inserts into Word
```

### First Time Setup
1. Extract `HuaweiScreenshotTool.zip` to a folder (e.g., `C:\HuaweiScreenshotTool`)
2. **Do NOT move or delete the `ms-playwright/` folder** — it contains the browser
3. Put your `.txt` or `.log` files in the `logs/` folder
4. Start with `run.exe`

---

## 2. WHAT EACH EXE DOES

### `run.exe` — Screenshot Generator
**Purpose:** Reads Huawei VRP logs and generates terminal-style PNG screenshots

**How to use:**
- Double-click to process ALL files in `logs/`
- Or use Command Prompt:
  ```cmd
  run.exe  # process all .txt/.log files in logs/
  ```

**Output:** PNG files in `screenshots/` folder

**Config:** `run_config.json`
```json
{
  "logs_dir": "logs",
  "output_dir": "screenshots",
  "whitelist": [
    "stelnet 10.1.1.1",
    "stelnet 10.10.10.10"
  ],
  "max_line_length": 130,
  "max_output_lines": 70,
  "screenshot_width": 1000
}
```
- `whitelist`: Empty = process all commands. Add commands to filter (e.g., `["display device", "display clock"]`)
### REMARK about this => you can use whitelist_gui to create a whitelist
                      => it use prefix match so ["display"] will match every display xxx command
                      => for the nested command (serie of command) ex. system-view..., stelnet... simply put ["sys"] or ["stelnet"] in the whitelist
                      => if in the log contain an abbreviation commmand please put it in the white list ex. ["sys"] will match sys, system, system-view but ["system-view"] won't match sys, and system
                      => the removeddevicetest/ stores baseline + changed variants when device cards are removed or new alarms appear (auto-created).
---

### `log_stats.exe` — Log Analyzer
**Purpose:** Shows statistics about commands in your log files

**How to use:**
- Double-click to see a table of all commands with counts

**Output:** Console window showing:
```
Command                                              Standalone     Nested    Total
--------------------------------------------------------------------------------
display device                                                1          0        1
display clock                                                 1          0        1
system-view                                                   0          1        1
...
```
### REMARK about this => it count a nested command (serie of command) as a many command ex. system-view display this = 2
**Note:** Window stays open with "[Press Enter to close]" prompt

---

### `putpnginword.exe` — Word Document Inserter
**Purpose:** Matches screenshots to commands in Word tables and inserts them

**How to use:**
1. Make sure `run.exe` has already generated PNGs in `screenshots/`
2. Double-click `putpnginword.exe`
3. It reads `comprehensive_test_cases_updated.docx`
4. Inserts matching PNGs at device nodes (`<TUC-TEST01>`, etc.)
5. Saves result as `comprehensive_test_cases_updated_RESULT_v2.docx`

**Config:** `putpnginword_config.json`
```json
{
  "docx_input": "comprehensive_test_cases_updated.docx",
  "png_path": "screenshots\\*.png",
  "docx_output": "comprehensive_test_cases_updated_RESULT_v2.docx",
  "target_sections": []
}
```

**Matching Logic:**
- Reads commands from Word table cells (e.g., `<HUAWEI>display device`)
- Matches to PNG filenames (e.g., `TUC-TEST01 display device.png`)
- Uses **exact token matching with abbreviation expansion** — full command sequence must match token-for-token in PNG filename
- The full command sequence from the Word cell must match the PNG filename token-for-token (after expanding abbreviations like `dis`→`display`). Abbreviations work because they are expanded before matching, but partial or out-of-order tokens do not match.
- Skips `[error]` PNGs in favor of clean ones
- Supports abbreviated commands: `dis` → `display`, `dis th` → `display this`

### REMARK about this => the part that want to match a certain file type please change a file type in the docx to match ex. startup saved-configuration xxx.zip if in the log is .cfg please change .zip to .cfg
                      => this is the only script that can handle abbreviation
---

### `putpnginxlsx.exe` — Excel Inserter
**Purpose:** Inserts PNGs into Excel spreadsheet based on sheet configs

**How to use:**
1. Generate screenshots with `run.exe`
2. Edit `putpnginxlsx_config.json` to map sheet names to commands
3. Double-click `putpnginxlsx.exe`

**Config:** `putpnginxlsx_config.json`
```json
{
  "xlsx_input": "template.xlsx",
  "xlsx_output": "output.xlsx",
  "png_path": "screenshots/*.png",
  "sheet_configs": [
    ["DisplayClock", "display clock"],
    ["DisplayDevice", "display device"],
    ["DisplayDevice", "dis device"]
  ],
  "start_cell": "B2",
  "image_width_inches": 6,
  "gap_rows": 3
}
```
### REMARK about this => this script can't handle abbreviation by itself please add an abbreviation in the "sheet_configs"
---

### `whitelist_gui.exe` — GUI Whitelist Builder
**Purpose:** Interactive tool to pick which commands to include in whitelist

**How to use:**
1. Double-click to open GUI window
2. Scans `logs/` folder and lists all unique commands with counts
3. Check the commands you want to whitelist
4. Click "Generate Config" → shows JSON array to copy into `run_config.json`

**Why use it:** Instead of manually editing JSON, visually pick commands from a checkbox list
---

## 3. FOLDER STRUCTURE EXPLAINED

```
HuaweiScreenshotTool/
│
├── run.exe                          # Main screenshot generator
├── log_stats.exe                    # Log statistics viewer
├── putpnginword.exe                 # Word inserter
├── putpnginxlsx.exe                 # Excel inserter
├── whitelist_gui.exe                # GUI whitelist picker
│
├── run_config.json                  # Config for run.exe
├── putpnginword_config.json         # Config for Word inserter
├── putpnginxlsx_config.json         # Config for Excel inserter
│
├── comprehensive_test_cases_updated.docx    # Sample Word doc for testing
├── template.xlsx                    # Sample Excel template
├── README.md                       # Short reference card
│
├── logs/                            # ⬅️ PUT YOUR LOG FILES HERE
│   └── (your .txt and .log files)
│
├── screenshots/                     # ⬅️ PNG OUTPUT GOES HERE (auto-created)
│   └── TUC-TEST01 display device.png
│   └── TUC-TEST01 system-view interface ... .png
│
├── removeddevicetest/               # ⬅️ Baseline + changed variants (auto-created)
│   └── (copies of display device baselines when cards change)
│
└── ms-playwright/                   # ⬅️ BUNDLED CHROMIUM BROWSER
    └── chromium_headless_shell-1208/
        └── chrome-headless-shell-win64/
            └── chrome-headless-shell.exe   # The actual browser binary
```

### Why each folder exists:

| Folder | Purpose | Can I delete? |
|---|---|---|
| `logs/` | Input folder for your `.txt`/`.log` files | Yes (but add your logs) |
| `screenshots/` | Output folder for generated PNGs | Yes (recreated automatically) |
| `removeddevicetest/` | Stores baseline + changed PNGs when device cards are removed or alarms appear | Yes (recreated automatically) |
| `ms-playwright/` | **Bundled Chromium browser** required by Playwright for screenshot rendering | **NO — will break everything** |

**Critical:** Do NOT move or rename `ms-playwright/`. The EXE looks for it in the same folder.

---

## 4. LOG FILE FORMAT REQUIREMENTS

Your log files **must** use Huawei VRP prompt format:

```
<DeviceName> command              ← User view (depth 0)
[DeviceName] command              ← System view (depth 1)
[DeviceName-subview] command      ← Sub-view (depth 2+)
```

### Examples:
```
<TUC-TEST01> display device       ← standalone command
<TUC-TEST01> system-view          ← starts nested block
[TUC-TEST01] interface GE0/0/1    ← inside block
[TUC-TEST01-GE0/0/1] display this  ← deeper inside block
[TUC-TEST01-GE0/0/1] quit         ← back up
[TUC-TEST01] quit                  ← back to user view
<TUC-TEST01> display clock        ← new standalone command
```

### Critical Rule:
**Every nested block MUST end with \`quit\` back to \`<DeviceName>\` user view.**
If you don't return to user view, the next command gets swallowed into the previous block.

---

## 5. CONFIGURATION FILES

All configs are JSON files. Edit with Notepad or any text editor.

### `run_config.json`
```json
{
  "logs_dir": "logs",
  "output_dir": "screenshots",
  "whitelist": [
    "stelnet 10.1.1.1",
    "stelnet 10.10.10.10"
  ],
  "max_line_length": 130,
  "max_output_lines": 70,
  "screenshot_width": 1000
}
```
- `logs_dir`: Where to find input logs
- `output_dir`: Where to save PNGs
- `whitelist`: `[]` = all commands. `["display device"]` = only that command
- `max_line_length`: 130 — Max characters per line before truncating long output lines
- `max_output_lines`: 70 — Max output lines per screenshot before truncating
- `screenshot_width`: 1000 — HTML container width in pixels for PNG rendering

### `putpnginword_config.json`
```json
{
  "docx_input": "comprehensive_test_cases_updated.docx",
  "png_path": "screenshots\\*.png",
  "docx_output": "comprehensive_test_cases_updated_RESULT_v2.docx",
  "target_sections": []
}
```
- `docx_input`: Your Word template with commands and device nodes
- `png_path`: Glob pattern to find PNGs (usually `screenshots\*.png`)
- `docx_output`: Result filename
- `target_sections`: Empty = all tables. `["Section1"]` = only that section

### `putpnginxlsx_config.json`
```json
{
  "xlsx_input": "template.xlsx",
  "xlsx_output": "output.xlsx",
  "png_path": "screenshots/*.png",
  "sheet_configs": [
    ["SheetName", "command to match"]
  ],
  "start_cell": "B2",
  "image_width_inches": 6,
  "gap_rows": 3
}
```
- `sheet_configs`: Maps Excel sheet names to PNG filename patterns
- `start_cell`: Where first image goes
- `image_width_inches`: Width of inserted images
- `gap_rows`: Empty rows between images

---

## 6. SCREENSHOT NAMING

### Standalone commands:
```
TUC-TEST01 display device.png
TUC-TEST01 display clock.png
```

### Nested blocks (all commands concatenated):
```
TUC-TEST01 system-view interface GigabitEthernet0_0_1 display this quit quit.png
```
- `/` in interface names becomes `_` (e.g., `GigabitEthernet0/0/1` → `GigabitEthernet0_0_1`)
- Spaces preserved in filenames

---

## 7. TROUBLESHOOTING

### "Executable doesn't exist" error
**Cause:** Playwright can't find Chromium browser  
**Fix:** Make sure `ms-playwright/` folder is in the same folder as the EXE. Don't move it.

### "No log files found"
**Cause:** `logs/` folder is empty or missing  
**Fix:** Copy your `.txt` or `.log` files into `logs/`

### "No screenshots generated"
**Cause:** Log format doesn't match Huawei VRP prompts  
**Fix:** Check that your logs start with `<DeviceName>` or `[DeviceName]` prompts

### putpnginword.exe: "No match" for everything
**Cause:** No PNGs in `screenshots/` or filenames don't match  
**Fix:** Run `run.exe` first to generate screenshots

### log_stats.exe window closes instantly
**Fixed in v1.2.0** — now shows "[Press Enter to close]" prompt  
(If using old version, run from Command Prompt instead)

### whitelist_gui.exe shows "No .txt/.log files found"
**Cause:** `logs/` folder empty or EXE can't find path  
**Fixed in v1.2.0** — now correctly resolves EXE directory

### SmartScreen / Windows Defender blocks the EXE
**Cause:** Unsigned executable (PyInstaller builds are commonly flagged)  
**Fix:** Click "More info → Run anyway" or right-click → Properties → Unblock  
**Permanent fix:** Purchase code signing certificate (~$70/year)

---

## 8. COMPLETE WORKFLOW EXAMPLE

### Scenario: You have 3 log files and want screenshots in a Word doc

**Step 1 — Prepare:**
```
Copy TUC-CORE-01.txt → logs/
Copy TUC-EDGE-02.txt → logs/
Copy TUC-ACCESS-03.txt → logs/
```

**Step 2 — Generate screenshots:**
```
Double-click run.exe
```
Output:
```
screenshots/
  TUC-CORE-01 display device.png
  TUC-CORE-01 display clock.png
  TUC-CORE-01 system-view interface GigabitEthernet0_0_1 display this quit quit.png
  TUC-EDGE-02 display device.png
  ...
```

**Step 3 — (Optional) Check stats:**
```
Double-click log_stats.exe
```
Shows command frequency table

**Step 4 — Insert into Word:**
```
Double-click putpnginword.exe
```
Reads: `comprehensive_test_cases_updated.docx`  
Writes: `comprehensive_test_cases_updated_RESULT_v2.docx`  
Inserts matching PNGs at each `<TUC-...>` node

**Step 5 — Verify:**
```
Open comprehensive_test_cases_updated_RESULT_v2.docx
Check that images appear under each device node
```

---

## 9. TECHNICAL NOTES

### What are these EXEs?
They are **PyInstaller one-file builds**. Each EXE contains:
- Embedded Python interpreter
- All required libraries (Playwright, python-docx, Jinja2, etc.)
- Your script code

They run **identically** to `python script.py` but don't require Python installed.

### Why is the ZIP 291 MB?
The browser (`ms-playwright/`) is 258 MB. The 5 EXEs are ~180 MB combined (each bundles Python + libraries).

### Can I run on Mac/Linux?
No. These EXEs are Windows-only. The source `.py` files work on any OS with Python installed.

---

## 10. SUPPORT

Please contact Kacha Thanaphithak 50057696.

**Internal use only.**
