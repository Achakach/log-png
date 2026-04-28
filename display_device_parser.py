import re


def parse_display_device(output_text: str) -> list[dict]:
    """Parse `display device` CLI output into structured card records.

    Each record: {slot: str, card: str, type_: str}.
    Only lines inside the table (between dashed separators) are processed.
    The chassis line (card == '-') is included but typically ignored by callers.
    """
    cards = []
    current_slot = None
    in_table = False

    for line in output_text.splitlines():
        stripped = line.strip()

        # Detect separator / header start
        if '---' in stripped:
            in_table = True
            continue

        if not in_table:
            continue

        # Detect end-of-table: next dashed line
        if '---' in stripped:
            in_table = False
            continue

        if not stripped:
            continue

        # Split fields on whitespace/tabs
        fields = stripped.split()
        if not fields:
            continue

        # If first field is a number → main slot line
        if re.match(r'^\d+$', fields[0]):
            current_slot = fields[0]
            # e.g. 1  -  CE8855-32CQ4BQ  Present  On  Registered  Normal  Master
            card = fields[1] if len(fields) > 1 else '-'
            type_ = fields[2] if len(fields) > 2 else ''
            cards.append({'slot': current_slot, 'card': card, 'type_': type_})
        else:
            # Indented sub-card line, e.g. FAN1  FAN  Present  On  ...
            if current_slot is None:
                continue
            card = fields[0]
            type_ = fields[1] if len(fields) > 1 else ''
            cards.append({'slot': current_slot, 'card': card, 'type_': type_})

    return cards


def compare_devices(baseline: list[dict], current: list[dict]) -> list[str]:
    """Return card names present in baseline but absent in current.

    Uses (slot, card) as the unique key.
    Result is sorted alphabetically.
    """
    baseline_keys = {(c['slot'], c['card']) for c in baseline}
    current_keys = {(c['slot'], c['card']) for c in current}
    missing_keys = baseline_keys - current_keys
    # Return just the card name (e.g. 'FAN3'); if same card in multiple slots,
    # each slot is a separate entry, but we return unique card names.
    missing_cards = sorted({k[1] for k in missing_keys})
    return missing_cards


def format_removed_suffix(missing: list[str]) -> str:
    """Convert list of missing card names into filename suffix.

    Examples:
      ['FAN3']      -> '[FAN3 removed]'
      ['FAN3', 'PWR1'] -> '[FAN3 PWR1 removed]'
    """
    if not missing:
        return ''
    return f"[{' '.join(missing)} removed]"
