import json, os
from html import escape as e
import numpy as np, pandas as pd, streamlit as st, joblib
import config
from src import data, predict, ui, threat_intelligence as TI

st.set_page_config(page_title="Opcode family lookup", layout="centered")
st.markdown(f"<style>{ui.CSS}</style>", unsafe_allow_html=True)

st.markdown("<h1>Opcode family lookup</h1>"
            "<p class='lede'>Assigns a malware sample to one of 21 families using the first 256 opcodes of its "
            "disassembly. Two models read the same sequence: a linear SVM on opcode n-grams and a small Transformer "
            "trained from scratch.</p>"
            "<p class='note'>Research prototype on a public dataset. It reports the family names that dataset uses. "
            "It does not detect industrial-control malware and it does not say who wrote a sample.</p>",
            unsafe_allow_html=True)

need = [f"{config.PROC_DIR}/meta.json", f"{config.MODELS_DIR}/svm.joblib"]
if not all(os.path.exists(f) for f in need):
    st.error("Trained models are missing. Run: python run_all.py --data data/raw/all_data.csv")
    st.stop()

@st.cache_resource
def load_models():
    z, meta = data.load_processed()
    svm = joblib.load(f"{config.MODELS_DIR}/svm.joblib")
    tp = None
    path = f"{config.MODELS_DIR}/transformer_np.npz"
    if os.path.exists(path):
        from src import np_transformer as npt
        tp = npt.load(path)
    return z, meta, svm, tp

z, meta, svm, tp = load_models()
labels = meta["labels"]
ids, true_label = None, None

# ---------------------------------------------------------------- Sample
st.markdown("<h2>Sample</h2>", unsafe_allow_html=True)
src = st.radio("Where does the sample come from?", ["A sample from the test split", "Opcode ids I paste"], horizontal=True)
if src == "A sample from the test split":
    te = z["idx_test"]
    k = st.selectbox("Test sample", list(range(len(te))), format_func=lambda i: f"Test sample {i + 1} of {len(te)}")
    ids = z["ids"][te[k]][None, :]
    true_label = labels[int(z["y"][te[k]])]
else:
    txt = st.text_area("Opcode ids, integers separated by spaces or commas (the 'Opcode: N' columns of one row)")
    if txt.strip():
        ids = predict.ids_from_text(txt, meta["vocab_size"], meta["max_len"])
        if (ids > 0).sum() == 0:
            st.warning("No valid opcode ids found. Paste whole numbers such as: 22 18 0 1 22 1")
            ids = None

if ids is None:
    st.markdown("<p class='muted'>Choose a test sample or paste opcode ids to see the models' verdict.</p>", unsafe_allow_html=True)
    st.stop()

row = ids[0][ids[0] > 0]
rows = [("Source", "Test split of the public dataset" if true_label else "Pasted by the user"),
        ("Opcodes used", f"{len(row)} of {meta['max_len']}"),
        ("First opcode ids", f"<span class='mono'>{e(' '.join(str(int(t) - 2) for t in row[:30]))}{' ...' if len(row) > 30 else ''}</span>")]
if true_label:
    rows.insert(1, ("Label in the dataset", e(true_label)))
st.markdown(ui.kv(rows), unsafe_allow_html=True)
st.markdown(ui.strip(ids[0]) + "<p class='cap'>One cell per opcode, in order. Equal colours are equal opcode ids. "
            "Hover a cell to read its position and id.</p>", unsafe_allow_html=True)

# ---------------------------------------------------------------- Verdict
st.markdown("<h2>What the models say</h2>", unsafe_allow_html=True)
fam_s, top_s = predict.svm_predict(svm, ids, labels)
fam_t, top_t = (predict.transformer_predict(tp[0], tp[1], ids, labels) if tp is not None else (None, None))

metrics = {}
mp = f"{config.RESULTS_DIR}/metrics.json"
if os.path.exists(mp):
    metrics = json.load(open(mp)).get("models", {})
use_t = fam_t is not None and metrics.get("Transformer", {}).get("f1_macro", 0) > metrics.get("SVM", {}).get("f1_macro", 1)
final, final_name = (fam_t, "Transformer") if use_t else (fam_s, "SVM")

if fam_t is None:
    verdict = f"The SVM says <b>{e(fam_s)}</b>. The Transformer model file was not found."
elif fam_s == fam_t:
    verdict = f"Both models say <b>{e(fam_s)}</b>."
else:
    verdict = f"<span class='bad'>The models disagree.</span> SVM: <b>{e(fam_s)}</b>. Transformer: <b>{e(fam_t)}</b>."
st.markdown(f"<p class='verdict'>{verdict}</p>", unsafe_allow_html=True)

head = ["", "SVM"] + (["Transformer"] if fam_t else [])
def yesno(f):
    return "<span class='ok'>yes</span>" if f == true_label else "<span class='bad'>no</span>"
body = [["Predicted family", e(fam_s)] + ([e(fam_t)] if fam_t else []),
        ["Top three (score)", ui.candidates(top_s)] + ([ui.candidates(top_t)] if fam_t else [])]
