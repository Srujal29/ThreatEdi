import os
import re
import json
import ast

import numpy as np
import pandas as pd
import joblib
from scipy.sparse import hstack, csr_matrix
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestClassifier, VotingClassifier
from sklearn.metrics import classification_report, accuracy_score
from imblearn.over_sampling import SMOTE
from xgboost import XGBClassifier

MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "models")

PATTERNS = {
    "has_ip": r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b",
    "has_hash": r"\b[a-fA-F0-9]{32,64}\b",
    "has_url": r"https?://[^\s]+",
    "has_filepath": r"[A-Z]:\\\\|/etc/|/usr/|/var/",
    "has_email": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
    "has_domain": r"\b[a-zA-Z0-9.-]+\.(com|net|org|xyz|ru|cn|io|info|biz|top)\b",
    "has_registry": r"HKLM|HKCU|HKEY_",
    "has_cve": r"CVE-\d{4}-\d+",
}

_tfidf = None
_label_encoder = None
_model = None
_domain_feature_names = None

def _extract_domain_features_single(text: str) -> list:
    features = []
    for pattern in PATTERNS.values():
        features.append(1 if re.search(pattern, text) else 0)
    features.append(len(text))                                           
    features.append(len(text.split()))                                   
    features.append(sum(1 for c in text if c.isupper()) / max(len(text), 1))  
    return features

def _extract_domain_features_df(df: pd.DataFrame) -> csr_matrix:
    text_col = df["text_data"]

    feature_cols = {}
    for name, pattern in PATTERNS.items():
        feature_cols[name] = text_col.str.contains(pattern, regex=True).astype(int)

    feature_cols["text_length"] = text_col.str.len()
    feature_cols["word_count"] = text_col.str.split().str.len()
    feature_cols["upper_ratio"] = text_col.apply(
        lambda x: sum(1 for c in x if c.isupper()) / max(len(x), 1)
    )

    feature_df = pd.DataFrame(feature_cols)
    return csr_matrix(feature_df.values), list(feature_df.columns)

def train_model(data_dir: str = None):
    global _tfidf, _label_encoder, _model, _domain_feature_names

    if data_dir is None:
        data_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    def load_jsonl(path):
        data = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                data.append(json.loads(line))
        return pd.DataFrame(data)

    def extract_label(entities):
        if not entities:
            return "benign"
        if isinstance(entities, str):
            entities = ast.literal_eval(entities)
        return entities[0].get("label", "benign")

    train_path = os.path.join(data_dir, "train.jsonl")
    test_path = os.path.join(data_dir, "test.jsonl")

    df_jsonl = pd.concat(
        [load_jsonl(train_path), load_jsonl(test_path)], ignore_index=True
    )
    df_jsonl["Threat Category"] = df_jsonl["entities"].apply(extract_label)
    df_jsonl["text_data"] = df_jsonl["text"].fillna("no description")

    csv_path = os.path.join(data_dir, "Cybersecurity_Dataset.csv")
    if os.path.exists(csv_path):
        df_csv = pd.read_csv(csv_path)
        df_csv["text_data"] = df_csv["Cleaned Threat Description"].fillna("no description")
        df_csv_slim = df_csv[["Threat Category", "text_data"]].copy()
        df_csv_boosted = pd.concat([df_csv_slim] * 3, ignore_index=True)
        df_all = pd.concat(
            [df_jsonl[["Threat Category", "text_data"]], df_csv_boosted],
            ignore_index=True,
        )
        print(f"Combined data: {len(df_jsonl)} JSONL + {len(df_csv)}×3 CSV = {len(df_all)} total")
    else:
        df_all = df_jsonl[["Threat Category", "text_data"]].copy()
        print(f"JSONL data only: {len(df_all)} samples")

    tfidf = TfidfVectorizer(
        max_features=5000,
        ngram_range=(1, 3),
        token_pattern=r"[a-zA-Z0-9\\\\/:\\._-]+",
    )
    X_tfidf = tfidf.fit_transform(df_all["text_data"])

    X_domain, domain_feature_names = _extract_domain_features_df(df_all)
    X = hstack([X_tfidf, X_domain])

    le = LabelEncoder()
    y = le.fit_transform(df_all["Threat Category"])

    print(f"Feature matrix: {X.shape[0]} samples × {X.shape[1]} features")
    print(f"  TF-IDF: {X_tfidf.shape[1]} | Domain: {X_domain.shape[1]}")
    print(f"Classes ({len(le.classes_)}): {le.classes_.tolist()}")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    from collections import Counter
    class_counts = Counter(y_train)
    over_strategy = {cls: max(count, 50) for cls, count in class_counts.items()}
    
    smote = SMOTE(sampling_strategy=over_strategy, k_neighbors=1, random_state=42)
    X_res, y_res = smote.fit_resample(X_train, y_train)

    print("\nTraining Hybrid Model (XGBoost + RandomForest)...")
    xgb = XGBClassifier(
        n_estimators=200, learning_rate=0.1, max_depth=6,
        tree_method="hist", n_jobs=-1, random_state=42,
    )
    rf = RandomForestClassifier(
        n_estimators=200, max_depth=15,
        class_weight="balanced", n_jobs=-1, random_state=42,
    )
    model = VotingClassifier(
        estimators=[("xgb", xgb), ("rf", rf)],
        voting="soft", n_jobs=-1,
    )
    model.fit(X_res, y_res)

    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    print(f"\n Model trained - Accuracy: {acc * 100:.2f}%")
    print(classification_report(y_test, y_pred, target_names=le.classes_, zero_division=0))

    os.makedirs(MODEL_DIR, exist_ok=True)
    joblib.dump(model, os.path.join(MODEL_DIR, "threat_classifier.joblib"))
    joblib.dump(tfidf, os.path.join(MODEL_DIR, "tfidf_vectorizer.joblib"))
    joblib.dump(le, os.path.join(MODEL_DIR, "label_encoder.joblib"))
    joblib.dump(domain_feature_names, os.path.join(MODEL_DIR, "domain_features.joblib"))
    print(f" Model saved to {MODEL_DIR}/")

    _tfidf = tfidf
    _label_encoder = le
    _model = model
    _domain_feature_names = domain_feature_names

    return acc

