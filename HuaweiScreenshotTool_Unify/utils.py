import os
import sys


def get_sibling_exe(name: str) -> str:
    """Return the absolute path to a sibling executable/script.

    In frozen mode: look for `name.exe` next to `sys.executable`.
    In dev mode (non-frozen): first try `name.exe` next to `sys.executable`,
    then fall back to `name.py` in the repo root.
    If neither exists, raise FileNotFoundError with the searched directory.
    """
    exe_dir = os.path.dirname(os.path.realpath(sys.executable))
    sibling_exe = os.path.join(exe_dir, f"{name}.exe")
    if os.path.isfile(sibling_exe):
        return sibling_exe

    if not getattr(sys, "frozen", False):
        repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        py_script = os.path.join(repo_root, f"{name}.py")
        if os.path.isfile(py_script):
            return py_script

    searched = exe_dir if getattr(sys, "frozen", False) else f"{exe_dir} and {repo_root}"
    raise FileNotFoundError(
        f"Cannot find '{name}.exe' or '{name}.py' (searched in: {searched})"
    )


def get_repo_root():
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.realpath(sys.executable))
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
