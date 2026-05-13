# putpnginxlsx.py Design Spec

## Overview
Utility script that filters PNG screenshots by command keyword and inserts them vertically into a specified Excel sheet.

## Configuration (Hardcoded Constants)
| Constant | Default | Description |
|---|---|---|
| `XLSX_INPUT` | `"template.xlsx"` | Source .xlsx file |
| `XLSX_OUTPUT` | `"output.xlsx"` | Output .xlsx file (never overwrites input) |
| `PNG_PATH` | `r"screenshots\*.png"` | Glob pattern for PNG files |
| `SHEET_NAME` | `"Sheet1"` | Target sheet (created if missing) |
| `KEYWORD` | `"display clock"` | Case-insensitive filter on PNG filename |
| `START_CELL` | `"B2"` | First image anchor cell |
| `IMAGE_WIDTH_INCHES` | `6` | Image width in inches |
| `GAP_ROWS` | `3` | Empty rows between images |

## Algorithm
1. `glob.glob(PNG_PATH)` → list all PNGs
2. Filter: `KEYWORD.lower() in png_filename.lower()`
3. Sort by device name (first token of filename)
4. `load_workbook(XLSX_INPUT)` → get/create `SHEET_NAME`
5. For each filtered PNG:
   - Load image, set width = `IMAGE_WIDTH_INCHES * 914400` EMUs
   - Height auto-calculated from aspect ratio
   - `ws.add_image(img, f"B{current_row}")`
   - `rows_occupied = ceil(img_height_inches / 0.21)`
   - `current_row += rows_occupied + GAP_ROWS`
6. `wb.save(XLSX_OUTPUT)`

## Error Handling
- Missing `XLSX_INPUT`: clear error message, sys.exit(1)
- No PNGs match KEYWORD: warning, save empty sheet
- `screenshots/` missing: clear error message
- Invalid START_CELL format (must be letter+number): validation error

## Dependencies
- `openpyxl` (not in current requirements.txt — user installs separately)

## Scope
Single-file utility. No CLI arguments. No Word/COM integration. No baseline tracking.
