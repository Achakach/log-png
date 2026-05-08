import process_network_logs
import os

# Simulate the actual error scenario:
# - display device elabel (nested block because [slot_1] looks like [Router])
# - output contains $[ArchivesInfo Version]
# - ends with <Router> to finalize the group

log_content = """<TUC-SNK61E01HWLEFBQ01-UPLEF21>display device elabel

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

<TUC-SNK61E01HWLEFBQ01-UPLEF21>display device
  Chassis  Slot  Board Type      Status  Type
  1        1     CE8850-32CQ-EI  Normal  Master"""

print("Testing sanitization with realistic device name + template placeholders")
print("-" * 60)

try:
    result = process_network_logs.process_network_logs(log_content, output_dir="screenshots")
    print(f"SUCCESS: Generated {len(result)} screenshot(s)")
    for r in result:
        print(f"  File: {os.path.basename(r['screenshot_path'])}")
        print(f"  Commands count: {r['commands_count']}")
except Exception as e:
    print(f"ERROR: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
