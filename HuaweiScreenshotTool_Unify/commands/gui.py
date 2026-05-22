"""GUI subcommand.

Launches whitelist_gui.py via subprocess.
Blocks until the GUI closes (tkinter mainloop behavior).
"""
import subprocess
import sys

from HuaweiScreenshotTool_Unify.utils import get_sibling_exe


def run(args):
    print("[gui] Launching whitelist_gui.py...")
    result = subprocess.run(
        [get_sibling_exe("whitelist_gui")],
    )
    sys.exit(result.returncode)
