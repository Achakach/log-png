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


def parse_paragraphs(paragraphs):
    """Extract commands and node names from cell paragraphs.

    Returns (commands, nodes) where:
      commands: list of command strings from prompt lines
      nodes: list of device names from <NodeName> lines
    """
    commands = []
    nodes = []
    for para in paragraphs:
        text = para.text.strip()
        if not text:
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
            if cmd:  # Skip empty commands (e.g. prompt-only lines)
                commands.append(cmd)
    return commands, nodes


def find_best_match(device: str, commands: list[str], png_files: list[str]) -> str | None:
    """Find the PNG that best matches device + commands using prefix matching.

    Uses longest initial prefix match to prioritize correct interface numbers.
    Example: search 'GE0_0_29' matches PNG with 'GE0_0_29' over PNG with 'GE0_0_20'.
    """
    search_tokens = sanitize_filename(device).lower().split()
    for cmd in commands:
        search_tokens.extend(sanitize_filename(cmd).lower().split())

    best_match = None
    best_prefix = 0  # longest consecutive matching tokens from start
    best_score = 0   # total matching tokens (tiebreaker)

    for png_path in png_files:
        png_name = os.path.basename(png_path).replace('.png', '').lower()
        png_tokens = png_name.split()

        # Device name must match exactly
        if not png_tokens or png_tokens[0] != search_tokens[0]:
            continue

        # Count total matching tokens AND consecutive matches from start
        score = 0
        prefix = 0
        for i, st in enumerate(search_tokens):
            if i < len(png_tokens) and png_tokens[i].startswith(st):
                score += 1
                if i == prefix:
                    prefix += 1

        # Prefer: longest initial prefix, then highest total score
        if prefix > best_prefix or (prefix == best_prefix and score > best_score):
            best_prefix = prefix
            best_score = score
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