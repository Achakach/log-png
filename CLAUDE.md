# Huawei Network Log Screenshot Generator

## Project Overview
Tool that converts Huawei VRP CLI session logs into terminal-style PNG screenshots. Parses raw log text, groups commands by prompt depth, renders HTML, and captures screenshots via Playwright (headless Chromium).

## Architecture
Pipeline: **Log Generation** → **Parse & Group** → **Screenshot** → **Insert into Word**

### Core Engine (`process_network_logs.py`)
- `_split_into_segments()` — Regex parser, splits raw log into `{prompt, command, output}` segments. Recognizes Huawei VRP prompts: `<Router>` (user view), `[Router]`/`[~Router]`/`[*Router]` (system view), `[Router-subview]`/`[~Router-subview]`/`[*Router-subview]` (sub-view). The `~` prefix = unsaved config changes, `*` prefix = alarm/fault state
- `_prompt_depth()` — Returns nesting depth (0=user, 1=system, 2+=sub-view). Strips `~` and `*` prefixes before processing. Counts sub-view keywords in prompt remainder
- `_extract_device_name()` — Strips `~` and `*` prefixes, then sub-view suffixes from prompt using keyword list. Requires `idx > 2` to avoid false matches on short device names
- `_group_segments()` — Depth-based grouping: standalone commands get own PNG, nested blocks (system-view + sub-views) become one PNG. Depth-0 segments after nested blocks fall through as standalone
- `_finalize_group()` — Adds `prompt_raw` and `router` (sanitized filename) fields. HTML escaping is handled by Jinja2 autoescape, NOT here
- `generate_screenshots()` — Async Playwright renderer with Jinja2 autoescape. Viewport 1200x900. **Nested block filenames concatenate all commands**: `{device} {cmd1} {cmd2} ... .png`. Also handles baseline tracking for `display device` and `display alarm active` commands
- `process_network_logs()` — Sync entry point. Detects existing event loop and uses ThreadPoolExecutor if needed (Jupyter compatibility)
- `sanitize_filename()` — Strips only OS-invalid chars (`\/:*?"<>|`), preserves spaces and hyphens. `|` replaced with space. `/` replaced with `_` (e.g. `GigabitEthernet0/0/1` → `GigabitEthernet0_0_1`). Fallback `'unnamed'` for empty input, `max_length=200`

### Display Device Baseline Tracker (`display_device_parser.py`)
- `parse_display_device()` — Parses `display device` CLI output into card records `{slot, card, type_}`. Extracts table rows between dashed separators. Chassis line (card `-`) is included but typically ignored by callers
- `compare_devices()` — Returns card names present in baseline but absent in current. Uses `(slot, card)` as unique key to handle same card name in multiple slots
- `format_removed_suffix()` — Converts missing cards into filename suffix, e.g. `[FAN3 removed]` or `[FAN3 PWR1 removed]`
- Integration: First `display device` per NE establishes baseline. Subsequent runs compare against baseline and append `[CARD removed]` to PNG filename if cards are missing

### Display Alarm Active Baseline Tracker (`display_alarm_parser.py`)
- `parse_display_alarm_active()` — Parses `display alarm active` CLI output. Extracts EntPhysicalName from Description column: `EntPhysicalName=FAN slot 1/3` → `FAN3`
- `compare_alarms()` — Returns new card names (from EntPhysicalName) present in current but not in baseline. Uses `(alarm_id, card_name)` as unique key
- `format_alarm_suffix()` — Converts new alarms into filename suffix, e.g. `[FAN3 removed]`
- Integration: First `display alarm active` per NE establishes baseline. Subsequent runs compare and append `[CARD removed]` for new alarms caused by removed cards

### Removed Device Test Folder (`removeddevicetest/`)
- Created alongside `screenshots/` when baseline changes detected
- Contains baseline copy + changed variant for easy review
- **display device** missing cards: copies baseline `display device.png` + saves `[CARD removed].png`
- **display alarm active** new alarms: copies baseline `display alarm active.png` + saves `[CARD removed].png`

