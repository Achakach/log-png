# Create a test log with TUC-TEST01 device for Case 15 (long output truncation)
lines = ["<TUC-TEST01> display current-configuration"]
lines.append("  Current system configuration")
lines.append("")
for i in range(1, 101):
    lines.append(f"  interface GigabitEthernet0/0/{i}")
    lines.append(f"   port link-type trunk")
    lines.append(f"   port trunk allow-pass vlan 10 20 30")
    lines.append(f"   undo shutdown")
lines.append("")
lines.append("  # end of file")
lines.append("")
lines.append("<TUC-TEST01> display device")
lines.append("  Slot 1   FAN1   Present")

with open("logs/test_long_output2.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

print("Created: logs/test_long_output2.txt")
