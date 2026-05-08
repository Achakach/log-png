import re

test_strings = [
    ("<Router> display device", True),      # Should match
    ("[Router]display device", True),           # Should match
    ("[Router]", False),                        # Should NOT match - no command
    ("[slot_1]", False),                        # Should NOT match - no command
]

old_re = re.compile(r'^(<\[A-Za-z][\w.\-]*>|\[~?\*?[A-Za-z][\w.\-/]*\])\s*(.+)$', re.MULTILINE)

print("Testing Old Regex:")
for text, expected in test_strings:
    m = old_re.match(text)
    matched = m is not None
    status = "OK" if matched == expected else "WRONG"
    if m:
        print(f"  '{text}' -> MATCHED (Prompt: {m.group(1)}, Command: {m.group(2)})")
    else:
        print(f"  '{text}' -> No match")
    print(f"     Expected: {expected}, Status: {status}")
    print()

print("=" * 70)
print("PROBLEM DEMONSTRATION with multiline text:")
print("=" * 70)

multiline_text = """<TUCxx01>display device elabel
[slot_1]
/$[ArvhicesInfo Version]"""

print("Text to parse:")
print(repr(multiline_text))
print()

matches = list(old_re.finditer(multiline_text))
print(f"Number of matches: {len(matches)}")
for i, m in enumerate(matches):
    print(f"\nMatch {i+1}:")
    print(f"  Full match: {m.group(0)!r}")
    print(f"  Position: {m.start()}-{m.end()}")
    print(f"  Prompt:   {m.group(1)!r}")
    print(f"  Command:  {m.group(2)!r}")
