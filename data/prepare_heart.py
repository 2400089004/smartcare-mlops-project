from pathlib import Path
import pandas as pd

DATA_DIR = Path(__file__).resolve().parent
SOURCE = DATA_DIR / "processed.cleveland.data"
OUTPUT = DATA_DIR / "heart.csv"

COLUMNS = [
    "age", "sex", "cp", "trestbps", "chol", "fbs", "restecg",
    "thalach", "exang", "oldpeak", "slope", "ca", "thal", "num",
]

def main():
    if not SOURCE.exists():
        raise SystemExit(f"Missing source dataset: {SOURCE}")
    frame = pd.read_csv(SOURCE, header=None, names=COLUMNS, na_values="?")
    frame.to_csv(OUTPUT, index=False)
    print(f"Prepared {len(frame)} rows, {len(COLUMNS)} columns -> {OUTPUT}")
    print(f"Missing values retained for training-time imputation: {int(frame.isna().sum().sum())}")

if __name__ == "__main__":
    main()
