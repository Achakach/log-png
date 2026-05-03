import shutil
import os

# Copy real PNGs to create proper mock error files
src_dir = 'screenshots'
dst_dir = 'test_error_scenario'

# Clean and recreate
dst_files = os.listdir(dst_dir)
for f in dst_files:
    os.remove(os.path.join(dst_dir, f))

# Copy clean files
shutil.copy(os.path.join(src_dir, 'TUC-TEST01 display device.png'), os.path.join(dst_dir, 'TUC-TEST01 display device.png'))
shutil.copy(os.path.join(src_dir, 'TUC-TEST02 display clock.png'), os.path.join(dst_dir, 'TUC-TEST02 display clock.png'))
shutil.copy(os.path.join(src_dir, 'TUC-TEST03 display device.png'), os.path.join(dst_dir, 'TUC-TEST03 display device.png'))
shutil.copy(os.path.join(src_dir, 'TUC-TEST03 display clock.png'), os.path.join(dst_dir, 'TUC-TEST03 display clock.png'))

# Copy as error files
shutil.copy(os.path.join(src_dir, 'TUC-TEST01 display device.png'), os.path.join(dst_dir, 'TUC-TEST01 display clock [error].png'))
shutil.copy(os.path.join(src_dir, 'TUC-TEST02 display clock.png'), os.path.join(dst_dir, 'TUC-TEST02 display device [error].png'))

print("Mock PNG files created successfully:")
for f in sorted(os.listdir(dst_dir)):
    print(f"  {f}")
