import pytest
from process_network_logs import _split_into_segments, _group_segments, _finalize_group, _has_error_in_output


def test_error_suffix_standalone_command():
    log = """
<HW-Core-BKK-01> display wrong-command
  Unrecognized command found at '^' position.

<HW-Core-BKK-01> display clock
  2026-04-07 21:15:30+07:00
  Tuesday
"""
    segments = _split_into_segments(log)
    groups = _group_segments(segments)
    assert len(groups) == 2

    group0 = _finalize_group(groups[0])
    assert _has_error_in_output(group0[0]['output']) is True

    group1 = _finalize_group(groups[1])
    assert _has_error_in_output(group1[0]['output']) is False


def test_error_suffix_nested_block():
    log = """
<HW-Core-BKK-01> system-view
[HW-Core-BKK-01] interface LoopBack999
[HW-Core-BKK-01-LoopBack999] display this
  Error: The interface does not exist.
[HW-Core-BKK-01-LoopBack999] quit
[HW-Core-BKK-01] quit
<HW-Core-BKK-01> display clock
  2026-04-07 21:15:30+07:00
"""
    segments = _split_into_segments(log)
    groups = _group_segments(segments)
    assert len(groups) == 2

    group0 = _finalize_group(groups[0])
    assert any(_has_error_in_output(seg['output']) for seg in group0) is True

    group1 = _finalize_group(groups[1])
    assert any(_has_error_in_output(seg['output']) for seg in group1) is False


def test_error_suffix_multiple_commands_in_group():
    log = """
<HW> display device
CE8855-32CQ4BQ'S Device status:
----------------------------------------------------------------------------------------
Slot    Card    Type          		Online   Power Register   Alarm   Primary
----------------------------------------------------------------------------------------
1       -       CE8855-32CQ4BQ 		Present	 On    Registered Normal  Master
	FAN1	FAN			Present  On    Registered Normal  NA
----------------------------------------------------------------------------------------

<HW> display wrong-cmd
  Wrong parameter found at '^' position.

<HW> display clock
  2026-04-07 21:15:30+07:00
"""
    segments = _split_into_segments(log)
    groups = _group_segments(segments)
    assert len(groups) == 3

    assert any(_has_error_in_output(seg['output']) for seg in _finalize_group(groups[0])) is False
    assert any(_has_error_in_output(seg['output']) for seg in _finalize_group(groups[1])) is True
    assert any(_has_error_in_output(seg['output']) for seg in _finalize_group(groups[2])) is False


def test_no_false_positive_on_warning_in_normal_output():
    output = """\
Sequence	AlarmId		Severity	Date Time	Description
----------------------------------------------------------------------------------------
1		0x8132249	Warning		2026-02-18	The Bios...
"""
    assert _has_error_in_output(output) is False


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
