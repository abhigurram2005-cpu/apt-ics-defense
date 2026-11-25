"""Per-family precision/recall/F1 on the test split for both models -> results/per_class_report.csv"""
import joblib, numpy as np, pandas as pd
from sklearn.metrics import precision_recall_fscore_support
import config
from src import data, baseline, np_transformer as npt
z, meta = data.load_processed(); labels = meta["labels"]
te = z["idx_test"]; X, y = z["ids"][te], z["y"][te]
rows = {"support": np.bincount(y, minlength=len(labels))}
pred = {"SVM": baseline.predict(joblib.load(f"{config.MODELS_DIR}/svm.joblib"), X)}
try:
    p, cfg = npt.load(); pred["Transformer"] = npt.predict_proba(p, X, cfg["heads"], cfg["layers"]).argmax(1)
except FileNotFoundError:
    print("Transformer model not found; SVM only")
for name, yp in pred.items():
    pr, rc, f1, _ = precision_recall_fscore_support(y, yp, labels=range(len(labels)), zero_division=0)
    rows[f"{name}_precision"], rows[f"{name}_recall"], rows[f"{name}_f1"] = pr, rc, f1
df = pd.DataFrame(rows, index=labels).round(3)
df.to_csv(f"{config.RESULTS_DIR}/per_class_report.csv"); print(df.to_string())
