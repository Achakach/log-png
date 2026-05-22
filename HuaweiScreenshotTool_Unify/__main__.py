"""Unified CLI entry point for Huawei Screenshot Tool.

Supports 6 subcommands:
  process, word, excel, extract, stats, gui

When run without arguments, shows an interactive numbered menu.
"""
import argparse
import os
import sys

repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

# Import command modules from our own package
from HuaweiScreenshotTool_Unify.commands import process, word, excel, extract, stats, gui

# Dispatch table: subcommand name -> callable(args)
SUBCOMMANDS = {
    "process": process.run,
    "word": word.run,
    "excel": excel.run,
    "extract": extract.run,
    "stats": stats.run,
    "gui": gui.run,
}


def _show_menu():
    print("Huawei Screenshot Tool")
    print("======================")
    print("1. Process logs -> screenshots")
    print("2. Insert into Word document")
    print("3. Insert into Excel")
    print("4. Extract commands from logs")
    print("5. Show log statistics")
    print("6. Launch GUI whitelist picker")
    print()


def _get_menu_choice():
    try:
        while True:
            choice = input("Select (1-6, or q to quit): ").strip().lower()
            if choice:
                return choice
    except EOFError:
        return "q"


def _pause():
    print()
    try:
        input("Press Enter to exit...")
    except EOFError:
        pass


def _dispatch(command_name, args):
    handler = SUBCOMMANDS.get(command_name)
    if handler is None:
        print(f"Unknown subcommand: {command_name}")
        sys.exit(1)
    handler(args)


def main():
    parser = argparse.ArgumentParser(
        prog="huawei-tool",
        description="Unified CLI for Huawei VRP log screenshot and document tools.",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    subparsers.add_parser("process", help="Process logs -> screenshots")
    subparsers.add_parser("word", help="Insert PNGs into Word document")
    subparsers.add_parser("excel", help="Insert PNGs into Excel")
    extract_parser = subparsers.add_parser("extract", help="Extract commands from logs")
    extract_parser.add_argument("file", nargs="?", default=None, help="Optional path to a single log file")
    stats_parser = subparsers.add_parser("stats", help="Show log statistics")
    stats_parser.add_argument("--devices", action="store_true", help="Show device breakdown per command")
    subparsers.add_parser("gui", help="Launch GUI whitelist picker")

    # If no arguments provided, show interactive menu instead of help+exit.
    if len(sys.argv) == 1:
        while True:
            _show_menu()
            choice = _get_menu_choice()
            if choice == "q":
                print("Goodbye.")
                _pause()
                break
            mapping = {
                "1": "process",
                "2": "word",
                "3": "excel",
                "4": "extract",
                "5": "stats",
                "6": "gui",
            }
            command_name = mapping.get(choice)
            if command_name is None:
                print("Invalid choice.")
                _pause()
                continue
            # Parse empty args for the selected command so flags have defaults
            args = parser.parse_args([command_name])
            _dispatch(command_name, args)
            _pause()
        return

    args = parser.parse_args()
    if args.command is None:
        parser.print_help()
        sys.exit(1)

    _dispatch(args.command, args)


if __name__ == "__main__":
    main()
