"""Stats subcommand: runs log_stats.py via subprocess."""

import subprocess
import sys

from HuaweiScreenshotTool_Unify.utils import get_sibling_exe


def run(args):
    print("[stats] Running log_stats.py...")

    cmd = [get_sibling_exe("log_stats")]
    if getattr(args, "devices", False):
        cmd.append("--devices")

    result = subprocess.run(cmd)
    sys.exit(result.returncode)
