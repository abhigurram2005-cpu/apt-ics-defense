"""Load the opcode CSV, tokenize (ids already integers), dedupe, split, save."""
import json, os
import numpy as np, pandas as pd
from sklearn.model_selection import train_test_split
import config
PAD, UNK, OFFSET = 0, 1, 2   # real opcode id k -> token k+2

def load(path, max_len=config.MAX_LEN, dedupe=True):
    df = pd.read_csv(path)
    cols = [c for c in df.columns if c.startswith("Opcode:")]
    if "Family" not in df.columns or not cols:
        raise SystemExit("CSV must have a 'Family' column and 'Opcode: N' columns")
    raw = df[cols].to_numpy(dtype=float)[:, :max_len]
    ids = np.where(np.isnan(raw), PAD, raw + OFFSET).astype(np.int64)
    fam = df["Family"].astype(str).to_numpy()
    info = {"rows_loaded": int(len(df))}
    if dedupe:
        keys = pd.Series([f + "|" + r.tobytes().hex() for f, r in zip(fam, ids)])
        keep = ~keys.duplicated().to_numpy()
        info["duplicates_removed"] = int((~keep).sum())
        ids, fam = ids[keep], fam[keep]
    info["rows_used"] = int(len(ids))
    return ids, fam, info

def split(ids, fam, seed=config.SEED):
    labels = sorted(set(fam)); y = np.array([labels.index(f) for f in fam])
    strat = y if np.bincount(y).min() >= 3 else None
    if strat is None: print("WARNING: a class has <3 samples; split is NOT stratified")
    tr, rest = config.SPLIT[0], config.SPLIT[1] + config.SPLIT[2]
    i_tr, i_rest = train_test_split(np.arange(len(y)), test_size=rest, random_state=seed, stratify=strat)
    s2 = y[i_rest] if strat is not None and np.bincount(y[i_rest]).min() >= 2 else None
    i_va, i_te = train_test_split(i_rest, test_size=config.SPLIT[2] / rest, random_state=seed, stratify=s2)
    return labels, {"train": i_tr, "val": i_va, "test": i_te}, y

def save(ids, y, labels, parts, info):
    os.makedirs(config.PROC_DIR, exist_ok=True)
    np.savez_compressed(f"{config.PROC_DIR}/dataset.npz", ids=ids, y=y, **{f"idx_{k}": v for k, v in parts.items()})
    meta = {"labels": labels, "vocab_size": int(ids.max()) + 1, "max_len": int(ids.shape[1]), **info,
            "class_counts": {l: int((y == i).sum()) for i, l in enumerate(labels)}}
    json.dump(meta, open(f"{config.PROC_DIR}/meta.json", "w"), indent=2)
    return meta

def load_processed():
    z = np.load(f"{config.PROC_DIR}/dataset.npz")
    meta = json.load(open(f"{config.PROC_DIR}/meta.json"))
    return z, meta
