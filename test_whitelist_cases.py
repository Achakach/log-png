#!/usr/bin/env python
"""Test whitelist edge cases comprehensively."""
import json
import os
import shutil
import tempfile

from process_network_logs import (
    _command_matches_whitelist,
    _group_matches_whitelist,
    _should_truncate_and_log,
    _filter_groups_by_whitelist,
    parse_log,
    process_network_logs,
)


TEST_LOG = """\
<HW-Core-BKK-01> display device
CE8855-32CQ4BQ'S Device status:
----------------------------------------------------------------------------------------
Slot    Card    Type          		Online   Power Register   Alarm   Primary
----------------------------------------------------------------------------------------
1       -       CE8855-32CQ4BQ 		Present	 On    Registered Normal  Master
----------------------------------------------------------------------------------------

<HW-Core-BKK-01> display clock
  2026-04-07 21:15:30+07:00
  Tuesday

<HW-Core-BKK-01> stelnet 10.1.1.1
[TUC-REMOTE] display current-configuration
[TUC-REMOTE] quit
[TUC-REMOTE] quit
"""

def test_empty_whitelist():
    """Empty whitelist should process everything."""
    segments = parse_log(TEST_LOG, whitelist=[])
    commands = [g[0]['command'] for g in segments]
    assert len(commands) == 3, f"Expected 3 groups, got {len(commands)}: {commands}"
    assert 'display device' in commands
    assert 'display clock' in commands
    assert 'stelnet 10.1.1.1' in commands
    print("✅ Empty whitelist: ALL commands processed")

def test_whitelist_single_command():
    """Only display device should be kept."""
    segments = parse_log(TEST_LOG, whitelist=['display device'])
    # Apply filter like process_network_logs does
    segments = _filter_groups_by_whitelist(segments, ['display device'])
    commands = [g[0]['command'] for g in segments]
    assert commands == ['display device'], f"Expected ['display device'], got {commands}"
    print("✅ Single command whitelist: Only display device")

def test_whitelist_multiple_commands():
    """display device + display clock."""
    segments = parse_log(TEST_LOG, whitelist=['display device', 'display clock'])
    segments = _filter_groups_by_whitelist(segments, ['display device', 'display clock'])
    commands = [g[0]['command'] for g in segments]
    assert 'display device' in commands
    assert 'display clock' in commands
    assert 'stelnet 10.1.1.1' not in commands
    assert len(commands) == 2, f"Expected 2, got {len(commands)}: {commands}"
    print("✅ Multiple commands whitelist: 2 commands kept")

def test_whitelist_prefix_match():
    """'display' should match display device, display clock."""
    segments = parse_log(TEST_LOG, whitelist=['display'])
    segments = _filter_groups_by_whitelist(segments, ['display'])
    commands = [g[0]['command'] for g in segments]
    assert 'display device' in commands
    assert 'display clock' in commands
    assert 'stelnet 10.1.1.1' not in commands
    print("✅ Prefix match: 'display' matches display* commands")

def test_whitelist_ssh_merge():
    """SSH session should match stelnet prefix."""
    segments = parse_log(TEST_LOG, whitelist=['stelnet'])
    segments = _filter_groups_by_whitelist(segments, ['stelnet'])
    commands = [g[0]['command'] for g in segments]
    assert len(commands) == 1, f"Expected 1 SSH group, got {len(commands)}: {commands}"
    assert commands[0].startswith('stelnet'), f"Expected stelnet group, got {commands}"
    print("✅ SSH merged group matches stelnet prefix")

def test_whitelist_display_cur_in_ssh():
    """dis cur merged with stelnet should match 'stelnet' in whitelist."""
    segments = parse_log(TEST_LOG, whitelist=['stelnet'])
    segments = _filter_groups_by_whitelist(segments, ['stelnet'])
    commands = [g[0]['command'] for g in segments]
    assert len(commands) == 1
    # The merged group starts with stelnet
    assert 'stelnet' in commands[0].lower()
    print("✅ SSH merged group with dis cur matches stelnet whitelist")

def test_whitelist_no_log_for_skipped():
    """Skipped commands should NOT create .log files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        results = process_network_logs(TEST_LOG, output_dir=tmpdir, whitelist=['display device'])
        assert len(results) == 1, f"Expected 1 PNG, got {len(results)}"

        log_files = [f for f in os.listdir(tmpdir) if f.endswith('.log')]
        assert len(log_files) == 0, f"Expected 0 .log files, got {log_files}"
    print("✅ No .log files created for skipped commands")

if __name__ == "__main__":
    print("Running whitelist edge case tests...\n")

    test_empty_whitelist()
    test_whitelist_single_command()
    test_whitelist_multiple_commands()
    test_whitelist_prefix_match()
    test_whitelist_ssh_merge()
    test_whitelist_display_cur_in_ssh()
    test_whitelist_no_log_for_skipped()

    print("\n✅ All edge case tests passed!")
