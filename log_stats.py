"""
log_stats.py
============
Summarize commands found in Huawei VRP log files.

Usage
-----
    python log_stats.py

Reads all .txt/.log files from logs_dir (configured in run_config.json),
parses commands, and prints a frequency table with standalone vs nested counts.
"""

import json
import os
import sys
from collections import Counter, defaultdict

from process_network_logs import _split_into_segments, _prompt_depth


def get_base_dir():
    """Get the directory where the .exe or .py script lives."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

SCRIPT_DIR = get_base_dir()
CONFIG_PATH = os.path.join(SCRIPT_DIR, "run_config.json")


def load_config_path(key: str, default: str) -> str:
    """Read run_config.json if it exists, otherwise return default."""
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        return cfg.get(key, default)
    return default


def summarize_log(content: str) -> tuple[Counter, Counter, dict]:
    """
    Parse a log and count commands.

    Returns
    -------
    standalone : Counter
        Command -> count for standalone (single-command) groups.
    nested : Counter
        Command -> count for commands that appear inside nested blocks.
    devices : dict[str, set[str]]
        Command -> set of device names that ran this command.
    """
    segments = _split_into_segments(content)
    if not segments:
        return Counter(), Counter(), {}

    standalone = Counter()
    nested = Counter()
    devices = defaultdict(set)

    # Determine standalone vs nested purely by prompt depth:
    #   depth 0  -> standalone (system-view, display clock, stelnet, etc.)
    #   depth >0 -> nested (interface, display this, quit, etc.)
    for idx, seg in enumerate(segments):
        depth = _prompt_depth(seg['prompt'])

        cmd = seg['command'].strip()
        device = seg['prompt'].strip('[]<>')
        # Strip ~ and * prefixes
        while device and device[0] in ('~', '*'):
            device = device[1:]
        # Truncate at first sub-view keyword
        for kw in ('-ospf', '-GigabitEthernet', '-Loopback', '-Vlanif', '-bgp', '-isis', '-acl', '-vpn-instance', '-port-group'):
            if kw in device:
                device = device.split(kw)[0]
                break

        if depth > 0:
            nested[cmd] += 1
        else:
            standalone[cmd] += 1

        devices[cmd].add(device)

    return standalone, nested, devices


def main():
    logs_dir_name = load_config_path("logs_dir", "logs")
    logs_dir = os.path.join(SCRIPT_DIR, logs_dir_name)

    if not os.path.isdir(logs_dir):
        print(f"[ERROR] logs directory not found at {logs_dir}")
        sys.exit(1)

    log_files = sorted(
        os.path.join(logs_dir, f)
        for f in os.listdir(logs_dir)
        if f.lower().endswith(('.txt', '.log')) and os.path.isfile(os.path.join(logs_dir, f))
    )

    if not log_files:
        print(f"[WARN] No .txt or .log files found in {logs_dir}")
        sys.exit(1)

    total_standalone = Counter()
    total_nested = Counter()
    total_devices = defaultdict(set)

    for log_path in log_files:
        with open(log_path, "r", encoding="utf-8") as f:
            content = f.read()
        s, n, d = summarize_log(content)
        total_standalone.update(s)
        total_nested.update(n)
        for cmd, devs in d.items():
            total_devices[cmd].update(devs)

    # Merge and print
    all_cmds = sorted(set(total_standalone.keys()) | set(total_nested.keys()))

    print(f"\n{'=' * 80}")
    print(f"Log Summary: {len(log_files)} file(s) from {logs_dir}")
    print(f"{'=' * 80}\n")
    print(f"{'Command':<50} {'Standalone':>12} {'Nested':>10} {'Total':>8}")
    print("-" * 80)

    grand_standalone = 0
    grand_nested = 0
    for cmd in all_cmds:
        s = total_standalone.get(cmd, 0)
        n = total_nested.get(cmd, 0)
        t = s + n
        grand_standalone += s
        grand_nested += n
        print(f"{cmd:<50} {s:>12} {n:>10} {t:>8}")

    print("-" * 80)
    print(f"{'TOTAL':<50} {grand_standalone:>12} {grand_nested:>10} {grand_standalone + grand_nested:>8}")
    print(f"\nUnique commands: {len(all_cmds)}")
    print(f"Total command occurrences: {grand_standalone + grand_nested}")

    # Per-command device summary (if requested via flag)
    if "--devices" in sys.argv:
        print(f"\n{'=' * 80}")
        print("Device breakdown per command")
        print(f"{'=' * 80}\n")
        for cmd in all_cmds:
            devs = sorted(total_devices[cmd])
            print(f"{cmd}")
            print(f"  Devices ({len(devs)}): {', '.join(devs)}")


if __name__ == "__main__":
    main()
    if getattr(sys, 'frozen', False):
        # Pause when double-clicked as .exe so user can read output
        input("\n[Press Enter to close]")
