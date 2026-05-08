import process_network_logs
import os

# Simulate a log where [slot_1] creates a false nested block
# and the output has $[ArchivesInfo Version] in it

log_content = """<TUCxx01>display device elabel

[slot_1]
/$[ArchivesInfo Version]
/$ArvhicesInfoVersion=3.0

[Board Properties]
asdasdas
asdasdad
asdadasd
asdasdas
sadasd
asdasd

[Board Properties]
asdasdsad
asdasdasda
asdadasd
asdasd
dasdasdasd

<TUCxx01>"""

print("Testing scenario: [slot_1] false prompt + board properties")
print("-" * 60)

try:
    result = process_network_logs.process_network_logs(log_content, output_dir="screenshots")
    print(f"Successfully generated {len(result)} screenshot(s)")
    for r in result:
        print(f"  {r['screenshot_path']}")
        print(f"    Commands: {r['commands_count']}")
        print(f"    First router: {r['first_router']}")
        print(f"    First command: {r['first_command']}")
except Exception as e:
    print(f"ERROR: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
