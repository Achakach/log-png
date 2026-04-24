# Section Filtering for putpnginword.py

## Problem

`putpnginword.py` currently processes **all tables** in the Word document. In practice, test documents contain hierarchical sections (e.g., `T01` → `T01-01` → `T01-0101`) and users often want to insert PNGs **only into specific sections** rather than the entire document.

Processing all tables causes:
- Unwanted image insertions in header/description tables
- Slower execution on large documents
- Difficulty controlling which test cases get images

## Solution

Add a `TARGET_SECTIONS` configuration that filters which tables to process based on the nearest preceding heading in the document hierarchy.

---

## Architecture

### 1. Config

Add a new constant at the top of `putpnginword.py`:

```python
# --- Section Filtering ---
# Empty list [] = process ALL tables (default, backward-compatible)
# List of prefixes = process only tables whose nearest heading starts with any prefix
# Examples:
#   ['T01']        → T01 and all sub-sections (T01-01, T01-0101, T01-02, ...)
#   ['T01-01']     → T01-01 and deeper (T01-0101, T01-0102, ...)
#   ['T01-0101']   → T01-0101 only (no deeper levels)
#   ['T01-01', 'T02-02'] → multiple independent sections
TARGET_SECTIONS = []
```

### 2. Section Detection

Add a helper function `get_table_section(document, table)` that:
- Scans `document.paragraphs` in order
- For each paragraph before the table, records the heading text
- When the table is encountered, returns the **most recent heading text**
- Returns `None` if no heading is found before the table

Heading detection: match paragraphs where `style.name.startswith('Heading')` and text is non-empty.

### 3. Match Logic

In the main loop, before processing each table:

```python
section = get_table_section(document, table)

if TARGET_SECTIONS:
    if not section or not any(section.startswith(target) for target in TARGET_SECTIONS):
        continue  # skip this table
```

**Prefix match behavior:**
- `T01-01` matches `T01-0101`, `T01-0102`, `T01-0199`
- `T01-01` does **not** match `T01-010` (no separator), but this naming convention is not used in practice
- `T01` matches everything under `T01`

### 4. Section Discovery Helper

Add a standalone function `list_sections(doc)` that prints all section headings found in the document, in order, to help users decide what to put in `TARGET_SECTIONS`.

Usage:
```bash
python -c "from putpnginword import list_sections; from docx import Document; list_sections(Document('test_document_v3.docx'))"
```

---

## Files to Modify

| File | Action |
|------|--------|
| `putpnginword.py` | Add `TARGET_SECTIONS`, `get_table_section()`, `list_sections()`, update main loop |

## Backward Compatibility

- Default `TARGET_SECTIONS = []` → behavior identical to current code
- Existing users do not need to change anything
- `PERMIT_FALSE_KEYWORDS` / `PERMIT_TRUE_KEYWORDS` remain independent and unchanged

## Verification

1. Set `TARGET_SECTIONS = ['T01-01']`
2. Run on `document structure example.docx`
3. Verify only tables under `T01-01` (and deeper) get images
4. Tables under `T01-02` or other top-level sections are skipped
