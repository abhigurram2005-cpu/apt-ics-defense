import json
import os
from html import escape as e

import joblib
import numpy as np
import pandas as pd
import streamlit as st

import config
from src import data, predict, threat_intelligence as TI, ui

# --------------------------------------------------------------
# 1️⃣ Page configuration & theme handling
# --------------------------------------------------------------
st.set_page_config(page_title="APT-ICS Defense | Opcode Family Lookup", layout="wide")

with st.sidebar:
    st.title("🛡️ APT-ICS Defense")
    page = st.radio(
        "Navigate",
        ["Home", "Performance", "Threat intel", "About"],
        index=0,
    )
    dark_mode = st.checkbox("Dark mode", key="dark_mode")
    st.markdown("---")
    st.caption("Version 1.1")

st.markdown(f"<style>{ui.get_css(dark_mode)}</style>", unsafe_allow_html=True)

# --------------------------------------------------------------
# 2️⃣ Model availability checks (show status chips)
# --------------------------------------------------------------
svm_ok = os.path.exists(f"{config.MODELS_DIR}/svm.joblib")
transformer_ok = os.path.exists(f"{config.MODELS_DIR}/transformer_np.npz")

model_status = f"SVM {ui.status_chip(svm_ok)} &nbsp;|&nbsp; Transformer {ui.status_chip(transformer_ok)}"
st.sidebar.markdown(f"**Models:**<br>{model_status}", unsafe_allow_html=True)


# --------------------------------------------------------------
# 3️⃣ Load data & models (cached)
# --------------------------------------------------------------
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
labels = list(meta["labels"])
all_intel = TI.load_all()


def _kpi_summary() -> list:
    """Build 4 KPI tuples (label, value, subtitle) for the top overview."""
    n_test = len(z["idx_test"])
    n_fam = len(labels)
    verified_cnt = sum(1 for v in all_intel.values() if v.get("verified"))
    acc_str = "N/A"
    cp = f"{config.RESULTS_DIR}/comparison.csv"
    if os.path.exists(cp):
        cdf = pd.read_csv(cp, index_col=0)
        if "accuracy" in cdf.columns:
            parts = [f"{idx}: {cdf.loc[idx, 'accuracy']*100:.1f}%" for idx in cdf.index]
            acc_str = " / ".join(parts)
    return [
        ("Test Samples", f"{n_test:,}", "Held-out evaluation split"),
        ("Malware Families", str(n_fam), "Static opcode classes"),
        ("Test Accuracy", acc_str, "Measured on unseen split"),
        ("Threat Intel", f"{verified_cnt} / {n_fam}", "Verified family entries"),
    ]


