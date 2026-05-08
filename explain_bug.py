"""
Regex Problem Demonstration
===========================

The regex: r'^(<[A-Za-z][\w.\-]*>|\[~?\*?[A-Za-z][\w.\-/]*\])\s*(.+)$'
What it SHOULD match (Huawei VRP): [Router]display device

What happens with [slot_1] in wth.txt:

TEXT (3 separate lines):
  Line 1: [slot_1]
  Line 2: /$[ArvhicesInfo Version]
  Line 3: /$ArvhicesInfoVersion=3.0

REGEX ENGINE:
1. Position at start of line: "[slot_1]"
2. Match prompt: "[slot_1]" ✓
3. Match \s*: Matches the \n after "[slot_1]" ← THIS IS THE BUG
4. Match (.+): Grabs "ArvhicesInfo Version]" from line 2
5. Match $: End of line 2

RESULT: False prompt match
  Prompt: "[slot_1]"
  Command: "/$[ArvhicesInfo Version]"

WHY IT'S A BUG:
In a real Huawei VRP log, prompt and command are on the SAME line:
  [Router]display device    ← both on one line
  
In wth.txt:
  [slot_1]                    ← standalone, NO command
                              ← \n here
  /$[ArvhicesInfo Version]    ← this is OUTPUT, not a command

\s* should NOT match \n between prompt and command.
Command must be on the same line.

THE FIX:
Change \s* to [^\S\n\r]* (spaces/tabs only, no newlines)
This forces command to be on the SAME line as the prompt.
"""

import re

print("=" * 60)
print("EXPLANATION: Why [slot_1] false-matches")
print("=" * 60)

# Visualize what the regex sees
multiline_text = """[slot_1]
/$[ArvhicesInfo Version]
/$ArvhicesInfoVersion=3.0"""

print("\nTEXT STRUCTURE:")
print("Line 1: [slot_1]")
print("Line 2: /$[ArvhicesInfo Version]")
print("Line 3: /$ArvhicesInfoVersion=3.0")

print("\nREGEX MATCH:")
old_re = re.compile(
    r'^(<[A-Za-z][\w.\-]*>|\[~?\*?[A-Za-z][\w.\-/]*\])\s*(.+)$',
    re.MULTILINE
)

matches = list(old_re.finditer(multiline_text))
print(f"Found {len(matches)} matches (should be 0):")

for m in matches:
    print(f"  Match: {m.group(0)!r}")
    print(f"    Prompt:   {m.group(1)!r}")
    print(f"    Command:  {m.group(2)!r}")
    print(f"    Span:     lines {m.string[:m.start()].count(chr(10))+1}-"
          f"{m.string[:m.end()].count(chr(10))+1}")

print("\n" + "=" * 60)
print("FIXED REGEX (\s* -> [^\S\n\r]*):")
print("=" * 60)

new_re = re.compile(
    r'^(<[A-Za-z][\w.\-]*>|\[~?\*?[A-Za-z][\w.\-/]*\])[^\S\n\r]*(.+)$',
    re.MULTILINE
)

matches = list(new_re.finditer(multiline_text))
print(f"Found {len(matches)} matches (should be 0):")

print("\n" + "=" * 60)
print("REAL VRP EXAMPLE (should still match):")
print("=" * 60)

real_vrp = """[Router]display device
   Chassis  Slot  Board Type  Status
   1        0     CE8850      Normal
<Router>display device
   Chassis  Slot  Board Type  Status
   1        0     CE8850      Normal"""

matches = list(new_re.finditer(real_vrp))
print(f"Found {len(matches)} matches:")
for m in matches:
    print(f"  {m.group(1)!r} -> {m.group(2)!r}")
