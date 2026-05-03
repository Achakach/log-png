# Option B: Block-Scoped Node Matching Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Modify `putpnginword.py` to match PNG images against command blocks on a per-block basis (not cell-wide), allowing the same node name to receive multiple images when it appears after different command blocks in the same cell.

**Architecture:** Change the main loop from cell-wide node deduplication (`all_nodes` + `inserted_nodes` set) to per-block processing. Each block maintains its own node list; nodes are "owned" by the block they immediately follow. The matching logic (`find_best_match`) and error preference remain unchanged — only the orchestration layer changes.

**Tech Stack:** Python 3.10+, python-docx, pytest

---

## File Structure

| File | Role | Action |
|------|------|--------|
| `putpnginword.py` | Main script — matching & insertion logic | **Modify** main loop (lines ~297–365) |
| `tests/test_putpnginword.py` | Existing unit tests for core functions | **Add** new test class for block-scoped matching |
| `tests/test_multi_block_preference.py` | Existing multi-block error preference tests | **Update** to reflect new block-scored behavior |
| `tests/test_option_b_integration.py` | **New file** — integration tests for Option B | **Create** |
| `document structure example.docx` | Reference document showing desired behavior | **Read-only** (used for verification) |

---

## Problem Statement (Current vs Desired)

### Current Behavior (Cell-Wide)
```
Cell content:
  <huawei>cmd 7
  <device1>
  <device2>
  <huawei>cmd 8
  <device1>
  <device2>

parse_paragraphs() output:
  blocks = [
    (['cmd', '7'], ['device1', 'device2']),
    (['cmd', '8'], ['device1', 'device2'])
  ]

Current main loop:
  all_nodes = {'device1', 'device2'}  ← cell-wide dedup
  for node in all_nodes:              ← each node processed ONCE
    ...insert image...
    inserted_nodes.add(node)         ← prevents duplicates

Result: 2 images (device1×1, device2×1) ❌
```

### Desired Behavior (Block-Scoped — Option B)
```
Same cell content → same blocks output

Desired main loop:
  for block_idx, (commands, block_nodes) in enumerate(blocks):
    for node in block_nodes:          ← node processed PER BLOCK
      ...find match for THIS block's commands...
      ...insert at THIS block's node paragraph...
      # NO cell-wide dedup — same node can appear in multiple blocks

Result: 4 images (device1×2, device2×2) ✅
```

**Key insight:** `parse_paragraphs()` already splits into multiple blocks correctly. The bug is in the **main loop** that operates on `all_nodes` instead of per-block nodes.

---

## Task 1: Write Failing Test for Block-Scoped Matching

**Files:**
- Create: `tests/test_option_b_integration.py`

**Context:** This test captures the exact Table 3 case from `document structure example.docx`.

- [ ] **Step 1.1: Write the failing test**

