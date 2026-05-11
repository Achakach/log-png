# putpnginword.py Fix — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix false-positive PNG matching and duplicate image insertion in `putpnginword.py` by replacing prefix matching with contiguous subsequence matching and adding deduplication.

**Architecture:** Replace `find_best_match()` prefix logic with exact contiguous subsequence matching. Add `expand_abbreviations()` for CLI abbreviations. Add per-cell deduplication to guarantee 1 image per node.

**Tech Stack:** Python 3.10+, python-docx, regex

---

## File Structure

| File | Action | Purpose |
|------|--------|---------|
| `putpnginword.py` | Modify | Main script: parsing, matching, insertion |
| `tests/test_putpnginword.py` | Create | Unit tests for parsing, matching, dedup |

---

### Task 1: Skip Empty Prompts in `parse_paragraphs()`

**Files:**
- Modify: `putpnginword.py:30-54`

- [ ] **Step 1: Modify `parse_paragraphs()` to skip prompt-only lines**

In the loop that processes paragraphs, after extracting `text`, check if it matches a prompt-only pattern and skip it.

```python
def parse_paragraphs(paragraphs):
    """Extract commands and node names from cell paragraphs.

    Returns (commands, nodes) where:
      commands: list of command strings from prompt lines
      nodes: list of device names from <NodeName> lines
    """
    commands = []
    nodes = []
    # Match prompt-only lines like [Router] or <Router> with no command
    PROMPT_ONLY_RE = re.compile(
        r'^(<[A-Za-z][\w.\-]*>|\[~?\*?[A-Za-z][\w.\-/]*\])\s*$'
    )
    for para in paragraphs:
        text = para.text.strip()
        if not text:
            continue
        # Skip prompt-only lines (no command after prompt)
        if PROMPT_ONLY_RE.match(text):
            continue
        # Check if this line is a node-only: <NodeName> with no command
        m = NODE_LINE_RE.match(text)
        if m:
            nodes.append(m.group(1))
            continue
        # Check if this line is a prompt+command
        m = PROMPT_LINE_RE.match(text)
        if m:
            cmd = m.group(2).strip()
            if cmd:
                commands.append(cmd)
    return commands, nodes
```

- [ ] **Step 2: Commit**

```bash
git add putpnginword.py
git commit -m "$(cat <<'EOF'
fix(putpnginword): skip empty prompt lines during parse

Prevents empty prompts like [HUAWEI] from being treated as commands.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

### Task 2: Add `expand_abbreviations()` Function

**Files:**
- Modify: `putpnginword.py` (add before `parse_paragraphs`)

- [ ] **Step 1: Add the abbreviation expansion function**

Insert this function before `parse_paragraphs`:

```python
# --- Abbreviation Expansion ---

# Longest-first to avoid partial expansion (e.g. 'dis th' before 'dis')
_ABBREVIATIONS = [
    ('dis th', 'display this'),
    ('dis', 'display'),
    ('system', 'system-view'),
    ('q', 'quit'),
]


def expand_abbreviations(commands: list[str]) -> list[str]:
    """Expand Huawei CLI abbreviations in commands.

    Uses longest-match-first to avoid partial expansion.
    Example: 'dis th' -> 'display this', not 'display th'.
    """
    result = []
    for cmd in commands:
        expanded = cmd
        for abbrev, full in _ABBREVIATIONS:
            # Match as whole words (or start of string) to avoid mid-word replacement
            pattern = re.compile(r'^(\s*)' + re.escape(abbrev) + r'(\s|$)')
            expanded = pattern.sub(r'\1' + full + r'\2', expanded)
        result.append(expanded)
    return result
```

- [ ] **Step 2: Commit**

```bash
git add putpnginword.py
git commit -m "$(cat <<'EOF'
feat(putpnginword): add abbreviation expansion for CLI commands

Supports: dis th->display this, dis->display, system->system-view, q->quit.
Uses longest-match-first to avoid partial expansion.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

### Task 3: Rewrite `find_best_match()` with Contiguous Subsequence

**Files:**
- Modify: `putpnginword.py:57-94`

- [ ] **Step 1: Replace `find_best_match()` with contiguous subsequence logic**

Replace the entire `find_best_match()` function:

