import re

# Test strings showing the difference
# True/Expected = is the line a real Huawei VRP prompt+command?

test_strings = [
    ("<Router> display device", True),      # normal with space
    ("[Router]display device", True),        # no space
    ("[Router]  display device", True),      # multiple spaces
    ("<Router>display device", True),        # no space
    ("[slot_1]", False),                      # no command
    ("[Router]", False),                      # no command
    ("[Router]\ndisplay device", False),     # newline between prompt and command (INVALID)
]

old_re = re.compile(
    r'^(<[A-Za-z][\w.\-]*>|\[~?\*?[A-Za-z][\w.\-/]*\])\s*(.+)$',
    re.MULTILINE
)

print(f"{'Input':40s} | Old regex | Expected | Match?")
print("-" * 75)

for text, expected in test_strings:
    m = old_re.match(text)
    matched = m is not None
    status = "OK" if matched == expected else "WRONG"
    
    prompt = m.group(1) if m else "N/A"
    cmd = m.group(2) if m else "N/A"
    
    print(f"{text:40s} | {matched:4s}      | {expected:4s}     | {status}")
    if m:
        print(f"  -> Prompt: {prompt!r}, Command: {cmd!r}")

print()
print("=" * 75)
print("The problem: [slot_1] has no command after it.")
print("But \s* matches the newline, so (.+) grabs the NEXT line as 'command'.")
print("This is a FALSE POSITIVE.")
