import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from putpnginword import find_best_match


def test_prefer_non_error_over_error():
    """When both error and non-error PNGs exist, must choose non-error."""
    png_files = [
        'TUC-DEVICE1 display cpu [error].png',
        'TUC-DEVICE1 display cpu.png',
    ]
    result = find_best_match('TUC-DEVICE1', ['display', 'cpu'], png_files)
    assert result is not None
    assert '[error]' not in result


def test_prefer_shorter_non_error():
    """When both non-error PNGs exist, prefer shorter filename."""
    png_files = [
        'TUC-DEVICE1 display cpu [FAN3 removed].png',
        'TUC-DEVICE1 display cpu.png',
    ]
    result = find_best_match('TUC-DEVICE1', ['display', 'cpu'], png_files)
    assert result is not None
    assert result.endswith('display cpu.png')


def test_only_error_available():
    """If ONLY error PNG exists, skip insertion entirely."""
    png_files = [
        'TUC-DEVICE1 display cpu [error].png',
    ]
    result = find_best_match('TUC-DEVICE1', ['display', 'cpu'], png_files)
    assert result is not None  # find_best_match still finds it
    # But the main loop would skip because it's [error]
    # This is tested in integration in test_multi_block_preference.py


def test_error_suffix_not_accidental_match():
    """The [error] token should not interfere with command matching."""
    # Note: the filename tokens after '[error]' are 'quit' 'quit' 'display' etc
    # which do NOT match ['system-view', 'interface', 'GE0_0_1' ...]
    png_files = [
        'TUC-DEVICE1 system-view interface GE0_0_1 display this [error].png',
        'TUC-DEVICE1 system-view interface GE0_0_1 display this.png',
    ]
    result = find_best_match(
        'TUC-DEVICE1',
        ['system-view', 'interface', 'GE0_0_1', 'display', 'this'],
        png_files
    )
    assert result is not None
    assert '[error]' not in result


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
