"""Verify username matching behavior after dead-code removal in find_best_match."""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from putpnginword import find_best_match


# --- Username matching tests ---

def test_docx_has_username_png_has_same_username():
    """DOCX has 'username kacha1' + PNG has 'username kacha1' → match."""
    png_files = [
        'HW-Core-BKK-01 display cpu username kacha1.png',
        'HW-Core-BKK-01 display cpu username kacha2.png',
    ]
    result = find_best_match(
        'HW-Core-BKK-01',
        ['display', 'cpu', 'username', 'kacha1'],
        png_files
    )
    assert result is not None
    assert 'username kacha1' in result


def test_docx_has_username_png_no_username():
    """DOCX has 'username kacha1' + PNG has no username → skip (no match)."""
    png_files = [
        'HW-Core-BKK-01 display cpu.png',
    ]
    result = find_best_match(
        'HW-Core-BKK-01',
        ['display', 'cpu', 'username', 'kacha1'],
        png_files
    )
    assert result is None


def test_docx_no_username_png_has_username():
    """DOCX has no username + PNG has 'username kacha1' → skip (no match)."""
    png_files = [
        'HW-Core-BKK-01 display cpu username kacha1.png',
    ]
    result = find_best_match(
        'HW-Core-BKK-01',
        ['display', 'cpu'],
        png_files
    )
    assert result is None


def test_docx_no_username_png_no_username():
    """Both have no username → match normally."""
    png_files = [
        'HW-Core-BKK-01 display cpu.png',
    ]
    result = find_best_match(
        'HW-Core-BKK-01',
        ['display', 'cpu'],
        png_files
    )
    assert result is not None


def test_docx_username_mismatch_different_users():
    """DOCX 'username kacha1' + PNG 'username kacha2' → skip (no match)."""
    png_files = [
        'HW-Core-BKK-01 display cpu username kacha2.png',
    ]
    result = find_best_match(
        'HW-Core-BKK-01',
        ['display', 'cpu', 'username', 'kacha1'],
        png_files
    )
    assert result is None


# --- Error preference still works ---

def test_error_preference_with_username():
    """When prefer_error=True, error PNG wins even with username."""
    png_files = [
        'HW-Core-BKK-01 display cpu username kacha1 [error].png',
        'HW-Core-BKK-01 display cpu username kacha1.png',
    ]
    result = find_best_match(
        'HW-Core-BKK-01',
        ['display', 'cpu', 'username', 'kacha1'],
        png_files,
        prefer_error=True
    )
    assert result is not None
    assert '[error]' in result


def test_clean_preference_with_username():
    """When prefer_error=False (default), clean PNG wins."""
    png_files = [
        'HW-Core-BKK-01 display cpu username kacha1 [error].png',
        'HW-Core-BKK-01 display cpu username kacha1.png',
    ]
    result = find_best_match(
        'HW-Core-BKK-01',
        ['display', 'cpu', 'username', 'kacha1'],
        png_files,
        prefer_error=False
    )
    assert result is not None
    assert '[error]' not in result


# --- Tie-breaking: shorter filename still wins ---

def test_shorter_filename_preference_no_username():
    """Among clean PNGs, shorter filename wins."""
    png_files = [
        'HW-Core-BKK-01 display cpu [FAN3 removed].png',
        'HW-Core-BKK-01 display cpu.png',
    ]
    result = find_best_match(
        'HW-Core-BKK-01',
        ['display', 'cpu'],
        png_files
    )
    assert result is not None
    assert result.endswith('display cpu.png')


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
