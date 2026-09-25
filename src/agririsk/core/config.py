"""Configuration management for AgriRisk Kenya combining YAML files and Pydantic validation."""

from pathlib import Path
from typing import Any, Dict, Optional
import os
import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings

# Absolute path to repository root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent


class PathsConfig(BaseModel):
    """Path configuration within the repository."""
    data_dir: Path = Field(default_factory=lambda: PROJECT_ROOT / "data")
    raw_data_dir: Path = Field(default_factory=lambda: PROJECT_ROOT / "data" / "raw")
    processed_data_dir: Path = Field(default_factory=lambda: PROJECT_ROOT / "data" / "processed")
    fixtures_dir: Path = Field(default_factory=lambda: PROJECT_ROOT / "data" / "fixtures")
    models_dir: Path = Field(default_factory=lambda: PROJECT_ROOT / "artifacts" / "models")


class DatabaseConfig(BaseModel):
    """Database connection configuration."""
    url: str = "sqlite:///data/agririsk.db"
    echo_sql: bool = False


class ApiConfig(BaseModel):
    """FastAPI service settings."""
    host: str = "127.0.0.1"
    port: int = 8000
    title: str = "AgriRisk Kenya API"
    version: str = "v1"


class DashboardConfig(BaseModel):
    """Streamlit UI configuration."""
    port: int = 8501


class GeospatialConfig(BaseModel):
    """Geospatial boundary settings."""
    country_name: str = "Kenya"
    num_counties: int = 47
    default_crs: str = "EPSG:4326"


class ModelingConfig(BaseModel):
    """Machine learning modeling configuration."""
    random_seed: int = 42
    test_size_months: int = 6
    target_column: str = "ipc_phase"


def _deep_merge(target: Dict[str, Any], source: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively merge two dictionaries."""
    for key, value in source.items():
        if isinstance(value, dict) and key in target and isinstance(target[key], dict):
            target[key] = _deep_merge(target[key], value)
        else:
            target[key] = value
    return target


def load_yaml_config(env_name: Optional[str] = None) -> Dict[str, Any]:
    """Load base.yaml and merge with the environment-specific YAML configuration."""
    config_dir = PROJECT_ROOT / "config"
    base_file = config_dir / "base.yaml"

    config: Dict[str, Any] = {}
    if base_file.exists():
        with open(base_file, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f) or {}

    env = env_name or os.getenv("APP_ENV", "development")
    env_file = config_dir / f"{env}.yaml"
    if env_file.exists():
        with open(env_file, "r", encoding="utf-8") as f:
            env_config = yaml.safe_load(f) or {}
            config = _deep_merge(config, env_config)

    return config


class Settings(BaseSettings):
    """Root application settings class with typed schemas and environment variable support."""

    app_env: str = Field(default="development", alias="APP_ENV")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    # Project metadata
    project_name: str = "AgriRisk Kenya"
    version: str = "0.1.0"

    # Sub-configurations
    paths: PathsConfig = Field(default_factory=PathsConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    api: ApiConfig = Field(default_factory=ApiConfig)
    dashboard: DashboardConfig = Field(default_factory=DashboardConfig)
    geospatial: GeospatialConfig = Field(default_factory=GeospatialConfig)
    modeling: ModelingConfig = Field(default_factory=ModelingConfig)

    @classmethod
    def from_yaml_and_env(cls, env_name: Optional[str] = None) -> "Settings":
        """Instantiate settings from YAML files, then override with environment variables."""
        raw_config = load_yaml_config(env_name=env_name)

        # Allow environment variables to override values
        env = os.getenv("APP_ENV", raw_config.get("environment", "development"))
        log_level = os.getenv("LOG_LEVEL", raw_config.get("log_level", "INFO"))
        db_url = os.getenv("DATABASE_URL")
        api_host = os.getenv("API_HOST")
        api_port = os.getenv("API_PORT")

        paths_dict = raw_config.get("paths", {})
        db_dict = raw_config.get("database", {})
        if db_url:
            db_dict["url"] = db_url

        api_dict = raw_config.get("api", {})
        if api_host:
            api_dict["host"] = api_host
        if api_port:
            api_dict["port"] = int(api_port)

        dashboard_dict = raw_config.get("dashboard", {})
        geo_dict = raw_config.get("geospatial", {})
        modeling_dict = raw_config.get("modeling", {})

        # Resolve paths relative to PROJECT_ROOT if strings
        resolved_paths = PathsConfig(
            data_dir=PROJECT_ROOT / paths_dict.get("data_dir", "data"),
            raw_data_dir=PROJECT_ROOT / paths_dict.get("raw_data_dir", "data/raw"),
            processed_data_dir=PROJECT_ROOT / paths_dict.get("processed_data_dir", "data/processed"),
            fixtures_dir=PROJECT_ROOT / paths_dict.get("fixtures_dir", "data/fixtures"),
            models_dir=PROJECT_ROOT / paths_dict.get("models_dir", "artifacts/models"),
        )

        return cls(
            APP_ENV=env,
            LOG_LEVEL=log_level,
            project_name=raw_config.get("project", {}).get("name", "AgriRisk Kenya"),
            version=raw_config.get("project", {}).get("version", "0.1.0"),
            paths=resolved_paths,
            database=DatabaseConfig(**db_dict),
            api=ApiConfig(**api_dict),
            dashboard=DashboardConfig(**dashboard_dict),
            geospatial=GeospatialConfig(**geo_dict),
            modeling=ModelingConfig(**modeling_dict),
        )

    def ensure_directories(self) -> None:
        """Create necessary project runtime directories."""
        self.paths.data_dir.mkdir(parents=True, exist_ok=True)
        self.paths.raw_data_dir.mkdir(parents=True, exist_ok=True)
        self.paths.processed_data_dir.mkdir(parents=True, exist_ok=True)
        self.paths.fixtures_dir.mkdir(parents=True, exist_ok=True)
        self.paths.models_dir.mkdir(parents=True, exist_ok=True)


# Global settings singleton
settings = Settings.from_yaml_and_env()
settings.ensure_directories()
