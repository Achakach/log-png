"""Test for EOF/incomplete nested block flush fix."""
import sys
sys.path.insert(0, '.')
from process_network_logs import _split_into_segments, _group_segments

def test_incomplete_nested_block_flush():
    """Log ends mid-nested-block → incomplete block should be flushed."""
    log = """<HW> system-view
[HW] interface GE0/0/1
[HW-GE0/0/1] shutdown
[HW-GE0/0/1] quit
[HW] quit
<HW>
"""
    segs = _split_into_segments(log)
    groups = _group_segments(segs)
    assert len(groups) > 0, "Incomplete nested block was dropped at EOF"
    assert len(groups[0]) == 5, f"Expected 5 segments, got {len(groups[0])}"
    cmds = [s['command'] for s in groups[0]]
    assert cmds == ['system-view', 'interface GE0/0/1', 'shutdown', 'quit', 'quit']
    print("✅ test_incomplete_nested_block_flush passed")

def test_disconnect_mid_subview():
    """Log disconnects in sub-view → block should still be saved."""
    log = """<HW> system-view
[HW] interface GE0/0/1
[HW-GE0/0/1] display this
"""
    segs = _split_into_segments(log)
    groups = _group_segments(segs)
    assert len(groups) > 0, "Mid-subview disconnect dropped the block"
    assert len(groups[0]) == 3
    cmds = [s['command'] for s in groups[0]]
    assert cmds == ['system-view', 'interface GE0/0/1', 'display this']
    print("✅ test_disconnect_mid_subview passed")

def test_complete_nested_block_with_empty_prompt():
    """Nested block ending with prompt-only <HW> (no space) → regex skips empty prompt."""
    log = """<HW> system-view
[HW] interface GE0/0/1
[HW-GE0/0/1] shutdown
[HW-GE0/0/1] quit
[HW] quit
<HW>
"""
    segs = _split_into_segments(log)
    # Last segment is [HW] quit (depth 1)
    # Empty <HW> is skipped by regex
    groups = _group_segments(segs)
    assert len(groups) > 0
    assert len(groups[0]) == 5
    cmds = [s['command'] for s in groups[0]]
    assert cmds == ['system-view', 'interface GE0/0/1', 'shutdown', 'quit', 'quit']
    print("✅ test_complete_nested_block_with_empty_prompt passed")

if __name__ == '__main__':
    test_incomplete_nested_block_flush()
    test_disconnect_mid_subview()
    test_complete_nested_block_with_empty_prompt()
    print("\nAll EOF tests passed!")
