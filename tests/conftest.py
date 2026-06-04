"""Pytest configuration — shared fixtures and markers."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
import process_network_logs


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (performance / integration)"
    )


@pytest.fixture(autouse=True)
def reset_caches():
    """Reset module-level caches before every test to avoid state leakage."""
    process_network_logs.reset_caches()
