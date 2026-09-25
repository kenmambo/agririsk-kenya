"""Unit tests for configuration management."""

from pathlib import Path
from agririsk.core.config import Settings, load_yaml_config


def test_base_yaml_loading():
    """Verify that base.yaml is loaded with correct default values."""
    config = load_yaml_config()
    assert config["project"]["name"] == "AgriRisk Kenya"
    assert config["geospatial"]["num_counties"] == 47


def test_environment_override():
    """Verify that environment-specific settings override base settings."""
    test_config = load_yaml_config(env_name="test")
    assert test_config["environment"] == "test"
    assert test_config["database"]["url"] == "sqlite:///:memory:"


def test_settings_instantiation():
    """Verify typed Settings object attributes and directory paths."""
    settings = Settings.from_yaml_and_env(env_name="test")
    assert settings.project_name == "AgriRisk Kenya"
    assert settings.database.url == "sqlite:///:memory:"
    assert isinstance(settings.paths.data_dir, Path)
