# =============================================================
# RISK ENGINE — Context-Aware Risk Scoring
# =============================================================
# Computes a composite risk score (0–10) using:
#   - ML confidence (40%)
#   - Rank hierarchy (20%)
#   - Active deployment status (20%)
#   - Threat severity keywords (20%)

CRITICAL_KEYWORDS = [
    "unauthorized", "wannacry", "malware", "attack", "exploit",
    "ransomware", "trojan", "backdoor", "rootkit", "zero-day",
    "breach", "exfiltration", "command and control", "c2",
    "apt", "spyware", "keylogger", "data theft", "brute force",
]

HIGH_SEVERITY_CATEGORIES = [
    "malware", "ransomware", "attack-pattern", "threat-actor",
    "Malware", "Ransomware", "DDoS",
]

MAX_HIERARCHY_LEVEL = 16  # General


def compute_risk_score(
    ml_category: str,
    ml_confidence: float,
    report_text: str,
    rank_hierarchy_level: int = 1,
    is_active_deployment: bool = False,
) -> dict:
    """
    Compute a weighted risk score and priority level.

    Returns:
        dict with keys: risk_score, priority_level, breakdown
    """
    text_lower = report_text.lower()

    # --- Component 1: ML Confidence Score (40% weight) ---
    # If the ML predicts a threatening category with high confidence, risk is high
    if ml_category.lower() in ["benign"]:
        confidence_component = (1.0 - ml_confidence) * 10.0  # benign = low risk
    else:
        confidence_component = ml_confidence * 10.0
    confidence_weighted = confidence_component * 0.40

    # --- Component 2: Rank Hierarchy (20% weight) ---
    # Higher-ranked targets are higher-value targets → more risk
    rank_component = (rank_hierarchy_level / MAX_HIERARCHY_LEVEL) * 10.0
    rank_weighted = rank_component * 0.20

    # --- Component 3: Active Deployment (20% weight) ---
    # Incidents from active deployment zones get a flat risk boost
    deployment_component = 8.0 if is_active_deployment else 2.0
    deployment_weighted = deployment_component * 0.20

    # --- Component 4: Threat Severity Keywords (20% weight) ---
    keyword_hits = sum(1 for kw in CRITICAL_KEYWORDS if kw in text_lower)
    severity_component = min(10.0, keyword_hits * 2.5)

    # Boost if ML category itself is high-severity
    if ml_category in HIGH_SEVERITY_CATEGORIES:
        severity_component = max(severity_component, 6.0)

    severity_weighted = severity_component * 0.20

    # --- FINAL SCORE ---
    risk_score = round(
        min(10.0, confidence_weighted + rank_weighted + deployment_weighted + severity_weighted),
        1,
    )

    # --- PRIORITY MAPPING ---
    if risk_score >= 7.5:
        priority = "Critical"
    elif risk_score >= 5.0:
        priority = "High"
    elif risk_score >= 2.5:
        priority = "Medium"
    else:
        priority = "Low"

    return {
        "risk_score": risk_score,
        "priority_level": priority,
        "breakdown": {
            "ml_confidence_component": round(confidence_weighted, 2),
            "rank_component": round(rank_weighted, 2),
            "deployment_component": round(deployment_weighted, 2),
            "severity_component": round(severity_weighted, 2),
            "keyword_hits": keyword_hits,
        },
    }
