import pytest
import sys
from pathlib import Path

# Add parent directory to path so we can import putpnginword
sys.path.insert(0, str(Path(__file__).parent.parent))

from putpnginword import (
    parse_paragraphs,
    expand_abbreviations,
    find_best_match,
    list_sections,
    extract_title,
    get_heading_level,
    should_process_table,
)
from filename_utils import sanitize_filename
from docx import Document


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
    blocks = parse_paragraphs(paragraphs)
    assert blocks == [(['sys'], ['NODE1'])]


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
    blocks = parse_paragraphs(paragraphs)
    assert blocks == [
        ([
            'system-view',
            'interface GE0/0/1',
            'display this',
            'quit',
            'quit',
        ], ['TUC-NODE1', 'TUC-NODE2'])
    ]


def test_parse_splits_on_standalone_user_view():
    """Standalone <Router>cmd after nested block starts a new block."""
    paragraphs = [
        MockParagraph('<HUAWEI>system-view'),
        MockParagraph('[HUAWEI]interface GE0/0/1'),
        MockParagraph('[HUAWEI-GE0/0/1]display this'),
        MockParagraph('[HUAWEI-GE0/0/1]quit'),
        MockParagraph('[HUAWEI]quit'),
        MockParagraph('<HUAWEI>display device'),
        MockParagraph('<TUC-NODE1>'),
    ]
    blocks = parse_paragraphs(paragraphs)
    assert blocks == [
        ([
            'system-view',
            'interface GE0/0/1',
            'display this',
            'quit',
            'quit',
        ], []),
        (['display device'], ['TUC-NODE1']),
    ]


# --- expand_abbreviations tests ---

def test_expand_system():
    assert expand_abbreviations(['system']) == ['system-view']


def test_expand_dis():
    assert expand_abbreviations(['dis']) == ['display']


def test_expand_dis_th():
    assert expand_abbreviations(['dis th']) == ['display this']


def test_expand_q():
    assert expand_abbreviations(['q']) == ['quit']


def test_expand_comm():
    assert expand_abbreviations(['comm']) == ['commit']


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


def test_find_best_match_standalone_system_view_no_nested_match():
    """Cell with just 'system-view' should not match nested block PNG."""
    png_files = [
        'HW-Core-BKK-01 system-view interface GigabitEthernet0_0_1 display this quit quit.png',
    ]
    result = find_best_match('HW-Core-BKK-01', ['system-view'], png_files)
    assert result is None


def test_find_best_match_no_false_positive():
    """Cell commands not present in PNG should not match."""
    png_files = [
        'HW-Core-BKK-01 system-view display current-configuration quit.png',
    ]
    result = find_best_match('HW-Core-BKK-01', ['system-view', 'set', 'cpu'], png_files)
    assert result is None


def test_find_best_match_standalone_vs_nested():
    """Standalone command should not match nested block PNG starting with different command."""
    png_files = [
        'HW-Core-BKK-01 system-view display current-configuration display ip routing-table quit.png',
        'HW-Core-BKK-01 display current-configuration.png',
    ]
    # Cell with just "display current-configuration" should match standalone PNG only
    result = find_best_match('HW-Core-BKK-01', ['display', 'current-configuration'], png_files)
    assert result is not None
    assert 'display current-configuration.png' in result
    assert 'system-view' not in result


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


# --- list_sections tests ---

class MockStyle:
    def __init__(self, name):
        self.name = name


class MockPara:
    def __init__(self, text, style_name='Normal'):
        self.text = text
        self.style = MockStyle(style_name) if style_name else None


def test_list_sections(capsys):
    doc = type('Doc', (), {'paragraphs': [
        MockPara('T01', 'Heading 2'),
        MockPara('T01-01', 'Heading 3'),
        MockPara('Some text', 'Normal'),
        MockPara('T01-0101', 'Heading 4'),
    ]})()
    list_sections(doc)
    captured = capsys.readouterr()
    assert 'T01' in captured.out
    assert 'T01-01' in captured.out
    assert 'T01-0101' in captured.out
    assert 'Some text' not in captured.out


# --- extract_title tests ---

def test_extract_title_with_id():
    assert extract_title('T01-0201-01 login protocol SSH') == 'login protocol SSH'


def test_extract_title_without_id():
    assert extract_title('Device Management Acceptance') == 'Device Management Acceptance'


def test_extract_title_with_dash_id():
    assert extract_title('T01-01 system Hardware Maintenance') == 'system Hardware Maintenance'


# --- get_heading_level tests ---

def test_get_heading_level_heading3():
    para = MockPara('Foo', 'Heading 3')
    assert get_heading_level(para) == 3


def test_get_heading_level_normal():
    para = MockPara('Foo', 'Normal')
    assert get_heading_level(para) is None


# --- should_process_table integration test ---

def test_should_process_table_match():
    doc_path = Path('document structure example.docx')
    if not doc_path.exists():
        pytest.skip('document structure example.docx not found')
    doc = Document(str(doc_path))
    assert len(doc.tables) >= 1
    # Table 0 under T01-01
    assert should_process_table(doc, 0, ['T01-01'])
    assert should_process_table(doc, 0, ['T01'])
    # Table 1 under T01-02
    assert should_process_table(doc, 1, ['T01-02'])
    assert not should_process_table(doc, 1, ['T01-01'])


# --- Multi-device per-cell matching tests ---

def test_multi_device_match_any_block():
    """Nodes at end of cell should match against any command block."""
    paragraphs = [
        MockParagraph('<HUAWEI>display cpu-usage'),
        MockParagraph('<HUAWEI>display cpu'),
        MockParagraph('<device1>'),
        MockParagraph('<device2>'),
    ]
    blocks = parse_paragraphs(paragraphs)
    # Should have 2 blocks (both standalone, split on second <HUAWEI>)
    assert len(blocks) == 2
    # Collect all nodes cell-wide
    all_nodes = set()
    for _, block_nodes in blocks:
        all_nodes.update(block_nodes)
    assert all_nodes == {'device1', 'device2'}


def test_newline_split_in_paragraph():
    """Word cell with multiple lines in single paragraph should split correctly."""
    paragraphs = [
        MockParagraph('<HUAWEI>commandx1\n[HUAWEI]commandx2\n<device1>\npicx1\n<device2>\npicx2'),
    ]
    blocks = parse_paragraphs(paragraphs)
    assert len(blocks) == 1
    assert blocks[0][0] == ['commandx1', 'commandx2']
    assert blocks[0][1] == ['device1', 'device2']
