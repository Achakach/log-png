import os
import sys
import tempfile
import pytest

# Ensure root-level modules are importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import extract_commands as extract_commands_module
from extract_commands import (
    extract_commands,
    process_file,
    compare_with_abbreviations,
    get_base_dir,
)


BASIC_LOG = """\
<R> display device
Device output here
<R> system-view
System output
<R> display clock
  2026-04-07 21:15:30+07:00
  Tuesday
  Time Zone : Bangkok
"""


def test_extract_commands_basic():
    """Flat extraction from multi-line log, no expansion."""
    cmds = extract_commands(BASIC_LOG, expand_abbrevs=False)
    assert cmds == ["display device", "system-view", "display clock"]


def test_extract_commands_with_abbreviation_expansion():
    """Verify dis th -> display this and dis dev -> display device."""
    log = "<R> dis th\noutput\n<R> dis dev\noutput\n"
    cmds = extract_commands(log, expand_abbrevs=True)
    assert cmds == ["display this", "display device"]


def test_extract_commands_empty_log():
    """No prompts -> empty list."""
    cmds = extract_commands("No prompts here at all", expand_abbrevs=False)
    assert cmds == []


def test_process_file_creates_output():
    """End-to-end file I/O test with temp dir."""
    log_data = "<R> display device\noutput\n<R> system-view\nout\n"
    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = os.path.join(tmpdir, "test.log")
        out_dir = os.path.join(tmpdir, "out")
        with open(log_path, "w", encoding="utf-8") as f:
            f.write(log_data)

        process_file(log_path, out_dir, expand_abbrevs=False)

        commands_path = os.path.join(out_dir, "test_commands.txt")
        missing_path = os.path.join(out_dir, "test_missing.txt")
        assert os.path.exists(commands_path)
        assert os.path.exists(missing_path)

        with open(commands_path, "r", encoding="utf-8") as f:
            lines = [line.rstrip("\n") for line in f.readlines()]
        assert lines == ["display device", "system-view"]


def test_compare_with_abbreviations_found():
    """Commands that exist in abbreviations.json."""
    found, missing = compare_with_abbreviations(["display device", "system-view"])
    assert "display device" in found
    assert "system-view" in found
    assert missing == []


def test_compare_with_abbreviations_missing():
    """Commands that do NOT exist in abbreviations.json."""
    found, missing = compare_with_abbreviations(["display custom-command", "display another-custom"])
    assert found == []
    assert "display custom-command" in missing
    assert "display another-custom" in missing


def test_compare_mixed_commands():
    """Some found, some missing."""
    found, missing = compare_with_abbreviations(["display device", "display custom-command"])
    assert "display device" in found
    assert "display custom-command" in missing
    assert len(found) == 1
    assert len(missing) == 1


def test_directory_mode_combined_output(monkeypatch, tmp_path):
    """Directory mode accumulates all files into combined output."""
    import json

    # Setup temp base dir
    monkeypatch.setattr(sys, "argv", ["extract_commands.py"])
    monkeypatch.setattr(extract_commands_module, "_BASE_DIR", str(tmp_path))

    # Write config
    config = {
        "logs_dir": "logs",
        "output_dir": "out",
        "expand_abbreviations": False,
        "combine_output": True,
    }
    (tmp_path / "extract_commands_config.json").write_text(
        json.dumps(config), encoding="utf-8"
    )

    # Write abbreviations.json
    abb = {"abbreviations": {"display device": [], "display clock": []}}
    (tmp_path / "abbreviations.json").write_text(
        json.dumps(abb), encoding="utf-8"
    )

    # Write log files
    (tmp_path / "logs").mkdir()
    (tmp_path / "logs" / "log1.txt").write_text(
        "<R> display device\n", encoding="utf-8"
    )
    (tmp_path / "logs" / "log2.txt").write_text(
        "<R> display clock\n<R> display custom\n", encoding="utf-8"
    )

    # Run
    extract_commands_module.main()

    # Assert combined files
    all_cmds = (tmp_path / "out" / "all_commands.txt").read_text().splitlines()
    all_missing = (tmp_path / "out" / "all_missing.txt").read_text().splitlines()

    assert "display clock" in all_cmds
    assert "display device" in all_cmds
    assert "display custom" in all_cmds
    assert len(all_cmds) == 3  # deduplicated and sorted

    assert "display custom" in all_missing
    assert len(all_missing) == 1


def test_sanitize_command_removes_username():
    """Username tag is stripped before comparison."""
    from extract_commands import _sanitize_command_for_comparison
    assert _sanitize_command_for_comparison("display cpu-usage username kacha1") == "display cpu-usage"


def test_sanitize_command_removes_placeholder():
    """Placeholder tokens are stripped before comparison."""
    from extract_commands import _sanitize_command_for_comparison
    assert _sanitize_command_for_comparison("display startup xxx.zip") == "display startup"


def test_sanitize_command_removes_wildcard():
    """xxx.* wildcard is stripped before comparison."""
    from extract_commands import _sanitize_command_for_comparison
    assert _sanitize_command_for_comparison("display startup xxx.*") == "display startup"


def test_compare_with_abbreviations_sanitized():
    """Commands with username/placeholder are matched after sanitization."""
    found, missing = compare_with_abbreviations([
        "display device username kacha1",
        "display startup xxx.zip",
        "display custom-command",
    ])
    assert "display device username kacha1" in found
    assert "display startup xxx.zip" in found
    assert "display custom-command" in missing


def test_sanitize_local_user():
    """local-user tag is stripped."""
    from extract_commands import _sanitize_command_for_comparison
    assert _sanitize_command_for_comparison("display local-user kacha1") == "display"


def test_sanitize_file_extension():
    """File extension tokens are stripped."""
    from extract_commands import _sanitize_command_for_comparison
    assert _sanitize_command_for_comparison("startup saved-configuration backup.zip") == "startup saved-configuration"


def test_sanitize_interface():
    """Interface identifiers are stripped."""
    from extract_commands import _sanitize_command_for_comparison
    assert _sanitize_command_for_comparison("interface GigabitEthernet0/0/1") == "interface"


def test_sanitize_ip_address():
    """IP addresses are stripped."""
    from extract_commands import _sanitize_command_for_comparison
    assert _sanitize_command_for_comparison("ip address 192.168.1.1") == "ip address"


def test_sanitize_combined():
    """Multiple non-command tokens stripped together."""
    from extract_commands import _sanitize_command_for_comparison
    cmd = "local-user kacha1 startup saved-configuration backup.zip interface GigabitEthernet0/0/1"
    assert _sanitize_command_for_comparison(cmd) == "startup saved-configuration interface"


def test_sanitize_trailing_all():
    """Trailing 'all' is stripped."""
    from extract_commands import _sanitize_command_for_comparison
    assert _sanitize_command_for_comparison("silent-interface all") == "silent-interface"


def test_sanitize_trailing_number():
    """Trailing numbers are stripped."""
    from extract_commands import _sanitize_command_for_comparison
    assert _sanitize_command_for_comparison("ospf 1") == "ospf"
