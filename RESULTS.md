# Results (test split, 1,133 samples, 21 families; produced by run_all.py)
| Metric | SVM | Transformer |
|---|---|---|
| Accuracy | 0.858 | 0.763 |
| Macro precision | 0.753 | 0.664 |
| Macro recall | 0.760 | 0.677 |
| Macro F1 | 0.751 | 0.665 |
| Training time | 2 s | ~1,500 s (1 CPU core, NumPy) |

Data: 9,725 rows loaded, 2,178 exact duplicates removed (first 256 opcodes + family), 7,547 used
(train 5,282 / val 1,132 / test 1,133). Transformer best validation accuracy 0.754 (epoch 8; still improving slowly).

Findings to state honestly
- The SVM outperforms the Transformer in this setup. The Transformer was not tuned and is likely undertrained.
- Strong families (F1 > 0.9, SVM): ALLAPLE_A, CYCBOT_G, VOBFUS, VUNDO, FAKEREAN, WINWEBSEC, RENOS.
- Weak families: INJECTOR, BIFROSE, SMALL, AGENT (F1 < 0.5 for both models).
- HOTBAR (2 test samples), ADLOAD (9), RIMECUD_A (10): per-family numbers are not reliable.
- Only the first 256 of 1,000 available opcodes are used.
- Split/dedup choice matters: without dedup, accuracy would be inflated by near-identical samples.
See results/per_class_report.csv, results/confusion_matrix_*.png, results/transformer_training_log.json.
