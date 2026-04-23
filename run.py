"""Process all Huawei VRP log files from the logs/ folder into screenshots."""
import process_network_logs
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOGS_DIR = os.path.join(SCRIPT_DIR, "logs")
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "screenshots")


def main():
    if not os.path.isdir(LOGS_DIR):
        print(f"[ERROR] logs/ directory not found at {LOGS_DIR}")
        sys.exit(1)

    log_files = sorted(
        os.path.join(LOGS_DIR, f)
        for f in os.listdir(LOGS_DIR)
        if f.endswith('.txt') and os.path.isfile(os.path.join(LOGS_DIR, f))
    )

    if not log_files:
        print(f"[WARN] No .txt files found in {LOGS_DIR}")
        sys.exit(1)

    total = 0
    for log_path in log_files:
        with open(log_path, "r", encoding="utf-8") as f:
            content = f.read()
        print(f"\nProcessing {log_path} -> {OUTPUT_DIR}/...")
        results = process_network_logs.process_network_logs(content, output_dir=OUTPUT_DIR)
        total += len(results)
        print(f"  {len(results)} screenshots generated")

    print(f"\n[DONE] {total} total screenshots from {len(log_files)} log file(s)")


if __name__ == "__main__":
    main()