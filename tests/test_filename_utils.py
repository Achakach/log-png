"""Tests for sanitize_filename from filename_utils."""
import sys
from pathlib import Path

# Add parent directory to path so we can import filename_utils
sys.path.insert(0, str(Path(__file__).parent.parent))

from filename_utils import sanitize_filename


def test_sanitize_basic():
    assert sanitize_filename('hello world') == 'hello world'


def test_sanitize_hash():
    assert sanitize_filename('display #test') == 'display _test'


def test_sanitize_multiple_hash():
    # ### → ___ → _ (collapsed) → '' (stripped) → 'unnamed'
    assert sanitize_filename('###') == 'unnamed'


def test_sanitize_slash():
    assert sanitize_filename('GE0/0/1') == 'GE0_0_1'


def test_sanitize_pipe():
    assert sanitize_filename('a|b') == 'a b'


def test_sanitize_empty():
    assert sanitize_filename('') == 'unnamed'


def test_sanitize_whitespace_only():
    assert sanitize_filename('   ') == 'unnamed'
