from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger("preflight.rag.calibration")

DEFAULT_CALIBRATION: dict[str, float] = {
    "vector_threshold": 0.25,
    "fuzzy_threshold": 0.78,
    "confident_threshold": 0.75,
    "tier4_min_confidence": 0.70,
}

_CALIBRATION_FILE = Path("evals/calibration.json")


def get_calibrated_thresholds() -> dict[str, float]:
    """Load calibrated dynamic thresholds from evals/calibration.json, or return defaults.

    This replaces hardcoded thresholds with dynamically evaluated thresholds.
    """
    if _CALIBRATION_FILE.exists():
        try:
            data = json.loads(_CALIBRATION_FILE.read_text(encoding="utf-8"))
            return {
                "vector_threshold": float(data.get("vector_threshold", DEFAULT_CALIBRATION["vector_threshold"])),
                "fuzzy_threshold": float(data.get("fuzzy_threshold", DEFAULT_CALIBRATION["fuzzy_threshold"])),
                "confident_threshold": float(data.get("confident_threshold", DEFAULT_CALIBRATION["confident_threshold"])),
                "tier4_min_confidence": float(data.get("tier4_min_confidence", DEFAULT_CALIBRATION["tier4_min_confidence"])),
            }
        except Exception as exc:
            logger.warning("Failed to load calibration file '%s': %s. Using defaults.", _CALIBRATION_FILE, exc)

    return dict(DEFAULT_CALIBRATION)


def save_calibrated_thresholds(thresholds: dict[str, float]) -> None:
    """Save calibrated thresholds to evals/calibration.json."""
    _CALIBRATION_FILE.parent.mkdir(parents=True, exist_ok=True)
    _CALIBRATION_FILE.write_text(json.dumps(thresholds, indent=2), encoding="utf-8")
    logger.info("Saved calibrated thresholds to '%s': %s", _CALIBRATION_FILE, thresholds)
