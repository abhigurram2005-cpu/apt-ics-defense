import importlib, glob, sys
import pandas as pd
ok = True
print("Python", sys.version.split()[0])
for p in ["numpy", "pandas", "sklearn", "matplotlib", "joblib"]:
    try: importlib.import_module(p); print("[OK]", p)
    except Exception: print("[FAIL]", p, "-> run: pip install -r requirements.txt"); ok = False
try: importlib.import_module("streamlit"); print("[OK] streamlit")
except Exception: print("[WARN] streamlit missing (only needed for the dashboard)")
files = glob.glob("data/raw/*.csv")
if not files: print("[TODO] put all_data.csv in data/raw/"); ok = False
for f in files[:1]:
    cols = pd.read_csv(f, nrows=1).columns
    good = "Family" in cols and any(c.startswith("Opcode:") for c in cols)
    print("[OK]" if good else "[FAIL]", f); ok &= good
print("READY" if ok else "NOT READY")