### Word Inserter (`putpnginword.py`)
- `parse_paragraphs()` — Extracts commands and nodes from cell paragraphs. Returns `(commands, [nodes])` tuples. Splits on standalone user-view `<Router>cmd` after nested blocks
- `parse_paragraphs_detailed()` — Same as `parse_paragraphs()` but returns paragraph indices for each node. Format: `(commands, [(node, para_idx), ...])`. Enables block-scoped insertion
- `_merge_empty_blocks()` — **Empty Block Merge**: If a standalone block has no nodes, prepend its commands to the next block with nodes. This creates a "command pool" where all bottom nodes can try all commands
- `match_cell_blocks()` — **Option B** matching: each block's nodes are matched independently. For merged blocks, each node tries commands individually until finding a non-error match. Returns dicts with `node`, `block_idx`, `para_idx`, `commands`, `match_path`, `action` (`inserted` | `skipped_error` | `no_match`)
- `expand_abbreviations()` — Expands CLI abbreviations before matching: `system`→`system-view`, `dis`→`display`, `dis th`→`display this`, `q`→`quit`. Uses longest-match-first to avoid partial expansion
- `find_best_match()` — Matches cell commands to PNG filenames using **contiguous subsequence matching** (case-insensitive). Requires the full command sequence from the cell to appear consecutively in the PNG filename. Missing trailing tokens (e.g. `quit`) are allowed. Device name must match exactly
- `sanitize_filename()` — Same logic as `process_network_logs.py` for consistent filename handling
- Main loop: Option B + Empty Block Merge — iterates blocks independently. Merged blocks try each command per device until first non-error match. Same node can receive multiple images if it appears after different command blocks. Paragraph tracking via `para_idx` ensures correct insertion point
- `PERMIT_FALSE_KEYWORDS` / `PERMIT_TRUE_KEYWORDS` — configurable constants to control which test cases get images

### Sub-view Keywords (used in `_extract_device_name` and `_prompt_depth`)
`ospf`, `GigabitEthernet`, `Loopback`, `Vlanif`, `bgp`, `isis`, `acl`, `vpn-instance`, `port-group`
- **Do not** add short keywords like `GE` or `Eth` — they cause false matches on device names (e.g. `[HW-AGE-01]`)

### Log Generator
- `nested_log_gen.py` — Generates deterministic Huawei VRP log. Single NE (`HW-Core-BKK-01`), every command runs once. Each nested session (interface/OSPF) enters and exits system-view independently. After config changes (shutdown, network, silent-interface), prompts show `~` indicator (unsaved config)

### Entry Points
- `run.py` — Reads all `.txt` from `logs/`, outputs PNGs to `screenshots/`
- `process_network_logs.py __main__` — CLI with file/directory argument
- `putpnginword.py` — Inserts PNGs into Word .docx UAT document (reads PNGs from folder, matches by device+command, saves new .docx)

## Dependencies
- `jinja2` — HTML template rendering (with autoescape enabled)
- `playwright` — Headless Chromium for screenshot capture
- `python-docx` — Word document manipulation (for `putpnginword.py`)
- Install: `pip install -r requirements.txt && playwright install chromium`

## Filename Format
- Standalone: `HW-Core-BKK-01 display device.png`
- Nested: `HW-Core-BKK-01 system-view interface GigabitEthernet0_0_1 display this quit quit.png` (all commands concatenated)
- `/` in interface names replaced with `_` by `sanitize_filename()`
- No index suffix — each command appears only once in production logs

## Rules and Conventions

### Mandatory: Return to user view after nested commands
ทุกครั้งที่จบชุดคำสั่ง nested (system-view / interface / OSPF) ต้องมี `quit` กลับไป user view (`<Router>`) เสมอ ก่อนจะเริ่มชุดใหม่

**ถูกต้อง:**
```
<HW-Core-BKK-01> system-view
[HW-Core-BKK-01] interface GE0/0/1
[HW-Core-BKK-01-GE0/0/1] display this
[HW-Core-BKK-01-GE0/0/1] quit
[HW-Core-BKK-01] quit
<HW-Core-BKK-01> system-view          ← เข้าใหม่หลังกลับ user view
[HW-Core-BKK-01] ospf 1
...
[HW-Core-BKK-01] quit
<HW-Core-BKK-01> display clock         ← standalone ใหม่
```

**ผิด:** อยู่ system-view ต่อเนื่องโดยไม่กลับ user view → grouping จะผิด