# --------------------------------------------------------------
# 4️⃣ Page rendering – split by sidebar navigation
# --------------------------------------------------------------
if page == "Home":
    st.markdown(
        """
        <h1>Opcode family lookup</h1>
        <p class='lede'>
        Assigns a malware sample to one of 21 families using the first 256 opcodes of its disassembly.
        Two models read the same sequence: a linear SVM on opcode n-grams and a small Transformer trained from scratch.
        </p>
        <p class='note'>
        Research prototype on a public dataset. It does not detect industrial-control malware and it does not say who wrote a sample.
        </p>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(ui.kpi_row(_kpi_summary()), unsafe_allow_html=True)

    # ---- Sample selection ----------------------------------------
    st.markdown("## Sample")
    src = st.radio(
        "Where does the sample come from?",
        ["A sample from the test split", "Paste or upload .txt", "Batch upload (.txt / .csv)"],
        horizontal=True,
    )

    ids, true_label, sample_source_label = None, None, "User input"

    if src == "Batch upload (.txt / .csv)":
        up = st.file_uploader(
            "Upload a .txt or .csv file (one space/comma-separated opcode sequence per line, max 200 rows)",
            type=["txt", "csv"],
        )
        if up is not None:
            lines = [ln.strip() for ln in up.getvalue().decode("utf-8", errors="ignore").splitlines() if ln.strip()]
            lines = lines[:200]
            rows_out = []
            for idx_row, ln in enumerate(lines, start=1):
                seq = predict.ids_from_text(ln, meta["vocab_size"], meta["max_len"])
                if (seq > 0).sum() == 0:
                    continue
                fs, ts = predict.svm_predict(svm, seq, labels)
                ft, tt = (
                    predict.transformer_predict(tp[0], tp[1], seq, labels)
                    if tp is not None
                    else (None, None)
                )
                rows_out.append({
                    "Row": idx_row,
                    "Opcodes": int((seq > 0).sum()),
                    "SVM": fs,
                    "SVM Score": round(ts[0][1], 3),
                    "Transformer": ft or "N/A",
                    "Transformer Prob": round(tt[0][1], 3) if tt else None,
                    "Agreement": "Agree" if (ft is None or fs == ft) else "Disagree",
                })
            if not rows_out:
                st.warning("No valid opcode sequences found in the uploaded file.")
            else:
                bdf = pd.DataFrame(rows_out)
                agree_rate = (bdf["Agreement"] == "Agree").mean() * 100
                st.success(f"Processed {len(bdf)} sequences — Model agreement: {agree_rate:.1f}%")
                st.dataframe(bdf, use_container_width=True, hide_index=True)
                st.download_button(
                    "Download batch results (CSV)",
                    data=bdf.to_csv(index=False).encode("utf-8"),
                    file_name="batch_predictions.csv",
                    mime="text/csv",
                )
        st.stop()

    if src == "A sample from the test split":
        te = z["idx_test"]
        te_y = z["y"][te]
        col_f, col_s = st.columns([1, 2])
        with col_f:
            fam_filter = st.selectbox("Filter by true family", ["All families"] + sorted(labels))
        if fam_filter == "All families":
            filtered_indices = list(range(len(te)))
        else:
            target_y = labels.index(fam_filter)
            filtered_indices = [i for i, yv in enumerate(te_y) if int(yv) == target_y]

        b1, b2, _ = st.columns([1, 1.4, 2.6])
        if b1.button("Random sample") and filtered_indices:
            st.session_state["sample_choice"] = int(np.random.choice(filtered_indices))
        if b2.button("Find model disagreement") and tp is not None and filtered_indices:
            cur = st.session_state.get("sample_choice", filtered_indices[0])
            pos = filtered_indices.index(cur) if cur in filtered_indices else 0
            found = None
            for step in range(1, len(filtered_indices) + 1):
                cand_idx = filtered_indices[(pos + step) % len(filtered_indices)]
                cand_ids = z["ids"][te[cand_idx]][None, :]
                fs, _ = predict.svm_predict(svm, cand_ids, labels)
                ft, _ = predict.transformer_predict(tp[0], tp[1], cand_ids, labels)
                if fs != ft:
                    found = cand_idx
                    break
            if found is not None:
                st.session_state["sample_choice"] = found
            else:
                st.info("No disagreements found in the current filter.")

        default_choice = st.session_state.get("sample_choice")
        sel_index = filtered_indices.index(default_choice) if default_choice in filtered_indices else 0
        with col_s:
            k = st.selectbox(
                f"Test sample ({len(filtered_indices)} matching)",
                filtered_indices,
                index=sel_index,
                format_func=lambda i: f"Test sample {i+1} of {len(te)} ({labels[int(te_y[i])]})",
            )
            st.session_state["sample_choice"] = k
        ids = z["ids"][te[k]][None, :]
        true_label = labels[int(z["y"][te[k]])]
        sample_source_label = "Test split"
    else:
        c_paste, c_drop = st.columns([1.3, 1])
        with c_paste:
            txt = st.text_area(
                "Paste opcode ids (space, comma, or newline separated)",
                placeholder="22 18 0 1 22 1 …",
                height=120,
            )
        with c_drop:
            up_single = st.file_uploader(
                "Or drop a .txt file with opcodes",
                type=["txt"],
                key="single_txt_upload",
            )
        raw_input = ""
        if up_single is not None:
            raw_input = up_single.getvalue().decode("utf-8", errors="ignore")
            sample_source_label = f"Uploaded file ({up_single.name})"
        elif txt.strip():
            raw_input = txt
            sample_source_label = "User input"

        if raw_input.strip():
            ids = predict.ids_from_text(raw_input, meta["vocab_size"], meta["max_len"])
            if (ids > 0).sum() == 0:
                st.warning("No valid opcode ids found.")
                ids = None

    if ids is None:
        st.stop()

    # ---- Sample info box -----------------------------------------
    row = ids[0][ids[0] > 0]
    preview = " ".join(
        "UNK" if int(t) == 1 else str(int(t) - 2) for t in row[:30]
    )
    kv_rows = [
        ("Source", e(sample_source_label)),
        ("Opcodes used", f"{len(row)} of {meta['max_len']}"),
        ("First opcode ids", f"<span class='mono'>{e(preview)}{' …' if len(row) > 30 else ''}</span>"),
    ]
    if true_label:
        kv_rows.insert(1, ("Label in the dataset", e(true_label)))
    st.markdown(ui.card(ui.kv(kv_rows)), unsafe_allow_html=True)

    st.markdown(ui.strip(ids[0]) + "<p class='cap'>One cell per opcode – hover for its id.</p>", unsafe_allow_html=True)

    # Top 5 most frequent opcodes in this sample
    vals, counts = np.unique(row, return_counts=True)
    top_idx = np.argsort(-counts)[:5]
    pills = "".join(
        f"<span class='op-pill'>{'UNK' if int(vals[i]) == 1 else f'op {int(vals[i]) - 2}'}: "
        f"{int(counts[i])} ({counts[i] / len(row) * 100:.1f}%)</span>"
        for i in top_idx
    )
    st.markdown(f"<p class='cap' style='margin-bottom:0.2rem;'>Top opcodes in sample:</p><div class='pill-row'>{pills}</div>", unsafe_allow_html=True)

    # ---- Model verdict -------------------------------------------
    st.markdown("## What the models say")
    fam_s, top_s = predict.svm_predict(svm, ids, labels)
    fam_t, top_t = (
        predict.transformer_predict(tp[0], tp[1], ids, labels) if tp is not None else (None, None)
    )
    verdict = (
        f"The SVM says <b>{e(fam_s)}</b>."
        if fam_t is None
        else (
            f"Both models say <b>{e(fam_s)}</b>."
            if fam_s == fam_t
            else f"<span class='bad'>The models disagree.</span> SVM: <b>{e(fam_s)}</b>. Transformer: <b>{e(fam_t)}</b>."
        )
    )
    st.markdown(f"<p class='verdict'>{verdict}</p>", unsafe_allow_html=True)

    final_fam = fam_t if fam_t is not None else fam_s
    final_model = "Transformer" if fam_t is not None else "SVM"
    st.session_state["last_family"] = final_fam
    st.session_state["last_model"] = final_model

    # ---- Detailed table with confidence bars ---------------------
    head = ["Metric", "SVM"] + (["Transformer"] if fam_t else [])
    body = [
        ["Predicted family", f"<b>{e(fam_s)}</b>"] + ([f"<b>{e(fam_t)}</b>"] if fam_t else []),
        ["Top three (confidence)", ui.confidence_bars(top_s, is_prob=False)]
        + ([ui.confidence_bars(top_t, is_prob=True)] if fam_t else []),
    ]
    if true_label:
        body.append(
            ["Matches dataset label", ui.ok if fam_s == true_label else ui.bad]
            + ([ui.ok if fam_t == true_label else ui.bad] if fam_t else [])
        )
    st.markdown(ui.card(ui.table(head, body)), unsafe_allow_html=True)

    # ---- Inline Threat Intel context & export --------------------
    intel = TI.lookup(final_fam)
    intel_chip = ui.status_chip(bool(intel.get("verified")), ok_text="Reviewed", bad_text="Unverified")
    st.markdown(
        ui.card(
            f"<div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:0.5rem;'>"
            f"<b>Threat Intelligence Context — {e(final_fam)}</b>{intel_chip}</div>"
            + ui.kv([
                ("Summary", e(intel.get("summary", "")) or '<span class="muted">none recorded</span>'),
                ("ATT&CK techniques", ui.listing(intel.get("attack_techniques"))),
                ("Confidence note", e(str(intel.get("confidence", "none")))),
            ])
        ),
        unsafe_allow_html=True,
    )

    report = {
        "source": "test_split" if true_label else "user_input",
        "true_label": true_label,
        "opcodes_used": int(len(row)),
        "svm": {"predicted": fam_s, "top_3": [{"family": f, "score": s} for f, s in top_s]},
        "transformer": (
            {"predicted": fam_t, "top_3": [{"family": f, "probability": p} for f, p in top_t]}
            if fam_t
            else None
        ),
        "threat_intel": intel,
    }
    st.download_button(
        "Download sample report (JSON)",
        data=json.dumps(report, indent=2).encode("utf-8"),
        file_name=f"verdict_{final_fam}.json",
        mime="application/json",
    )

    # ---- Comparison with a training sample -----------------------
    tr = z["idx_train"]
    same = tr[z["y"][tr] == labels.index(final_fam)]
    if len(same):
        st.markdown(
            f"<p class='cap'>Training sample for {e(final_fam)}:</p>" + ui.strip(z["ids"][same[0]]),
            unsafe_allow_html=True,
        )

elif page == "Performance":
    st.markdown("## How well the models do")
    cp = f"{config.RESULTS_DIR}/comparison.csv"
    if os.path.exists(cp):
        df = pd.read_csv(cp, index_col=0)
        names = {
            "accuracy": "Accuracy",
            "precision_macro": "Macro precision",
            "recall_macro": "Macro recall",
            "f1_macro": "Macro F1",
            "train_time_s": "Training time",
        }
        cols = [c for c in names if c in df.columns]
        rows = [
            [e(str(m))]
            + [f"{df.loc[m, c]:.3f}" for c in cols if c != "train_time_s"]
            + ([ui.fmt_time(df.loc[m, "train_time_s"])] if "train_time_s" in cols else [])
            for m in df.index
        ]
        hdr = ["Model"] + [names[c] for c in cols if c != "train_time_s"] + (
            ["Training time"] if "train_time_s" in cols else []
        )
        st.markdown(ui.card(ui.table(hdr, rows, num_cols=range(1, len(hdr)))), unsafe_allow_html=True)
        st.caption(
            f"Measured on {len(z['idx_test'])} unseen samples. "
            "Macro scores treat all families equally – small families count as much as large ones."
        )
    else:
        st.info("No performance file found – run `run_all.py` first.")

    # Interactive training log chart
    tlog_path = f"{config.RESULTS_DIR}/transformer_training_log.json"
    if os.path.exists(tlog_path):
        st.markdown("### Transformer training progression")
        with open(tlog_path, encoding="utf-8") as f:
            tdf = pd.DataFrame(json.load(f)).set_index("epoch")
        c1, c2 = st.columns(2)
        with c1:
            st.caption("Validation Accuracy by Epoch")
            st.line_chart(tdf[["val_acc"]], height=240, color="#16A34A")
        with c2:
            st.caption("Training Loss by Epoch")
            st.line_chart(tdf[["train_loss"]], height=240, color="#2563EB")

    # Confusion matrices
    with st.expander("Confusion matrices"):
        for f in sorted(os.listdir(config.RESULTS_DIR)):
            if f.startswith("confusion_matrix") and f.endswith(".png"):
                st.image(f"{config.RESULTS_DIR}/{f}", width=560)

    # Per-class report + interactive F1 bar chart
    pc = f"{config.RESULTS_DIR}/per_class_report.csv"
    if os.path.exists(pc):
        d = pd.read_csv(pc, index_col=0)
        f1_cols = [c for c in ["SVM_f1", "Transformer_f1"] if c in d.columns]
        if f1_cols:
            st.markdown("### Per-family F1 comparison")
            chart_colors = ["#2563EB", "#16A34A"][:len(f1_cols)]
            st.bar_chart(d[f1_cols], height=300, color=chart_colors)

        keep = [c for c in ["support", "SVM_f1", "Transformer_f1"] if c in d.columns]
        rows = [
            [e(str(i))] + [f"{d.loc[i, c]:.0f}" if c == "support" else f"{d.loc[i, c]:.2f}" for c in keep]
            for i in d.index
        ]
        hdr = ["Family", "Test samples"] + [c.replace("_f1", " F1") for c in keep[1:]]
        st.markdown(ui.card(ui.table(hdr, rows, num_cols=range(1, len(hdr)))), unsafe_allow_html=True)
        st.caption("Families with < 20 test samples (e.g., HOTBAR) give unreliable scores.")
    else:
        st.info("Per-class report not found.")

elif page == "Threat intel":
    st.markdown("## Threat intelligence")
    default_fam = st.session_state.get("last_family", labels[0])
    default_idx = labels.index(default_fam) if default_fam in labels else 0
    final = st.selectbox("Malware family", labels, index=default_idx)
    name = st.session_state.get("last_model", "Selected")
    t = TI.lookup(final)

    status = ui.status_chip(bool(t.get("verified")), ok_text="Reviewed", bad_text="No verified entry")
    st.markdown(
        ui.card(
            ui.kv(
                [
                    ("Looked up for", f"{e(final)} ({name} prediction)"),
                    ("Status", status),
                    ("Summary", e(t.get("summary", "")) or '<span class="muted">none recorded</span>'),
                    ("ATT&CK techniques", ui.listing(t.get("attack_techniques"))),
                    ("Group associations", ui.listing(t.get("apt_associations"))),
                    ("Sources", ui.listing(t.get("sources"))),
                    ("Attribution confidence", e(str(t.get("confidence", "none")))),
                ]
            )
        ),
        unsafe_allow_html=True,
    )
    st.caption("A family label from a classifier is not attribution. Populate `data/threat_intel.json` only with cited public reports.")

    st.markdown("### All 21 families directory")
    q = st.text_input("Search families, summaries, or ATT&CK techniques", placeholder="e.g. T1055, keylogging, worm…")
    q_low = q.strip().lower()
    dir_rows = []
    for fam in sorted(labels):
        entry = all_intel.get(fam, TI.DEFAULT)
        techs = ", ".join(entry.get("attack_techniques", []))
        summary = entry.get("summary", "")
        if q_low and q_low not in fam.lower() and q_low not in summary.lower() and q_low not in techs.lower():
            continue
        chip = ui.status_chip(bool(entry.get("verified")), ok_text="Reviewed", bad_text="Missing")
        dir_rows.append([
            f"<b>{e(fam)}</b>",
            chip,
            ui.listing(entry.get("attack_techniques")),
            e(summary[:140] + ("…" if len(summary) > 140 else "")) or '<span class="muted">none</span>',
        ])
    if dir_rows:
        st.markdown(
            ui.card(ui.table(["Family", "Status", "ATT&CK Techniques", "Summary"], dir_rows)),
            unsafe_allow_html=True,
        )
    else:
        st.info("No families match your search query.")

elif page == "About":
    st.markdown("## About")
    st.markdown(
        ui.card(
            ui.kv(
                [
                    ("Project", "APT-ICS Defense"),
                    ("Architecture", "Linear SVM (opcode n-grams) + NumPy Transformer (from scratch)"),
                    ("Dataset Scope", "21 public malware families (first 256 opcodes)"),
                    ("License", "MIT"),
                    ("Repo", '<a href="https://github.com/abhigurram2005-cpu/apt-ics-defense">GitHub</a>'),
                ]
            )
        ),
        unsafe_allow_html=True,
    )
