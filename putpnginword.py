import re
import os
import glob
from docx import Document
from docx.shared import Inches


# --- Configuration ---
DOCX_INPUT = r"testthisplease.docx"
PNG_PATH = r"screenshots\*.png"
DOCX_OUTPUT = "testthisplease_RESULT_v5.docx"


# --- Section Filtering ---
# Empty list [] = process ALL tables (default, backward-compatible)
# List of titles = process only tables under matching heading titles and deeper
# Examples:
#   ['Device Management Acceptance'] → process this section and all sub-sections
#   ['login protocol SSH'] → process specific sub-section
TARGET_SECTIONS = []


# --- Regex patterns ---
# Match prompt+command: <Router>cmd or [~*Router]cmd or [~*Router-sub]cmd
PROMPT_LINE_RE = re.compile(r'^(<[A-Za-z][\w.\-]*>|\[~?\*?[A-Za-z][\w.\-/]*\])\s*(.+)$')

# Match node-only: <NodeName> with nothing after
NODE_LINE_RE = re.compile(r'^<([A-Za-z][\w.\-]*)>\s*$')


def extract_title(text):
    """Remove ID prefix like T01-0201-01 from heading text."""
    m = re.match(r'^[A-Z]\d+(?:[.-]\d+)*\s+(.*)$', text)
    if m:
        return m.group(1).strip()
    return text.strip()


def get_heading_level(para):
    """Extract level number from 'Heading N' style."""
    if para.style and para.style.name:
        name = para.style.name
        if name.startswith('Heading'):
            parts = name.split()
            if len(parts) == 2 and parts[1].isdigit():
                return int(parts[1])
    return None


def should_process_table(document, table_idx, target_titles):
    """Walk body elements in order. Activate on heading match, deactivate on same/higher level."""
    para_map = {para._p: para for para in document.paragraphs}
    seen_tables = 0
    active_level = None

    for child in document.element.body:
        if child.tag.endswith('tbl'):
            if seen_tables == table_idx:
                return active_level is not None
            seen_tables += 1
            continue

        if child.tag.endswith('p'):
            para = para_map.get(child)
            if not para:
                continue

            level = get_heading_level(para)
            if level is None:
                continue

            title = extract_title(para.text)

            if title in target_titles:
                active_level = level
            elif active_level is not None and level <= active_level:
                active_level = None

    return False


def list_sections(doc):
    """Print all heading sections found in the document, in order."""
    print("Sections found in document:")
    for para in doc.paragraphs:
        level = get_heading_level(para)
        if level is not None and para.text.strip():
            title = extract_title(para.text)
            print(f"  [Heading {level}] {title}")


def sanitize_filename(name: str, max_length: int = 200) -> str:
    result = re.sub(r'[\\/:*?"<>\n\r\t]', '_', name)
    result = result.replace('|', ' ')
    if not result.strip():
        return 'unnamed'
    return result[:max_length]


# --- Abbreviation Expansion ---