```python
"""Integration tests for Option B: block-scoped node matching.

A node that appears after multiple command blocks should get
an image for EACH block (not just one per cell).
"""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from putpnginword import parse_paragraphs, find_best_match, expand_abbreviations


class MockParagraph:
    def __init__(self, text):
        self.text = text


def simulate_option_b_matching(paragraphs, png_files):
    """Simulate the NEW block-scoped matching logic.

    Returns list of (node, block_idx, action, match_path) tuples.
    """
    blocks = parse_paragraphs(paragraphs)
    results = []

    for block_idx, (commands, block_nodes) in enumerate(blocks):
        if not commands or not block_nodes:
            continue

        expanded_commands = expand_abbreviations(commands)

        for node in block_nodes:
            png_match = find_best_match(node, expanded_commands, png_files)
            if not png_match:
                results.append((node, block_idx, 'no_match', None))
                continue

            has_error = '[error]' in png_match.lower()
            if has_error:
                results.append((node, block_idx, 'skipped_error', png_match))
            else:
                results.append((node, block_idx, 'inserted', png_match))

    return results


# --- Core Option B Tests ---

def test_same_node_multiple_blocks_gets_multiple_images():
    """Table 3 case: device1 appears after cmd 7 and cmd 8.
    Should get 2 images (one per block)."""
    paragraphs = [
        MockParagraph('<huawei>cmd 7'),
        MockParagraph('<device1>'),
        MockParagraph('<device2>'),
        MockParagraph('<huawei>cmd 8'),
        MockParagraph('<device1>'),
        MockParagraph('<device2>'),
    ]
    png_files = [
        'device1 cmd 7.png',
        'device1 cmd 8.png',
        'device2 cmd 7.png',
        'device2 cmd 8.png',
    ]
    results = simulate_option_b_matching(paragraphs, png_files)

    # Count images per node
    device1_images = [r for r in results if r[0] == 'device1' and r[2] == 'inserted']
    device2_images = [r for r in results if r[0] == 'device2' and r[2] == 'inserted']

    assert len(device1_images) == 2, f"Expected 2 images for device1, got {len(device1_images)}: {device1_images}"
    assert len(device2_images) == 2, f"Expected 2 images for device2, got {len(device2_images)}: {device2_images}"

    # Verify block assignments
    device1_blocks = sorted([r[1] for r in device1_images])
    assert device1_blocks == [0, 1]


def test_block_isolated_matching():
    """Block 1 commands should NOT match block 2's PNGs."""
    paragraphs = [
        MockParagraph('<huawei>display device'),
        MockParagraph('<device1>'),
        MockParagraph('<huawei>display clock'),
        MockParagraph('<device1>'),
    ]
    png_files = [
        'device1 display device.png',
        'device1 display clock.png',
    ]
    results = simulate_option_b_matching(paragraphs, png_files)

    inserted = [r for r in results if r[2] == 'inserted']
    assert len(inserted) == 2

    # Block 0 should match display device
    block0_match = [r for r in inserted if r[1] == 0][0][3]
    assert 'display device' in block0_match

    # Block 1 should match display clock
    block1_match = [r for r in inserted if r[1] == 1][0][3]
    assert 'display clock' in block1_match


def test_error_per_block_independent():
    """One block has error, another doesn't — should insert for non-error block."""
    paragraphs = [
        MockParagraph('<huawei>display cpu-usage'),
        MockParagraph('<device1>'),
        MockParagraph('<huawei>display cpu'),
        MockParagraph('<device1>'),
    ]
    png_files = [
        'device1 display cpu-usage [error].png',
        'device1 display cpu.png',
    ]
    results = simulate_option_b_matching(paragraphs, png_files)

    inserted = [r for r in results if r[2] == 'inserted']
    skipped = [r for r in results if r[2] == 'skipped_error']

    # Block 0 (display cpu-usage) is error → skipped
    assert len(skipped) == 1
    assert skipped[0][1] == 0

    # Block 1 (display cpu) is OK → inserted
    assert len(inserted) == 1
    assert inserted[0][1] == 1
```

- [ ] **Step 1.2: Run test to verify it fails**

Run: `pytest tests/test_option_b_integration.py -v`

Expected: **FAIL** — `simulate_option_b_matching` uses new logic, but the real `putpnginword.py` main loop still uses old cell-wide logic. If we test against real `putpnginword.py` behavior, it will fail.

Actually — wait. This test file defines its own `simulate_option_b_matching`. It will PASS because it's testing the *desired* logic, not the current code. We need a test that calls the REAL main loop.

Let me revise: the test should call a refactored function from `putpnginword.py` directly.

REVISED Step 1.1:

```python
# We will create a new function in putpnginword.py: process_cell_blocks()
# The test will import it and test it directly.
# For now, we write the test assuming that function exists.

from putpnginword import process_cell_blocks

def test_same_node_multiple_blocks():
    paragraphs = [...]
    png_files = [...]
    results = process_cell_blocks(paragraphs, png_files)
    ...
```

Since `process_cell_blocks` doesn't exist yet, this test will fail with ImportError — which is the correct first step for TDD.

---

## Task 2: Extract Cell Processing into Testable Function

**Files:**
- Modify: `putpnginword.py:297-365` (main loop cell processing)
- Create: `putpnginword.py:~280` (new function before main loop)

- [ ] **Step 2.1: Create `process_cell_blocks()` function**

Extract the per-cell matching+insertion logic into a pure function that returns results without side effects (for testing). The real main loop will call this and apply the actual DOCX insertions.

