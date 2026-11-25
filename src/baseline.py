"""SVM baseline: TF-IDF over opcode n-grams (1-3) + LinearSVC."""
import time, joblib, os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC
import config

def to_text(ids):
    return [" ".join(f"t{t}" for t in row if t > 0) for row in ids]

def train_svm(ids, y):
    pipe = Pipeline([
        ("tfidf", TfidfVectorizer(token_pattern=r"\S+", lowercase=False, ngram_range=(1, 3),
                                  max_features=50000, sublinear_tf=True)),
        ("svm", LinearSVC(C=1.0, class_weight="balanced", random_state=config.SEED)),
    ])
    t = time.time(); pipe.fit(to_text(ids), y)
    dt = time.time() - t
    os.makedirs(config.MODELS_DIR, exist_ok=True)
    joblib.dump(pipe, f"{config.MODELS_DIR}/svm.joblib")
    return pipe, dt

def predict(pipe, ids):
    return pipe.predict(to_text(ids))
