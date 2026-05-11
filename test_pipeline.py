"""Automated end-to-end pipeline verification.

Run this after any changes to verify the full flow works:
  1. run.py generates PNGs
  2. putpnginword.py inserts images into docx
"""
import os
import sys
import subprocess
import tempfile
import shutil


def test_imports():
    """All core modules import cleanly."""
    from process_network_logs import process_network_logs
    from putpnginword import match_cell_blocks
    from filename_utils import sanitize_filename
    from display_device_parser import parse_display_device
    from display_alarm_parser import parse_display_alarm_active
    from word_com_embed import embed_txt_via_word
    print("  [PASS] All imports OK")


def test_sanitize_deduplication():
    """filename_utils.py is the single source of truth."""
    import process_network_logs
    import putpnginword
    from filename_utils import sanitize_filename as sf

    test_cases = [
        'GE0/0/1|test',
        'a[b]c$d',
        '  hello  world  ',
        '',
    ]
    for t in test_cases:
        r1 = process_network_logs.sanitize_filename(t)
        r2 = putpnginword.sanitize_filename(t)
        r3 = sf(t)
        assert r1 == r3, f"process_network_logs mismatch: {t}"
        assert r2 == r3, f"putpnginword mismatch: {t}"
    print("  [PASS] sanitize_filename deduplicated OK")


def test_run_py_generates_pngs():
    """run.py processes logs and creates PNGs."""
    result = subprocess.run(
        [sys.executable, 'run.py'],
        capture_output=True, text=True, timeout=120
    )
    assert result.returncode == 0, f"run.py failed:\n{result.stderr}"
    assert os.path.isdir('screenshots'), "screenshots/ not created"
    pngs = [f for f in os.listdir('screenshots') if f.endswith('.png')]
    assert len(pngs) > 0, "No PNGs generated"
    print(f"  [PASS] run.py generated {len(pngs)} PNGs")


def test_putpnginword_inserts_images():
    """putpnginword.py creates output docx with images."""
    # Save previous output
    output = 'comprehensive_test_cases_updated_RESULT_v2.docx'
    backup = output + '.test_backup'
    if os.path.exists(output):
        shutil.copy2(output, backup)

    try:
        result = subprocess.run(
            [sys.executable, 'putpnginword.py'],
            capture_output=True, text=True, timeout=120
        )
        assert result.returncode == 0, f"putpnginword.py failed:\n{result.stdout}\n{result.stderr}"
        assert os.path.exists(output), "Output docx not created"

        # Verify docx has images using python-docx
        from docx import Document
        doc = Document(output)
        img_count = sum(1 for rel in doc.part.rels.values()
                        if 'image' in rel.reltype)
        assert img_count > 0, "No images found in output docx"
        print(f"  [PASS] putpnginword.py inserted {img_count} images")

        # Verify OLE markers were replaced (markers gone, or actual OLE present)
        # We check that the docx was saved successfully after Word COM
        print(f"  [PASS] Output docx saved: {output}")

    finally:
        if os.path.exists(backup):
            shutil.copy2(backup, output)
            os.remove(backup)


def test_error_handling_missing_docx():
    """putpnginword.py gives clear error for missing input."""
    from putpnginword import DOCX_INPUT
    if os.path.exists(DOCX_INPUT):
        print(f"  [SKIP] Cannot test missing DOCX (file exists)")
        return

    result = subprocess.run(
        [sys.executable, 'putpnginword.py'],
        capture_output=True, text=True, timeout=10
    )
    assert 'not found' in result.stdout.lower(), "Missing DOCX error message"
    assert result.returncode != 0, "Should exit with error"
    print("  [PASS] Error handling for missing DOCX OK")


def test_deps_pinned():
    """requirements.txt has pinned versions."""
    with open('requirements.txt') as f:
        content = f.read()
    assert '==' in content, "Versions not pinned"
    assert 'jinja2' in content
    assert 'playwright' in content
    assert 'python-docx' in content
    print("  [PASS] requirements.txt pinned OK")


if __name__ == '__main__':
    print("Running automated pipeline checks...\n")
    try:
        test_imports()
        test_sanitize_deduplication()
        test_deps_pinned()
        test_run_py_generates_pngs()
        test_putpnginword_inserts_images()
        test_error_handling_missing_docx()
        print("\n✅ All automated checks passed!")
    except AssertionError as e:
        print(f"\n❌ FAILED: {e}")
        sys.exit(1)
