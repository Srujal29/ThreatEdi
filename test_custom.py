import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.ml_model import predict, load_model
from app.risk_engine import compute_risk_score
from app.mitigation_engine import get_mitigation_steps

load_model()

TEST_CASES = [
    ("Suspicious phishing email received by battalion HQ from unknown sender asking for login credentials.", "Phishing", 12), 
    ("WannaCry ransomware detected on 3 workstations. Files encrypted with .wcry extension.", "Ransomware", 10), 
    ("DDoS attack targeting command portal. 500k requests per second from botnet.", "DDoS", 14), 
    ("Routine backup completed successfully for server cluster 4.", "benign", 5), 
    ("Malware signature detected in encrypted traffic from command server.", "Malware", 8), 
]

print("\n" + "=" * 90)
print(" CYBER INCIDENT PORTAL - END-TO-END PIPELINE TEST")
print("=" * 90)

correct_ml = 0

for i, (text, expected_ml, rank_level) in enumerate(TEST_CASES, 1):
    print(f"\n[ REPORT {i} ]")
    print(f"  Incident Text : '{text}'")
    print(f"  Context       : Rank Level {rank_level}, Active Deployment: True")
    
    ml_result = predict(text)
    pred_cat = ml_result["category"]
    conf = ml_result["confidence"]
    
    if pred_cat.lower() == expected_ml.lower():
        correct_ml += 1
        ml_status = f"[OK] (Expected: {expected_ml})"
    else:
        ml_status = f"[FAIL] (Expected: {expected_ml})"
        
    print(f"\n  [STEP 1] ML CLASSIFICATION")
    print(f"    Category    : {pred_cat.upper()} {ml_status}")
    print(f"    Confidence  : {conf:.2f}")

    risk_result = compute_risk_score(
        ml_category=pred_cat,
        ml_confidence=conf,
        report_text=text,
        rank_hierarchy_level=rank_level,
        is_active_deployment=True
    )
    score = risk_result["risk_score"]
    priority = risk_result["priority_level"]
    
    print(f"  [STEP 2] RISK ENGINE")
    print(f"    Priority    : {priority}")
    print(f"    Risk Score  : {score}/10")

    steps = get_mitigation_steps(pred_cat)
    
    print(f"  [STEP 3] MITIGATION PLAYBOOK")
    for j, step in enumerate(steps, 1):
        print(f"    {j}. {step}")
        
    print("-" * 90)

print(f"\n[PASS] ML ACCURACY ON TEST BATCH: {correct_ml}/{len(TEST_CASES)} = {correct_ml/len(TEST_CASES)*100:.1f}%\n")
