"""Verify the exact EOF disconnect bug scenario."""
import sys
sys.path.insert(0, '.')
from process_network_logs import _split_into_segments, _group_segments

# EXACT scenario user described:
# Nested block ending with prompt-only <HW> (NO trailing space)
# The regex skips the empty prompt, so last segment is [HW] quit at depth 1
log = """<HW> system-view
[HW] interface GE0/0/1
[HW-GE0/0/1] shutdown
[HW-GE0/0/1] quit
[HW] quit
<HW>
"""

print("=" * 70)
print("User's scenario: Nested block ends with prompt-only <HW> (no trailing space)")
print("=" * 70)
segs = _split_into_segments(log)
print(f"Segments found: {len(segs)}")
for i, s in enumerate(segs):
    depth = 0 if s['prompt'].startswith('<') else (2 if '-' in s['prompt'] else 1)
    print(f"  {i}: prompt={s['prompt']!r}, cmd={s['command']!r}, depth={depth}")

groups = _group_segments(segs)
print(f"\nGroups created: {len(groups)}")
for i, g in enumerate(groups):
    cmds = [s['command'] for s in g]
    print(f"  Group {i}: {cmds}")

print()
if len(groups) == 0:
    print("❌ BUG CONFIRMED: Nested block was DROPPED at EOF!")
    print("   Last segment [HW] quit at depth 1, no flush code exists.")
else:
    print("✅ Block was saved correctly.")
