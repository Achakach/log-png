"""Verify every subcommand delegates without hitting ``FileNotFoundError``.

In dev mode `get_sibling_exe` falls back to sibling ``.py`` scripts, so
``python -m HuaweiScreenshotTool_Unify <subcmd>`` should successfully *start*
each command module (we use ``--help`` to get a clean, non-interactive exit).
"""

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent
PACKAGE_NAME = "HuaweiScreenshotTool_Unify"

SUBCOMMANDS = [
    "process",
    "word",
    "excel",
    "extract",
    "stats",
    "gui",
]


@pytest.mark.parametrize("subcmd", SUBCOMMANDS)
def test_subcommand_delegates(subcmd):
    """Each subcommand should be reachable; FileNotFoundError means the sibling script is missing."""
    cmd = [sys.executable, "-m", PACKAGE_NAME, subcmd, "--help"]
    result = subprocess.run(
        cmd,
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
    )
    combined = result.stdout + result.stderr
    assert "FileNotFoundError" not in combined, (
        f"FileNotFoundError raised for subcommand '{subcmd}'"
    )
