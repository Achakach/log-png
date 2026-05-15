import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from process_network_logs import load_limits


def test_load_limits_defaults(monkeypatch):
    """When config file is missing, load_limits() returns default values."""
    original_exists = os.path.exists

    def mock_exists(path):
        if path == "run_config.json":
            return False
        return original_exists(path)

    monkeypatch.setattr(os.path, "exists", mock_exists)

    result = load_limits()
    assert result == {
        "max_line_length": 130,
        "max_output_lines": 70,
        "screenshot_width": 1000,
    }


def test_load_limits_custom(tmp_path):
    """When a valid custom config is provided, load_limits() returns custom values."""
    config = {
        "max_line_length": 150,
        "max_output_lines": 80,
        "screenshot_width": 1200,
    }
    config_file = tmp_path / "custom_config.json"
    config_file.write_text(json.dumps(config), encoding="utf-8")

    result = load_limits(config_path=str(config_file))
    assert result == {
        "max_line_length": 150,
        "max_output_lines": 80,
        "screenshot_width": 1200,
    }


def test_load_limits_invalid(tmp_path):
    """When config has invalid values, load_limits() falls back to defaults for ALL keys."""
    config = {
        "max_line_length": -50,
        "max_output_lines": "abc",
        "screenshot_width": 0,
    }
    config_file = tmp_path / "invalid_config.json"
    config_file.write_text(json.dumps(config), encoding="utf-8")

    result = load_limits(config_path=str(config_file))
    assert result == {
        "max_line_length": 130,
        "max_output_lines": 70,
        "screenshot_width": 1000,
    }


def test_load_limits_partial(tmp_path):
    """When config has only some keys, missing keys fall back to defaults."""
    config = {"max_line_length": 200}
    config_file = tmp_path / "partial_config.json"
    config_file.write_text(json.dumps(config), encoding="utf-8")

    result = load_limits(config_path=str(config_file))
    assert result == {
        "max_line_length": 200,
        "max_output_lines": 70,
        "screenshot_width": 1000,
    }
