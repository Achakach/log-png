"""Extract subcommand — delegates to extract_commands.py via subprocess."""
import subprocess
import sys

from HuaweiScreenshotTool_Unify.utils import get_sibling_exe


def run(args):
    cmd = [get_sibling_exe("extract_commands")]
    if getattr(args, "file", None):
        cmd.append(args.file)
    print("[extract] Running extract_commands.py...", flush=True)
    result = subprocess.run(cmd)
    sys.exit(result.returncode)