```python
def find_best_match(device: str, commands: list[str], png_files: list[str]) -> str | None:
    """Find the PNG whose filename contains the exact command sequence as a contiguous subsequence.

    The device name must match exactly (case-insensitive).
    All commands must appear consecutively and in order within the PNG filename tokens.
    Missing trailing tokens (e.g. quit) in the cell are allowed.
    """
    if not commands:
        return None

    search_tokens = sanitize_filename(device).lower().split()
    for cmd in commands:
        search_tokens.extend(sanitize_filename(cmd).lower().split())

    best_match = None

    for png_path in png_files:
        png_name = os.path.basename(png_path).replace('.png', '').lower()
        png_tokens = png_name.split()

        # Device name must match exactly as first token
        if not png_tokens or png_tokens[0] != search_tokens[0]:
            continue

        # Find contiguous subsequence of command tokens within PNG tokens
        # search_tokens[1:] = command tokens only (skip device)
        cmd_tokens = search_tokens[1:]
        if not cmd_tokens:
            # Device-only match (rare, but handle it)
            best_match = png_path
            break

        found = False
        for i in range(1, len(png_tokens) - len(cmd_tokens) + 1):
            if png_tokens[i:i + len(cmd_tokens)] == cmd_tokens:
                found = True
                break

        if found:
            # Prefer shorter filenames (fewer extra commands) on tie
            if best_match is None or len(png_tokens) < len(os.path.basename(best_match).replace('.png', '').lower().split()):
                best_match = png_path

    return best_match
```

- [ ] **Step 2: Commit**

```bash
git add putpnginword.py
git commit -m "$(cat <<'EOF'
fix(putpnginword): replace prefix match with contiguous subsequence match

Commands in a cell must now appear consecutively in the PNG filename.
Prevents false positives like system-view matching display current-configuration.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

### Task 4: Add Deduplication in Main Loop

**Files:**
- Modify: `putpnginword.py:118-162`

- [ ] **Step 1: Add `inserted_nodes` set and deduplication logic**

In the main loop, before iterating nodes, add a set. Inside the node loop, check dedup before inserting. Also break after first paragraph match.

```python
for table_index, table in enumerate(document.tables):
    print(f"\n--- Table {table_index + 1} ---")

    for row in table.rows:
        for cell in row.cells:
            cell_text = cell.text

            # Determine permit
            permit = True
            for kw in PERMIT_FALSE_KEYWORDS:
                if kw in cell_text:
                    permit = False
            for kw in PERMIT_TRUE_KEYWORDS:
                if kw in cell_text:
                    permit = True

            if not permit:
                continue

            # Parse cell paragraphs
            commands, nodes = parse_paragraphs(cell.paragraphs)

            if not commands or not nodes:
                continue

            # Expand abbreviations before matching
            expanded_commands = expand_abbreviations(commands)

            # Track inserted nodes per cell to prevent duplicates
            inserted_nodes = set()

            # For each node, find matching PNG and insert
            for node in nodes:
                if node in inserted_nodes:
                    continue

                png_match = find_best_match(node, expanded_commands, png_files)
                if not png_match:
                    print(f"  No match: {node} + {' '.join(expanded_commands)}")
                    continue

                # Insert image at the first <NodeName> paragraph found
                inserted = False
                for paragraph in cell.paragraphs:
                    if f'<{node}>' in paragraph.text:
                        paragraph.paragraph_format.first_line_indent = 0
                        paragraph.paragraph_format.left_indent = 0
                        run = paragraph.add_run()
                        run.add_break()
                        run.add_break()
                        run = paragraph.add_run()
                        run.add_picture(png_match, width=Inches(6.495))
                        print(f"  Inserted: {os.path.basename(png_match)}")
                        inserted_nodes.add(node)
                        inserted = True
                        break  # Stop after first match per node

                if not inserted:
                    print(f"  Warning: found match but no <{node}> paragraph in cell")
```

- [ ] **Step 2: Commit**

```bash
git add putpnginword.py
git commit -m "$(cat <<'EOF'
fix(putpnginword): deduplicate images — one per node per cell

Adds inserted_nodes set per cell. Breaks after first paragraph match.
Prevents multiple images being inserted for the same node.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

### Task 5: Write Unit Tests

**Files:**
- Create: `tests/test_putpnginword.py`

- [ ] **Step 1: Create test file with tests for parsing, expansion, matching**

