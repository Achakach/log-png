#!/usr/bin/env python
"""Test [FAN2 removed] case with various whitelists."""
import os
import tempfile
import shutil

import process_network_logs

TEST_LOG = """\
<HW-Core-BKK-01> display device
CE8855-32CQ4BQ'S Device status:
---
Slot    Card    Type          		Online   Power Register   Alarm   Primary
---
1       -       CE8855-32CQ4BQ 		Present	 On    Registered Normal  Master
	FAN1	FAN			Present  On    Registered Normal  NA
	FAN2	FAN			Present  On    Registered Normal  NA
---

<HW-Core-BKK-01> display device
CE8855-32CQ4BQ'S Device status:
---
Slot    Card    Type          		Online   Power Register   Alarm   Primary
---
1       -       CE8855-32CQ4BQ 		Present	 On    Registered Normal  Master
	FAN1	FAN			Present  On    Registered Normal  NA
---

<HW-Core-BKK-01> display clock
  2026-04-07 21:15:30+07:00
  Tuesday
"""


def run_scenario(name, whitelist):
    """Run a single scenario and report results."""
    print(f"\n{'=' * 60}")
    print(f"Scenario: {name}")
    print(f"Whitelist: {whitelist!r}")
    print(f"{'=' * 60}")

    tmpdir = tempfile.mkdtemp(prefix="test_removed_")
    removed_dir = os.path.join(os.path.dirname(tmpdir), "removeddevicetest")
    try:
        results = process_network_logs.process_network_logs(
            TEST_LOG, output_dir=tmpdir, whitelist=whitelist
        )
        print(f"  Generated: {len(results)} screenshot(s)")
        for r in results:
            # results is list[dict] from generate_screenshots
            for key in r:
                print(f"    - {key}: {r[key]}")

        # Check temp dir for PNGs
        png_files = sorted(os.listdir(tmpdir)) if os.path.exists(tmpdir) else []
        png_files = [f for f in png_files if f.endswith('.png')]
        print(f"  PNGs in output dir: {png_files}")

        # Check removeddevicetest
        if os.path.isdir(removed_dir):
            removed_files = sorted(os.listdir(removed_dir))
            removed_files = [f for f in removed_files if f.endswith('.png')]
            print(f"  PNGs in removeddevicetest/: {removed_files}")
        else:
            print(f"  removeddevicetest/: (not created)")
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
        shutil.rmtree(removed_dir, ignore_errors=True)


if __name__ == "__main__":
    print("Testing [FAN2 removed] behavior with different whitelists...")

    # A: Whitelist includes display device -> baseline + removed case
    run_scenario("A: whitelist=['display device']", ["display device"])

    # B: Whitelist excludes display device -> skip everything
    run_scenario("B: whitelist=['display clock']", ["display clock"])

    # C: Empty whitelist -> process all (backward compatible)
    run_scenario("C: whitelist=[]", [])

    print("\n✅ All scenarios completed!")
