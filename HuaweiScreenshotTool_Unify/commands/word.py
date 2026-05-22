"""Word subcommand: delegates to putpnginword.py via subprocess."""

import subprocess
import sys

from HuaweiScreenshotTool_Unify.utils import get_sibling_exe


def run(args):
    print("[word] Running putpnginword.py...")
    result = subprocess.run(
        [get_sibling_exe("putpnginword"),],
    )
    if result.returncode == 0:
        print("[word] putpnginword.py completed successfully.")
    else:
        print(f"[word] putpnginword.py exited with code {result.returncode}.")
    sys.exit(result.returncode)