# Longest-first to avoid partial expansion (e.g. 'dis th' before 'dis')
_ABBREVIATIONS = [
    ('dis th', 'display this'),
    ('dis', 'display'),
    ('system', 'system-view'),
    ('sys', 'system-view'),
    ('comm', 'commit'),
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


def parse_paragraphs(paragraphs):
    """Extract command blocks and node names from cell paragraphs.

    Splits commands into separate blocks when a standalone user-view
    command (<Router>cmd) is encountered after a nested block has started.

    Returns list of (commands, nodes) tuples, one per logical block.
    """
    blocks = []
    current_commands = []
    nodes = []

    # Match prompt-only lines like [Router] or <Router> with no command
    PROMPT_ONLY_RE = re.compile(
        r'^(<[A-Za-z][\w.\-]*>|\[~?\*?[A-Za-z][\w.\-/]*\])\s*$'
    )

    for para in paragraphs:
        # Split paragraph text by newlines to handle Word table cells
        # where multiple lines are in a single paragraph
        for line in para.text.split('\n'):
            text = line.strip()
            if not text:
                continue

            # Check if this line is a node-only: <NodeName> with no command
            m = NODE_LINE_RE.match(text)
            if m:
                nodes.append(m.group(1))
                continue

            # Skip prompt-only lines (no command after prompt)
            if PROMPT_ONLY_RE.match(text):
                continue

            # Check if this line is a prompt+command
            m = PROMPT_LINE_RE.match(text)
            if m:
                cmd = m.group(2).strip()
                prompt = m.group(1)
                if not cmd:
                    continue

                # Detect standalone user-view command: <Router>cmd (depth 0)
                # If we already have commands in current block, this starts a new block
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


def parse_paragraphs_detailed(paragraphs):
    """Extract command blocks and node names from cell paragraphs.

    Same logic as parse_paragraphs(), but returns paragraph indices for each node.

    Returns list of (commands, [(node, para_idx), ...]) tuples.
    """
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


def _merge_empty_blocks(blocks):
    """Merge empty standalone blocks into the next block with nodes.
    
    If a block has commands but NO nodes, prepend its commands to the NEXT
    block that has nodes. Blocks that already have nodes are untouched.
    """
    if not blocks:
        return blocks

    merged = []
    pending_commands = []

    for bi, (commands, nodes) in enumerate(blocks):
        if not commands:
            continue

        if nodes:
            if pending_commands:
                merged_commands = pending_commands + commands
                merged.append((merged_commands, nodes))
                pending_commands = []
            else:
                merged.append((commands, nodes))
        else:
            pending_commands.extend(commands)

    return merged


def match_cell_blocks(paragraphs, png_files):
    """Match PNGs to command blocks for a single cell (Option B + empty block merge).

    Empty standalone blocks (no nodes) are merged into the next block with nodes.
    For merged blocks, each node tries each command individually until finding
    a non-error match.
    Returns list of dicts: {
        'node': str,
        'block_idx': int,
        'para_idx': int,
        'commands': list[str],
        'match_path': str | None,
        'action': 'inserted' | 'skipped_error' | 'no_match',
    }
    """
    blocks = parse_paragraphs_detailed(paragraphs)
    
    # Check if any merge happened
    original_blocks = blocks[:]
    blocks = _merge_empty_blocks(blocks)
    was_merged = len(blocks) < len(original_blocks)
    
    results = []

    for block_idx, (commands, block_nodes) in enumerate(blocks):
        if not commands or not block_nodes:
            continue

        expanded_commands = expand_abbreviations(commands)

        for node, para_idx in block_nodes:
            png_match = None
            best_commands = None
            
            if was_merged:
                # For merged blocks, try each command individually
                for i in range(len(expanded_commands)):
                    single_cmd = expanded_commands[i]
                    match = find_best_match(node, [single_cmd], png_files)
                    if not match:
                        continue
                    
                    has_error = '[error]' in os.path.basename(match).lower()
                    if not has_error:
                        png_match = match
                        best_commands = [single_cmd]
                        break
                    elif png_match is None:
                        # Remember first error match as fallback
                        png_match = match
                        best_commands = [single_cmd]
            else:
                # Normal block matching (full command sequence)
                png_match = find_best_match(node, expanded_commands, png_files)
                best_commands = expanded_commands

            if not png_match:
                results.append({
                    'node': node,
                    'block_idx': block_idx,
                    'para_idx': para_idx,
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
                    'para_idx': para_idx,
                    'commands': best_commands or expanded_commands,
                    'match_path': png_match,
                    'action': 'skipped_error',
                })
            else:
                results.append({
                    'node': node,
                    'block_idx': block_idx,
                    'para_idx': para_idx,
                    'commands': best_commands or expanded_commands,
                    'match_path': png_match,
                    'action': 'inserted',
                })

    return results


def find_best_match(device: str, commands: list[str], png_files: list[str]) -> str | None:
    """Find the PNG whose filename matches the exact command sequence.

    The device name must match exactly (case-insensitive).
    Trailing 'quit' tokens are stripped from both cell commands and PNG filename
    before comparison, so cells with or without quit match correctly.
    The remaining command sequence must match exactly (same tokens, same order).
    """
    if not commands:
        return None

    # Build search tokens from device + commands
    search_tokens = sanitize_filename(device).lower().split()
    for cmd in commands:
        search_tokens.extend(sanitize_filename(cmd).lower().split())

    # Strip trailing 'quit' from search tokens (cell side)
    while len(search_tokens) > 1 and search_tokens[-1] == 'quit':
        search_tokens.pop()

    cmd_tokens = search_tokens[1:]  # Skip device name
    if not cmd_tokens:
        # Device-only match
        for png_path in png_files:
            png_name = os.path.basename(png_path).replace('.png', '').lower()
            png_tokens = png_name.split()
            if png_tokens and png_tokens[0] == search_tokens[0]:
                return png_path
        return None

    best_match = None
    current_best_score = None

    for png_path in png_files:
        png_name = os.path.basename(png_path).replace('.png', '').lower()
        png_tokens = png_name.split()

        # Device name must match exactly as first token
        if not png_tokens or png_tokens[0] != search_tokens[0]:
            continue

        # Strip trailing 'quit' from PNG tokens (PNG side)
        png_cmd_tokens = png_tokens[1:]
        while png_cmd_tokens and png_cmd_tokens[-1] in ('quit', '[error]'):
            png_cmd_tokens.pop()

        # Exact match required
        if png_cmd_tokens == cmd_tokens:
            # Scoring: prefer non-error over error, then prefer shorter filenames
            is_error = '[error]' in png_name
            score = (
                0 if not is_error else 1,   # Non-error wins
                len(png_tokens)              # Then shorter wins
            )
            if best_match is None or score < current_best_score:
                best_match = png_path
                current_best_score = score

    return best_match


# --- Main ---
if __name__ == "__main__":
    document = Document(DOCX_INPUT)
    png_files = sorted(glob.glob(PNG_PATH))

    print(f"Loaded: {DOCX_INPUT}")
    print(f"Found {len(png_files)} PNG files in {PNG_PATH}")

    # Permit logic — controls which test cases get images
    # (customizable per document)
    PERMIT_FALSE_KEYWORDS = (
        'Reboot device.',
        'To verify power module resetting on a switch',
        'Reinsert the power module into slot 1-',
        'To verify fan module resetting on a CE',
    )
    PERMIT_TRUE_KEYWORDS = (
        'T01-02',
        'Simulate alarms and view alarms on NMS',
        'T01-05',
    )

    for table_index, table in enumerate(document.tables):
        if TARGET_SECTIONS:
            if not should_process_table(document, table_index, TARGET_SECTIONS):
                continue

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

                # Option B: Block-scoped node matching
                match_results = match_cell_blocks(cell.paragraphs, png_files)

                if not match_results:
                    continue

                # Track inserted paragraphs to prevent double-insertion
                inserted_paragraphs = set()

                for result in match_results:
                    if result['action'] != 'inserted':
                        if result['action'] == 'skipped_error':
                            print(f"  Skipped (error): {result['node']} block {result['block_idx']}")
                        else:
                            print(f"  No match: {result['node']} block {result['block_idx']}")
                        continue

                    para_idx = result['para_idx']
                    if para_idx in inserted_paragraphs:
                        continue  # Safety: don't double-insert

                    paragraph = cell.paragraphs[para_idx]
                    match_path = result['match_path']
                    commands = result['commands']

                    paragraph.paragraph_format.first_line_indent = 0
                    paragraph.paragraph_format.left_indent = 0
                    run = paragraph.add_run()
                    run.add_break()
                    run.add_break()
                    run = paragraph.add_run()
                    run.add_picture(match_path, width=Inches(6.495))
                    print(f"  Inserted: {os.path.basename(match_path)}")
                    print(f"    Node: {result['node']}, Block: {result['block_idx']}")
                    print(f"    Command: {' '.join(commands)}")
                    inserted_paragraphs.add(para_idx)

    document.save(DOCX_OUTPUT)
    print(f"\nSaved: {DOCX_OUTPUT}")
