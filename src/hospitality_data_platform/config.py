from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
RAW = DATA / "raw"
BRONZE = DATA / "bronze"
SILVER = DATA / "silver"
GOLD = DATA / "gold"
ARTIFACTS = ROOT / "artifacts"
MODELS = ARTIFACTS / "models"
METRICS = ARTIFACTS / "metrics"
PREDICTIONS = ARTIFACTS / "predictions"
MONITORING = ARTIFACTS / "monitoring"
DB_PATH = ARTIFACTS / "hospitality_data_platform.sqlite"
SEED = 42

RUNTIME_DIRECTORIES = (
    RAW,
    BRONZE,
    SILVER,
    GOLD,
    MODELS,
    METRICS,
    PREDICTIONS,
    MONITORING,
)


def ensure_runtime_directories() -> None:
    """Create writable pipeline directories only for data and training execution.

    Importing application configuration must remain side-effect free so the scoring
    service can run with a read-only root filesystem.
    """

    for path in RUNTIME_DIRECTORIES:
        path.mkdir(parents=True, exist_ok=True)
