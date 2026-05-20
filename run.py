"""Process all Huawei VRP log files from the logs/ folder into screenshots.

Configuration is read from run_config.json in the same directory.
If run_config.json is missing, a template will be auto-generated.

Whitelist behavior:
  - If whitelist is empty/null: all commands are processed (backward-compatible)
  - If whitelist has items: only matching commands (standalone or nested blocks
    containing at least one matching command) are rendered to PNG.
"""
import json
import os
import sys
import glob

import process_network_logs

def get_base_dir():
    """Get the directory where the .exe or .py script lives."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

SCRIPT_DIR = get_base_dir()
CONFIG_PATH = os.path.join(SCRIPT_DIR, "run_config.json")

_DEFAULT_CONFIG = {
    "logs_dir": "logs",
    "output_dir": "screenshots",
    "whitelist": [],
    "font_size": 6,
    "line_height": 1.3
}


def _ensure_config():
    """If run_config.json is missing, create a template and exit."""
    if os.path.exists(CONFIG_PATH):
        return
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(_DEFAULT_CONFIG, f, indent=2, ensure_ascii=False)
    print(f"Created template: {CONFIG_PATH}")
    print("Please edit it with your paths and whitelist, then run again.")
    sys.exit(0)


def load_config():
    """Read and validate run_config.json."""
    _ensure_config()
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    whitelist = cfg.get("whitelist") or []
    if not isinstance(whitelist, list):
        print("WARNING: 'whitelist' must be a list; using empty whitelist (process all commands).")
        whitelist = []

    # Normalize whitelist to lowercase for case-insensitive exact matching
    whitelist = [str(cmd).strip().lower() for cmd in whitelist if str(cmd).strip()]

    logs_dir = cfg.get("logs_dir", "logs")
    output_dir = cfg.get("output_dir", "screenshots")
    return logs_dir, output_dir, whitelist


def main():
    logs_dir_name, output_dir_name, whitelist = load_config()

    logs_dir = os.path.join(SCRIPT_DIR, logs_dir_name)
    output_dir = os.path.join(SCRIPT_DIR, output_dir_name)

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

    total = 0
    skipped = 0
    for log_path in log_files:
        with open(log_path, "r", encoding="utf-8") as f:
            content = f.read()
        print(f"\nProcessing {log_path} -> {output_dir}/...")
        results = process_network_logs.process_network_logs(
            content, output_dir=output_dir, whitelist=whitelist
        )
        total += len(results)
        # Count skipped by comparing grouped vs rendered
        print(f"  {len(results)} screenshots generated")

    whitelist_msg = f" (whitelist: {whitelist})" if whitelist else ""
    print(f"\n[DONE] {total} total screenshots from {len(log_files)} log file(s){whitelist_msg}")


if __name__ == "__main__":
    main()