```python
import pytest
import sys
from pathlib import Path

# Add parent directory to path so we can import putpnginword
sys.path.insert(0, str(Path(__file__).parent.parent))

from putpnginword import (
    parse_paragraphs,
    expand_abbreviations,
    find_best_match,
    sanitize_filename,
)


# --- parse_paragraphs tests ---

class MockParagraph:
    def __init__(self, text):
        self.text = text


def test_parse_empty_prompt_skipped():
    paragraphs = [
        MockParagraph('<HUAWEI>sys'),
        MockParagraph('[HUAWEI]'),
        MockParagraph('<NODE1>'),
    ]
    commands, nodes = parse_paragraphs(paragraphs)
    assert commands == ['sys']
    assert nodes == ['NODE1']


def test_parse_commands_and_nodes():
    paragraphs = [
        MockParagraph('<HUAWEI>system-view'),
        MockParagraph('[HUAWEI]interface GE0/0/1'),
        MockParagraph('[HUAWEI-GE0/0/1]display this'),
        MockParagraph('[HUAWEI-GE0/0/1]quit'),
        MockParagraph('[HUAWEI]quit'),
        MockParagraph('<TUC-NODE1>'),
        MockParagraph('<TUC-NODE2>'),
    ]
    commands, nodes = parse_paragraphs(paragraphs)
    assert commands == [
        'system-view',
        'interface GE0/0/1',
        'display this',
        'quit',
        'quit',
    ]
    assert nodes == ['TUC-NODE1', 'TUC-NODE2']


# --- expand_abbreviations tests ---

def test_expand_system():
    assert expand_abbreviations(['system']) == ['system-view']


def test_expand_dis():
    assert expand_abbreviations(['dis']) == ['display']


def test_expand_dis_th():
    assert expand_abbreviations(['dis th']) == ['display this']


def test_expand_q():
    assert expand_abbreviations(['q']) == ['quit']


def test_expand_multiple():
    assert expand_abbreviations(['system', 'dis', 'q']) == [
        'system-view',
        'display',
        'quit',
    ]


def test_expand_no_match():
    assert expand_abbreviations(['display device']) == ['display device']


# --- find_best_match tests ---

def test_find_best_match_exact_subsequence():
    png_files = [
        'HW-Core-BKK-01 system-view cmd2 cmd3 quit quit.png',
        'HW-Core-BKK-01 system-view set cpu threshold 4.png',
    ]
    result = find_best_match('HW-Core-BKK-01', ['system-view', 'cmd2', 'cmd3'], png_files)
    assert result is not None
    assert 'cmd2 cmd3' in result


def test_find_best_match_no_false_positive():
    png_files = [
        'HW-Core-BKK-01 system-view display current-configuration quit.png',
    ]
    result = find_best_match('HW-Core-BKK-01', ['system-view', 'set', 'cpu'], png_files)
    assert result is None


def test_find_best_match_missing_quit():
    """Cell omits quit commands — should still match."""
    png_files = [
        'HW-Core-BKK-01 system-view cmd2 cmd3 quit quit.png',
    ]
    result = find_best_match('HW-Core-BKK-01', ['system-view', 'cmd2', 'cmd3'], png_files)
    assert result is not None


def test_find_best_match_wrong_device():
    png_files = [
        'HW-Core-BKK-01 display device.png',
    ]
    result = find_best_match('OTHER-DEVICE', ['display', 'device'], png_files)
    assert result is None


# --- sanitize_filename tests ---

def test_sanitize_basic():
    assert sanitize_filename('hello world') == 'hello world'


def test_sanitize_pipe():
    assert sanitize_filename('a|b') == 'a b'


def test_sanitize_slash():
    assert sanitize_filename('GE0/0/1') == 'GE0_0_1'
```

- [ ] **Step 2: Run tests**

Run:
```bash
pytest tests/test_putpnginword.py -v
```

Expected: All 11 tests PASS.

- [ ] **Step 3: Commit**

```bash
git add tests/test_putpnginword.py
git commit -m "$(cat <<'EOF'
test(putpnginword): add unit tests for parsing, expansion, matching

Covers empty prompt skipping, abbreviation expansion, contiguous subsequence matching,
and deduplication behavior.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

## Self-Review

**Spec coverage:**
- ✅ Requirement 1 (one image per node): Task 4 — `inserted_nodes` set + break after first match
- ✅ Requirement 2 (accurate matching): Task 3 — contiguous subsequence replaces prefix
- ✅ Requirement 3 (abbreviation expansion): Task 2 — `expand_abbreviations()`
- ✅ Requirement 4 (handle empty prompts): Task 1 — skip prompt-only lines
- ✅ Requirement 5 (preserve permit logic): Task 4 — permit logic unchanged

**Placeholder scan:** No TBDs, TODOs, or vague steps. All code is complete.

**Type consistency:**
- `find_best_match()` signature: `(device: str, commands: list[str], png_files: list[str]) -> str | None` — consistent
- `expand_abbreviations()`: `(commands: list[str]) -> list[str]` — consistent
- `parse_paragraphs()`: `(paragraphs) -> tuple[list[str], list[str]]` — consistent

No issues found. Ready for execution.
