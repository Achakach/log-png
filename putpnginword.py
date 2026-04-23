import re
import os
import glob
from docx import Document
from docx.shared import Inches


# --- Configuration ---
DOCX_INPUT = r"test_document_v3.docx"
PNG_PATH = r"screenshots\*.png"
DOCX_OUTPUT = "test_document_v3_with_png.docx"


# --- Regex patterns ---
# Match prompt+command: <Router>cmd or [~*Router]cmd or [~*Router-sub]cmd
PROMPT_LINE_RE = re.compile(r'^(<[A-Za-z][\w.\-]*>|\[~?\*?[A-Za-z][\w.\-/]*\])\s*(.+)$')

# Match node-only: <NodeName> with nothing after
NODE_LINE_RE = re.compile(r'^<([A-Za-z][\w.\-]*)>\s*$')


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
        text = para.text.strip()
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

    for png_path in png_files:
        png_name = os.path.basename(png_path).replace('.png', '').lower()
        png_tokens = png_name.split()

        # Device name must match exactly as first token
        if not png_tokens or png_tokens[0] != search_tokens[0]:
            continue

        # Strip trailing 'quit' from PNG tokens (PNG side)
        png_cmd_tokens = png_tokens[1:]
        while png_cmd_tokens and png_cmd_tokens[-1] == 'quit':
            png_cmd_tokens.pop()

        # Exact match required
        if png_cmd_tokens == cmd_tokens:
            # Prefer shorter filenames on tie (fewer extra commands)
            if best_match is None or len(png_tokens) < len(os.path.basename(best_match).replace('.png', '').lower().split()):
                best_match = png_path

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

                # Parse cell paragraphs into command blocks
                blocks = parse_paragraphs(cell.paragraphs)

                # Collect all nodes from all blocks for deduplication
                all_nodes = set()
                for _, block_nodes in blocks:
                    all_nodes.update(block_nodes)

                if not blocks or not all_nodes:
                    continue

                # Track search position so each block inserts under its own nodes
                search_start_idx = 0

                # Process each block independently
                for commands, nodes in blocks:
                    if not commands:
                        continue

                    # Expand abbreviations before matching
                    expanded_commands = expand_abbreviations(commands)

                    # Track inserted nodes per block to prevent duplicates within the same block
                    inserted_nodes = set()

                    # For each node in this block, find matching PNG and insert
                    for node in nodes:
                        if node in inserted_nodes:
                            continue

                        png_match = find_best_match(node, expanded_commands, png_files)
                        if not png_match:
                            print(f"  No match: {node} + {' '.join(expanded_commands)}")
                            continue

                        # Insert image at the next unused <NodeName> paragraph
                        inserted = False
                        for para_idx, paragraph in enumerate(cell.paragraphs):
                            if para_idx < search_start_idx:
                                continue
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
                                search_start_idx = para_idx + 1
                                break

                        if not inserted:
                            print(f"  Warning: found match but no <{node}> paragraph in cell")

    document.save(DOCX_OUTPUT)
    print(f"\nSaved: {DOCX_OUTPUT}")