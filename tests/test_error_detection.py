import pytest
from process_network_logs import _has_error_in_output


# --- Tests for _has_error_in_output ---

def test_error_unrecognized_command():
    output = "  Unrecognized command found at '^' position."
    assert _has_error_in_output(output) is True


def test_error_ambiguous_command():
    output = "  Ambiguous command found at '^' position."
    assert _has_error_in_output(output) is True


def test_error_incomplete_command():
    output = "  Incomplete command found at '^' position."
    assert _has_error_in_output(output) is True


def test_error_generic_error_colon():
    output = "  Error: The interface does not exist."
    assert _has_error_in_output(output) is True


def test_error_percent_error():
    output = "  %Error: Command invalid."
    assert _has_error_in_output(output) is True


def test_error_not_enough_privilege():
    output = "  Not enough privilege."
    assert _has_error_in_output(output) is True


def test_error_failed_to():
    output = "  Failed to connect to the server."
    assert _has_error_in_output(output) is True


def test_error_not_supported():
    output = "  Not supported on this device."
    assert _has_error_in_output(output) is True


def test_error_this_command_is():
    output = "  This command is not available."
    assert _has_error_in_output(output) is True


def test_error_wrong_parameter():
    output = "  Wrong parameter found at '^' position."
    assert _has_error_in_output(output) is True


def test_error_case_insensitive():
    output = "  ERROR: Something went wrong."
    assert _has_error_in_output(output) is True


def test_warning_is_error():
    output = "  Warning: All interfaces are silent."
    assert _has_error_in_output(output) is True


def test_no_error_successful_output():
    output = """\
CE8855-32CQ4BQ'S Device status:
----------------------------------------------------------------------------------------
Slot    Card    Type          		Online   Power Register   Alarm   Primary
----------------------------------------------------------------------------------------
1       -       CE8855-32CQ4BQ 		Present	 On    Registered Normal  Master
----------------------------------------------------------------------------------------
"""
    assert _has_error_in_output(output) is False


def test_no_error_normal_ping():
    output = """\
  PING 10.10.1.2: 56  data bytes, press CTRL_C to break
    Reply from 10.10.1.2: bytes=56 Sequence=1 ttl=255 time=1 ms
"""
    assert _has_error_in_output(output) is False


def test_no_error_empty_output():
    assert _has_error_in_output("") is False


def test_no_error_only_whitespace():
    assert _has_error_in_output("   \n\t  ") is False


def test_error_in_middle_of_output():
    output = """\
  Some normal output here
  Error: The interface does not exist.
  Some more output
"""
    assert _has_error_in_output(output) is True


def test_error_not_matching_mid_string():
    # The word "error" inside normal text should NOT match
    output = "  No error was found in the system."
    assert _has_error_in_output(output) is False


def test_error_prefixed_with_timestamp():
    # Error at start of line after whitespace
    output = "  Error: Invalid input."
    assert _has_error_in_output(output) is True


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
