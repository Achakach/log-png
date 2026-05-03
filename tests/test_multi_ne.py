import pytest
from process_network_logs import _split_into_segments, _group_segments, parse_log


MULTI_NE_LOG = """\
<NE-A> display device
CE8855-32CQ4BQ'S Device status:
----------------------------------------------------------------------------------------
Slot    Card    Type          		Online   Power Register   Alarm   Primary
----------------------------------------------------------------------------------------
1       -       CE8855-32CQ4BQ 		Present	 On    Registered Normal  Master
	FAN1	FAN			Present  On    Registered Normal  NA
	FAN2	FAN			Present  On    Registered Normal  NA
	FAN3	FAN			Present  On    Registered Normal  NA
----------------------------------------------------------------------------------------

<NE-B> display device
CE8855-32CQ4BQ'S Device status:
----------------------------------------------------------------------------------------
Slot    Card    Type          		Online   Power Register   Alarm   Primary
----------------------------------------------------------------------------------------
1       -       CE8855-32CQ4BQ 		Present	 On    Registered Normal  Master
	FAN1	FAN			Present  On    Registered Normal  NA
	FAN2	FAN			Present  On    Registered Normal  NA
----------------------------------------------------------------------------------------

<NE-A> display device
CE8855-32CQ4BQ'S Device status:
----------------------------------------------------------------------------------------
Slot    Card    Type          		Online   Power Register   Alarm   Primary
----------------------------------------------------------------------------------------
1       -       CE8855-32CQ4BQ 		Present	 On    Registered Normal  Master
	FAN1	FAN			Present  On    Registered Normal  NA
	FAN2	FAN			Present  On    Registered Normal  NA
----------------------------------------------------------------------------------------

<NE-A> display clock
  2026-04-07 21:15:30+07:00
  Tuesday
  Time Zone : Bangkok

<NE-B> display clock
  2026-04-07 21:15:30+07:00
  Tuesday
  Time Zone : Bangkok

<NE-A> system-view
[NE-A] interface GigabitEthernet0/0/1
[NE-A-GigabitEthernet0/0/1] display this
  #
  interface GigabitEthernet0/0/1
  #
[NE-A-GigabitEthernet0/0/1] quit
[NE-A] quit

<NE-B> system-view
[NE-B] interface GigabitEthernet0/0/1
[NE-B-GigabitEthernet0/0/1] display this
  #
  interface GigabitEthernet0/0/1
  #
[NE-B-GigabitEthernet0/0/1] quit
[NE-B] quit

<NE-A> display device
CE8855-32CQ4BQ'S Device status:
----------------------------------------------------------------------------------------
Slot    Card    Type          		Online   Power Register   Alarm   Primary
----------------------------------------------------------------------------------------
1       -       CE8855-32CQ4BQ 		Present	 On    Registered Normal  Master
	FAN1	FAN			Present  On    Registered Normal  NA
	FAN2	FAN			Present  On    Registered Normal  NA
----------------------------------------------------------------------------------------
"""


def test_multi_ne_split_into_segments():
    segments = _split_into_segments(MULTI_NE_LOG)
    # Should have 16 segments (including quit commands)
    assert len(segments) == 16

    # Check prompt device names
    prompts = [seg['prompt'] for seg in segments]
    assert prompts[0] == '<NE-A>'
    assert prompts[1] == '<NE-B>'
    assert prompts[2] == '<NE-A>'
    assert prompts[3] == '<NE-A>'
    assert prompts[4] == '<NE-B>'
    assert prompts[5] == '<NE-A>'
    assert prompts[6] == '[NE-A]'
    assert prompts[7] == '[NE-A-GigabitEthernet0/0/1]'
    assert prompts[8] == '[NE-A-GigabitEthernet0/0/1]'
    assert prompts[9] == '[NE-A]'
    assert prompts[10] == '<NE-B>'
    assert prompts[11] == '[NE-B]'
    assert prompts[12] == '[NE-B-GigabitEthernet0/0/1]'
    assert prompts[13] == '[NE-B-GigabitEthernet0/0/1]'
    assert prompts[14] == '[NE-B]'
    assert prompts[15] == '<NE-A>'