if true_label:
    body.append(["Matches the dataset label", yesno(fam_s)] + ([yesno(fam_t)] if fam_t else []))
st.markdown(ui.table(head, body), unsafe_allow_html=True)
st.markdown("<p class='cap'>SVM scores are distances from the decision boundary and are not probabilities. "
            "Transformer scores are softmax probabilities. Neither is calibrated, so do not read them as confidence.</p>",
            unsafe_allow_html=True)

# a training sample of the predicted family, for a visual comparison
tr = z["idx_train"]
same = tr[z["y"][tr] == labels.index(final)]
if len(same):
    st.markdown(f"<p class='cap'>For comparison, a training sample labelled {e(final)}:</p>" + ui.strip(z["ids"][same[0]]),
                unsafe_allow_html=True)

# ---------------------------------------------------------------- Performance
st.markdown("<h2>How well the models do</h2>", unsafe_allow_html=True)
cp = f"{config.RESULTS_DIR}/comparison.csv"
if os.path.exists(cp):
    df = pd.read_csv(cp, index_col=0)
    names = {"accuracy": "Accuracy", "precision_macro": "Macro precision", "recall_macro": "Macro recall",
             "f1_macro": "Macro F1", "train_time_s": "Training time"}
    cols = [c for c in names if c in df.columns]
    rows_ = [[e(str(m))] + [f"{df.loc[m, c]:.3f}" for c in cols if c != "train_time_s"] +
             ([ui.fmt_time(df.loc[m, "train_time_s"])] if "train_time_s" in cols else []) for m in df.index]
    hdr = ["Model"] + [names[c] for c in cols if c != "train_time_s"] + (["Training time"] if "train_time_s" in cols else [])
    st.markdown(ui.table(hdr, rows_, num_cols=range(1, len(hdr))), unsafe_allow_html=True)
    st.markdown(f"<p class='cap'>Measured on {len(z['idx_test'])} samples the models never saw during training. "
                "Macro scores average the 21 families equally, so small families count as much as large ones. "
                "Training time is wall-clock on the machine that trained them.</p>", unsafe_allow_html=True)
else:
    st.markdown("<p class='muted'>No results file yet. Run run_all.py first.</p>", unsafe_allow_html=True)

with st.expander("Confusion matrices"):
    for f in sorted(os.listdir(config.RESULTS_DIR)) if os.path.isdir(config.RESULTS_DIR) else []:
        if f.startswith("confusion_matrix") and f.endswith(".png"):
            st.image(f"{config.RESULTS_DIR}/{f}", width=560)
pc = f"{config.RESULTS_DIR}/per_class_report.csv"
if os.path.exists(pc):
    with st.expander("Results for each family"):
        d = pd.read_csv(pc, index_col=0)
        keep = [c for c in ["support", "SVM_f1", "Transformer_f1"] if c in d.columns]
        st.markdown(ui.table(["Family", "Test samples"] + [c.replace("_f1", " F1") for c in keep[1:]],
                             [[e(str(i))] + [f"{d.loc[i, c]:.0f}" if c == "support" else f"{d.loc[i, c]:.2f}" for c in keep] for i in d.index],
                             num_cols=range(1, len(keep) + 1)), unsafe_allow_html=True)
        st.markdown("<p class='cap'>Families with fewer than about 20 test samples (HOTBAR has 2) give unreliable scores.</p>",
                    unsafe_allow_html=True)

# ---------------------------------------------------------------- Threat intelligence
st.markdown(f"<h2>What is documented about {e(final)}</h2>", unsafe_allow_html=True)
t = TI.lookup(final)
if t.get("verified"):
    status = "Entry reviewed against the sources listed below."
else:
    status = "<span class='bad'>No verified entry.</span> Nothing here has been checked against a public source."
st.markdown(ui.kv([
    ("Looked up for", f"{e(final)} (the {final_name} result, the better model on the test split)"),
    ("Status", status),
    ("Summary", e(t.get("summary") or "") or "<span class='muted'>none recorded</span>"),
    ("ATT&CK techniques", ui.listing(t.get("attack_techniques"))),
    ("Group associations", ui.listing(t.get("apt_associations"))),
    ("Sources", ui.listing(t.get("sources"))),
    ("Attribution confidence", e(str(t.get("confidence", "none")))),
]), unsafe_allow_html=True)
st.markdown("<p class='cap'>A family label from a classifier is not attribution. "
            "Fill data/threat_intel.json only from cited public reports.</p>", unsafe_allow_html=True)

# ---------------------------------------------------------------- Data
st.markdown("<h2>About the data</h2>", unsafe_allow_html=True)
n_tr, n_va, n_te = (len(z[f"idx_{k}"]) for k in ("train", "val", "test"))
st.markdown(ui.kv([
    ("Rows in the file", f"{meta.get('rows_loaded', '?')}"),
    ("Exact duplicates removed", f"{meta.get('duplicates_removed', '?')} (same family and same first {meta['max_len']} opcodes)"),
    ("Rows used", f"{meta.get('rows_used', '?')}: {n_tr} to train, {n_va} to tune, {n_te} to test"),
    ("Families", f"{len(labels)}"),
]), unsafe_allow_html=True)
