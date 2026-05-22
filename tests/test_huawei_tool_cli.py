"""Pytest suite for the unified HuaweiScreenshotTool_Unify CLI wrapper.

Tests use subprocess invocation for realistic CLI behaviour.
"""
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent
PACKAGE_NAME = "HuaweiScreenshotTool_Unify"


def _run_cli(args, input_text=None, cwd=None):
    """Run the unified CLI via ``python -m HuaweiScreenshotTool_Unify <args>``."""
    cmd = [sys.executable, "-m", PACKAGE_NAME] + args
    return subprocess.run(
        cmd,
        cwd=cwd or str(REPO_ROOT),
        capture_output=True,
        text=True,
        input=input_text,
    )


# ── 1. Help output ──

def test_help_prints_all_subcommands():
    """``--help`` must list all 6 supported subcommands."""
    result = _run_cli(["--help"])
    assert result.returncode == 0
    stdout = result.stdout
    for name in (
        "process",
        "word",
        "excel",
        "extract",
        "stats",
        "gui",
    ):
        assert name in stdout, f"Subcommand '{name}' missing from --help"


def test_process_help_prints_process_specific_help():
    """``process --help`` should contain process-specific usage text."""
    result = _run_cli(["process", "--help"])
    assert result.returncode == 0
    text = result.stdout.lower()
    assert "process" in text


# ── 2. Invalid input ──

def test_invalid_subcommand_returns_nonzero():
    """An unknown subcommand must exit with a non-zero code."""
    result = _run_cli(["nonexistent-subcommand"])
    assert result.returncode != 0
    combined = result.stdout + result.stderr
    assert (
        "nonexistent" in combined.lower()
        or "invalid" in combined.lower()
        or "unrecognized" in combined.lower()
    )


# ── 3. Build smoke test ──

def test_build_smoke():
    """Building the unified EXE via PyInstaller should succeed and create dist/huawei-tool.exe."""
    result = subprocess.run(
        ["pyinstaller", "--clean", "-y", str(REPO_ROOT / "HuaweiScreenshotTool_Unify.spec")],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        timeout=300,
    )
    assert result.returncode == 0, f"PyInstaller failed:\n{result.stderr}"
    exe_path = REPO_ROOT / "dist" / "huawei-tool.exe"
    assert exe_path.exists(), f"Expected EXE not found: {exe_path}"


# ── 4. Frozen EXE help ──

@pytest.mark.skipif(not os.path.exists(str(REPO_ROOT / "dist" / "huawei-tool.exe")),
                    reason="dist/huawei-tool.exe not built yet")
def test_help_from_frozen_exe():
    """``dist/huawei-tool.exe --help`` should print the help text and include all 6 subcommands."""
    exe_path = REPO_ROOT / "dist" / "huawei-tool.exe"
    result = subprocess.run(
        [str(exe_path), "--help"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    combined = result.stdout + result.stderr
    for name in ("process", "word", "excel", "extract", "stats", "gui"):
        assert name in combined, f"Subcommand '{name}' missing from frozen --help"


# ── 5. Interactive menu ──

def test_menu_display_no_args():
    """Running with no arguments shows the numbered menu."""
    result = _run_cli([], input_text="")
    assert result.returncode == 0
    stdout = result.stdout
    assert "Huawei Screenshot Tool" in stdout
    assert "1." in stdout
    assert "6." in stdout


def test_menu_quit():
    """Piping ``q`` should print ``Goodbye.`` and exit cleanly."""
    result = _run_cli([], input_text="q\n")
    assert result.returncode == 0
    assert "Goodbye." in result.stdout


def test_menu_invalid_choice():
    """An invalid menu choice prints ``Invalid choice.`` and returns to the menu."""
    result = _run_cli([], input_text="99\nq\n")
    assert result.returncode == 0
    assert "Invalid choice." in result.stdout
    assert "Goodbye." in result.stdout


# ── 5. Dispatch internals ──

def test_dispatch_unknown_command_exits():
    """``_dispatch`` with an unregistered name must call ``sys.exit(1)``."""
    sys.path.insert(0, str(REPO_ROOT))
    from HuaweiScreenshotTool_Unify.__main__ import _dispatch

    with pytest.raises(SystemExit) as exc_info:
        _dispatch("not-a-command", None)
    assert exc_info.value.code == 1
