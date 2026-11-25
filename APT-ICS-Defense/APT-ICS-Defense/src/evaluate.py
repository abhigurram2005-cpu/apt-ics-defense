import os, json
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, confusion_matrix
import config

def evaluate(name, y_true, y_pred, labels, train_time):
    p, r, f, _ = precision_recall_fscore_support(y_true, y_pred, average="macro", zero_division=0)
    m = {"accuracy": accuracy_score(y_true, y_pred), "precision_macro": p, "recall_macro": r,
         "f1_macro": f, "train_time_s": train_time}
    cm = confusion_matrix(y_true, y_pred, labels=range(len(labels)))
    os.makedirs(config.RESULTS_DIR, exist_ok=True)
    fig, ax = plt.subplots(figsize=(max(4, len(labels) * 0.9),) * 2)
    ax.imshow(cm, cmap="Blues"); ax.set_xticks(range(len(labels))); ax.set_yticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=45, ha="right"); ax.set_yticklabels(labels)
    for i in range(len(labels)):
        for j in range(len(labels)): ax.text(j, i, cm[i, j], ha="center", va="center", fontsize=8)
    ax.set_xlabel("Predicted"); ax.set_ylabel("True"); ax.set_title(f"{name} (test set)")
    fig.tight_layout(); fig.savefig(f"{config.RESULTS_DIR}/confusion_matrix_{name.lower()}.png", dpi=150); plt.close(fig)
    return m

def write_all(results, meta):
    json.dump({"dataset": meta, "models": results}, open(f"{config.RESULTS_DIR}/metrics.json", "w"), indent=2)
    pd.DataFrame(results).T.round(4).to_csv(f"{config.RESULTS_DIR}/comparison.csv")
