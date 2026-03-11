
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

MAX_HIERARCHY_LEVEL = 16  

def compute_risk_score(
    ml_category: str,
    ml_confidence: float,
    report_text: str,
    rank_hierarchy_level: int = 1,
    is_active_deployment: bool = False,
) -> dict:
    text_lower = report_text.lower()

    if ml_category.lower() in ["benign"]:
        confidence_component = (1.0 - ml_confidence) * 10.0  
    else:
        confidence_component = ml_confidence * 10.0
    confidence_weighted = confidence_component * 0.40

    rank_component = (rank_hierarchy_level / MAX_HIERARCHY_LEVEL) * 10.0
    rank_weighted = rank_component * 0.20

    deployment_component = 8.0 if is_active_deployment else 2.0
    deployment_weighted = deployment_component * 0.20

    keyword_hits = sum(1 for kw in CRITICAL_KEYWORDS if kw in text_lower)
    severity_component = min(10.0, keyword_hits * 2.5)

    if ml_category in HIGH_SEVERITY_CATEGORIES:
        severity_component = max(severity_component, 6.0)

    severity_weighted = severity_component * 0.20

    risk_score = round(
        min(10.0, confidence_weighted + rank_weighted + deployment_weighted + severity_weighted),
        1,
    )

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