```python
def match_cell_blocks(paragraphs, png_files):
    """Match PNGs to command blocks for a single cell.

    Returns list of dicts: {
        'node': str,
        'block_idx': int,
        'commands': list[str],
        'match_path': str | None,
        'action': 'inserted' | 'skipped_error' | 'no_match',
    }

    This is Option B: each block's nodes are matched independently.
    """
    blocks = parse_paragraphs(paragraphs)
    results = []

    for block_idx, (commands, block_nodes) in enumerate(blocks):
        if not commands or not block_nodes:
            continue

        expanded_commands = expand_abbreviations(commands)

        for node in block_nodes:
            png_match = find_best_match(node, expanded_commands, png_files)
            if not png_match:
                results.append({
                    'node': node,
                    'block_idx': block_idx,
                    'commands': expanded_commands,
                    'match_path': None,
                    'action': 'no_match',
                })
                continue

            has_error = '[error]' in os.path.basename(png_match).lower()
            if has_error:
                results.append({
                    'node': node,
                    'block_idx': block_idx,
                    'commands': expanded_commands,
                    'match_path': png_match,
                    'action': 'skipped_error',
                })
            else:
                results.append({
                    'node': node,
                    'block_idx': block_idx,
                    'commands': expanded_commands,
                    'match_path': png_match,
                    'action': 'inserted',
                })

    return results
```

- [ ] **Step 2.2: Update test to import and test `match_cell_blocks()`**

```python
from putpnginword import match_cell_blocks

# Then all tests use match_cell_blocks directly
```

- [ ] **Step 2.3: Run tests — expect PASS**

Run: `pytest tests/test_option_b_integration.py -v`

Expected: **PASS** — the new function implements Option B correctly.

---

## Task 3: Rewrite Main Loop to Use `match_cell_blocks()`

**Files:**
- Modify: `putpnginword.py:274-365` (main loop)

- [ ] **Step 3.1: Replace cell processing logic in main loop**

Current code (lines ~297–365):
```python
                # Parse cell paragraphs into command blocks
                blocks = parse_paragraphs(cell.paragraphs)

                # Collect all nodes from all blocks (cell-wide)
                all_nodes = set()
                for _, block_nodes in blocks:
                    all_nodes.update(block_nodes)

                if not blocks or not all_nodes:
                    continue

                # Track inserted nodes per cell to prevent duplicates
                inserted_nodes = set()

                # For each node, scan ALL blocks to find the best match...
                for node in all_nodes:
                    if node in inserted_nodes:
                        continue
                    # ... complex matching logic ...
                    inserted_nodes.add(node)
```

Replace with:
```python
                # Parse cell paragraphs into command blocks (Option B)
                match_results = match_cell_blocks(cell.paragraphs, png_files)

                if not match_results:
                    continue

                # Track which paragraphs already have images inserted
                # to prevent inserting multiple images at the same paragraph
                inserted_paragraphs = set()

                for result in match_results:
                    if result['action'] != 'inserted':
                        if result['action'] == 'skipped_error':
                            print(f"  Skipped (error): {result['node']} block {result['block_idx']}")
                        else:
                            print(f"  No match: {result['node']} block {result['block_idx']}")
                        continue

                    node = result['node']
                    match_path = result['match_path']
                    commands = result['commands']

                    # Find the correct paragraph for THIS block's node
                    # We need to insert at the paragraph that appears in the correct block
                    for para_idx, paragraph in enumerate(cell.paragraphs):
                        if para_idx in inserted_paragraphs:
                            continue
                        if f'<{node}>' in paragraph.text:
                            paragraph.paragraph_format.first_line_indent = 0
                            paragraph.paragraph_format.left_indent = 0
                            run = paragraph.add_run()
                            run.add_break()
                            run.add_break()
                            run = paragraph.add_run()
                            run.add_picture(match_path, width=Inches(6.495))
                            print(f"  Inserted: {os.path.basename(match_path)}")
                            print(f"    Node: {node}, Block: {result['block_idx']}")
                            print(f"    Command: {' '.join(commands)}")
                            inserted_paragraphs.add(para_idx)
                            break
```

**IMPORTANT:** The paragraph-finding logic needs improvement. Currently it scans all paragraphs and finds the first `<node>`. But with Option B, the same node appears multiple times — we need to insert at the paragraph that corresponds to the correct block.

- [ ] **Step 3.2: Improve paragraph-to-block mapping**

We need to know which paragraph contains which block's nodes. Modify `parse_paragraphs()` to return paragraph indices, OR add a helper that maps nodes to their paragraph index.

Revised approach: add `match_cell_blocks_with_paragraphs()` that returns `para_idx` along with match results.

