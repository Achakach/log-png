# Fix putpnginword.py — Accurate Matching & One Image Per Node

## Date: 2026-04-23

## Problem Statement

`putpnginword.py` has two critical issues when inserting PNG screenshots into Word documents:

1. **Multiple images per node**: The script inserts more than one image per `<NodeName>` line, causing duplicate or incorrect screenshots in the output document.
2. **False-positive matching**: The current prefix-matching logic in `find_best_match()` is too loose. For example, `system-view` in a cell can incorrectly match a PNG filename like `HW-Core-BKK-01 system-view display current-configuration quit.png`, even when the cell's actual commands are `system-view set cpu threshold 4`.

Additionally, Word cells often omit `quit` commands and end with empty prompts (e.g., `[HUAWEI]` with no command), so the matcher must not require `quit` tokens to be present in the cell text.

## Requirements

1. **One image per node per cell**: Each `<NodeName>` in a cell should receive exactly one image, inserted at the first matching paragraph.
2. **Accurate command matching**: A cell's command sequence must be found as a contiguous subsequence within a PNG filename's tokens, not just as a prefix.
3. **Abbreviation expansion**: Support common Huawei CLI abbreviations (`system` → `system-view`, `dis` → `display`, `dis th` → `display this`, `q` → `quit`).
4. **Handle empty prompts**: Skip prompt lines with no commands (e.g., `[HUAWEI]`). Do not require `quit` in the cell text.
5. **Preserve existing permit/false-keyword logic**: `PERMIT_FALSE_KEYWORDS` and `PERMIT_TRUE_KEYWORDS` must continue to work unchanged.

## Architecture

```
Word Cell paragraphs
    ↓
parse_paragraphs() — แยก commands + nodes (ข้าม prompt เปล่า)
    ↓
expand_abbreviations() — system→system-view, dis→display, q→quit, dis th→display this
    ↓
find_best_match() — contiguous subsequence match (ไม่ใช่ prefix)
    ↓
deduplicate() — 1 node = 1 image ต่อ cell
    ↓
insert_image() — ที่ <NodeName> paragraph แรกที่เจอ
```

## Components

### 1. Parsing (Modified)

- `parse_paragraphs()` skips prompt lines that have no command after the prompt (e.g., `[HUAWEI]`).
- Extracts commands from prompt lines (`<Router>cmd` and `[Router]cmd`).
- Extracts node names from `<NodeName>` lines.

**Example:**
```
<huawei>sys          → command: "sys"
[huawei]cmd2         → command: "cmd2"
[huawei]cmd3         → command: "cmd3"
[huawei]             → skipped (empty prompt)
```

### 2. Abbreviation Expansion (New)

Expands tokens **before** matching. Uses **longest-match-first** to avoid partial expansion.

| Abbreviation | Expansion       |
|--------------|-----------------|
| `dis th`     | `display this`  |
| `dis`        | `display`       |
| `system`     | `system-view`   |
| `q`          | `quit`          |

**Why longest-match-first:** If we expand `dis` before `dis th`, `dis th` becomes `display th` (invalid). By expanding `dis th` first, it correctly becomes `display this`, then `dis` applies to standalone `dis`.

### 3. Contiguous Subsequence Match (Replaces Prefix Match)

**Old behavior (prefix match):**
- Cell commands: `["system-view", "set", "cpu", "threshold", "4"]`
- Checks if PNG tokens start with cell tokens → too loose

**New behavior (contiguous subsequence):**
- Cell commands must appear **consecutively** and **in order** within the PNG filename tokens.
- Match starts from the first command token (device name is checked separately).
- Missing trailing tokens (like `quit`) in the cell are allowed — the subsequence can end before the PNG filename ends.

**Example — Should MATCH:**
- Cell: `["system-view", "cmd2", "cmd3"]`
- PNG: `HW-Core-BKK-01 system-view cmd2 cmd3 quit quit.png`
- Result: ✅ Match (subsequence found at tokens 1-3)

**Example — Should NOT MATCH:**
- Cell: `["system-view", "set", "cpu", "threshold", "4"]`
- PNG: `HW-Core-BKK-01 system-view display current-configuration quit.png`
- Result: ❌ No match (cell tokens don't appear contiguously)

### 4. Deduplication (New)

- Track inserted nodes per cell using a `set` keyed by `(table_index, row_index, cell_index, node)`.
- If a node has already received an image in the current cell, skip subsequent attempts.
- This guarantees exactly **1 image per node per cell**, even if multiple command sets in the same cell could theoretically match the same PNG.

### 5. Insert Logic (Modified)

- Stop searching for `<NodeName>` paragraphs after the first match is found and inserted.
- If no PNG match is found for a node, log a warning showing the commands that were searched.

## Data Flow

```
for each table:
  for each row:
    for each cell:
      if not permitted (PERMIT_FALSE/TRUE keywords):
        continue

      commands, nodes = parse_paragraphs(cell.paragraphs)
      expanded = expand_abbreviations(commands)

      inserted_nodes = set()  # deduplicate per cell

      for node in nodes:
        if node in inserted_nodes:
          continue

        match = find_best_match(node, expanded, png_files)
        if match:
          insert_image_at_node_paragraph(cell, node, match)
          inserted_nodes.add(node)
        else:
          log_warning(node, expanded)
```

## Error Handling

- **No PNG match**: Log a warning with the node name and expanded commands so the user knows which cell failed to match.
- **Node without commands**: Skip — if a cell has `<NodeName>` but no preceding commands, there's nothing to match.
- **Empty cell**: Skip entirely.

## Testing

Test with:
1. `example.txt` (single + nested commands with multiple nodes)
2. Real logs where cells contain abbreviated commands (`sys`, `dis th`, `q`)
3. Edge case: cell ends with empty prompt `[HUAWEI]` (no command)
4. Verify `system-view set cpu threshold 4` does **not** match `system-view display current-configuration`

## Open Questions

- Should we add more abbreviations beyond the 4 listed above? (e.g., `int` → `interface`, `sh` → `shutdown`)
- Should we support partial cell-to-PNG matching where the cell contains *more* commands than the PNG? (Current design: no, must be exact subsequence)

## Approved By

- Achakach (2026-04-23)