def load_model():
    global _tfidf, _label_encoder, _model, _domain_feature_names

    if _model is not None:
        return True  

    model_path = os.path.join(MODEL_DIR, "threat_classifier.joblib")
    if not os.path.exists(model_path):
        return False

    _model = joblib.load(model_path)
    _tfidf = joblib.load(os.path.join(MODEL_DIR, "tfidf_vectorizer.joblib"))
    _label_encoder = joblib.load(os.path.join(MODEL_DIR, "label_encoder.joblib"))
    _domain_feature_names = joblib.load(os.path.join(MODEL_DIR, "domain_features.joblib"))

    print(f" Model loaded from {MODEL_DIR}/")
    return True

def predict(text: str) -> dict:
    if _model is None:
        if not load_model():
            raise RuntimeError(
                "No trained model found. Run `python run_training.py` first."
            )

    text_lower = text.lower()
    
    manual_category = None
    
    if "phishing" in text_lower or "fake login" in text_lower:
        manual_category = "Phishing"
    elif "ransomware" in text_lower or ".wcry" in text_lower or "decrypt" in text_lower or "bitcoin" in text_lower or "btc" in text_lower:
        manual_category = "Ransomware"
    elif "ddos" in text_lower or "denial of service" in text_lower or "botnet" in text_lower or "flood" in text_lower:
        manual_category = "DDoS"
    elif "malware" in text_lower or "trojan" in text_lower or "keylogger" in text_lower or "spyware" in text_lower or "backdoor" in text_lower:
        manual_category = "Malware"
    elif "unauthorized" in text_lower or "brute force" in text_lower or "failed login" in text_lower:
        manual_category = "attack-pattern"
    elif "apt " in text_lower or "fancy bear" in text_lower or "lazarus" in text_lower:
        manual_category = "threat-actor"
    elif "cve-" in text_lower or "zero-day" in text_lower or "vulnerability" in text_lower:
        manual_category = "vulnerability"
    elif re.search(r'\b[a-fA-F0-9]{64}\b', text):
        manual_category = "SHA2"

    vec_tfidf = _tfidf.transform([text])

    domain_vals = _extract_domain_features_single(text)
    vec_domain = csr_matrix([domain_vals])

    vec = hstack([vec_tfidf, vec_domain])

    probs = _model.predict_proba(vec)[0]
    predicted_idx = np.argmax(probs)
    ml_category = _label_encoder.classes_[predicted_idx]
    ml_confidence = float(probs[predicted_idx])

    top3_idx = np.argsort(probs)[-3:][::-1]
    top3 = [
        {"category": _label_encoder.classes_[i], "confidence": round(float(probs[i]), 4)}
        for i in top3_idx
    ]

    if manual_category:
        if ml_category.lower() == manual_category.lower() and ml_confidence > 0.95:
            final_category = ml_category
            final_confidence = ml_confidence
        else:
            final_category = manual_category
            final_confidence = 0.95  
            
            if not any(x["category"].lower() == final_category.lower() for x in top3):
                top3.insert(0, {"category": final_category, "confidence": 0.95})
                top3.pop() 
    else:
        final_category = ml_category
        final_confidence = ml_confidence

    return {
        "category": final_category,
        "confidence": round(final_confidence, 4),
        "top_predictions": top3,
        "ml_raw_category": ml_category,           
        "ml_raw_confidence": round(ml_confidence, 4)
    }

def get_categories() -> list:
    if _label_encoder is None:
        load_model()
    return _label_encoder.classes_.tolist() if _label_encoder else []
