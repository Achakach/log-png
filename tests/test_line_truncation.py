import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from process_network_logs import _truncate_long_lines


def test_long_line_truncated():
    """Lines >130 chars should be truncated to 130 chars."""
    group = [{'output': 'a' * 150 + '\n' + 'b' * 80}]
    _truncate_long_lines(group)
    lines = group[0]['output'].split('\n')
    assert len(lines[0]) == 130
    assert len(lines[1]) == 80   # unchanged


def test_short_line_unchanged():
    """Lines <=130 chars should remain unchanged."""
    original = 'short line\nanother line'
    group = [{'output': original}]
    _truncate_long_lines(group)
    assert group[0]['output'] == original


def test_exactly_130_unchanged():
    """Lines exactly 130 chars should NOT be truncated."""
    original = 'x' * 130
    group = [{'output': original}]
    _truncate_long_lines(group)
    assert group[0]['output'] == original


def test_multi_segment_group():
    """All segments in a group should have their output truncated to 130."""
    group = [
        {'output': 'a' * 200},
        {'output': 'b' * 50},
    ]
    _truncate_long_lines(group)
    assert len(group[0]['output']) == 130
    assert group[1]['output'] == 'b' * 50
