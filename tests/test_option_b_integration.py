"""Integration tests for Option B: block-scoped node matching.

A node that appears after multiple command blocks should get
an image for EACH block (not just one per cell).
"""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from putpnginword import (
    parse_paragraphs_detailed,
    match_cell_blocks,
)


class MockParagraph:
    def __init__(self, text):
        self.text = text


# --- parse_paragraphs_detailed tests ---

def test_parse_detailed_returns_para_indices():
    paragraphs = [
        MockParagraph('<HUAWEI>system-view'),
        MockParagraph('<TUC-NODE1>'),
    ]
    blocks = parse_paragraphs_detailed(paragraphs)
    assert blocks == [(['system-view'], [('TUC-NODE1', 1)], False)]


def test_parse_detailed_multiple_blocks():
    paragraphs = [
        MockParagraph('<huawei>cmd 7'),
        MockParagraph('<device1>'),
        MockParagraph('<device2>'),
        MockParagraph('<huawei>cmd 8'),
        MockParagraph('<device1>'),
        MockParagraph('<device2>'),
    ]
    blocks = parse_paragraphs_detailed(paragraphs)
    assert len(blocks) == 2
    assert blocks[0] == (['cmd 7'], [('device1', 1), ('device2', 2)], False)
    assert blocks[1] == (['cmd 8'], [('device1', 4), ('device2', 5)], False)


def test_parse_detailed_para_indices_correct():
    paragraphs = [
        MockParagraph('<huawei>display device'),
        MockParagraph('<device1>'),   # para_idx 1
        MockParagraph('<huawei>display clock'),
        MockParagraph('<device1>'),   # para_idx 3
    ]
    blocks = parse_paragraphs_detailed(paragraphs)
    assert len(blocks) == 2
    assert blocks[0][1] == [('device1', 1)]
    assert blocks[1][1] == [('device1', 3)]


# --- match_cell_blocks tests ---

def test_same_node_multiple_blocks_gets_multiple_images():
    """Table 3 case: device1 appears after cmd 7 and cmd 8.
    Should get 2 images (one per block)."""
    paragraphs = [
        MockParagraph('<huawei>cmd 7'),
        MockParagraph('<device1>'),
        MockParagraph('<device2>'),
        MockParagraph('<huawei>cmd 8'),
        MockParagraph('<device1>'),
        MockParagraph('<device2>'),
    ]
    png_files = [
        'device1 cmd 7.png',
        'device1 cmd 8.png',
        'device2 cmd 7.png',
        'device2 cmd 8.png',
    ]
    results = match_cell_blocks(paragraphs, png_files)

    # Count images per node
    device1_images = [r for r in results if r['node'] == 'device1' and r['action'] == 'inserted']
    device2_images = [r for r in results if r['node'] == 'device2' and r['action'] == 'inserted']

    assert len(device1_images) == 2, f"Expected 2 images for device1, got {len(device1_images)}: {device1_images}"
    assert len(device2_images) == 2, f"Expected 2 images for device2, got {len(device2_images)}: {device2_images}"

    # Verify block assignments
    device1_blocks = sorted([r['block_idx'] for r in device1_images])
    assert device1_blocks == [0, 1]


def test_block_isolated_matching():
    """Block 1 commands should NOT match block 2's PNGs."""
    paragraphs = [
        MockParagraph('<huawei>display device'),
        MockParagraph('<device1>'),
        MockParagraph('<huawei>display clock'),
        MockParagraph('<device1>'),
    ]
    png_files = [
        'device1 display device.png',
        'device1 display clock.png',
    ]
    results = match_cell_blocks(paragraphs, png_files)

    inserted = [r for r in results if r['action'] == 'inserted']
    assert len(inserted) == 2

    # Block 0 should match display device
    block0_match = [r for r in inserted if r['block_idx'] == 0][0]['match_path']
    assert 'display device' in block0_match

    # Block 1 should match display clock
    block1_match = [r for r in inserted if r['block_idx'] == 1][0]['match_path']
    assert 'display clock' in block1_match


def test_error_per_block_independent():
    """One block has error, another doesn't — should insert for non-error block."""
    paragraphs = [
        MockParagraph('<huawei>display cpu-usage'),
        MockParagraph('<device1>'),
        MockParagraph('<huawei>display cpu'),
        MockParagraph('<device1>'),
    ]
    png_files = [
        'device1 display cpu-usage [error].png',
        'device1 display cpu.png',
    ]
    results = match_cell_blocks(paragraphs, png_files)

    inserted = [r for r in results if r['action'] == 'inserted']
    skipped = [r for r in results if r['action'] == 'skipped_error']

    # Block 0 (display cpu-usage) is error → skipped
    assert len(skipped) == 1
    assert skipped[0]['block_idx'] == 0

    # Block 1 (display cpu) is OK → inserted
    assert len(inserted) == 1
    assert inserted[0]['block_idx'] == 1


def test_no_match_returns_no_match_action():
    paragraphs = [
        MockParagraph('<huawei>unknown command'),
        MockParagraph('<device1>'),
    ]
    png_files = [
        'device1 display device.png',
    ]
    results = match_cell_blocks(paragraphs, png_files)
    assert len(results) == 1
    assert results[0]['action'] == 'no_match'


def test_para_idx_points_to_correct_paragraph():
    paragraphs = [
        MockParagraph('<huawei>cmd 7'),
        MockParagraph('<device1>'),   # para_idx 1
        MockParagraph('<huawei>cmd 8'),
        MockParagraph('<device1>'),   # para_idx 3
    ]
    png_files = ['device1 cmd 7.png', 'device1 cmd 8.png']
    results = match_cell_blocks(paragraphs, png_files)

    device1_results = [r for r in results if r['node'] == 'device1']
    assert len(device1_results) == 2

    para_indices = sorted([r['para_idx'] for r in device1_results])
    assert para_indices == [1, 3]


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
