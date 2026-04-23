import re
import os
import glob
from docx import Document
from docx.shared import Inches


# --- Configuration ---
DOCX_INPUT = r"test_document_v2.docx"
PNG_PATH = r"screenshots\*.png"
DOCX_OUTPUT = "test_document_v2_with_png.docx"


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


# --- Main ---
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

            # Parse cell paragraphs
            commands, nodes = parse_paragraphs(cell.paragraphs)

            if not commands or not nodes:
                continue
                continue

            # For each node, find matching PNG and insert
            for node in nodes:
                png_match = find_best_match(node, commands, png_files)
                if not png_match:
                    print(f"  No match: {node} + {' '.join(commands)}")
                    continue

                # Insert image at the <NodeName> paragraph
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

document.save(DOCX_OUTPUT)
print(f"\nSaved: {DOCX_OUTPUT}")