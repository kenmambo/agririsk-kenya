"""Central application, model, and dataset version definitions for AgriRisk Kenya."""

__version__ = "0.1.0"

APP_VERSION = __version__
MODEL_VERSION = "v1.0.0-rf-calibrated"
DATASET_VERSION = "2024.12-asal-v1"
RELEASE_DATE = "2026-09-25"
MINIMUM_PYTHON_VERSION = (3, 12)

# Semantic build metadata
BUILD_METADATA = {
    "app_name": "AgriRisk Kenya",
    "app_version": APP_VERSION,
    "model_version": MODEL_VERSION,
    "dataset_version": DATASET_VERSION,
    "release_date": RELEASE_DATE,
    "environment_default": "development",
    "license": "MIT",
    "repository": "https://github.com/kenmambo/agririsk-kenya"
}
