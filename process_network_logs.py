import re
import asyncio
import os
import sys
import argparse
from jinja2 import Environment, select_autoescape
from playwright.async_api import async_playwright
from display_device_parser import parse_display_device, compare_devices, format_removed_suffix
from display_alarm_parser import parse_display_alarm_active, compare_alarms, format_alarm_suffix

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
            width: 1000px;
            box-sizing: border-box;
            font-family: 'Fira Code', 'Courier New', monospace;
            line-height: 1.5;
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
        r'^(<[A-Za-z][\w.\-]*>|\[~?\*?[A-Za-z][\w.\-/]*\])\s+(.+)$',
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


def _group_segments(segments: list[dict]) -> list[list[dict]]:
    """
    Group segments for screenshot generation based purely on prompt depth changes.

    Rules:
      1. Each **standalone** command (prompt stays at same depth, no deeper
         commands follow) gets its own group → its own PNG.

      2. When a command causes the next segment's prompt to go **deeper**,
         it starts a **nested block** — that command and all subsequent segments
         until we return to depth 0 are one group → one PNG.

    Nested block boundaries:
      - **Start**: <Router> system-view (depth 0, next depth 1)
      - **End**: return to <Router> (depth 0). The depth-0 segment that
        ends the block falls through and starts its own group (standalone
        or new nested block).

    Depth levels:
      - <Router>           → depth 0 (user view)
      - [Router]           → depth 1 (system view)
      - [Router-subview]   → depth 2+ (sub-view)

    Example:
      <HW> display device       → standalone PNG (next prompt same depth)
      <HW> system-view          → starts nested block (next prompt goes deeper)
      [HW] interface GE0/0/1   → part of block (next prompt goes deeper)
      [HW-GE0/0/1] display this → part of block (next prompt same or shallower)
      [HW-GE0/0/1] quit        → part of block (next prompt goes shallower)
      [HW] quit                 → part of block (next prompt goes to depth 0)
      <HW> display clock        → standalone PNG (depth 0, ends previous block)
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
                    groups.append(_finalize_group(current))
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
                groups.append(_finalize_group(current))
            current = [seg]
            groups.append(_finalize_group(current))
            current = []

    # Finalize any remaining group
    if current:
        groups.append(_finalize_group(current))

    return groups


def _finalize_group(group: list[dict]) -> list[dict]:
    """Add sanitized filenames to a group of segments. HTML escaping is handled by Jinja2 autoescape."""
    finalized = []
    for seg in group:
        finalized.append({
            'prompt': seg['prompt'],
            'prompt_raw': seg['prompt'],
            'router': sanitize_filename(seg['prompt']),
            'command': seg['command'],
            'output': seg['output'],
        })
    return finalized


def parse_log(log_content: str) -> list[list[dict]]:
    """
    Parse a network log file and return grouped segments.
    Each group represents a logical CLI session.
    """
    raw_segments = _split_into_segments(log_content)
    if not raw_segments:
        return []
    return _group_segments(raw_segments)


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


def sanitize_filename(name: str, max_length: int = 200) -> str:
    """Replaces invalid filename characters (but not spaces or hyphens) with underscores.
    Returns 'unnamed' if the result would be empty. Truncates to max_length."""
    result = re.sub(r'[\\/:*?"<>\n\r\t]', '_', name)
    result = result.replace('|', ' ')
    if not result.strip():
        return 'unnamed'
    return result[:max_length]


async def generate_screenshots(grouped_segments: list[list[dict]], output_dir: str = ".") -> list[dict]:
    """Uses Jinja2 and Playwright to render HTML and capture element screenshots."""
    env = Environment(autoescape=select_autoescape(default=True))
    template = env.from_string(HTML_TEMPLATE)
    results = []

    os.makedirs(output_dir, exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={'width': 1200, 'height': 900})

        try:
            # Per-NE baseline tracker for display device output
            # Stores {safe_device: {'cards': [...], 'filepath': '...'}}
            _device_baselines = {}
            # Per-NE baseline tracker for display alarm active output
            # Stores {safe_device: {'alarms': [...], 'filepath': '...'}}
            _alarm_baselines = {}
            removed_dir = os.path.normpath(os.path.join(output_dir, '..', 'removeddevicetest'))

            for idx, group in enumerate(grouped_segments):
                html_content = template.render(blocks=group)
                await page.set_content(html_content)
                element = await page.wait_for_selector('#capture-area')

                first_cmd = group[0]
                device_name = _extract_device_name(first_cmd['prompt_raw'])
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

                if len(group) == 1:
                    # Standalone command: "HW-Core-BKK-01 display device.png"
                    filename = f"{safe_device} {safe_first_cmd}{removed_suffix}{alarm_suffix}.png"
                else:
                    # Nested block: "HW-Core-BKK-01 system-view interface GE0_0_1 display this quit quit.png"
                    safe_cmds = " ".join(sanitize_filename(seg['command']) for seg in group)
                    filename = f"{safe_device} {safe_cmds}{removed_suffix}{alarm_suffix}.png"
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

    return results


def process_network_logs(log_content: str, output_dir: str = ".") -> list[dict]:
    """
    Main orchestration function to process the string content of a raw log file
    and output a list of dictionary segments with screenshot paths.
    """
    segments = parse_log(log_content)
    if not segments:
        print("⚠ No segments found in log content.")
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
            if f.endswith('.txt') and os.path.isfile(os.path.join(args.log_file, f))
        )
        if not log_files:
            print(f"⚠ No .txt files found in {args.log_file}")
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