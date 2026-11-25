import re
import numpy as np
from src import baseline

def ids_from_text(text, vocab_size, max_len):
    """Raw opcode ids (as in the CSV 'Opcode: N' columns), separated by spaces/commas.
    Returns (1, max_len) token array; ids outside the known range become UNK (1); 0 = PAD."""
    raw = [int(t) for t in re.split(r"[,\s]+", text.strip()) if t.isdigit()][:max_len]
    toks = [(t + 2) if (t + 2) < vocab_size else 1 for t in raw]
    return np.array([toks + [0] * (max_len - len(toks))], dtype=np.int64)

def svm_predict(pipe, ids, labels):
    scores = pipe.decision_function(baseline.to_text(ids))[0]
    order = np.argsort(-scores)
    return labels[order[0]], [(labels[i], float(scores[i])) for i in order[:3]]

def transformer_predict(params, cfg, ids, labels):
    from src import np_transformer as npt
    p = npt.predict_proba(params, ids, cfg["heads"], cfg["layers"])[0]
    order = np.argsort(-p)
    return labels[order[0]], [(labels[i], float(p[i])) for i in order[:3]]