def test_multi_ne_grouping():
    segments = _split_into_segments(MULTI_NE_LOG)
    groups = _group_segments(segments)

    # Should produce groups where each group is independent
    assert len(groups) == 8

    # Group 0: NE-A display device (standalone)
    assert len(groups[0]) == 1
    assert groups[0][0]['prompt'] == '<NE-A>'
    assert groups[0][0]['command'] == 'display device'

    # Group 1: NE-B display device (standalone)
    assert len(groups[1]) == 1
    assert groups[1][0]['prompt'] == '<NE-B>'
    assert groups[1][0]['command'] == 'display device'

    # Group 2: NE-A display device (standalone)
    assert len(groups[2]) == 1
    assert groups[2][0]['prompt'] == '<NE-A>'
    assert groups[2][0]['command'] == 'display device'

    # Group 3: NE-A display clock (standalone)
    assert len(groups[3]) == 1
    assert groups[3][0]['prompt'] == '<NE-A>'
    assert groups[3][0]['command'] == 'display clock'

    # Group 4: NE-B display clock (standalone)
    assert len(groups[4]) == 1
    assert groups[4][0]['prompt'] == '<NE-B>'
    assert groups[4][0]['command'] == 'display clock'

    # Group 5: NE-A system-view nested block
    assert len(groups[5]) == 5  # system-view, interface, display this, quit, quit
    assert groups[5][0]['prompt'] == '<NE-A>'
    assert groups[5][-1]['prompt'] == '[NE-A]'

    # Group 6: NE-B system-view nested block
    assert len(groups[6]) == 5
    assert groups[6][0]['prompt'] == '<NE-B>'
    assert groups[6][-1]['prompt'] == '[NE-B]'

    # Group 7: NE-A display device (standalone)
    assert len(groups[7]) == 1
    assert groups[7][0]['prompt'] == '<NE-A>'
    assert groups[7][0]['command'] == 'display device'
    # The FAN3 removed should be detected here because baseline was group 0


BASIC_MULTI_NE = """\
<NE-A> display device
CE8855-32CQ4BQ'S Device status:
----------------------------------------------------------------------------------------
Slot    Card    Type          		Online   Power Register   Alarm   Primary
----------------------------------------------------------------------------------------
1       -       CE8855-32CQ4BQ 		Present	 On    Registered Normal  Master
	FAN1	FAN			Present  On    Registered Normal  NA
----------------------------------------------------------------------------------------

<NE-B> display device
CE8855-32CQ4BQ'S Device status:
----------------------------------------------------------------------------------------
Slot    Card    Type          		Online   Power Register   Alarm   Primary
----------------------------------------------------------------------------------------
1       -       CE8855-32CQ4BQ 		Present	 On    Registered Normal  Master
	FAN1	FAN			Present  On    Registered Normal  NA
----------------------------------------------------------------------------------------
"""


def test_multi_ne_baseline_isolation():
    """Each NE should have its own independent baseline."""
    from process_network_logs import parse_log
    from display_device_parser import parse_display_device, compare_devices

    segments = _split_into_segments(BASIC_MULTI_NE)
    groups = _group_segments(segments)

    # Both are standalone display device commands
    assert len(groups) == 2

    # Parse both outputs
    ne_a_parsed = parse_display_device(groups[0][0]['output'])
    ne_b_parsed = parse_display_device(groups[1][0]['output'])

    # Each NE has its own cards
    assert len(ne_a_parsed) == 2  # chassis + FAN1
    assert len(ne_b_parsed) == 2

    # If we remove FAN1 from NE-B, NE-A should be unaffected
    ne_b_current = [
        {'slot': '1', 'card': '-', 'type_': 'S12708'},
    ]
    missing = compare_devices(ne_b_parsed, ne_b_current)
    assert missing == ['FAN1']

    # NE-A baseline still intact
    ne_a_current = parse_display_device(groups[0][0]['output'])
    missing_a = compare_devices(ne_a_parsed, ne_a_current)
    assert missing_a == []


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
