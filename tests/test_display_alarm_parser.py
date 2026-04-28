import pytest
from display_alarm_parser import parse_display_alarm_active, compare_alarms, format_alarm_suffix


BASELINE_OUTPUT = """\
A:Critical   MA:Major   MI:Minor   IN:Info
----------------------------------------------------------------------------------------
Sequence	AlarmId		Severity	Date Time	Description
----------------------------------------------------------------------------------------
1		0x8132249	Warning		2026-02-18	The Bios...
								12:40:23+
								07:00

----------------------------------------------------------------------------------------
"""

REMOVED_OUTPUT = """\
A:Critical   MA:Major   MI:Minor   IN:Info
----------------------------------------------------------------------------------------
Sequence	AlarmId		Severity	Date Time	Description
----------------------------------------------------------------------------------------
150		0x8130019	Warning		2026-03-06	The fan module was removed. (EntPhysicalName=FAN
																						slot 1/4, EntityTrapFaultID=138925)

1		0x8132249	Warning		2026-02-18	The Bios...
								12:40:23+
								07:00

----------------------------------------------------------------------------------------
"""


def test_parse_display_alarm_active_baseline():
    alarms = parse_display_alarm_active(BASELINE_OUTPUT)
    # The Bios... doesn't have EntPhysicalName, should be skipped
    assert len(alarms) == 0


def test_parse_display_alarm_active_removed():
    alarms = parse_display_alarm_active(REMOVED_OUTPUT)
    # Only FAN4 alarm has EntPhysicalName; The Bios... is skipped
    assert len(alarms) == 1

    assert alarms[0]['sequence'] == '150'
    assert alarms[0]['alarm_id'] == '0x8130019'
    assert alarms[0]['severity'] == 'Warning'
    assert alarms[0]['card_name'] == 'FAN4'


def test_parse_display_alarm_active_empty():
    assert parse_display_alarm_active("") == []
    assert parse_display_alarm_active("no table here\njust text") == []


def test_compare_alarms_no_new():
    baseline = [
        {'sequence': '1', 'alarm_id': '0x8132249', 'severity': 'Warning', 'card_name': 'FAN3'},
    ]
    current = [
        {'sequence': '1', 'alarm_id': '0x8132249', 'severity': 'Warning', 'card_name': 'FAN3'},
    ]
    assert compare_alarms(baseline, current) == []


def test_compare_alarms_new_alarm():
    baseline = [
        {'sequence': '1', 'alarm_id': '0x8132249', 'severity': 'Warning', 'card_name': 'FAN3'},
    ]
    current = [
        {'sequence': '150', 'alarm_id': '0x8130019', 'severity': 'Warning', 'card_name': 'FAN4'},
        {'sequence': '1', 'alarm_id': '0x8132249', 'severity': 'Warning', 'card_name': 'FAN3'},
    ]
    assert compare_alarms(baseline, current) == ['FAN4']


def test_compare_alarms_multiple_new():
    baseline = [
        {'sequence': '1', 'alarm_id': '0x8132249', 'severity': 'Warning', 'card_name': 'FAN3'},
    ]
    current = [
        {'sequence': '150', 'alarm_id': '0x8130019', 'severity': 'Warning', 'card_name': 'FAN4'},
        {'sequence': '151', 'alarm_id': '0x8130020', 'severity': 'Warning', 'card_name': 'PWR1'},
        {'sequence': '1', 'alarm_id': '0x8132249', 'severity': 'Warning', 'card_name': 'FAN3'},
    ]
    assert compare_alarms(baseline, current) == ['FAN4', 'PWR1']


def test_format_alarm_suffix_single():
    assert format_alarm_suffix(['FAN3']) == '[FAN3]'


def test_format_alarm_suffix_multiple():
    assert format_alarm_suffix(['FAN3', 'PWR1']) == '[FAN3 PWR1]'


def test_format_alarm_suffix_empty():
    assert format_alarm_suffix([]) == ''


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
