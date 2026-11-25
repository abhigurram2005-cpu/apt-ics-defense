"""One command: python run_all.py --data data/raw/all_data.csv
Options: --epochs N, --no-transformer, --no-dedupe, --torch (use the PyTorch Transformer instead of NumPy)"""
import argparse, os, numpy as np
import config
from src import data, baseline, evaluate

ap = argparse.ArgumentParser()
ap.add_argument("--data", required=True); ap.add_argument("--max-len", type=int, default=config.MAX_LEN)
ap.add_argument("--epochs", type=int, default=config.EPOCHS)
ap.add_argument("--no-transformer", action="store_true"); ap.add_argument("--no-dedupe", action="store_true")
ap.add_argument("--torch", action="store_true", help="use PyTorch implementation (needs torch)")
a = ap.parse_args()
os.makedirs(config.RESULTS_DIR, exist_ok=True)

ids, fam, info = data.load(a.data, a.max_len, dedupe=not a.no_dedupe)
labels, parts, y = data.split(ids, fam)
meta = data.save(ids, y, labels, parts, info)
print("Dataset:", meta, flush=True)
tr, va, te = (parts[k] for k in ("train", "val", "test"))
print(f"Split sizes: train {len(tr)}, val {len(va)}, test {len(te)}", flush=True)
results = {}

print("\n== SVM baseline ==", flush=True)
pipe, dt = baseline.train_svm(ids[tr], y[tr])
results["SVM"] = evaluate.evaluate("SVM", y[te], baseline.predict(pipe, ids[te]), labels, dt)
print(results["SVM"], flush=True)

if not a.no_transformer:
    print("\n== Transformer ==", flush=True)
    if a.torch:
        from src import transformer
        model, dt = transformer.train(ids[tr], y[tr], ids[va], y[va], meta["vocab_size"], len(labels), a.epochs)
        pred = transformer.predict_proba(model, ids[te]).argmax(1)
    else:
        from src import np_transformer as npt
        p, cfg, dt = npt.train(ids[tr], y[tr], ids[va], y[va], meta["vocab_size"], len(labels), a.epochs,
                               log=lambda s: print(s, flush=True))
        pred = npt.predict_proba(p, ids[te], cfg["heads"], cfg["layers"]).argmax(1)
    results["Transformer"] = evaluate.evaluate("Transformer", y[te], pred, labels, dt)
    print(results["Transformer"], flush=True)

evaluate.write_all(results, meta)
print("\nSaved results/metrics.json, results/comparison.csv, confusion matrices, models/")
