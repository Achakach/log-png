import re


def parse_display_alarm_active(output_text: str) -> list[dict]:
    """Parse `display alarm active` CLI output into structured alarm records.

    Each record: {sequence: str, alarm_id: str, severity: str, card_name: str}.
    Extracts EntPhysicalName from Description: 'EntPhysicalName=FAN slot 1/4' → 'FAN4'.
    Scans the entire output for alarm entries with EntPhysicalName.
    """
    alarms = []
    lines = output_text.splitlines()
    i = 0

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Look for alarm entry lines that start with a number (sequence)
        if not re.match(r'^\d+', stripped):
            i += 1
            continue

        # Parse alarm entry
        fields = stripped.split()
        if len(fields) < 4:
            i += 1
            continue

        sequence = fields[0]
        alarm_id = fields[1]
        severity = fields[2]

        # Collect description text (may span multiple lines)
        description = ' '.join(fields[4:]) if len(fields) > 4 else ''
        i += 1

        # Continue collecting continuation lines
        while i < len(lines):
            next_line = lines[i].strip()
            if not next_line or re.match(r'^\d+', next_line) or '---' in next_line:
                break
            description += ' ' + next_line
            i += 1

        # Extract card name from EntPhysicalName
        card_name = _extract_entphysical_name(description)
        if card_name:
            alarms.append({
                'sequence': sequence,
                'alarm_id': alarm_id,
                'severity': severity,
                'card_name': card_name,
            })

    return alarms


def _extract_entphysical_name(text: str) -> str:
    """Extract card name from EntPhysicalName in alarm description.

    Examples:
      'EntPhysicalName=FAN slot 1/3' → 'FAN3'
      'EntPhysicalName=PWR slot 1/1' → 'PWR1'
    Returns empty string if not found.
    """
    # Match EntPhysicalName=XXX slot 1/Y
    match = re.search(r'EntPhysicalName=(\w+)\s+slot\s+1/(\d+)', text)
    if match:
        base_name = match.group(1)
        slot_num = match.group(2)
        return f"{base_name}{slot_num}"

    # Fallback: EntPhysicalName=XXX without slot number
    match = re.search(r'EntPhysicalName=(\w+)', text)
    if match:
        return match.group(1)

    return ''


def compare_alarms(baseline: list[dict], current: list[dict]) -> list[str]:
    """Return card names present in current but not in baseline.

    Uses (alarm_id, card_name) as the unique key.
    Result is sorted alphabetically.
    """
    baseline_keys = {(a['alarm_id'], a['card_name']) for a in baseline}
    current_keys = {(a['alarm_id'], a['card_name']) for a in current}
    new_keys = current_keys - baseline_keys
    new_cards = sorted({k[1] for k in new_keys})
    return new_cards


def format_alarm_suffix(new_alarms: list[str]) -> str:
    """Convert list of new alarm card names into filename suffix.

    Examples:
      ['FAN3']      → '[FAN3]'
      ['FAN3', 'PWR1'] → '[FAN3 PWR1]'
    """
    if not new_alarms:
        return ''
    return f"[{' '.join(new_alarms)}]"
