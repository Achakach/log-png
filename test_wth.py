import process_network_logs

with open("wth.txt", "r", encoding="utf-8") as f:
    content = f.read()

print("File length:", len(content))
print("First line:", repr(content.split("\n")[0]))

try:
    result = process_network_logs.process_network_logs(content, output_dir="screenshots")
    print(f"SUCCESS: Generated {len(result)} screenshots")
    for r in result:
        print(f"  {r['screenshot_path']}")
except Exception as e:
    print(f"ERROR: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
