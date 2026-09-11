"""
Real-Time Machine Learning Anomaly Detection Service
Algorithm: Isolation Forest (Unsupervised Learning)

Why Unsupervised Learning:
  In real-world industrial IoT environments, ground truth anomaly labels are virtually nonexistent,
  costly to obtain, or highly delayed. Anomalies often represent novel equipment failure modes never
  seen during factory commissioning. Unsupervised Isolation Forest does not require labeled datasets.
  Instead, it operates on the mathematical premise that anomalies are 'few and different'. By randomly
  selecting features and partitioning values, outlier points become isolated at significantly shallower
  tree depths in the ensemble of isolation trees (iTrees) compared to nominal cluster points.

Features:
  - Temperature (°C)
  - Relative Humidity (%)
  - Atmospheric Pressure (hPa)

Outputs:
  - is_anomaly (bool)
  - status ("NORMAL" | "ANOMALY")
  - anomaly_score (normalized float 0.0 - 1.0, where >=0.6 indicates anomalous behavior)
  - raw_decision_score (float, Scikit-learn score_samples)
  - severity ("NORMAL" | "LOW" | "MEDIUM" | "HIGH" | "CRITICAL")
  - reason (diagnostic string)
"""

import os
import logging
import numpy as np
import joblib

logger = logging.getLogger("iot.ml")

class AnomalyDetector:
    def __init__(self, model_path: str = "backend/ml/isolation_forest_model.joblib"):
        self.model_path = model_path
        self.model = None
        self.is_loaded = False
        self.load_or_train()

    def load_or_train(self):
        """Loads trained Isolation Forest model or triggers automated on-the-fly training if missing."""
        try:
            if os.path.exists(self.model_path):
                self.model = joblib.load(self.model_path)
                self.is_loaded = True
                logger.info(f"Isolation Forest model loaded successfully from {self.model_path}")
            else:
                logger.warning(f"Model file '{self.model_path}' not found. Training baseline model...")
                from ml.train_model import train_and_export_model
                self.model = train_and_export_model(self.model_path)
                self.is_loaded = True
                logger.info("Fresh Isolation Forest model trained and loaded successfully.")
        except Exception as e:
            logger.error(f"Error loading Isolation Forest model: {e}. Activating heuristic fallback.", exc_info=True)
            self.model = None
            self.is_loaded = False

    def predict(self, temperature: float, humidity: float, pressure: float) -> dict:
        """
        Infers whether the telemetry vector represents normal operations or an anomaly.
        Returns:
            dict containing:
              - is_anomaly (bool)
              - status ("NORMAL" | "ANOMALY")
              - anomaly_score (float, scaled 0.0 to 1.0 where higher = more anomalous)
              - raw_decision_score (float)
              - severity ("NORMAL" | "LOW" | "MEDIUM" | "HIGH" | "CRITICAL")
              - reason (str)
        """
        # Hard limits for industrial safety sanity check (fail-safe heuristic layer)
        is_hard_anomaly = False
        hard_reasons = []

        if temperature < 10.0 or temperature > 60.0:
            is_hard_anomaly = True
            hard_reasons.append(f"Temperature {temperature:.1f}°C outside industrial boundary [10.0°C - 60.0°C]")
        if humidity < 20.0 or humidity > 85.0:
            is_hard_anomaly = True
            hard_reasons.append(f"Humidity {humidity:.1f}% outside safe limits [20.0% - 85.0%]")
        if pressure < 950.0 or pressure > 1050.0:
            is_hard_anomaly = True
            hard_reasons.append(f"Atmospheric Pressure {pressure:.1f} hPa outside safe operating range [950 - 1050 hPa]")

        raw_score = 0.0
        ml_is_anomaly = False

        if self.is_loaded and self.model is not None:
            try:
                features = np.array([[temperature, humidity, pressure]])
                # predict: 1 for inlier (normal), -1 for outlier (anomaly)
                pred = self.model.predict(features)[0]
                # score_samples: opposite of anomaly score; the lower, the more abnormal
                # typically ranges from ~ -0.30 (normal) down to -0.75 (extreme anomaly)
                raw_score = float(self.model.score_samples(features)[0])
                ml_is_anomaly = (pred == -1)
            except Exception as e:
                logger.error(f"ML inference error: {e}", exc_info=True)
                ml_is_anomaly = is_hard_anomaly
        else:
            ml_is_anomaly = is_hard_anomaly

        is_anomaly = ml_is_anomaly or is_hard_anomaly

        # Normalize score into intuitive [0.0 - 1.0] scale
        # For IsolationForest: score_samples in [-0.75, -0.30]
        # Normal samples are > -0.40 -> scaled score < 0.35
        # Anomalies are < -0.45 -> scaled score > 0.60
        if raw_score != 0.0:
            # Map [-0.30, -0.75] to [0.10, 0.99]
            normalized_score = np.clip((-(raw_score) - 0.30) / (0.75 - 0.30), 0.05, 0.99)
        else:
            normalized_score = 0.85 if is_anomaly else 0.15

        if is_hard_anomaly and normalized_score < 0.70:
            normalized_score = 0.85

        # Calculate Severity
        if not is_anomaly:
            severity = "NORMAL"
            status = "NORMAL"
            reason = "Operating parameters within nominal baseline."
        else:
            status = "ANOMALY"
            if normalized_score >= 0.85 or (temperature >= 85.0 or temperature <= 0.0 or pressure <= 880.0):
                severity = "CRITICAL"
            elif normalized_score >= 0.70 or (temperature >= 60.0 or humidity <= 15.0 or pressure <= 940.0):
                severity = "HIGH"
            elif normalized_score >= 0.50:
                severity = "MEDIUM"
            else:
                severity = "LOW"

            if hard_reasons:
                reason = " & ".join(hard_reasons)
            else:
                reason = f"Multivariate divergence detected by Isolation Forest (score: {normalized_score:.2f})"

        return {
            "is_anomaly": bool(is_anomaly),
            "status": status,
            "anomaly_score": round(float(normalized_score), 4),
            "raw_decision_score": round(float(raw_score), 4),
            "severity": severity,
            "reason": reason
        }

# Global singleton instance
ml_detector = AnomalyDetector()

# Explicit algorithmic alias for CI/CD pipeline and backwards compatibility
IsolationForestDetector = AnomalyDetector
