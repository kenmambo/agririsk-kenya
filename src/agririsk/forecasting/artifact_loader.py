"""Model artifact manager, schema validator, and fallback loader for AgriRisk Kenya."""

from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import json
import joblib
import pandas as pd
import numpy as np

from agririsk.core.config import settings, PROJECT_ROOT
from agririsk.core.logging import logger
from agririsk.version import MODEL_VERSION


class ModelArtifactError(Exception):
    """Raised when model artifacts cannot be loaded or validated."""
    pass


class ModelArtifactManager:
    """Manages loading, feature-schema validation, and fallback for serialized model artifacts."""

    def __init__(self, artifact_dir: Optional[Path] = None):
        self.artifact_dir = artifact_dir or (settings.paths.models_dir / "model_v1")
        self.model: Optional[Any] = None
        self.schema: Optional[Dict[str, Any]] = None
        self.metadata: Optional[Dict[str, Any]] = None
        self.threshold_config: Optional[Dict[str, Any]] = None
        self._is_loaded = False

    def load(self) -> "ModelArtifactManager":
        """Load model, metadata, schema, and threshold configs from artifact directory."""
        if not self.artifact_dir.exists():
            # Fall back to root models dir if model_v1 doesn't exist
            fallback_model = settings.paths.models_dir / "forecast_model_h1.joblib"
            if fallback_model.exists():
                logger.info("model_v1 not found, loading fallback root model %s", fallback_model)
                try:
                    self.model = joblib.load(fallback_model)
                    self._is_loaded = True
                    return self
                except Exception as e:
                    raise ModelArtifactError(f"Forecast unavailable because the model artefact could not be loaded: {e}") from e
            raise ModelArtifactError(f"Model artifact directory not found at: {self.artifact_dir}")

        model_path = self.artifact_dir / "model.joblib"
        schema_path = self.artifact_dir / "feature_schema.json"
        metadata_path = self.artifact_dir / "metadata.json"
        threshold_path = self.artifact_dir / "threshold.json"

        if not model_path.exists():
            raise ModelArtifactError(f"Forecast unavailable because the model artefact could not be loaded from {model_path}")

        try:
            self.model = joblib.load(model_path)
            if schema_path.exists():
                with open(schema_path, "r", encoding="utf-8") as f:
                    self.schema = json.load(f)
            if metadata_path.exists():
                with open(metadata_path, "r", encoding="utf-8") as f:
                    self.metadata = json.load(f)
            if threshold_path.exists():
                with open(threshold_path, "r", encoding="utf-8") as f:
                    self.threshold_config = json.load(f)

            self._is_loaded = True
            logger.info("Successfully loaded model artifact v1 from %s", self.artifact_dir)
            return self
        except Exception as e:
            logger.error("Failed to load model artifact: %s", str(e))
            raise ModelArtifactError(f"Forecast unavailable because the model artefact could not be loaded: {e}") from e

    def validate_features(self, df: pd.DataFrame) -> Tuple[bool, List[str]]:
        """Verify that incoming dataframe contains all required features matching model schema.
        
        Returns:
            Tuple of (is_valid, missing_features_list)
        """
        if self.schema is None:
            return True, []

        expected = self.schema.get("expected_features", [])
        missing = [f for f in expected if f not in df.columns]
        return len(missing) == 0, missing

    def predict_risk(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Perform calibrated inference with input schema validation."""
        if not self._is_loaded or self.model is None:
            self.load()

        is_valid, missing = self.validate_features(df)
        if not is_valid:
            raise ValueError(f"Input features do not match model schema. Missing columns: {missing}")

        probs = self.model.predict_proba(df)
        threshold = self.threshold_config.get("optimal_threshold", 0.50) if self.threshold_config else 0.50

        return {
            "model_version": self.metadata.get("model_version", MODEL_VERSION) if self.metadata else MODEL_VERSION,
            "probabilities": probs.tolist() if isinstance(probs, np.ndarray) else list(probs),
            "threshold": threshold,
        }