### PNG filenames use spaces, not underscores
- `HW-Core-BKK-01 display device.png` (not `HW_Core_BKK_01_display_device.png`)
- `sanitize_filename()` preserves spaces and hyphens, only strips `\/:*?"<>|`
- `~` (unsaved config indicator) is stripped before filename construction — it never appears in PNG filenames

### Single NE per log file
Each log file is for one network element. The router name is hardcoded as `HW-Core-BKK-01` in the generator.

### Deterministic log generation
No randomness — every command runs exactly once, in a fixed order. No `target_lines` loop.

### No duplicate code
- `run_mock.py` and `test_regex.py` have been removed — `run.py` is the single entry point
- Batch logic is in `process_network_logs.py __main__` only, `run.py` uses `process_network_logs.process_network_logs()` directly

## Key Design Decisions
- Jinja2 autoescape is ON — do not manually HTML-escape values before rendering
- `_finalize_group` stores `prompt_raw` (unescaped) for filename construction — never use escaped values for filenames
- Depth-0 segment after a nested block falls through to be processed as standalone, never appended to the block
- `asyncio.run()` is wrapped with event-loop detection for Jupyter/async compatibility
- Nested blocks are bounded by returns to `<Router>` (depth 0): each `system-view` through `quit` back to user-view = one PNG
- Log files must start with `<Router>` (depth 0) prompts — logs starting directly at `[Router]` (depth 1) are not supported
- `~` prefix in prompts (e.g. `[~RouterName]`) indicates unsaved config changes. `*` prefix (e.g. `[*RouterName]`) indicates alarm/fault state. Regex matches `~?\*?` after `[`, `_prompt_depth()` and `_extract_device_name()` strip these prefixes before processing. They are displayed in screenshots but never appear in filenames
- Nested block PNG filenames concatenate ALL commands (including `quit`), not just entry command + sub-view suffixes
- `putpnginword.py` uses word-by-word prefix matching — prompt text in Word cells is ignored, only the command portion is extracted and matched against PNG filenames
- `putpnginword.py` paths (`DOCX_INPUT`, `PNG_PATH`, `DOCX_OUTPUT`) and permit keywords are hardcoded constants at the top of the file — adjust per document

## Current Project State (2026-05-04)

### Files
```
process_network_logs.py    ← core engine (parse, group, screenshot, baseline tracking)
display_device_parser.py   ← parses display device output, compares baseline
display_alarm_parser.py    ← parses display alarm active output, compares baseline
putpnginword.py            ← inserts PNGs into Word .docx (contiguous subsequence matching)
run.py                     ← main entry point (reads logs/ → writes screenshots/)
nested_log_gen.py          ← generates mock log (single NE, deterministic)
example.txt                ← example of Word table cell format (single + nested)
requirements.txt           ← jinja2, playwright, python-docx, pytest
.gitignore                 ← __pycache__, *.pyc, screenshots/, *.png
README.md                  ← usage docs
CLAUDE.md                  ← this file
docs/                      ← design specs and implementation plans
  superpowers/
    specs/2026-04-23-putpnginword-fix-design.md
    specs/2026-04-28-display-device-baseline-design.md
    plans/2026-04-23-putpnginword-fix.md
tests/                     ← unit tests
  test_putpnginword.py     ← tests for parsing, expansion, matching, dedup
  test_display_device_parser.py  ← tests for device parser, compare, suffix
  test_display_alarm_parser.py   ← tests for alarm parser, compare, suffix
logs/                      ← input log files (.txt)
screenshots/               ← output PNG files
removeddevicetest/         ← baseline + removed card/alarm PNGs for review
```

### Removed files
- `loggen.py` — replaced by `nested_log_gen.py`
- `run_mock.py` — replaced by `run.py`
- `test_regex.py` — not a real test, removed
- `mock_log.txt` — Cisco format, incompatible with parser

