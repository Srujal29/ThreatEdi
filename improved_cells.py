"""
IMPROVED DEFENSE CYBERSECURITY TRIAGE MODEL
============================================
Copy each section below into the corresponding cell in your notebook.
Replace the old cell code with the new code below.

Cells 1, 3, 4, 5, 7 stay the same.
Only Cells 2, 6 (triage function) need to be replaced.
"""

# =====================================================================
# CELL 2 — REPLACE YOUR CURRENT CELL 2 WITH THIS
# =====================================================================

# ==========================================
# 2. FEATURE EXTRACTION & PREPROCESSING
# ==========================================
import re
from scipy.sparse import hstack

def extract_label(entities):
    if not entities: return "benign"
    if isinstance(entities, str): entities = ast.literal_eval(entities)
    return entities[0].get('label', 'benign')

df['Threat Category'] = df['entities'].apply(extract_label)
df['text_data'] = df['text'].fillna('no description')

# --- DOMAIN-SPECIFIC FEATURES ---
# These capture cybersecurity-specific patterns that TF-IDF alone misses

# IP address detection (IPv4)
df['has_ip'] = df['text_data'].str.contains(
    r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', regex=True
).astype(int)

# Hash detection (MD5=32 hex chars, SHA1=40, SHA256=64)
df['has_hash'] = df['text_data'].str.contains(
    r'\b[a-fA-F0-9]{32,64}\b', regex=True
).astype(int)

# URL detection  
df['has_url'] = df['text_data'].str.contains(
    r'https?://[^\s]+', regex=True
).astype(int)

# File path detection (Windows C:\... or Linux /etc/...)
df['has_filepath'] = df['text_data'].str.contains(
    r'[A-Z]:\\\\|/etc/|/usr/|/var/', regex=True
).astype(int)

# Email detection
df['has_email'] = df['text_data'].str.contains(
    r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', regex=True
).astype(int)

# Domain detection (e.g., example.com, malware-domain.xyz)
df['has_domain'] = df['text_data'].str.contains(
    r'\b[a-zA-Z0-9.-]+\.(com|net|org|xyz|ru|cn|io|info|biz|top)\b', regex=True
).astype(int)

# Registry key detection (Windows)
df['has_registry'] = df['text_data'].str.contains(
    r'HKLM|HKCU|HKEY_', regex=True
).astype(int)

# CVE detection (vulnerability identifiers)
df['has_cve'] = df['text_data'].str.contains(
    r'CVE-\d{4}-\d+', regex=True
).astype(int)

# Text statistics
df['text_length'] = df['text_data'].str.len()
df['word_count'] = df['text_data'].str.split().str.len()
df['upper_ratio'] = df['text_data'].apply(lambda x: sum(1 for c in x if c.isupper()) / max(len(x), 1))

# --- BUILD COMBINED FEATURE MATRIX ---
# TF-IDF features (text-based)
tfidf = TfidfVectorizer(
    max_features=5000, 
    ngram_range=(1, 3), 
    token_pattern=r'[a-zA-Z0-9\\\/:\._-]+'
)
X_tfidf = tfidf.fit_transform(df['text_data'])

# Domain-specific features (numeric)
domain_features = ['has_ip', 'has_hash', 'has_url', 'has_filepath', 
                   'has_email', 'has_domain', 'has_registry', 'has_cve',
                   'text_length', 'word_count', 'upper_ratio']

from scipy.sparse import csr_matrix
X_domain = csr_matrix(df[domain_features].values)

# Stack TF-IDF + domain features into one matrix
X = hstack([X_tfidf, X_domain])

le = LabelEncoder()
y = le.fit_transform(df['Threat Category'])

print(f"Feature matrix shape: {X.shape}")
print(f"  - TF-IDF features: {X_tfidf.shape[1]}")
print(f"  - Domain features: {X_domain.shape[1]}")
print(f"Classes: {le.classes_}")


# =====================================================================
# CELL 6 (TRIAGE FUNCTION) — REPLACE YOUR CURRENT TRIAGE CELL WITH THIS
# =====================================================================

# ==========================================
# 6. ENHANCED DEFENSE PORTAL TRIAGE
# ==========================================
import re as re_module

