"""Regression test: parallel (multi-worker) vs sequential processing equivalence.

Verifies that processing the same log files via two "workers" (batched calls
with different file subsets) produces the exact same screenshot filenames and
count as a single sequential run.
"""
import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import process_network_logs


# ── helpers ────────────────────────────────────────────────────────────────

def _make_log_content(device: str, num: int) -> str:
    """Minimal valid Huawei VRP log for one device."""
    return f"""<{device}>display version
Huawei Versatile Routing Platform Software
VRP (R) software, Version 8.150 (V800R012C00)
<{device}>display clock
2025-02-{num:02d} 10:00:00
Sunday
Time Zone(DefaultZoneName) : UTC
"""


def _make_nested_log_content(device: str, num: int) -> str:
    """Log with nested command block (system-view → interface → quit)."""
    return f"""<{device}>display version
Huawei Versatile Routing Platform Software
VRP (R) software, Version 8.150
<{device}>system-view
[{device}] interface GigabitEthernet0/0/1
[{device}-GigabitEthernet0/0/1] display this
#
interface GigabitEthernet0/0/1
 shutdown
#
return
[{device}-GigabitEthernet0/0/1] quit
[{device}] quit
<{device}>display clock
2025-02-{num:02d} 10:00:00
"""


def _create_log_files(tmp_path: Path, count: int = 10) -> list[Path]:
    """Create *count* test log files in *tmp_path*."""
    files = []
    for i in range(1, count + 1):
        device = f"HW-Reg-{i:02d}"
        content = _make_log_content(device, i)
        fpath = tmp_path / f"reg_{i:02d}.txt"
        fpath.write_text(content, encoding="utf-8")
        files.append(fpath)
    return files


def _filenames_from_results(results: list[dict]) -> set[str]:
    """Extract PNG basenames from a list of result dicts."""
    return {os.path.basename(r["screenshot_path"]) for r in results}


# ── tests ──────────────────────────────────────────────────────────────────

def test_parallel_vs_sequential_same_output(tmp_path: Path):
    """2-worker batched calls produce same screenshots as single sequential run."""
    process_network_logs.reset_caches()

    log_files = _create_log_files(tmp_path, count=10)

    # ── sequential: one call with all files ─────────────────────────────────
    file_list = [(lf.read_text(encoding="utf-8"), lf.name) for lf in log_files]
    seq_dir = tmp_path / "seq"
    seq_results = asyncio.run(
        process_network_logs.generate_screenshots_batched(
            file_list, str(seq_dir), whitelist=None, batch_size=25
        )
    )

    # ── "parallel": 2 workers = 2 batched calls on file subsets ─────────────
    par_dir = tmp_path / "par"
    half = len(file_list) // 2
    chunk_a = file_list[:half]
    chunk_b = file_list[half:]

    par_results = []
    for idx, chunk in enumerate([chunk_a, chunk_b]):
        res = asyncio.run(
            process_network_logs.generate_screenshots_batched(
                chunk, str(par_dir), whitelist=None,
                batch_size=25, worker_id=f"w{idx}"
            )
        )
        par_results.extend(res)

    # Merge per-worker truncated logs (mimics run.py's aggregate call)
    process_network_logs.aggregate_truncated_logs(str(par_dir))

    # ── assertions ──────────────────────────────────────────────────────────
    seq_names = _filenames_from_results(seq_results)
    par_names = _filenames_from_results(par_results)

    assert len(seq_results) == len(par_results), (
        f"Count mismatch: seq={len(seq_results)}, par={len(par_results)}"
    )
    assert seq_names == par_names, (
        f"Filename set mismatch.\n"
        f"  Only in sequential: {seq_names - par_names}\n"
        f"  Only in parallel:   {par_names - seq_names}"
    )