```python
def match_cell_blocks_with_paragraphs(paragraphs, png_files):
    """Match PNGs and return paragraph indices for insertion.

    Returns list of dicts with added 'para_idx' key.
    """
    blocks_with_paras = parse_paragraphs_with_indices(paragraphs)
    # blocks_with_paras = [(commands, [(node, para_idx), ...]), ...]
    ...
```

Actually, simpler: modify `parse_paragraphs()` to also track which paragraph each node came from.

REVISED `parse_paragraphs()` return format:
```python
# OLD: blocks = [([commands], [nodes]), ...]
# NEW: blocks = [([commands], [(node, para_idx), ...]), ...]
```

This requires updating all existing tests that use `parse_paragraphs`. Let's be careful.

Alternative: keep `parse_paragraphs()` unchanged, create new function `parse_paragraphs_detailed()` that returns paragraph indices.

**Decision:** Create `parse_paragraphs_detailed()` to avoid breaking existing tests.

```python
def parse_paragraphs_detailed(paragraphs):
    """Like parse_paragraphs, but returns (node, para_idx) tuples for nodes."""
    blocks = []
    current_commands = []
    nodes = []  # [(node_name, para_idx), ...]
    PROMPT_ONLY_RE = re.compile(
        r'^(<[A-Za-z][\w.\-]*>|\[~?\*?[A-Za-z][\w.\-/]*\])\s*$'
    )

    for para_idx, para in enumerate(paragraphs):
        for line in para.text.split('\n'):
            text = line.strip()
            if not text:
                continue

            m = NODE_LINE_RE.match(text)
            if m:
                nodes.append((m.group(1), para_idx))
                continue

            if PROMPT_ONLY_RE.match(text):
                continue

            m = PROMPT_LINE_RE.match(text)
            if m:
                cmd = m.group(2).strip()
                prompt = m.group(1)
                if not cmd:
                    continue

                if (prompt.startswith('<') and
                        not prompt.startswith('<~') and
                        not prompt.startswith('<*') and
                        current_commands):
                    blocks.append((current_commands, nodes))
                    current_commands = []
                    nodes = []

                current_commands.append(cmd)

    if current_commands:
        blocks.append((current_commands, nodes))

    return blocks
```

Then `match_cell_blocks()` uses `parse_paragraphs_detailed()` and returns `para_idx`:

```python
def match_cell_blocks(paragraphs, png_files):
    blocks = parse_paragraphs_detailed(paragraphs)
    results = []

    for block_idx, (commands, block_nodes) in enumerate(blocks):
        if not commands or not block_nodes:
            continue

        expanded_commands = expand_abbreviations(commands)

        for node, para_idx in block_nodes:
            png_match = find_best_match(node, expanded_commands, png_files)
            # ... same as before ...
            results.append({
                'node': node,
                'block_idx': block_idx,
                'para_idx': para_idx,  # ← NEW
                # ...
            })

    return results
```

And the main loop becomes clean:

```python
                match_results = match_cell_blocks(cell.paragraphs, png_files)
                inserted_paragraphs = set()

                for result in match_results:
                    if result['action'] != 'inserted':
                        # ... log skipped ...
                        continue

                    para_idx = result['para_idx']
                    if para_idx in inserted_paragraphs:
                        continue  # Safety: don't double-insert

                    paragraph = cell.paragraphs[para_idx]
                    match_path = result['match_path']
                    # ... insert image ...
                    inserted_paragraphs.add(para_idx)
```

- [ ] **Step 3.3: Update tests for paragraph index correctness**

Add test to verify `para_idx` points to the correct paragraph:

```python
def test_paragraph_index_correct():
    paragraphs = [
        MockParagraph('<huawei>cmd 7'),
        MockParagraph('<device1>'),   # para_idx 1
        MockParagraph('<huawei>cmd 8'),
        MockParagraph('<device1>'),   # para_idx 3
    ]
    png_files = ['device1 cmd 7.png', 'device1 cmd 8.png']
    results = match_cell_blocks(paragraphs, png_files)

    # Find results for device1
    device1_results = [r for r in results if r['node'] == 'device1']
    assert len(device1_results) == 2

    para_indices = sorted([r['para_idx'] for r in device1_results])
    assert para_indices == [1, 3]
```

---

## Task 4: Update Existing Tests

