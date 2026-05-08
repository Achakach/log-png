import re

with open("wth.txt", "r", encoding="utf-8") as f:
    content = f.read()

print("Content:")
print(repr(content[:100]))

prompt_re = re.compile(
    r'^(<[A-Za-z][\w.\-]*>|\[~?\*?[A-Za-z][\w.\-/]*\])\s*(.+)$',
    re.MULTILINE
)

matches = list(prompt_re.finditer(content))
print(f"\nFound {len(matches)} matches")
for m in matches:
    print(f"  Prompt: {m.group(1)!r}, Command: {m.group(2)!r}")
    print(f"  Match at {m.start()}-{m.end()}")
