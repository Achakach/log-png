"""Excel subcommand runner (v2 only)."""
import subprocess
import sys

from HuaweiScreenshotTool_Unify.utils import get_sibling_exe


def run(args):
    print("[excel-v2] Running putpnginxlsx_v2.py...")
    result = subprocess.run(
        [get_sibling_exe("putpnginxlsx_v2"),],
    )
    sys.exit(result.returncode)
