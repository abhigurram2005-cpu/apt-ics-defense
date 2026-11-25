# Report / slide outline (fill with YOUR results from results/metrics.json)
1. Problem: malware classification from opcode sequences
2. Base paper: Scalable APT Malware Classification (arXiv 2504.15497): Ghidra opcodes, SVM/KNN/DT vs CNN. Limitations: [read paper, list 2-3]
3. Dataset: [rows, classes, class counts, duplicates removed: from meta.json]
4. Method: opcode ids -> pad/truncate to 256 -> (a) TF-IDF 1-3-gram + LinearSVC, (b) Transformer encoder (2 layers, 128-dim, 4 heads; NumPy implementation)
5. Results: see RESULTS.md (SVM acc 0.858 / macro-F1 0.751 vs Transformer 0.763 / 0.665). SVM wins; discuss weak families and small classes.
6. Dashboard demo: input -> tokens -> prediction -> comparison -> threat-intel panel -> metrics
7. Limitations: first 256 opcodes only; single dataset; no ICS data; threat intel mapping minimal/unverified; no attribution
8. Future work: ICS dataset, full-length sequences, pretrained models, verified ATT&CK mapping
Contribution wording: "An experimental comparison of an n-gram SVM and a Transformer for opcode-based malware classification, with a prototype analyst dashboard."
