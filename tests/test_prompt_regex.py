import pytest
from process_network_logs import _split_into_segments


def test_syslog_line_not_matched():
    """[SYSLOG], msg should NOT be parsed as a prompt+command."""
    log = "[SYSLOG], Interface changed"
    segments = _split_into_segments(log)
    assert len(segments) == 0


def test_square_bracket_prompt_matched():
    """[HW-Core-BKK-01] display device should match as prompt+command."""
    log = "[HW-Core-BKK-01] display device\nDevice output here"
    segments = _split_into_segments(log)
    assert len(segments) == 1
    assert segments[0]['prompt'] == '[HW-Core-BKK-01]'
    assert segments[0]['command'] == 'display device'


def test_angle_bracket_prompt_matched():
    """<HW-Core-BKK-01> display clock should match as prompt+command."""
    log = "<HW-Core-BKK-01> display clock\nClock output here"
    segments = _split_into_segments(log)
    assert len(segments) == 1
    assert segments[0]['prompt'] == '<HW-Core-BKK-01>'
    assert segments[0]['command'] == 'display clock'


def test_empty_prompt_not_matched():
    """[HUAWEI] with no command should NOT match."""
    log = "[HUAWEI]\n"
    segments = _split_into_segments(log)
    assert len(segments) == 0
