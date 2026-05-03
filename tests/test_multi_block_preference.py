"""Test the new multi-block error preference in putpnginword.py main loop logic."""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from putpnginword import match_cell_blocks
import os


class MockParagraph:
    def __init__(self, text):
        self.text = text


def test_multi_block_first_error_second_ok():
    """If first block is [error] and second is OK, insert for the second block."""
    paragraphs = [
        MockParagraph('<HUAWEI>display cpu-usage'),
        MockParagraph('<TUC-DEVICE1>'),
        MockParagraph('<HUAWEI>display cpu'),
        MockParagraph('<TUC-DEVICE1>'),
    ]
    png_files = [
        'TUC-DEVICE1 display cpu-usage [error].png',
        'TUC-DEVICE1 display cpu.png',
    ]
    results = match_cell_blocks(paragraphs, png_files)

    # Both blocks processed, but only second inserted
    inserted = [r for r in results if r['action'] == 'inserted']
    skipped = [r for r in results if r['action'] == 'skipped_error']

    assert len(inserted) == 1
    assert inserted[0]['block_idx'] == 1
    assert 'display cpu.png' in inserted[0]['match_path']

    assert len(skipped) == 1
    assert skipped[0]['block_idx'] == 0


def test_multi_block_all_error_skip():
    """If ALL matching blocks are [error], skip all insertions."""
    paragraphs = [
        MockParagraph('<HUAWEI>display cpu-usage'),
        MockParagraph('<TUC-DEVICE1>'),
        MockParagraph('<HUAWEI>display cpu'),
        MockParagraph('<TUC-DEVICE1>'),
    ]
    png_files = [
        'TUC-DEVICE1 display cpu-usage [error].png',
        'TUC-DEVICE1 display cpu [error].png',
    ]
    results = match_cell_blocks(paragraphs, png_files)

    assert len(results) == 2
    for r in results:
        assert r['action'] == 'skipped_error'


def test_multi_block_first_ok_wins():
    """If the first block is non-error, it gets inserted. Second may be error or not."""
    paragraphs = [
        MockParagraph('<HUAWEI>display cpu-usage'),
        MockParagraph('<TUC-DEVICE1>'),
        MockParagraph('<HUAWEI>display cpu'),
        MockParagraph('<TUC-DEVICE1>'),
    ]
    png_files = [
        'TUC-DEVICE1 display cpu-usage.png',
        'TUC-DEVICE1 display cpu [error].png',
    ]
    results = match_cell_blocks(paragraphs, png_files)

    inserted = [r for r in results if r['action'] == 'inserted']
    skipped = [r for r in results if r['action'] == 'skipped_error']

    assert len(inserted) == 1
    assert inserted[0]['block_idx'] == 0
    assert 'display cpu-usage.png' in inserted[0]['match_path']

    assert len(skipped) == 1
    assert skipped[0]['block_idx'] == 1


def test_multi_block_only_one_match_ok():
    """If only one of multiple blocks produces a PNG match, that block gets inserted."""
    paragraphs = [
        MockParagraph('<HUAWEI>display cpu-usage'),
        MockParagraph('<TUC-DEVICE1>'),
        MockParagraph('<HUAWEI>display cpu'),
        MockParagraph('<TUC-DEVICE1>'),
    ]
    png_files = [
        'TUC-DEVICE1 display cpu.png',
    ]
    results = match_cell_blocks(paragraphs, png_files)

    # Only block 1 (display cpu) matches
    inserted = [r for r in results if r['action'] == 'inserted']
    no_match = [r for r in results if r['action'] == 'no_match']

    assert len(inserted) == 1
    assert inserted[0]['block_idx'] == 1

    assert len(no_match) == 1
    assert no_match[0]['block_idx'] == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
