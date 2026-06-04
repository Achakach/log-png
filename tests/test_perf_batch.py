"""Performance test: batched vs sequential screenshot generation.

Verifies that ``generate_screenshots_batched()`` is faster than calling
``process_network_logs()`` per file sequentially, and that batch processing
stays under 30 seconds for 10 small log files.
"""
import asyncio
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
import process_network_logs


# ── helpers ────────────────────────────────────────────────────────────────

def _make_log_content(device: str, num: int) -> str:
    """Minimal valid Huawei VRP log for a single device."""
    return f"""<{device}>display version
Huawei Versatile Routing Platform Software
VRP (R) software, Version 8.150 (V800R012C00)
Copyright (C) 2000-2025 Huawei Technologies Co., Ltd.
<{device}>display clock
2025-02-{num:02d} 10:00:00
Sunday
Time Zone(DefaultZoneName) : UTC
<{device}>display device
Slot  Card   Type                     Online   Power Register     Status
--------------------------------------------------------------------------------
1     -      MCUD                      Present  On    Registered   Normal
2     -      -                         Present  On    Registered   Normal
"""


def _create_log_files(tmp_path: Path, count: int = 10) -> list[Path]:
    """Create *count* test log files, return their paths."""
    files = []
    for i in range(1, count + 1):
        device = f"HW-Test-{i:02d}"
        content = _make_log_content(device, i)
        fpath = tmp_path / f"test_{i:02d}.txt"
        fpath.write_text(content, encoding="utf-8")
        files.append(fpath)
    return files


# ── slow test ──────────────────────────────────────────────────────────────

@pytest.mark.slow
def test_batched_is_faster_than_sequential(tmp_path: Path):
    """Batch (size=5) must be at least 20% faster than per-file sequential."""
    process_network_logs.reset_caches()

    log_files = _create_log_files(tmp_path, count=10)
    batched_dir = tmp_path / "batched"
    seq_dir = tmp_path / "sequential"

    # ── batched run ──────────────────────────────────────────────────────────
    file_list = []
    for lf in log_files:
        file_list.append((lf.read_text(encoding="utf-8"), lf.name))

    t0 = time.perf_counter()
    batched_results = asyncio.run(
        process_network_logs.generate_screenshots_batched(
            file_list, str(batched_dir), whitelist=None, batch_size=5
        )
    )
    batched_time = time.perf_counter() - t0

    # ── sequential run ───────────────────────────────────────────────────────
    t0 = time.perf_counter()
    sequential_results = []
    for lf in log_files:
        content = lf.read_text(encoding="utf-8")
        res = process_network_logs.process_network_logs(
            content, output_dir=str(seq_dir), whitelist=None
        )
        sequential_results.extend(res)
    sequential_time = time.perf_counter() - t0

    # ── assertions ───────────────────────────────────────────────────────────
    assert batched_time < 30, f"Batched too slow: {batched_time:.1f}s (limit 30s)"
    assert batched_time < sequential_time * 0.8, (
        f"Batched ({batched_time:.1f}s) not 20% faster than sequential "
        f"({sequential_time:.1f}s)"
    )
    assert len(batched_results) == len(sequential_results), (
        f"Count mismatch: batched={len(batched_results)} vs seq={len(sequential_results)}"
    )