### Bug fixes (resolved)
- Fixed `_group_segments()`: depth-0 segment after nested block no longer incorrectly appended to the block
- Fixed filename collisions: removed duplicate overwrite risk
- Fixed HTML escape anti-pattern: Jinja2 autoescape replaces manual `html.escape()` + reverse unescape
- Fixed `_extract_device_name()`: removed short keywords `GE`/`Eth`/`Vlan` that caused false matches; added `idx > 2` guard
- Fixed `_prompt_depth()`: now actually counts depth instead of hardcoding `return 2`
- Added format validation warning when no Huawei VRP prompts found
- Added viewport 1200x900 for Playwright
- Added event-loop detection for Jupyter/async compatibility
- Fixed `exit()` → `sys.exit()` in entry points
- Fixed directory scan to filter out subdirectories
- Added support for `~` and `*` prefixes in prompts (`[~RouterName]` = unsaved config, `[*RouterName]` = alarm/fault): regex now matches `~?\*?`, `_prompt_depth()` and `_extract_device_name()` strip these prefixes before processing
- Fixed `sanitize_filename()`: `|` (pipe) replaced with space instead of underscore
- Changed nested block PNG naming: from `{device} {first-cmd} {sub-view-suffixes}.png` to concatenating all commands `{device} {cmd1} {cmd2} ... .png`
- Added `putpnginword.py`: inserts PNGs into Word .docx using word-by-word prefix matching (supports abbreviated commands)
- **Fixed `putpnginword.py` matching logic (2026-04-23):** replaced prefix matching with contiguous subsequence matching to prevent false positives (e.g. `system-view set cpu` no longer matches `system-view display current-configuration`)
- **Added `putpnginword.py` deduplication (2026-04-23):** ensures 1 image per node per cell via `inserted_nodes` set
- **Added `putpnginword.py` abbreviation expansion (2026-04-23):** `expand_abbreviations()` supports `system`→`system-view`, `dis`→`display`, `dis th`→`display this`, `q`→`quit` with longest-match-first
- **Fixed `putpnginword.py` empty prompt parsing (2026-04-23):** `parse_paragraphs()` now skips prompt-only lines with no commands (e.g. `[HUAWEI]`)
- **Added unit tests (2026-04-23):** `tests/test_putpnginword.py` covers parsing, expansion, matching, and deduplication
- **Added display device baseline tracking (2026-04-28):** `display_device_parser.py` detects missing cards and appends `[CARD removed]` suffix to PNG filenames. Copies baseline + removed variant to `removeddevicetest/`
- **Added display alarm active baseline tracking (2026-04-28):** `display_alarm_parser.py` detects new alarms from removed cards via EntPhysicalName and appends `[CARD removed]` suffix. Copies baseline + alarm variant to `removeddevicetest/`
- **Added `removeddevicetest/` folder (2026-04-28):** Stores baseline copy + changed PNG for easy review when cards are removed or new alarms appear
- **Implemented Option B (2026-05-02):** Block-scoped node matching. Same node can receive multiple images when appearing after different command blocks. 93 tests pass.
- **Implemented Empty Block Merge (2026-05-02):** Empty standalone blocks merge into next block with nodes. Bottom nodes try all commands in pool. Requires `[ERROR]` PNGs for wrong command+device combos.
- **Implemented Error Preference (2026-05-02):** `[ERROR]` PNGs are skipped in favor of clean PNGs. First non-error match wins.
- **Added `test_option_b_integration.py` (2026-05-02):** 8 tests for block-scoped matching and paragraph tracking.
- **Added `test_multi_block_preference.py` (2026-05-02):** 4 tests for error preference across multiple blocks.

## Known Limitations
- Only supports Huawei VRP format (`<Router>` / `[Router]` prompts). Cisco IOS is NOT supported
- Regex may match output lines that resemble prompts if they start with `[` or `<` at column 0
- `putpnginword.py` abbreviation dictionary is hardcoded; new abbreviations must be added to `_ABBREVIATIONS` manually
- `putpnginword.py` paths and permit keywords are hardcoded constants at the top of the file
- `display_alarm_parser.py` extracts EntPhysicalName only; alarms without EntPhysicalName are skipped
- Baseline tracking is per-session only (not persisted to disk); if log files are processed separately, baselines are reset
- **Multi-model / empty block merge** depends on `[ERROR]` PNGs to filter wrong command+device matches. If `[ERROR]` is missing, the code may insert the wrong image (arbitrary first match)
- **User tracking** (username, login session) is NOT implemented — cannot track which user ran which command