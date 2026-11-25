SEED = 42
MAX_LEN = 256
SPLIT = (0.70, 0.15, 0.15)   # train / val / test
PROC_DIR, MODELS_DIR, RESULTS_DIR = "data/processed", "models", "results"
EMB_DIM, HEADS, LAYERS, FF_DIM, DROPOUT = 128, 4, 2, 256, 0.1
EPOCHS, BATCH, LR = 8, 32, 1e-3
