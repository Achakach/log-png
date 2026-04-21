import re
import os
import glob
from docx import Document
from docx.shared import Inches


# --- Configuration ---
DOCX_INPUT = r"replaced_document.docx"
PNG_PATH = r"D:\Documents\True_DTAC_Cloud Core\UAT\GEN Tool\png\*.png"
DOCX_OUTPUT = "ThaiCo_SW_UAT_Document_RST_DC61_PH21_nonSDN.docx"


# --- Regex patterns ---
# Match prompt+command lines: <Router>cmd or [~*Router]cmd or [~*Router-sub]cmd
PROMPT_RE = re.compile(
    r'^(<[A-Za-z][\w.\-]*>|\[~?\*?[A-Za-z][\w.\-/]*\])\s+(.+)$',
    re.MULTILINE
)

# Match node-only lines: <NodeName> with no command after
NODE_RE = re.compile(r'^<([A-Za-z][\w.\-]*)>\s*$', re.MULTILINE)


def sanitize_filename(name: str, max_length: int = 200) -> str:
    result = re.sub(r'[\\/:*?"<>\n\r\t]', '_', name)
    result = result.replace('|', ' ')
    if not result.strip():
        return 'unnamed'
    return result[:max_length]


def parse_cell_commands(cell_text: str) -> list[str]:
    """Extract commands from all prompt lines in a cell."""
    commands = []
    for match in PROMPT_RE.finditer(cell_text):
        cmd = match.group(2).strip()
        commands.append(cmd)
    return commands


def parse_cell_nodes(cell_text: str) -> list[str]:
    """Extract device names from <NodeName> lines (no command after)."""
    return [m.group(1) for m in NODE_RE.finditer(cell_text)]


def find_best_match(device: str, commands: list[str], png_files: list[str]) -> str | None:
    """Find the PNG that best matches device + commands using prefix matching.

    Token-by-token prefix matching (case-insensitive):
      cell 'system' matches PNG 'system-view' (prefix)
      cell 'dis' matches PNG 'display' (prefix)
      cell 'q' matches PNG 'quit' (prefix)
    """
    search_tokens = sanitize_filename(device).lower().split()
    for cmd in commands:
        search_tokens.extend(sanitize_filename(cmd).lower().split())

    best_match = None
    best_score = 0

    for png_path in png_files:
        png_name = os.path.basename(png_path).replace('.png', '').lower()
        png_tokens = png_name.split()

        # Device name must match exactly
        if not png_tokens or png_tokens[0] != search_tokens[0]:
            continue

        # Count prefix-matching tokens
        score = 0
        for i, st in enumerate(search_tokens):
            if i < len(png_tokens) and png_tokens[i].startswith(st):
                score += 1

        # Require at least 60% of search tokens to match
        if score > best_score and score >= len(search_tokens) * 0.6:
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

            # Parse cell
            commands = parse_cell_commands(cell_text)
            nodes = parse_cell_nodes(cell_text)

            if not commands or not nodes:
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