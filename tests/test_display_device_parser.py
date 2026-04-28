import pytest
from display_device_parser import parse_display_device, compare_devices, format_removed_suffix


SAMPLE_OUTPUT = """\
CE8855-32CQ4BQ'S Device status:
----------------------------------------------------------------------------------------
Slot    Card    Type          		Online   Power Register   Alarm   Primary
----------------------------------------------------------------------------------------
1       -       CE8855-32CQ4BQ 		Present	 On    Registered Normal  Master
	FAN1	FAN			Present  On    Registered Normal  NA
	FAN2	FAN			Present  On    Registered Normal  NA
	FAN3	FAN			Present  On    Registered Normal  NA
	FAN4	FAN			Present  On    Registered Normal  NA
	FAN5	FAN			Present  On    Registered Normal  NA
	PWR1	PDC1K2S12-CE		Present  On    Registered Normal  NA
	PWR2	PDC1K2S12-CE		Present  On    Registered Normal  NA
----------------------------------------------------------------------------------------
"""


def test_parse_display_device():
    cards = parse_display_device(SAMPLE_OUTPUT)
    assert len(cards) == 8

    # Slot 1 chassis
    assert cards[0] == {'slot': '1', 'card': '-', 'type_': 'CE8855-32CQ4BQ'}

    # FANs
    assert cards[1] == {'slot': '1', 'card': 'FAN1', 'type_': 'FAN'}
    assert cards[2] == {'slot': '1', 'card': 'FAN2', 'type_': 'FAN'}
    assert cards[3] == {'slot': '1', 'card': 'FAN3', 'type_': 'FAN'}
    assert cards[4] == {'slot': '1', 'card': 'FAN4', 'type_': 'FAN'}
    assert cards[5] == {'slot': '1', 'card': 'FAN5', 'type_': 'FAN'}

    # PWRs
    assert cards[6] == {'slot': '1', 'card': 'PWR1', 'type_': 'PDC1K2S12-CE'}
    assert cards[7] == {'slot': '1', 'card': 'PWR2', 'type_': 'PDC1K2S12-CE'}


def test_parse_display_device_empty():
    assert parse_display_device("") == []
    assert parse_display_device("no table here\njust text") == []


def test_compare_devices_no_missing():
    baseline = [
        {'slot': '1', 'card': 'FAN1', 'type_': 'FAN'},
        {'slot': '1', 'card': 'FAN2', 'type_': 'FAN'},
    ]
    current = [
        {'slot': '1', 'card': 'FAN1', 'type_': 'FAN'},
        {'slot': '1', 'card': 'FAN2', 'type_': 'FAN'},
    ]
    assert compare_devices(baseline, current) == []


def test_compare_devices_one_missing():
    baseline = [
        {'slot': '1', 'card': 'FAN1', 'type_': 'FAN'},
        {'slot': '1', 'card': 'FAN2', 'type_': 'FAN'},
        {'slot': '1', 'card': 'FAN3', 'type_': 'FAN'},
    ]
    current = [
        {'slot': '1', 'card': 'FAN1', 'type_': 'FAN'},
        {'slot': '1', 'card': 'FAN2', 'type_': 'FAN'},
    ]
    assert compare_devices(baseline, current) == ['FAN3']


def test_compare_devices_multiple_missing():
    baseline = [
        {'slot': '1', 'card': 'FAN1', 'type_': 'FAN'},
        {'slot': '1', 'card': 'FAN2', 'type_': 'FAN'},
        {'slot': '1', 'card': 'PWR1', 'type_': 'PDC'},
    ]
    current = [
        {'slot': '1', 'card': 'FAN1', 'type_': 'FAN'},
    ]
    assert compare_devices(baseline, current) == ['FAN2', 'PWR1']


def test_compare_devices_different_slot():
    """Same card name in different slots should be treated independently."""
    baseline = [
        {'slot': '1', 'card': 'FAN1', 'type_': 'FAN'},
        {'slot': '2', 'card': 'FAN1', 'type_': 'FAN'},
    ]
    current = [
        {'slot': '1', 'card': 'FAN1', 'type_': 'FAN'},
    ]
    # slot 2 FAN1 is missing
    assert compare_devices(baseline, current) == ['FAN1']


def test_format_removed_suffix_single():
    assert format_removed_suffix(['FAN3']) == '[FAN3 removed]'


def test_format_removed_suffix_multiple():
    assert format_removed_suffix(['FAN3', 'PWR1']) == '[FAN3 PWR1 removed]'


def test_format_removed_suffix_empty():
    assert format_removed_suffix([]) == ''


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
