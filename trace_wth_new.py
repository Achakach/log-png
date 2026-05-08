import process_network_logs

with open("wth.txt", "r", encoding="utf-8") as f:
    content = f.read()

print("Tracing wth.txt with NEW regex (cross-line matching disabled):")
print("=" * 60)

try:
    result = process_network_logs.process_network_logs(content, output_dir="screenshots")
    print(f"SUCCESS: {len(result)} screenshot(s) generated")
    for r in result:
        print(f"  File: {r['screenshot_path']}")
        print(f"  First router: {r['first_router']}")
        print(f"  First command: {r['first_command']}")
        print(f"  Commands count: {r['commands_count']}")
except Exception as e:
    print(f"ERROR: {type(e).__name__}: {e}")

print()
print("Expected behavior with wth.txt:")
print("  Line 1: <TUCxx01>display device elabel")
print("    -> Matches as ONE standalone segment (depth 0)")
print("    -> Filename: TUCxx01 display device elabel.png")
print()
print("  Lines 2-22: [slot_1], [Board Properties], output text")
print("    -> TREATED AS OUTPUT TEXT for the segment")
print("    -> NOT parsed as prompts (regex now requires command on same line)")
print()
print("  Line 23: <TUCxx01>")
print("    -> No command after prompt -> IGNORED")
print()
print("  So [slot_1] no longer creates a false nested block.")
print("  Result: 1 clean PNG with all output text.")