def test_nested_commands_parallel_consistency(tmp_path: Path):
    """Edge case: nested command logs give same results in both modes."""
    process_network_logs.reset_caches()

    # Create 4 log files with nested commands
    files_data: list[tuple[str, str]] = []
    for i in range(1, 5):
        device = f"HW-Nest-{i:02d}"
        content = _make_nested_log_content(device, i)
        fpath = tmp_path / f"nest_{i:02d}.txt"
        fpath.write_text(content, encoding="utf-8")
        files_data.append((content, fpath.name))

    # sequential
    seq_dir = tmp_path / "seq_nest"
    seq_results = asyncio.run(
        process_network_logs.generate_screenshots_batched(
            files_data, str(seq_dir), whitelist=None, batch_size=25
        )
    )

    # parallel (2 workers)
    par_dir = tmp_path / "par_nest"
    mid = len(files_data) // 2
    par_results = []
    for idx, chunk in enumerate([files_data[:mid], files_data[mid:]]):
        res = asyncio.run(
            process_network_logs.generate_screenshots_batched(
                chunk, str(par_dir), whitelist=None,
                batch_size=25, worker_id=f"n{idx}"
            )
        )
        par_results.extend(res)

    process_network_logs.aggregate_truncated_logs(str(par_dir))

    seq_names = _filenames_from_results(seq_results)
    par_names = _filenames_from_results(par_results)

    assert len(seq_results) == len(par_results), (
        f"Nested count mismatch: seq={len(seq_results)}, par={len(par_results)}"
    )
    assert seq_names == par_names, (
        f"Nested filename mismatch.\n"
        f"  Only seq: {seq_names - par_names}\n"
        f"  Only par: {par_names - seq_names}"
    )


def test_whitelist_filtering_parallel_consistency(tmp_path: Path):
    """Whitelist filtering produces same results in sequential and parallel modes."""
    process_network_logs.reset_caches()

    WHITELIST = ["display device"]

    # Create log files with mixed commands: "display device" (whitelisted)
    # and "display clock" (non-whitelisted), plus a nested block.
    files_data: list[tuple[str, str]] = []
    for i in range(1, 7):
        device = f"HW-WL-{i:02d}"
        content = f"""<{device}>display device
  Slot  Type             State    Subslot
  1     S12708          Normal   0
<{device}>display clock
  2025-02-{i:02d} 10:00:00
  Sunday
<{device}>display version
  VRP (R) software, Version 8.150
<{device}>system-view
[{device}] interface GigabitEthernet0/0/1
[{device}-GigabitEthernet0/0/1] display this
#
interface GigabitEthernet0/0/1
#
return
[{device}-GigabitEthernet0/0/1] quit
[{device}] quit
"""
        fpath = tmp_path / f"wl_{i:02d}.txt"
        fpath.write_text(content, encoding="utf-8")
        files_data.append((content, fpath.name))

    # ── sequential ──────────────────────────────────────────────────────
    seq_dir = tmp_path / "seq_wl"
    seq_results = asyncio.run(
        process_network_logs.generate_screenshots_batched(
            files_data, str(seq_dir), whitelist=WHITELIST, batch_size=25
        )
    )

    # ── parallel (2 workers) ────────────────────────────────────────────
    par_dir = tmp_path / "par_wl"
    mid = len(files_data) // 2
    par_results = []
    for idx, chunk in enumerate([files_data[:mid], files_data[mid:]]):
        res = asyncio.run(
            process_network_logs.generate_screenshots_batched(
                chunk, str(par_dir), whitelist=WHITELIST,
                batch_size=25, worker_id=f"wl{idx}"
            )
        )
        par_results.extend(res)

    process_network_logs.aggregate_truncated_logs(str(par_dir))

    # ── assertions ──────────────────────────────────────────────────────
    seq_names = _filenames_from_results(seq_results)
    par_names = _filenames_from_results(par_results)

    assert len(seq_results) == len(par_results), (
        f"Whitelist count mismatch: seq={len(seq_results)}, par={len(par_results)}"
    )
    assert seq_names == par_names, (
        f"Whitelist filename mismatch.\n"
        f"  Only seq: {seq_names - par_names}\n"
        f"  Only par: {par_names - seq_names}"
    )

    # Verify filtering: only whitelisted commands rendered
    assert len(seq_results) > 0, "Expected at least one whitelisted screenshot"
    whitelist_cmd = WHITELIST[0].lower()
    for name in seq_names:
        assert whitelist_cmd in name.lower(), (
            f"Non-whitelisted screenshot found: {name}"
        )

    # Verify non-whitelisted commands are excluded
    for name in seq_names:
        assert "display clock" not in name.lower(), (
            f"Non-whitelisted 'display clock' leaked into output: {name}"
        )
        assert "display version" not in name.lower(), (
            f"Non-whitelisted 'display version' leaked into output: {name}"
        )
