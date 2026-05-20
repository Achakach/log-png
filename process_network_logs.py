import datetime
import json
import re
import asyncio
import os
import sys
import argparse
from jinja2 import Environment, select_autoescape
from playwright.async_api import async_playwright
from display_device_parser import parse_display_device, compare_devices, format_removed_suffix
from display_alarm_parser import parse_display_alarm_active, compare_alarms, format_alarm_suffix
from filename_utils import sanitize_filename


# --- Playwright browser path for frozen (.exe) mode ---
def _setup_playwright_browsers_path():
    """
    When running as a frozen .exe (PyInstaller or Nuitka), Playwright looks
    for browsers alongside the .exe. This function points it to bundled
    ms-playwright folder, or lets standard install/env var take over.
    """
    # PyInstaller sets sys.frozen; Nuitka sets __compiled__
    is_frozen = getattr(sys, 'frozen', False) or hasattr(sys, '__compiled__')
    if is_frozen:
        exe_path = os.path.abspath(sys.argv[0])
        exe_dir = os.path.dirname(exe_path)
        bundled_browser = os.path.join(exe_dir, 'ms-playwright')
        if os.path.isdir(bundled_browser):
            os.environ['PLAYWRIGHT_BROWSERS_PATH'] = bundled_browser
            return


_setup_playwright_browsers_path()

# --- Huawei VRP Error Detection ---
# Regex patterns that indicate the command output contains an error.
# Each pattern MUST match at the start of a line (after optional whitespace).
_ERROR_PATTERNS = [
    re.compile(r'^\s*Error:\s*', re.IGNORECASE),
    re.compile(r'^\s*%Error\s*', re.IGNORECASE),
    re.compile(r'^\s*Warning:\s*', re.IGNORECASE),
    re.compile(r'^\s*Unrecognized command', re.IGNORECASE),
    re.compile(r'^\s*Ambiguous command', re.IGNORECASE),
    re.compile(r'^\s*Incomplete command', re.IGNORECASE),
    re.compile(r'^\s*Wrong parameter', re.IGNORECASE),
    re.compile(r'^\s*Not enough privilege', re.IGNORECASE),
    re.compile(r'^\s*Failed to', re.IGNORECASE),
    re.compile(r'^\s*Not supported', re.IGNORECASE),
    re.compile(r'^\s*This command is', re.IGNORECASE),
]


# --- Output Limiting ---
# Maximum number of output lines to render per screenshot.
# Longer outputs are truncated silently (no marker in PNG).
# Full output is still saved to .log file for reference.
_DEFAULT_MAX_OUTPUT_LINES = 70


# Maximum characters per line before visual wrapping occurs.
# Lines exceeding this are truncated to _MAX_LINE_LENGTH to prevent tall PNGs.
_DEFAULT_MAX_LINE_LENGTH = 130


def load_limits(config_path: str = "run_config.json") -> dict:
    """Read screenshot limits from a JSON config file with fallback defaults.

    Parameters
    ----------
    config_path : str
        Path to the JSON config file. Defaults to "run_config.json".

    Returns
    -------
    dict
        Resolved values with keys:
        - max_line_length   (default: 130)
        - max_output_lines  (default: 70)
        - screenshot_width  (default: 1000)

    Invalid or missing keys print a WARNING and fall back to defaults.
    Missing file is silent (no warning) and uses defaults.
    """
    defaults = {
        "max_line_length": _DEFAULT_MAX_LINE_LENGTH,
        "max_output_lines": _DEFAULT_MAX_OUTPUT_LINES,
        "screenshot_width": 1000,
        "font_size": 6,
        "line_height": 1.3,
    }
    if not os.path.exists(config_path):
        return defaults

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            cfg = json.load(f)
    except Exception:
        print(f"WARNING: Failed to read {config_path}; using default limits.")
        return defaults

    resolved = {}
    for key, default in defaults.items():
        value = cfg.get(key, default)
        if key == "font_size":
            if isinstance(value, int) and value > 0:
                resolved[key] = value
            else:
                print(f"WARNING: Invalid value for '{key}' in {config_path} "
                      f"(got {value!r}, expected positive integer); using default {default}.")
                resolved[key] = default
        elif key == "line_height":
            if isinstance(value, (int, float)) and value > 0:
                resolved[key] = value
            else:
                print(f"WARNING: Invalid value for '{key}' in {config_path} "
                      f"(got {value!r}, expected positive number); using default {default}.")
                resolved[key] = default
        else:
            if isinstance(value, int) and value > 0:
                resolved[key] = value
            else:
                print(f"WARNING: Invalid value for '{key}' in {config_path} "
                      f"(got {value!r}, expected positive integer); using default {default}.")
                resolved[key] = default
    return resolved