**Files:**
- Modify: `tests/test_putpnginword.py` (update parse_paragraphs tests)
- Modify: `tests/test_multi_block_preference.py` (update simulate logic)

- [ ] **Step 4.1: Add tests for `parse_paragraphs_detailed()`**

```python
def test_parse_detailed_returns_para_indices():
    from putpnginword import parse_paragraphs_detailed
    paragraphs = [
        MockParagraph('<HUAWEI>system-view'),
        MockParagraph('<TUC-NODE1>'),
    ]
    blocks = parse_paragraphs_detailed(paragraphs)
    assert blocks == [(['system-view'], [('TUC-NODE1', 1)])]
```

- [ ] **Step 4.2: Update `test_multi_block_preference.py`**

The `simulate_cell_matching()` function in this file implements the OLD cell-wide logic. We need to update it to use the NEW `match_cell_blocks()` function (which is the real function now, not simulated).

Actually — once `match_cell_blocks()` exists, we can delete `simulate_cell_matching()` entirely and test `match_cell_blocks()` directly.

```python
from putpnginword import match_cell_blocks

def test_multi_block_first_error_second_ok():
    paragraphs = [...]
    png_files = [...]
    results = match_cell_blocks(paragraphs, png_files)
    # Assert on results format
```

- [ ] **Step 4.3: Run full test suite**

Run: `pytest tests/ -v`

Expected: **All pass** — no regressions.

---

## Task 5: Manual Verification on `document structure example.docx`

**Files:**
- Read-only: `document structure example.docx`
- Output: `document_structure_example_RESULT.docx`

- [ ] **Step 5.1: Configure `putpnginword.py` to process the reference document**

Temporarily update at top of `putpnginword.py`:
```python
DOCX_INPUT = r"document structure example.docx"
PNG_PATH = r"screenshots\*.png"
DOCX_OUTPUT = "document_structure_example_RESULT.docx"
TARGET_SECTIONS = []  # Process all
```

- [ ] **Step 5.2: Generate or use existing PNGs**

Ensure PNGs exist that match the commands in `document structure example.docx`. If not, generate them using `run.py` with appropriate log files.

- [ ] **Step 5.3: Run `putpnginword.py`**

```bash
python putpnginword.py
```

- [ ] **Step 5.4: Verify Table 3** — Check that cells with multiple blocks have multiple images inserted.

Expected result for Table 3 new case:
- 4 images total in the cell (2 blocks × 2 nodes each)
- `device1` appears twice with different command matches
- `device2` appears twice with different command matches

- [ ] **Step 5.5: Revert temporary config changes**

Change `DOCX_INPUT` back to `testthisplease.docx` (or whatever the production default is).

---

## Task 6: Documentation Update

**Files:**
- Modify: `README.md`
- Modify: `CLAUDE.md`

- [ ] **Step 6.1: Update `README.md` — matching behavior section**

Change:
```markdown
### วิธีการทำงาน

4. **จับคู่** ... 1 node = 1 รูป ต่อ cell (deduplication)
```

To:
```markdown
### วิธีการทำงาน

4. **จับคู่** ... Each command block matches independently. If the same node appears after multiple command blocks, it receives an image for each block.
```

- [ ] **Step 6.2: Update `CLAUDE.md`**

Update the "Work Completed" section to document Option B implementation.

---

## Self-Review Checklist

### Spec Coverage
- [ ] Multiple blocks per cell with same node → multiple images ✅ Task 1, 3
- [ ] Block isolation → block 1 doesn't match block 2's PNGs ✅ Task 1
- [ ] Error preference per block ✅ Task 1
- [ ] Paragraph index tracking ✅ Task 3
- [ ] No regressions in existing tests ✅ Task 4
- [ ] Manual verification on reference doc ✅ Task 5
- [ ] Documentation updated ✅ Task 6

### Placeholder Scan
- [ ] No "TBD", "TODO", "implement later"
- [ ] All code shown explicitly
- [ ] No "similar to Task N" shortcuts

### Type Consistency
- [ ] `parse_paragraphs_detailed()` returns `[(commands, [(node, para_idx)])]` — consistent throughout
- [ ] `match_cell_blocks()` returns dict with `node`, `block_idx`, `para_idx`, `commands`, `match_path`, `action` — consistent

---

## Execution Handoff

**Plan complete.** Two execution options:

**1. Subagent-Driven (recommended)** — I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** — Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach do you prefer?**
