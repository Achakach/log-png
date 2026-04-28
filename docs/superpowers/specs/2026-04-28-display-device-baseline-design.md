# Display Device Baseline Tracking & Removed Card Detection

## Context

`process_network_logs.py` generates PNG screenshots from Huawei VRP CLI logs. Each log file may contain multiple `display device` commands. The first occurrence per NE establishes the baseline (expected card list: FAN1..5, PWR1..2). Subsequent `display device` commands compare against this baseline. Missing cards trigger a `[CARD removed]` suffix in the PNG filename.

## Goals

1. Parse `display device` output to extract card names (e.g., `FAN1`, `PWR2`).
2. Track baseline per NE (first `display device` per device name).
3. Compare subsequent runs against baseline and detect missing cards.
4. Append `[CARD removed]` to PNG filename when cards are missing.
5. Leave filename unchanged if nothing is missing (same as baseline).

## Architecture

### New Module: `display_device_parser.py`

Three public functions, no state:

- `parse_display_device(output_text: str) -> list[dict]`  
  Parses CLI output into structured records. Each record: `{slot: str, card: str, type_: str}`. Only lines with a card name (FAN, PWR, etc.) are included; the chassis line (Slot 1) is ignored for comparison.

- `compare_devices(baseline: list[dict], current: list[dict]) -> list[str]`  
  Returns card names present in baseline but absent in current, sorted. Uses `(slot, card)` as the unique key so that if the same card name appears in multiple slots they are treated independently.

- `format_removed_suffix(missing: list[str]) -> str`  
  Converts list of missing cards into the filename suffix, e.g. `[FAN3 removed]`.

### State: Per-NE Baseline Tracker

A simple `dict[str, list[dict]]` keyed by sanitized NE name.  
- Set on the first `display device` group for a given NE.  
- Read on every subsequent `display device` group for the same NE.  
- Lives only during a single `process_network_logs()` call (not persisted to disk).

### Integration Points in `process_network_logs.py`

1. **`_finalize_group()`** — no change. It adds raw fields.
2. **`generate_screenshots()`** — before building the filename:
   - Check if `first_cmd['command'] == 'display device'`.
   - If yes, call `parse_display_device(group[0]['output'])`.
   - If NE not yet in baseline dict → store as baseline, filename unchanged.
   - If NE already has baseline → call `compare_devices()`, if missing → append suffix.
   - If parse fails → log warning, fallback to original filename.

### Filename Rules

| Scenario | Example filename |
|----------|------------------|
| Baseline (first `display device`) | `TUC-TYB91G01HWLEFC303-CPLEF03 display device.png` |
| 2nd+ run, nothing missing | `TUC-TYB91G01HWLEFC303-CPLEF03 display device.png` |
| 2nd+ run, FAN3 missing | `TUC-TYB91G01HWLEFC303-CPLEF03 display device [FAN3 removed].png` |

## Error Handling

- Parse failure (malformed output): log warning, generate original filename.
- Empty card list: treat as baseline (first occurrence), no comparison.
- Missing baseline (should not happen): treat as baseline.

## Testing

- Unit test `parse_display_device` with sample output from `display device format.txt`.
- Unit test `compare_devices` with baseline vs current.
- Integration test: run `process_network_logs` on log with multiple `display device` commands, assert filenames.

## Files to Modify

- `process_network_logs.py` — integrate baseline tracking in `generate_screenshots()`
- New file: `display_device_parser.py` — parser + comparator
- New file: `tests/test_display_device_parser.py` — unit tests

## Dependencies

No new external dependencies. Uses existing `re` for parsing.
