"""
extract_commands.py
===================
Extracts all commands from Huawei VRP log files and writes them as a simple
list (one command per line) to a .txt file. Optionally expands abbreviations.
Also compares extracted commands against abbreviations.json and reports missing
commands.

Configuration is read from extract_commands_config.json.
If the config file is missing, a template will be auto-generated.
"""

import json
import os
import sys

import re

# Ensure base dir is on path before importing process_network_logs
_BASE_DIR = None


def get_base_dir():
    """Get the directory where the .exe or .py script lives."""
    global _BASE_DIR
    if _BASE_DIR is not None:
        return _BASE_DIR
    if getattr(sys, 'frozen', False):
        _BASE_DIR = os.path.dirname(sys.executable)
    else:
        _BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    return _BASE_DIR


sys.path.insert(0, get_base_dir())
from process_network_logs import (
    _split_into_segments,
    _expand_abbreviation,
    _load_abbreviations,
)


CONFIG_FILENAME = "extract_commands_config.json"

_DEFAULT_CONFIG = {
    "logs_dir": "logs",
    "output_dir": "extracted_commands",
    "expand_abbreviations": True,
    "combine_output": True,
}


def get_config_path():
    return os.path.join(get_base_dir(), CONFIG_FILENAME)


def load_config():
    """Read config.json; return defaults if file missing."""
    cfg_path = get_config_path()
    if not os.path.exists(cfg_path):
        return dict(_DEFAULT_CONFIG)
    with open(cfg_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    # Merge defaults for any missing keys
    merged = dict(_DEFAULT_CONFIG)
    merged.update(cfg)
    return merged


def ensure_config():
    """If config.json is missing, create a template and exit."""
    cfg_path = get_config_path()
    if os.path.exists(cfg_path):
        return
    with open(cfg_path, "w", encoding="utf-8") as f:
        json.dump(_DEFAULT_CONFIG, f, indent=2, ensure_ascii=False)
    print(f"Created template: {cfg_path}")
    print("Please edit it with your paths, then run again.")
    sys.exit(0)


def extract_commands(log_content, expand_abbrevs=True):
    """Extract all commands from log content.

    Parameters
    ----------
    log_content : str
        Raw log text.
    expand_abbrevs : bool
        If True, expand abbreviations via _expand_abbreviation.

    Returns
    -------
    list[str]
        List of command strings (one per segment), empty commands filtered out.
    """
    segments = _split_into_segments(log_content)
    abbrev_list = _load_abbreviations() if expand_abbrevs else []
    commands = []
    for seg in segments:
        cmd = seg.get("command", "").strip()
        if cmd:
            if expand_abbrevs:
                cmd = _expand_abbreviation(cmd, abbrev_list)
            commands.append(cmd)
    return commands


def compare_with_abbreviations(commands):
    """Compare commands against the full commands in abbreviations.json.

    Commands are sanitized before comparison to remove placeholder tokens
    and username tags that are not part of the actual command vocabulary.
    """
    abb_path = os.path.join(get_base_dir(), "abbreviations.json")
    if not os.path.exists(abb_path):
        full_commands = set()
    else:
        with open(abb_path, "r", encoding="utf-8-sig") as f:
            data = json.load(f)
        full_commands = set(data.get("abbreviations", {}).keys())

    found = []
    missing = []
    for cmd in commands:
        sanitized = _sanitize_command_for_comparison(cmd)
        if sanitized in full_commands:
            found.append(cmd)  # report original command as found
        else:
            missing.append(cmd)  # report original command as missing
    return found, missing


# Pre-compiled regexes for token sanitization
_USERNAME_RE = re.compile(r'^username$', re.IGNORECASE)
_LOCAL_USER_RE = re.compile(r'^local-user$', re.IGNORECASE)
_FILE_EXT_RE = re.compile(r'\.(zip|cfg|txt|log|dat|xml|csv|json|bin)$', re.IGNORECASE)
_INTERFACE_RE = re.compile(
    r'^(GigabitEthernet\d+[_/]\d+[_/]\d+|Vlanif\d+|Loopback\d+|Eth-Trunk\d+|MEth\d+/\d+/\d+)$',
    re.IGNORECASE
)
_IP_RE = re.compile(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$')
_IP_PREFIX_RE = re.compile(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/\d{1,3}$')
_PLACEHOLDER_RE = re.compile(r'^xxx\.[\w*]+$')


def _sanitize_command_for_comparison(command: str) -> str:
    """Strip non-command tokens before comparing with abbreviations.json.
    
    Removes:
    - Username tags: "username kacha1"
    - Local-user tags: "local-user kacha1"
    - Placeholder tokens: "xxx.zip", "xxx.cfg", "xxx.*"
    - File extensions: "backup.zip", "config.cfg"
    - Interface identifiers: "GigabitEthernet0/0/1", "Vlanif100", "Loopback0"
    - IP addresses: "192.168.1.1", "10.0.0.1/24"
    
    - Trailing "all": "silent-interface all", "display device all"
    - Trailing numbers: "ospf 1", "bgp 100"
    
    Returns the cleaned command string.
    """
    tokens = command.split()
    cleaned = []
    skip_next = False
    for i, token in enumerate(tokens):
        if skip_next:
            skip_next = False
            continue
        
        # Skip username / local-user + value
        if _USERNAME_RE.match(token) or _LOCAL_USER_RE.match(token):
            if i + 1 < len(tokens):
                skip_next = True
            continue
        
        # Skip placeholder tokens
        if _PLACEHOLDER_RE.match(token):
            continue
        
        # Skip file extension tokens
        if _FILE_EXT_RE.search(token):
            continue
        
        # Skip interface identifiers
        if _INTERFACE_RE.match(token):
            continue
        
        # Skip IP addresses and IP/prefix
        if _IP_RE.match(token) or _IP_PREFIX_RE.match(token):
            continue
        
        cleaned.append(token)
    
    # Strip trailing "all" if present
    if cleaned and cleaned[-1].lower() == 'all':
        cleaned.pop()
    
    # Strip trailing pure numbers (process IDs, instance numbers)
    if cleaned and cleaned[-1].isdigit():
        cleaned.pop()
    
    # If stripping left us with nothing, but the original command was a
    # keyword+value pattern, return the keyword itself so it can match
    # abbreviations.json (e.g. "username" is a valid command).
    if not cleaned and tokens:
        first = tokens[0].lower()
        if first == 'username':
            return 'username'
        if first == 'local-user':
            return 'local-user'
    
    return ' '.join(cleaned)


def process_file_data(file_path, expand_abbrevs):
    """Extract commands from a single file and return (commands_list, found_list, missing_list).

    Does NOT write any files.
    """
    with open(file_path, "r", encoding="utf-8-sig") as f:
        log_content = f.read()

    commands = extract_commands(log_content, expand_abbrevs=expand_abbrevs)
    found, missing = compare_with_abbreviations(commands)
    return commands, found, missing


def process_file(file_path, output_dir, expand_abbrevs):
    """Process a single log file and write per-file outputs."""
    commands, found, missing = process_file_data(file_path, expand_abbrevs)

    base_name = os.path.splitext(os.path.basename(file_path))[0]
    os.makedirs(output_dir, exist_ok=True)

    # Write commands file
    commands_path = os.path.join(output_dir, f"{base_name}_commands.txt")
    with open(commands_path, "w", encoding="utf-8") as f:
        for cmd in commands:
            f.write(cmd + "\n")

    # Write missing file
    missing_path = os.path.join(output_dir, f"{base_name}_missing.txt")
    with open(missing_path, "w", encoding="utf-8") as f:
        for cmd in missing:
            f.write(cmd + "\n")

    print(f"\nProcessed: {file_path}")
    print(f"  Commands extracted: {len(commands)}")
    print(f"  Output: {commands_path}")

    print("\n=== Commands Found in abbreviations.json ===")
    for cmd in found:
        print(cmd)
    if not found:
        print("(none)")

    print("\n=== Commands NOT in abbreviations.json (Missing) ===")
    for cmd in missing:
        sanitized = _sanitize_command_for_comparison(cmd)
        if sanitized != cmd:
            print(f"{cmd}  (cleaned: {sanitized})")
        else:
            print(cmd)
    if not missing:
        print("(none)")

    return commands_path, missing_path


def main():
    ensure_config()
    cfg = load_config()

    logs_dir = cfg.get("logs_dir", "logs")
    output_dir = cfg.get("output_dir", "extracted_commands")
    expand_abbrevs = cfg.get("expand_abbreviations", True)

    # Resolve logs_dir relative to base_dir if not absolute
    if not os.path.isabs(logs_dir):
        logs_dir = os.path.join(get_base_dir(), logs_dir)
    if not os.path.isabs(output_dir):
        output_dir = os.path.join(get_base_dir(), output_dir)

    # Single file argument
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        if not os.path.exists(file_path):
            print(f"❌ File not found: {file_path}")
            sys.exit(1)
        process_file(file_path, output_dir, expand_abbrevs)
        return

    # Directory mode: walk recursively for .txt and .log
    processed = 0
    all_commands = []
    all_missing = []
    combine_output = cfg.get("combine_output", _DEFAULT_CONFIG["combine_output"])

    for root, _dirs, files in os.walk(logs_dir):
        for fname in files:
            if fname.lower().endswith((".txt", ".log")):
                file_path = os.path.join(root, fname)

                if combine_output:
                    # Accumulate data for combined output
                    commands, found, missing = process_file_data(file_path, expand_abbrevs)
                    all_commands.extend(commands)
                    all_missing.extend(missing)
                else:
                    # Per-file output (old behavior)
                    process_file(file_path, output_dir, expand_abbrevs)

                processed += 1

    if processed == 0:
        print(f"⚠ No .txt or .log files found in {logs_dir}")
        sys.exit(1)

    if combine_output:
        # Deduplicate and sort
        unique_commands = sorted(set(all_commands))
        unique_missing = sorted(set(all_missing))

        os.makedirs(output_dir, exist_ok=True)

        # Write combined files
        all_cmds_path = os.path.join(output_dir, "all_commands.txt")
        with open(all_cmds_path, "w", encoding="utf-8") as f:
            for cmd in unique_commands:
                f.write(cmd + "\n")

        all_missing_path = os.path.join(output_dir, "all_missing.txt")
        with open(all_missing_path, "w", encoding="utf-8") as f:
            for cmd in unique_missing:
                f.write(cmd + "\n")

        # Print summary report
        print(f"\n✅ Done! Processed {processed} file(s).")
        print(f"  Total unique commands: {len(unique_commands)}")
        print(f"  Total unique missing:  {len(unique_missing)}")
        print(f"  Combined output: {all_cmds_path}")
        print(f"  Combined missing: {all_missing_path}")
    else:
        print(f"\n✅ Done! Processed {processed} file(s). Output in {output_dir}/")


if __name__ == "__main__":
    main()
