import argparse
import json
from pathlib import Path
import mlflow
import mlflow.sklearn
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, balanced_accuracy_score, f1_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

def main():
    parser = argparse.ArgumentParser()
    project_root = Path(__file__).resolve().parents[1]
    parser.add_argument("--data", default=str(project_root / "data" / "heart.csv"))
    parser.add_argument("--target", default=None)
    args = parser.parse_args()

    path = Path(args.data).expanduser().resolve()
    if not path.exists():
        raise SystemExit(f"Dataset not found: {path}. See README.md for source and placement instructions.")

    df = pd.read_csv(path)
    target = args.target or ("num" if "num" in df.columns else "target" if "target" in df.columns else None)
    if target is None or target not in df.columns:
        raise SystemExit("Could not find target column. Pass --target TARGET_COLUMN.")
    y = df[target]
    # UCI Cleveland task convention: values > 0 mean target-positive.
    y = (pd.to_numeric(y, errors="coerce").fillna(0) > 0).astype(int)
    X = df.drop(columns=[target])
    if len(df) < 50 or y.nunique() != 2:
        raise SystemExit("Dataset is too small or target is not binary after target normalization.")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=y
    )
    numeric = X.select_dtypes(include=["number"]).columns.tolist()
    categorical = [c for c in X.columns if c not in numeric]
    transformers = []
    if numeric:
        transformers.append(("num", Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("scale", StandardScaler())
        ]), numeric))
    if categorical:
        transformers.append(("cat", Pipeline([
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("encode", OneHotEncoder(handle_unknown="ignore"))
        ]), categorical))
    preprocessor = ColumnTransformer(transformers)
    model = Pipeline([
        ("preprocess", preprocessor),
        ("classifier", LogisticRegression(max_iter=2000, class_weight="balanced"))
    ])
    mlflow.set_experiment("smartcare-heart-baseline")
    with mlflow.start_run():
        model.fit(X_train, y_train)
        pred = model.predict(X_test)
        metrics = {
            "accuracy": float(accuracy_score(y_test, pred)),
            "balanced_accuracy": float(balanced_accuracy_score(y_test, pred)),
            "f1": float(f1_score(y_test, pred, zero_division=0))
        }
        if hasattr(model, "predict_proba") and y_test.nunique() == 2:
            metrics["roc_auc"] = float(roc_auc_score(y_test, model.predict_proba(X_test)[:, 1]))
        mlflow.log_params({"model": "LogisticRegression", "random_state": 42, "test_size": 0.25})
        mlflow.log_metrics(metrics)
        mlflow.sklearn.log_model(model, name="heart-baseline")
        out = project_root / "artifacts"
        out.mkdir(parents=True, exist_ok=True)
        import joblib
        joblib.dump(model, out / "heart_model.joblib")
        (out / "heart_metrics.json").write_text(json.dumps(metrics, indent=2))
        print(json.dumps(metrics, indent=2))
        print("Saved educational artifact to", out / "heart_model.joblib")

if __name__ == "__main__":
    main()
