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

for path in [RAW, BRONZE, SILVER, GOLD, MODELS, METRICS, PREDICTIONS, MONITORING]:
    path.mkdir(parents=True, exist_ok=True)
