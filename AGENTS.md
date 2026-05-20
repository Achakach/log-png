# Agent Instructions

## Project
Huawei VRP CLI log → PNG screenshot generator + Word/Excel inserters.
10 test files, ~199 pytest tests.
No package structure — scripts import each other directly.

## Developer Commands

```bash
# Install
pip install -r requirements.txt
playwright install chromium

# Run all tests
pytest tests/
# Run specific test file
pytest tests/test_putpnginword.py -v

# Build EXE (Windows)
pyinstaller --clean -y putpnginxlsx_v3.spec
```

## Entry Points

| Script | Purpose |
|--------|---------|
| `run.py` | Process all `.txt`/`.log` in `logs/` → `screenshots/` |
| `process_network_logs.py` | Core engine: parse, group, render, screenshot. Can be imported or run as `__main__` with file/dir arg |
| `putpnginword.py` | Match PNGs → insert into `.docx` UAT document |
| `putpnginxlsx.py` | Legacy: insert into Excel (vertical stack) |
| `putpnginxlsx_v2.py` | Horizontal gallery: one row per device |
| `putpnginxlsx_v3.py` | Vertical gallery: one column per device, headers in Row 1 |

## Architecture

Pipeline: `logs/*.txt` → `_split_into_segments()` → `_group_segments()` → Jinja2 + Playwright → `screenshots/*.png`

- **`process_network_logs.py`** — regex parser, depth-based grouping, async Playwright renderer
- **`filename_utils.py`** — shared `sanitize_filename()` (used by core + inserters)
- **`display_device_parser.py`** / **`display_alarm_parser.py`** — baseline tracking for removed cards/alarm detection
- **`putpnginword.py`** — contiguous subsequence matching, Option B block-scoped insertion, empty block merge, error preference

### Key Conventions

- **Jinja2 autoescape is ON** — do NOT manually `html.escape()` values
- **`_finalize_group()` stores `prompt_raw`** — use unescaped for filenames, never escaped
- **Depth-0 segments after nested blocks fall through** as standalone, never appended to block
- **Nested block filenames concatenate ALL commands** (including `quit`)
- **`~` prefix** = unsaved config changes, **`*` prefix** = alarm/fault state — both stripped before filename construction
- **PNG filenames use spaces**, not underscores — `sanitize_filename()` preserves spaces/hyphens, strips only `\/:*?"<>|`
- **`/` in interface names** → `_` (e.g., `GigabitEthernet0/0/1` → `GigabitEthernet0_0_1`)
- **Log files must start with `<Router>`** (depth 0) — logs starting at `[Router]` (depth 1) are not supported
- **Every nested block must end with `quit` back to `<Router>`** — or grouping breaks

### Config Pattern

All inserters follow the same config pattern:
- Config file named `<script>_config.json` in same dir
- If missing, auto-generated with defaults, script exits with message
- `get_base_dir()` resolves relative to script/exe location (works for both `.py` and PyInstaller `.exe`)

## Multi-version Inserters

Three Excel inserter versions coexist. **Do not merge or modify old versions.** Create new ones as separate files.

| Version | Layout | Config keys |
|---------|--------|-------------|
| v1 (`putpnginxlsx.py`) | Vertical stack (one column) | `image_width_inches`, `columns_per_image` |
| v2 (`putpnginxlsx_v2.py`) | Horizontal gallery (one row per device) | `image_col_gap` (columns), `device_row_gap` (rows) |
| v3 (`putpnginxlsx_v3.py`) | Vertical gallery (one column per device, headers in Row 1) | `image_col_gap` (rows), `device_row_gap` (columns) |

All auto-calculate sizing from PNG native dimensions (v2: width→columns, v3: height→rows). No hardcoded sizing.

## Testing

- **199 tests** across 10+ test files
- No test config (`pytest.ini`, `tox.ini`) found — pytest runs with defaults
- Test files follow naming convention `test_*.py`
- Key test categories: parsing, matching, baseline tracking, error preference, multi-NE, username matching, docx real cases

### Testing Pitfalls

- **Do not add `GE`, `Eth`, or `Vlan` as sub-view keywords** — causes false matches on device names like `[HW-AGE-01]`. See `_extract_device_name()`: requires `idx > 2` guard and only full keywords (`GigabitEthernet`, `Vlanif`, `ospf`, etc.)
- **Username tags in Word cells** — handled as noise via `NOISE_COMMANDS = {'username'}` in `putpnginword.py` parser. If adding new noise commands, update set + match test.

## Excel Inserter Notes

- `putpnginxlsx_v3.py`: device names are written in **Row 1 (bold)**. Column A left empty. `start_cell` default is `B2`.
- `putpnginxlsx_v2.py`: one **row per device**, images placed horizontally. Row gap controlled by `device_row_gap`.
- Both v2 and v3 use `openpyxl.utils.get_column_letter` / `column_index_from_string` for column math. `start_cell` parses `B2` → column letter + integer.

## PyInstaller / Distribution

- `.spec` files exist for each build target (`putpnginxlsx_v3.spec`, etc.)
- `pyinstaller --clean -y <name>.spec` is the standard build command
- Windows Defender may flag PyInstaller binaries unpredictably — rebuilds produce different hashes. If blocked, rebuild until one works.
- EXEs deployed to `HuaweiScreenshotTool/`

## Known Limitations (preserved from CLAUDE.md)

- Only Huawei VRP format supported — Cisco IOS is NOT supported
- Regex may match output lines resembling prompts starting with `[` or `<` at column 0
- `putpnginword.py` abbreviation dictionary is hardcoded — new abbreviations must be added manually to `_ABBREVIATIONS`
- Baseline tracking is per-session only (not persisted to disk)
- Empty block merge depends on `[ERROR]` PNGs to filter wrong command+device matches

## Files to Know

| File | Role |
|------|------|
| `process_network_logs.py` | Core engine |
| `filename_utils.py` | Shared filename sanitization |
| `display_device_parser.py` | Baseline tracking for `display device` |
| `display_alarm_parser.py` | Baseline tracking for `display alarm active` |
| `putpnginword.py` | Word .docx inserter |
| `putpnginxlsx_v3.py` | Excel inserter (vertical gallery) |
| `run.py` | Main entry point |
| `requirements.txt` | Pinned deps (jinja2, playwright, python-docx) |
| `CLAUDE.md` | Full architecture reference — keep in sync |
