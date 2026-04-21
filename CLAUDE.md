# Huawei Network Log Screenshot Generator

## Project Overview
Tool that converts Huawei VRP CLI session logs into terminal-style PNG screenshots. Parses raw log text, groups commands by prompt depth, renders HTML, and captures screenshots via Playwright (headless Chromium).

## Architecture
Pipeline: **Log Generation** → **Parse & Group** → **Screenshot**

### Core Engine (`process_network_logs.py`)
- `_split_into_segments()` — Regex parser, splits raw log into `{prompt, command, output}` segments. Recognizes Huawei VRP prompts: `<Router>` (user view), `[Router]`/`[~Router]`/`[*Router]` (system view), `[Router-subview]`/`[~Router-subview]`/`[*Router-subview]` (sub-view). The `~` prefix = unsaved config changes, `*` prefix = alarm/fault state
- `_prompt_depth()` — Returns nesting depth (0=user, 1=system, 2+=sub-view). Strips `~` and `*` prefixes before processing. Counts sub-view keywords in prompt remainder
- `_extract_device_name()` — Strips `~` and `*` prefixes, then sub-view suffixes from prompt using keyword list. Requires `idx > 2` to avoid false matches on short device names
- `_group_segments()` — Depth-based grouping: standalone commands get own PNG, nested blocks (system-view + sub-views) become one PNG. Depth-0 segments after nested blocks fall through as standalone
- `_finalize_group()` — Adds `prompt_raw` and `router` (sanitized filename) fields. HTML escaping is handled by Jinja2 autoescape, NOT here
- `generate_screenshots()` — Async Playwright renderer with Jinja2 autoescape. Viewport 1200x900
- `process_network_logs()` — Sync entry point. Detects existing event loop and uses ThreadPoolExecutor if needed (Jupyter compatibility)
- `sanitize_filename()` — Strips only OS-invalid chars (`\/:*?"<>|`), preserves spaces and hyphens. `|` replaced with space. `~` and `*` are valid in Windows filenames but are stripped during device name extraction before filename construction. Fallback `'unnamed'` for empty input, `max_length=200`

### Sub-view Keywords (used in `_extract_device_name` and `_prompt_depth`)
`ospf`, `GigabitEthernet`, `Loopback`, `Vlanif`, `bgp`, `isis`, `acl`, `vpn-instance`, `port-group`
- **Do not** add short keywords like `GE` or `Eth` — they cause false matches on device names (e.g. `[HW-AGE-01]`)

### Log Generator
- `nested_log_gen.py` — Generates deterministic Huawei VRP log. Single NE (`HW-Core-BKK-01`), every command runs once. Each nested session (interface/OSPF) enters and exits system-view independently. After config changes (shutdown, network, silent-interface), prompts show `~` indicator (unsaved config)

### Entry Points
- `run.py` — Reads all `.txt` from `logs/`, outputs PNGs to `screenshots/`
- `process_network_logs.py __main__` — CLI with file/directory argument

## Dependencies
- `jinja2` — HTML template rendering (with autoescape enabled)
- `playwright` — Headless Chromium for screenshot capture
- Install: `pip install -r requirements.txt && playwright install chromium`

## Filename Format
- Standalone: `HW-Core-BKK-01 display device.png`
- Nested with sub-views: `HW-Core-BKK-01 system-view ospf-1 GigabitEthernet0/0/1.png`
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

## Current Project State (2026-04-21)

### Files
```
process_network_logs.py   ← core engine (parse, group, screenshot)
run.py                    ← main entry point (reads logs/ → writes screenshots/)
nested_log_gen.py         ← generates mock log (single NE, deterministic)
requirements.txt          ← jinja2, playwright
.gitignore                ← __pycache__, *.pyc, screenshots/, *.png
README.md                 ← usage docs + mandatory rule about returning to user view
CLAUDE.md                 ← this file
logs/                     ← input log files (.txt)
screenshots/              ← output PNG files
```

### Removed files
- `loggen.py` — replaced by `nested_log_gen.py`
- `run_mock.py` — replaced by `run.py`
- `test_regex.py` — not a real test, removed
- `mock_log.txt` — Cisco format, incompatible with parser

### Bug fixes applied this session
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

## Known Limitations
- Only supports Huawei VRP format (`<Router>` / `[Router]` prompts). Cisco IOS is NOT supported
- Regex may match output lines that resemble prompts if they start with `[` or `<` at column 0