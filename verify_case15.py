"""Verify Case 15 PNG details"""
from PIL import Image
import os

print("=== Case 15 PNG Verification ===")
print()

img_path = "screenshots/TUC-TEST01 display current-configuration.png"
img = Image.open(img_path)
print(f"File: {img_path}")
print(f"  Size: {img.size[0]}x{img.size[1]} pixels")
print(f"  Height: {img.size[1]/96:.1f} inches (at 96dpi)")
print(f"  Width: {img.size[0]/96:.1f} inches (at 96dpi)")
print(f"  Font: 12px, Line-height: 1.3")
print(f"  Max output lines: 70")
print(f"  Estimated displayed lines: ~{img.size[1]/(12*1.3):.0f}")
print()

# Check all new PNGs
print("=== All New PNGs (12px + 70 lines) ===")
for f in sorted(os.listdir("screenshots")):
    if f.endswith(".png"):
        img = Image.open(os.path.join("screenshots", f))
        h_inches = img.size[1] / 96
        print(f"  {f[:60]:60s} {img.size[0]}x{img.size[1]} ({h_inches:.1f}in)")
