import process_network_logs
import os

# Same device SSH test: TUC-TEST01 -> TUC-TEST01
log_content = """<TUC-TEST01>stelnet 10.1.1.1
please input the username: admin
password:
banner
<TUC-TEST01>dis cur
!
sysname TUC-TEST01
#
return
<TUC-TEST01>"""

print("Same device SSH test:")
print("=" * 50)

result = process_network_logs.process_network_logs(log_content, output_dir="screenshots")
print(f"Generated {len(result)} screenshot(s):")
for r in result:
    print(f"  {os.path.basename(r['screenshot_path'])}")
    print(f"    Commands count: {r['commands_count']}")
    print(f"    First router: {r['first_router']}")
    print(f"    First command: {r['first_command']}")

# Now different device SSH for comparison
print()
print("Different device SSH test:")
print("=" * 50)

log_content2 = """<BORDER01>stelnet 10.1.1.1
please input the username: admin
password:
<TUC-TEST01>dis cur
!
sysname TUC-TEST01
#
return
<TUC-TEST01>"""

result2 = process_network_logs.process_network_logs(log_content2, output_dir="screenshots")
print(f"Generated {len(result2)} screenshot(s):")
for r in result2:
    print(f"  {os.path.basename(r['screenshot_path'])}")
    print(f"    Commands count: {r['commands_count']}")
    print(f"    First router: {r['first_router']}")
    print(f"    First command: {r['first_command']}")
