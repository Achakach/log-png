import re
import os
import glob
from docx import Document
from docx.shared import Inches


# --- Configuration ---
DOCX_INPUT = r"test_document_v3.docx"
PNG_PATH = r"screenshots\*.png"
DOCX_OUTPUT = "test_document_v3_with_png.docx"


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
                search_start_idx = 0

                # For each node, try each command block until match found
                for node in all_nodes:
                    if node in inserted_nodes:
                        continue

                    matched = False
                    for commands, _ in blocks:
                        if not commands:
                            continue

                        expanded_commands = expand_abbreviations(commands)
                        png_match = find_best_match(node, expanded_commands, png_files)
                        if not png_match:
                            continue

                        # Insert image at the next unused <NodeName> paragraph
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
                                print(f"    Command: {' '.join(expanded_commands)}")
                                inserted_nodes.add(node)
                                search_start_idx = para_idx + 1
                                matched = True
                                break

                        if matched:
                            break

                    if not matched:
                        print(f"  No match: {node}")

    document.save(DOCX_OUTPUT)
    print(f"\nSaved: {DOCX_OUTPUT}")