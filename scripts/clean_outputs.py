from pathlib import Path
import shutil

root = Path(__file__).resolve().parents[1]
for rel in ["data/raw", "data/bronze", "data/silver", "data/gold", "artifacts"]:
    path = root / rel
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)
print("Output folders reset.")
