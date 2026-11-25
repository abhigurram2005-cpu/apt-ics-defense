"""Reloads the SAVED models, re-scores the saved test split, checks the numbers match
results/metrics.json, and writes results/per_class_<model>.csv. Run after run_all.py."""
import json, joblib, numpy as np, pandas as pd
from sklearn.metrics import accuracy_score, classification_report
import config
from src import data, baseline, np_transformer as npt

z, meta = data.load_processed(); labels = meta["labels"]
te = z["idx_test"]; X, y = z["ids"][te], z["y"][te]
saved = json.load(open(f"{config.RESULTS_DIR}/metrics.json"))["models"]
preds = {"SVM": baseline.predict(joblib.load(f"{config.MODELS_DIR}/svm.joblib"), X)}
try:
    p, cfg = npt.load()
    preds["Transformer"] = npt.predict_proba(p, X, cfg["heads"], cfg["layers"]).argmax(1)
except FileNotFoundError:
    print("Transformer model not found, skipping")
for name, pr in preds.items():
    acc = accuracy_score(y, pr)
    match = abs(acc - saved[name]["accuracy"]) < 1e-9
    print(f"{name}: reloaded accuracy {acc:.4f}  matches metrics.json: {match}")
    rep = classification_report(y, pr, labels=range(len(labels)), target_names=labels, output_dict=True, zero_division=0)
    pd.DataFrame(rep).T.round(3).to_csv(f"{config.RESULTS_DIR}/per_class_{name.lower()}.csv")
    print(f"  wrote results/per_class_{name.lower()}.csv")
