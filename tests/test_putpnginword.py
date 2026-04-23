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