def defense_portal_triage(report_text):
    text_lower = report_text.lower()
    manual_category = None
    priority_boost = 0
    
    # 1. EXPANDED FORENSIC RULES (more patterns for defense use)
    # --- Hash detection ---
    if re_module.search(r'\b[a-fA-F0-9]{64}\b', report_text):
        manual_category = "SHA2"
    elif re_module.search(r'\bsha256\b|sha-256', text_lower):
        manual_category = "SHA2"
    elif re_module.search(r'\b[a-fA-F0-9]{40}\b', report_text):
        manual_category = "SHA1"
    elif re_module.search(r'\bsha1?\b|sha-1', text_lower):
        manual_category = "SHA1"
    elif re_module.search(r'\b[a-fA-F0-9]{32}\b', report_text):
        manual_category = "MD5"
    elif "hash" in text_lower:
        manual_category = "SHA2"
    
    # --- Network indicators ---
    elif re_module.search(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', report_text):
        manual_category = "IPV4"
    elif re_module.search(r'https?://[^\s]+', report_text):
        manual_category = "URL"
    elif re_module.search(r'\b[a-zA-Z0-9.-]+\.(com|net|org|xyz|ru|cn)\b', text_lower):
        manual_category = "DOMAIN"
    
    # --- File system indicators ---
    elif re_module.search(r'[A-Z]:\\\\|/etc/|/usr/|/var/', report_text):
        manual_category = "FILEPATH"
    elif re_module.search(r'HKLM|HKCU|HKEY_', report_text):
        manual_category = "REGISTRYKEY"
    
    # --- Email ---
    elif re_module.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', report_text):
        manual_category = "EMAIL"
    
    # --- CVE / Vulnerability ---
    elif re_module.search(r'CVE-\d{4}-\d+', report_text):
        manual_category = "vulnerability"
    
    # 2. CRITICAL THREAT BOOST
    critical_keywords = ["unauthorized", "wannacry", "malware", "attack", "exploit", 
                         "ransomware", "trojan", "backdoor", "rootkit", "zero-day",
                         "breach", "exfiltration", "command and control", "c2"]
    if any(word in text_lower for word in critical_keywords):
        priority_boost = 8.0
        if any(w in text_lower for w in ["unauthorized", "brute force", "injection", "exploit"]):
            manual_category = "attack-pattern"
        if any(w in text_lower for w in ["wannacry", "malware", "ransomware", "trojan", "backdoor", "rootkit"]):
            manual_category = "malware"
        if any(w in text_lower for w in ["apt", "lazarus", "fancy bear", "cozy bear"]):
            manual_category = "threat-actor"

    # 3. AI CLASSIFICATION (now with domain features)
    vec_tfidf = tfidf.transform([report_text])
    
    # Build domain features for this single report
    single_domain = csr_matrix([[
        1 if re_module.search(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', report_text) else 0,
        1 if re_module.search(r'\b[a-fA-F0-9]{32,64}\b', report_text) else 0,
        1 if re_module.search(r'https?://[^\s]+', report_text) else 0,
        1 if re_module.search(r'[A-Z]:\\\\|/etc/|/usr/|/var/', report_text) else 0,
        1 if re_module.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', report_text) else 0,
        1 if re_module.search(r'\b[a-zA-Z0-9.-]+\.(com|net|org|xyz|ru|cn|io|info|biz|top)\b', text_lower) else 0,
        1 if re_module.search(r'HKLM|HKCU|HKEY_', report_text) else 0,
        1 if re_module.search(r'CVE-\d{4}-\d+', report_text) else 0,
        len(report_text),
        len(report_text.split()),
        sum(1 for c in report_text if c.isupper()) / max(len(report_text), 1)
    ]])
    
    vec = hstack([vec_tfidf, single_domain])
    
    probs = final_model.predict_proba(vec)
    ai_confidence = np.max(probs)
    ai_category = le.classes_[np.argmax(probs)]
    
    # 4. CONFIDENCE CHECK — flag low confidence for human review
    needs_review = ai_confidence < 0.4
    
    # 5. FINAL LOGIC
    final_category = manual_category if manual_category else ai_category
    risk_score = min(10.0, (ai_confidence * 10) + priority_boost)
    
    print(f"\n--- [CERT-DEFENSE FINAL TRIAGE] ---")
    print(f"Final Classification: {final_category.upper()}")
    print(f"AI Confidence: {ai_confidence:.1%}")
    print(f"Calculated Risk: {round(risk_score, 1)}/10")
    print(f"Priority Level: {'CRITICAL' if risk_score >= 7.5 else 'HIGH' if risk_score >= 5.0 else 'MEDIUM'}")
    if needs_review:
        print(f"⚠️  LOW CONFIDENCE — Flagging for manual analyst review")
