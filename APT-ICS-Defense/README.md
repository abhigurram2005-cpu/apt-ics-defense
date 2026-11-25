# Opcode-based Malware Family Classification (SVM vs Transformer) + Dashboard

Dataset: `all_data.csv` (9,725 samples, 21 malware families, first 1,000 opcodes per sample as integer ids).
Scope: family classification on this public dataset only. NOT ICS-validated, NOT APT attribution.

## Already included (trained on the provided dataset)
`models/` (SVM + NumPy Transformer), `results/` (metrics, confusion matrices, per-family report, training log),
`data/processed/` (tokenized splits). The dashboard works immediately.

## Dashboard design
A single-page, report-style layout modelled on plain sample-entry pages (e.g. abuse.ch MalwareBazaar): key/value tables, plain verdict sentences, one custom element (the opcode strip). Styling lives in `src/ui.py` and `.streamlit/config.toml`. `docs/static_preview_not_real_streamlit.png` is a browser render of the page's own HTML, without Streamlit's input widgets.

## Quick start (no PyTorch needed)
1. `pip install -r requirements.txt`        (numpy, pandas, scikit-learn, matplotlib, joblib, streamlit)
2. `streamlit run app.py`

## Reproduce everything from scratch
1. Put `all_data.csv` in `data/raw/`
2. `python check_env.py`
3. `python run_all.py --data data/raw/all_data.csv`
   - SVM takes ~2 s. The Transformer (pure NumPy, 8 epochs) took ~25 min on a 1-core server; expect 5-15 min on a laptop.
   - `--no-transformer` runs the SVM only; `--epochs N` changes training length; `--torch` uses the optional PyTorch version.
4. `python per_class_report.py` (per-family table) and `python verify_and_report.py` (reloads saved models and confirms they reproduce metrics.json)

## Pipeline
first 256 opcode ids -> +2 offset (0=PAD, 1=UNK) -> exact-duplicate removal (same family + same 256 ids)
-> stratified 70/15/15 split (seed 42)
- SVM: TF-IDF over opcode 1-3-grams + LinearSVC (class-balanced)
- Transformer: 2 layers, 128-dim, 4 heads, FF 256, pre-LayerNorm, learned positions, masked mean pooling,
  class-weighted loss, Adam + warmup/cosine, best epoch chosen on validation accuracy. Implemented in NumPy with
  manual backprop (gradient-checked against numerical gradients).

## Threat intelligence
`data/threat_intel.json` is intentionally empty. Fill it only from cited public sources; otherwise the dashboard
shows "no verified threat intelligence". Never attribute a family to an APT/ICS group without a source.