def _has_error_in_output(output_text: str) -> bool:
    """Scan command output for Huawei VRP error/warning markers.

    Returns True if any line matches known error/warning patterns.
    """
    if not output_text:
        return False
    for line in output_text.splitlines():
        line = line.strip()
        if not line:
            continue
        for pattern in _ERROR_PATTERNS:
            if pattern.match(line):
                return True
    return False


# --- Username Extraction for SSH Sessions ---
_USERNAME_RE = re.compile(r'\busername\s*:\s*(\S+)', re.IGNORECASE)


def _extract_username(group: list[dict]) -> str | None:
    """Scan merged group output for username prompts.

    Looks for patterns like 'please input the username: kacha1',
    'Username: admin', etc. within the SSH session output.
    Returns the first username found, or None if not found.
    """
    for seg in group:
        output = seg.get('output', '')
        for line in output.splitlines():
            match = _USERNAME_RE.search(line.strip())
            if match:
                return match.group(1)
    return None


HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <style>
        body {
            background-color: transparent;
            margin: 0;
            padding: 20px;
        }
        #capture-area {
            background-color: #000000;
            padding: 20px;
            width: {{ screenshot_width }}px;
            max-width: {{ screenshot_width }}px;        /* ADD THIS LINE */
            box-sizing: border-box;
            font-family: 'Fira Code', 'Courier New', monospace;
            font-size: {{ font_size }}px;
            line-height: {{ line_height }};
            color: #ffffff;
            overflow-wrap: break-word;
            word-wrap: break-word;
        }
        .prompt {
            color: #ffffff;
        }
        .command {
            color: #ffffff;
        }
        .output {
            color: #ffffff;
            white-space: pre-wrap;
            overflow-wrap: break-word;
        }
    </style>
