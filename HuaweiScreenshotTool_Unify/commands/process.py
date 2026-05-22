"""Process subcommand: run run.py via subprocess."""
import subprocess
import sys

from HuaweiScreenshotTool_Unify.utils import get_sibling_exe


def run(args):
    print("[process] Running run.py...")
    result = subprocess.run(
        [get_sibling_exe("run")],
    )
    if result.returncode == 0:
        print("[process] Completed successfully.")
    else:
        print(f"[process] Completed with exit code {result.returncode}.")
    sys.exit(result.returncode)
