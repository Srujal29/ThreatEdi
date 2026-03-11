import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.risk_engine import compute_risk_score, MAX_HIERARCHY_LEVEL, CRITICAL_KEYWORDS, HIGH_SEVERITY_CATEGORIES

def calculate_expected(ml_category, ml_confidence, report_text, rank_hierarchy_level, is_active_deployment):
    text_lower = report_text.lower()

    if ml_category.lower() == "benign":
        conf_comp = (1.0 - ml_confidence) * 10.0
    else:
        conf_comp = ml_confidence * 10.0
    conf_w = conf_comp * 0.4

    rank_w = (rank_hierarchy_level / MAX_HIERARCHY_LEVEL) * 10.0 * 0.2

    dep_w = (8.0 if is_active_deployment else 2.0) * 0.2

    kw_hits = sum(1 for kw in CRITICAL_KEYWORDS if kw in text_lower)
    sev_comp = min(10.0, kw_hits * 2.5)
    if ml_category in HIGH_SEVERITY_CATEGORIES:
        sev_comp = max(sev_comp, 6.0)
    sev_w = sev_comp * 0.2

    total = round(min(10.0, conf_w + rank_w + dep_w + sev_w), 1)
    
    if total >= 7.5: p = "Critical"
    elif total >= 5.0: p = "High"
    elif total >= 2.5: p = "Medium"
    else: p = "Low"
    return total, p


TEST_SCENARIOS = [
    {
        "name": "General on active deployment reporting Ransomware (Max Risk Profile)",
        "ml_category": "Ransomware",
        "ml_confidence": 0.95,
        "report_text": "wannacry ransomware attack detected on primary c2 server",
        "rank_hierarchy_level": 16, # General
        "is_active_deployment": True,
    },
    {
        "name": "Sepoy on base reporting generic Phishing (Low-Mid Risk Profile)",
        "ml_category": "Phishing",
        "ml_confidence": 0.85,
        "report_text": "received a suspicious phishing email asking for login",
        "rank_hierarchy_level": 1, # Sepoy
        "is_active_deployment": False,
    },
    {
        "name": "Lieutenant on base reporting routine benign log (Lowest Risk)",
        "ml_category": "benign",
        "ml_confidence": 0.99,
        "report_text": "system backup completed normally",
        "rank_hierarchy_level": 8, # Lieutenant
        "is_active_deployment": False,
    },
    {
        "name": "Major on active deployment reporting DDoS (High Risk Profile)",
        "ml_category": "DDoS",
        "ml_confidence": 0.90,
        "report_text": "ddos flooding our unit network",
        "rank_hierarchy_level": 10, # Major
        "is_active_deployment": True,
    },
    {
        "name": "Colonel on base reporting APT espionage (Critical Risk despite no active deployment)",
        "ml_category": "threat-actor",
        "ml_confidence": 0.80,
        "report_text": "apt group spotted attempting data theft and exfiltration",
        "rank_hierarchy_level": 12, # Colonel
        "is_active_deployment": False,
    }
]

print("=" * 100)
print(" RISK ENGINE VALIDATION — Expected vs Real Calculation")
print("=" * 100)

all_passed = True

for i, scenario in enumerate(TEST_SCENARIOS, 1):
    name = scenario.pop("name")
    
    # 1. Expected calculation manually computed to double-check
    exp_score, exp_priority = calculate_expected(**scenario)
    
    # 2. Real calculation from risk_engine.py
    real_result = compute_risk_score(**scenario)
    real_score = real_result["risk_score"]
    real_priority = real_result["priority_level"]
    
    match = exp_score == real_score and exp_priority == real_priority
    if not match:
        all_passed = False
        
    print(f"\nScenario {i}: {name}")
    print(f"  Inputs: Rank={scenario['rank_hierarchy_level']}, Deployment={scenario['is_active_deployment']}, "
          f"ML=[{scenario['ml_category']}:{scenario['ml_confidence']:.2f}]")
    print(f"  Text:   '{scenario['report_text']}'")
    
    if match:
        print(f"  [PASS] Score: {real_score}/10 | Priority: {real_priority}")
        print(f"     Breakdown: {real_result['breakdown']}")
    else:
        print(f"  [FAIL] MISMATCH!")
        print(f"     Expected: Score: {exp_score}/10 | Priority: {exp_priority}")
        print(f"     Real:     Score: {real_score}/10 | Priority: {real_priority}")
        print(f"     Real Breakdown: {real_result['breakdown']}")

print("\n" + "=" * 100)
if all_passed:
    print("[PASS] ALL TESTS PASSED! Risk Engine accurately computes contextual risk.")
else:
    print("[FAIL] SOME TESTS FAILED! Check logic mismatch.")
print("=" * 100)