</head>
<body>
    <div id="capture-area">
{%- for b in blocks %}
<span class="prompt">{{ b.prompt }}</span> <span class="command">{{ b.command }}</span>
<div class="output">{{ b.output }}</div>
{%- endfor %}
</div>
</body>
</html>
"""


def _split_into_segments(log_content: str) -> list[dict]:
    """
    Parse raw log content into a flat list of segments.
    Each segment = {prompt, command, output} with raw (unescaped) values.

    Prompt patterns recognized:
      <RouterName>         — user view
      [RouterName]         — system view
      [RouterName-subview] — sub-view (interface, ospf, etc.)
    """
    # Match a line starting with a prompt (angle or square bracket),
    # followed by the command text on the rest of that line,
    # then everything up to the next prompt line (or end of input).
    prompt_re = re.compile(
        r'^(\u003c[A-Za-z][\w.\-]*\u003e|\[~?\*?[A-Za-z][\w.\-/]*\])[^\S\n\r]*(?!,)(.+)$',
        re.MULTILINE
    )

    positions = []
    for match in prompt_re.finditer(log_content):
        positions.append((match.start(), match.end(), match.group(1).strip(), match.group(2).strip()))

    if not positions:
        print("⚠ No Huawei VRP prompts found. The log format may not be Huawei VRP "
              "(expected <RouterName> or [RouterName] prompts). "
              "If this is a Cisco IOS log, it is not supported.")

    segments = []
    for idx, (start, end, prompt_raw, command_raw) in enumerate(positions):
        # Output = everything from end of this prompt line to start of next prompt line
        if idx + 1 < len(positions):
            output_raw = log_content[end:positions[idx + 1][0]]
        else:
            output_raw = log_content[end:]
        output_raw = output_raw.strip("\r\n").rstrip()

        segments.append({
            'prompt': prompt_raw,
            'command': command_raw,
            'output': output_raw,
        })

    return segments


def _prompt_depth(prompt: str) -> int:
    """Return nesting depth: user=0, system=1, sub=2+.

    Uses _extract_device_name() to find where the device name ends,
    then counts sub-view segments in the remainder.
    """
    if prompt.startswith('<') and prompt.endswith('>'):
        return 0
    if prompt.startswith('[') and prompt.endswith(']'):
        inner = prompt[1:-1]
        # Strip status indicators: ~ (unsaved config), * (alarm/fault)
        while inner and inner[0] in ('~', '*'):
            inner = inner[1:]
        device = _extract_device_name(prompt)
        if inner == device:
            return 1  # system view, no sub-view
        # Count sub-view segments by matching known keywords in the remainder
        remainder = inner[len(device):]  # e.g. "-ospf-1" or "-GigabitEthernet0/0/1"
        sub_keywords = ('ospf', 'GigabitEthernet', 'Loopback',
                        'Vlanif', 'bgp', 'isis', 'acl', 'vpn-instance', 'port-group')
        depth = 1
        pos = 0
        while pos < len(remainder):
            for kw in sub_keywords:
                kw_with_dash = f'-{kw}'
                if remainder[pos:].startswith(kw_with_dash):
                    depth += 1
                    pos += len(kw_with_dash)
                    # Skip past the rest of this sub-view token (e.g. "-1" or "0/0/1")
                    while pos < len(remainder) and remainder[pos] not in ('-', '['):
                        pos += 1
                    break
            else:
                pos += 1
        return depth
    return 0


def _group_segments(segments: list[dict], whitelist: list[str] | None = None) -> list[list[dict]]:
    """
    Group segments for screenshot generation based purely on prompt depth changes.

    Parameters
    ----------
    segments : list[dict]
        Raw segments from _split_into_segments.
    whitelist : list[str] | None
        If provided, non-whitelisted groups will NOT have truncation logging,
        preventing .log file creation for skipped commands.

    Rules:
      1. Each **standalone** command (prompt stays at same depth, no deeper
         commands follow) gets its own group → its own PNG.

      2. When a command causes the next segment's prompt to go **deeper**,
         it starts a **nested block** — that command and all subsequent segments
         until we return to depth 0 are one group → one PNG.
    """
    if not segments:
        return []

    groups = []
    current: list[dict] = []
    in_nested = False  # True when we're inside a nested block (depth > 0)

    for idx, seg in enumerate(segments):
        depth = _prompt_depth(seg['prompt'])
        # Look ahead: what's the next segment's depth?
        next_depth = _prompt_depth(segments[idx + 1]['prompt']) if idx + 1 < len(segments) else depth

        if in_nested:
            if depth == 0:
                # Returned to user view — nested block is done
                # Do NOT append this depth-0 segment to the block;
                # let it fall through to be processed as standalone/new block
                if current:
                    groups.append(_finalize_group(current, whitelist))
                current = []
                in_nested = False
                # Fall through to re-process this segment below
            else:
                # Still inside nested block — keep collecting
                current.append(seg)
                continue

        # Not in a nested block (at depth 0)
        if next_depth > depth:
            # Next command goes deeper → this command starts a nested block
            current.append(seg)
            in_nested = True
        else:
            # Next command stays at same depth → standalone command
            if current:
                groups.append(_finalize_group(current, whitelist))
            current = [seg]
            groups.append(_finalize_group(current, whitelist))
            current = []

    # Flush any incomplete nested block (e.g., log disconnect)
    if in_nested and current:
        groups.append(_finalize_group(current, whitelist))

    # Post-process: merge consecutive groups when previous block was ssh/stelnet
    # and current block is on a different device
    if groups:
        merged = []
        prev_group = groups[0]
        for i in range(1, len(groups)):
            curr_group = groups[i]
            prev_last_seg = prev_group[-1]
            curr_first_seg = curr_group[0]
            # Check if prev seg was stelnet/ssh/telnet session
            prev_cmd = prev_last_seg['command'].strip().lower()
            if prev_cmd.startswith(('stelnet', 'ssh', 'telnet')):
                # SSH session — merge with next group regardless of device
                prev_group = prev_group + curr_group
            else:
                merged.append(prev_group)
                prev_group = curr_group
        merged.append(prev_group)
        groups = merged

    return groups


def _command_matches_whitelist(command: str, whitelist: list[str]) -> bool:
    """Check if a command matches any entry in the whitelist (prefix, case-insensitive).

    Prefix matching allows users to whitelist a base command and automatically
    match all variations with arguments (e.g. 'stelnet' matches
    'stelnet 10.1.1.1', 'stelnet 20.20.20.20', etc.)"""
    if not whitelist:
        return True
    cmd_lower = command.strip().lower()
    return any(cmd_lower.startswith(wl.lower().strip()) for wl in whitelist)


def _group_matches_whitelist(group: list[dict], whitelist: list[str]) -> bool:
    """Check if the group matches the whitelist.

    - Standalone (1 command): match the command itself.
    - Nested block (>1 command): match by the ENTRY command (first command).
      This allows whitelisting all nested blocks via 'system-view' / 'system' / 'sys'.
    """
    if not whitelist:
        return True
    if not group:
        return False
    entry_cmd = group[0]['command'].strip().lower()
    if len(group) == 1:
        # Standalone: match the command itself (prefix matching)
        return _command_matches_whitelist(entry_cmd, whitelist)
    else:
        # Nested block: match by entry command (e.g. system-view) using prefix matching
        return _command_matches_whitelist(entry_cmd, whitelist)


def _filter_groups_by_whitelist(groups: list[list[dict]], whitelist: list[str]) -> list[list[dict]]:
    """Return only groups that contain at least one whitelisted command."""
    if not whitelist:
        return groups
    filtered = [g for g in groups if _group_matches_whitelist(g, whitelist)]
    skipped = len(groups) - len(filtered)
    if skipped > 0:
        print(f"  (skipped {skipped} non-whitelisted command group(s))")
    return filtered


_truncated_commands_log = []


def _should_truncate_and_log(group: list[dict], whitelist: list[str] | None) -> bool:
    """Return True if this group should have truncation logging enabled.

    When a whitelist is active, skip truncation logging for non-whitelisted
    groups so that no .log files are created for commands that will never
    be rendered to PNG.
    """
    if not whitelist:
        return True
    return _group_matches_whitelist(group, whitelist)


def _truncate_long_lines(group: list[dict]) -> None:
    """Truncate individual output lines that exceed max visual width.

    Prevents visual wrapping in screenshots by cutting lines at max_line_length.
    The .log file preserves the full output (original_output is captured before this runs).
    """
    limits = load_limits()
    max_line_length = limits['max_line_length']
    for seg in group:
        lines = seg['output'].split('\n')
        truncated = []
        for line in lines:
            if len(line) > max_line_length:
                line = line[:max_line_length]
            truncated.append(line)
        seg['output'] = '\n'.join(truncated)


def _finalize_group(group: list[dict], whitelist: list[str] | None = None) -> list[dict]:
    """Add sanitized filenames to a group of segments and optionally truncate long outputs."""
    do_log = _should_truncate_and_log(group, whitelist)
    limits = load_limits()
    max_output_lines = limits['max_output_lines']
    finalized = []
    for seg in group:
        original_output = seg['output']   # CAPTURE BEFORE TRUNCATION
        _truncate_long_lines([seg])        # TRUNCATE LONG LINES (mutates seg['output'])
        lines = seg['output'].splitlines()
        output = seg['output']
        if len(lines) > max_output_lines and do_log:
            remaining = len(lines) - max_output_lines
            _truncated_commands_log.append({
                'device': _extract_device_name(seg['prompt']),
                'command': seg['command'],
                'total_lines': len(lines),
                'kept_lines': max_output_lines,
                'omitted_lines': remaining,
                'full_output': original_output,   # LOGS THE TRULY ORIGINAL OUTPUT
            })
            lines = lines[:max_output_lines]
            output = '\n'.join(lines)
        finalized.append({
            'prompt': seg['prompt'],
            'prompt_raw': seg['prompt'],
            'router': sanitize_filename(seg['prompt']),
            'command': seg['command'],
            'output': output,
        })
    return finalized


def parse_log(log_content: str, whitelist: list[str] | None = None) -> list[list[dict]]:
    """
    Parse a network log file and return grouped segments.
    Each group represents a logical CLI session.

    Parameters
    ----------
    log_content : str
        Raw log text.
    whitelist : list[str] | None
        If provided, non-whitelisted groups will NOT have truncation logging.
    """
    raw_segments = _split_into_segments(log_content)
    if not raw_segments:
        return []
    return _group_segments(raw_segments, whitelist)


def _extract_device_name(prompt: str) -> str:
    """
    Extract the base device name from a prompt, stripping sub-view suffixes
    and the unsaved-config indicator (~).
    e.g. '<HW-Core-BKK-01>' → 'HW-Core-BKK-01'
         '[HW-Core-BKK-01]' → 'HW-Core-BKK-01'
         '[~HW-Core-BKK-01]' → 'HW-Core-BKK-01'
         '[HW-Core-BKK-01-ospf-1]' → 'HW-Core-BKK-01'
         '[HW-Core-BKK-01-GigabitEthernet0/0/1]' → 'HW-Core-BKK-01'
         '[~HW-Core-BKK-01]' → 'HW-Core-BKK-01'
         '[*HW-Core-BKK-01]' → 'HW-Core-BKK-01'
         '[CE-Leaf-01]' → 'CE-Leaf-01'
    """
    inner = prompt[1:-1]  # strip < > or [ ]
    # Strip status indicators: ~ (unsaved config), * (alarm/fault)
    while inner and inner[0] in ('~', '*'):
        inner = inner[1:]
    # Sub-view suffixes always start with a known keyword after the device name
    sub_keywords = ('ospf', 'GigabitEthernet', 'Loopback',
                    'Vlanif', 'bgp', 'isis', 'acl', 'vpn-instance', 'port-group')
    for kw in sub_keywords:
        # Find '-keyword' in the string — that's where the sub-view starts
        idx = inner.find(f'-{kw}')
        # Require at least 2 chars before the keyword to avoid false matches
        # (e.g. device name "Vlan-01" should not be split at "-Vlan")
        if idx > 2:
            return inner[:idx]
    # No sub-view keyword found → the whole thing is the device name
    return inner


async def generate_screenshots(grouped_segments: list[list[dict]], output_dir: str = ".") -> list[dict]:
    """Uses Jinja2 and Playwright to render HTML and capture element screenshots."""
    env = Environment(autoescape=select_autoescape(default=True))
    template = env.from_string(HTML_TEMPLATE)
    results = []

    os.makedirs(output_dir, exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={'width': 1200, 'height': 900})

        limits = load_limits()
        screenshot_width = limits['screenshot_width']

        try:
            # Per-NE baseline tracker for display device output
            # Stores {safe_device: {'cards': [...], 'filepath': '...'}}
            _device_baselines = {}
            # Per-NE baseline tracker for display alarm active output
            # Stores {safe_device: {'alarms': [...], 'filepath': '...'}}
            _alarm_baselines = {}
            removed_dir = os.path.normpath(os.path.join(output_dir, '..', 'removeddevicetest'))

            for idx, group in enumerate(grouped_segments):
                html_content = template.render(blocks=group, screenshot_width=screenshot_width, font_size=limits['font_size'], line_height=limits['line_height'])
                await page.set_content(html_content)
                element = await page.wait_for_selector('#capture-area')

                # For merged SSH groups, find the last display command as terminal command
                terminal_cmd = None
                for seg in reversed(group):
                    cmd_lower = seg['command'].strip().lower()
                    if cmd_lower.startswith(('dis', 'display')):
                        terminal_cmd = seg
                        break
                if not terminal_cmd:
                    terminal_cmd = group[0]

                first_cmd = group[0]
                # Use terminal command's device for the filename (not SSH source)
                device_name = _extract_device_name(terminal_cmd['prompt_raw'])
                safe_device = sanitize_filename(device_name)
                safe_first_cmd = sanitize_filename(first_cmd['command'])

                # Baseline tracking for display device
                removed_suffix = ''
                is_removed_case = False
                alarm_suffix = ''
                is_new_alarm_case = False
                if first_cmd['command'].strip().lower() == 'display device':
                    try:
                        parsed = parse_display_device(first_cmd['output'])
                        if parsed:
                            if safe_device not in _device_baselines:
                                # First occurrence → establish baseline
                                _device_baselines[safe_device] = {'cards': parsed, 'filepath': None}
                            else:
                                baseline = _device_baselines[safe_device]['cards']
                                missing = compare_devices(baseline, parsed)
                                if missing:
                                    removed_suffix = ' ' + format_removed_suffix(missing)
                                    is_removed_case = True
                    except Exception as e:
                        print(f"⚠ Failed to parse display device for {safe_device}: {e}")

                # Baseline tracking for display alarm active
                if first_cmd['command'].strip().lower() == 'display alarm active':
                    try:
                        parsed_alarms = parse_display_alarm_active(first_cmd['output'])
                        if safe_device not in _alarm_baselines:
                            # First occurrence → establish baseline
                            _alarm_baselines[safe_device] = {'alarms': parsed_alarms, 'filepath': None}
                        else:
                            baseline_alarms = _alarm_baselines[safe_device]['alarms']
                            new_alarms = compare_alarms(baseline_alarms, parsed_alarms)
                            if new_alarms:
                                alarm_suffix = ' ' + format_alarm_suffix(new_alarms)
                                is_new_alarm_case = True
                    except Exception as e:
                        print(f"⚠ Failed to parse display alarm active for {safe_device}: {e}")

                # --- Error detection ---
                # Scan the entire group for any command that returned an error
                has_error = any(
                    _has_error_in_output(seg['output'])
                    for seg in group
                )
                error_suffix = ' [error]' if has_error else ''

                # For merged groups where the first command is SSH/stelnet/telnet
                # and the terminal command is a display/dis command,
                # use only the terminal command for the filename.
                is_ssh_merged = (
                    first_cmd['command'].strip().lower().startswith(('stelnet', 'ssh', 'telnet'))
                    and terminal_cmd is not first_cmd
                )

                # Extract username from SSH session output (if any)
                username = None
                if is_ssh_merged:
                    username = _extract_username(group)
                username_suffix = f' username {username}' if username else ''

                if len(group) == 1:
                    # Standalone command: "HW-Core-BKK-01 display device.png"
                    filename_cmd = safe_first_cmd
                elif is_ssh_merged:
                    # Merged SSH session: use terminal display command for filename
                    filename_cmd = sanitize_filename(terminal_cmd['command'])
                else:
                    # Nested block: "HW-Core-BKK-01 system-view interface GE0_0_1 display this quit quit.png"
                    filename_cmd = " ".join(sanitize_filename(seg['command']) for seg in group)
                
                filename = f"{safe_device} {filename_cmd}{removed_suffix}{alarm_suffix}{username_suffix}{error_suffix}.png"
                filepath = os.path.join(output_dir, filename)

                await element.screenshot(path=filepath, type='png')
                print(f"[{idx+1}/{len(grouped_segments)}] Generated: {filepath} ({len(group)} cmds)")

                # If this is a removed case, copy baseline and save to removeddevicetest/
                if is_removed_case or is_new_alarm_case:
                    os.makedirs(removed_dir, exist_ok=True)

                if is_removed_case:
                    baseline_info = _device_baselines[safe_device]
                    baseline_filepath = baseline_info['filepath']
                    if baseline_filepath and os.path.exists(baseline_filepath):
                        baseline_basename = os.path.basename(baseline_filepath)
                        removed_baseline = os.path.join(removed_dir, baseline_basename)
                        if not os.path.exists(removed_baseline):
                            import shutil
                            shutil.copy2(baseline_filepath, removed_baseline)
                            print(f"  Copied baseline to: {removed_baseline}")

                    # Copy display alarm active if exists
                    alarm_filename = f"{safe_device} display alarm active.png"
                    alarm_filepath = os.path.join(output_dir, alarm_filename)
                    if os.path.exists(alarm_filepath):
                        alarm_basename = os.path.basename(alarm_filepath)
                        removed_alarm = os.path.join(removed_dir, alarm_basename)
                        if not os.path.exists(removed_alarm):
                            import shutil
                            shutil.copy2(alarm_filepath, removed_alarm)
                            print(f"  Copied alarm active to: {removed_alarm}")

                    removed_filename = filename
                    removed_filepath = os.path.join(removed_dir, removed_filename)
                    await element.screenshot(path=removed_filepath, type='png')
                    print(f"  Saved removed case to: {removed_filepath}")

                # If this is a new alarm case, copy baseline alarm and save to removeddevicetest/
                if is_new_alarm_case:
                    alarm_baseline_info = _alarm_baselines[safe_device]
                    alarm_baseline_filepath = alarm_baseline_info['filepath']
                    if alarm_baseline_filepath and os.path.exists(alarm_baseline_filepath):
                        alarm_baseline_basename = os.path.basename(alarm_baseline_filepath)
                        removed_alarm_baseline = os.path.join(removed_dir, alarm_baseline_basename)
                        if not os.path.exists(removed_alarm_baseline):
                            import shutil
                            shutil.copy2(alarm_baseline_filepath, removed_alarm_baseline)
                            print(f"  Copied alarm baseline to: {removed_alarm_baseline}")

                    alarm_removed_filename = filename
                    alarm_removed_filepath = os.path.join(removed_dir, alarm_removed_filename)
                    await element.screenshot(path=alarm_removed_filepath, type='png')
                    print(f"  Saved new alarm case to: {alarm_removed_filepath}")

                # Store filepath for baseline tracking
                if first_cmd['command'].strip().lower() == 'display device' and safe_device in _device_baselines:
                    if _device_baselines[safe_device]['filepath'] is None:
                        _device_baselines[safe_device]['filepath'] = filepath
                if first_cmd['command'].strip().lower() == 'display alarm active' and safe_device in _alarm_baselines:
                    if _alarm_baselines[safe_device]['filepath'] is None:
                        _alarm_baselines[safe_device]['filepath'] = filepath

                results.append({
                    'screenshot_path': filepath,
                    'commands_count': len(group),
                    'first_router': first_cmd['router'],
                    'first_command': first_cmd['command'],
                })
        finally:
            await browser.close()

        # Write truncated commands log if any were truncated
        _write_truncated_log(output_dir)

    return results


def _write_truncated_log(output_dir: str):
    """Write truncated commands to a text file and full-output .txt files if any exist."""
    global _truncated_commands_log
    if not _truncated_commands_log:
        return

    log_path = os.path.join(output_dir, 'truncated_commands.log')
    mode = 'a' if os.path.exists(log_path) else 'w'
    with open(log_path, mode, encoding='utf-8') as f:
        if mode == 'w':
            f.write("# Truncated Commands Log\n")
            f.write(f"# Started: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        for entry in _truncated_commands_log:
            f.write(f"{entry['device']} {entry['command']}\n")
            f.write(f"  Total lines: {entry['total_lines']}\n")
            f.write(f"  Kept lines: {entry['kept_lines']}\n")
            f.write(f"  Omitted lines: {entry['omitted_lines']}\n")
            f.write(f"  Output: {entry['device']} {entry['command']}.png\n")
            f.write("\n")
    print(f"\nTruncated commands log saved to: {log_path}")

    # Write individual .txt files with full output for each truncated command
    for entry in _truncated_commands_log:
        safe_device = sanitize_filename(entry['device'])
        safe_cmd = sanitize_filename(entry['command'])
        txt_filename = f"{safe_device} {safe_cmd}.log"
        txt_path = os.path.join(output_dir, txt_filename)
        with open(txt_path, 'w', encoding='utf-8') as f:
            device = entry['device']
            command = entry['command']
            f.write(f"<{device}>{command}\n")
            f.write(entry['full_output'])
        print(f"  Full output saved to: {txt_path}")

    _truncated_commands_log = []  # Clear after writing


def process_network_logs(log_content: str, output_dir: str = ".", whitelist: list[str] | None = None) -> list[dict]:
    """
    Main orchestration function to process the string content of a raw log file
    and output a list of dictionary segments with screenshot paths.

    Parameters
    ----------
    log_content : str
        Raw log text.
    output_dir : str
        Directory to write PNG screenshots.
    whitelist : list[str] | None
        If provided, only groups containing at least one of these commands
        (exact, case-insensitive match) will be rendered to PNG.
    """
    segments = parse_log(log_content, whitelist)
    if not segments:
        print("⚠ No segments found in log content.")
        return []

    # Apply whitelist filter before rendering
    if whitelist:
        segments = _filter_groups_by_whitelist(segments, whitelist)
        if not segments:
            print("⚠ No segments matched the whitelist.")
            return []

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        # Already inside an event loop (e.g. Jupyter) — create a new thread
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            future = pool.submit(asyncio.run, generate_screenshots(segments, output_dir))
            return future.result()
    else:
        return asyncio.run(generate_screenshots(segments, output_dir))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process Huawei network logs into screenshots")
    parser.add_argument("log_file", help="Path to the log file or directory containing .txt log files")
    parser.add_argument("-o", "--output-dir", default="screenshots", help="Output directory for screenshots")
    args = parser.parse_args()

    if not os.path.exists(args.log_file):
        print(f"❌ File not found: {args.log_file}")
        sys.exit(1)

    if os.path.isdir(args.log_file):
        # Batch mode: process all .txt files in the directory
        log_files = sorted(
            os.path.join(args.log_file, f)
            for f in os.listdir(args.log_file)
            if f.lower().endswith(('.txt', '.log')) and os.path.isfile(os.path.join(args.log_file, f))
        )
        if not log_files:
            print(f"⚠ No .txt or .log files found in {args.log_file}")
            sys.exit(1)

        total_results = []
        for log_path in log_files:
            with open(log_path, "r", encoding="utf-8") as f:
                content = f.read()
            print(f"\nProcessing {log_path} → {args.output_dir}/...")
            results = process_network_logs(content, output_dir=args.output_dir)
            total_results.extend(results)
            print(f"  {len(results)} screenshots generated")

        print(f"\n✅ Done! {len(total_results)} total screenshots across {len(log_files)} log files")
    else:
        # Single file mode: original behavior
        with open(args.log_file, "r", encoding="utf-8") as f:
            content = f.read()

        print(f"Processing {args.log_file}...")
        results = process_network_logs(content, output_dir=args.output_dir)
        print(f"\n✅ Done! {len(results)} screenshots generated in {args.output_dir}/")