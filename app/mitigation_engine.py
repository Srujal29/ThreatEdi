import json
from typing import List, Dict

MITIGATION_PLAYBOOKS: Dict[str, List[str]] = {
    "phishing": [
        "DO NOT click any links or download attachments.",
        "Report the suspicious sender to the unit IT/Security team immediately.",
        "If credentials were entered, change passwords immediately and alert superiors.",
        "Enable or verify Two-Factor Authentication (2FA) is active.",
    ],
    "malware": [
        "IMMEDIATELY disconnect the affected device from all networks (Wi-Fi, LAN).",
        "Do NOT turn off the device (preserve RAM for forensics).",
        "Avoid inserting any external USB drives or removable media.",
        "Inform the cybersecurity operations center (CSOC) immediately.",
    ],
    "ransomware": [
        "Disconnect the infected machine from the network IMMEDIATELY.",
        "Do NOT pay the ransom or communicate with the threat actor.",
        "Identify and disconnect any shared network drives to prevent lateral spread.",
        "Notify the chain of command and await CSOC response protocols.",
    ],
    "ddos": [
        "Report the service degradation to network administrators immediately.",
        "Do not repeatedly attempt to access the affected portal.",
        "Switch to backup/analog communication channels for critical operations.",
        "Await official word from command before resuming portal usage.",
    ],
    "impersonation": [
        "Verify identity through official, out-of-band military channels.",
        "Do NOT share ANY sensitive or operational information.",
        "Report the impersonator's details to the counter-intelligence unit.",
    ],
    "opsec_risk": [
        "Remove the identified sensitive content immediately.",
        "Notify your superior authority about the potential leak.",
        "Review and lock down privacy settings on all linked accounts.",
        "Acknowledge and review the unit's OPSEC and social media guidelines.",
    ],
    "financial_fraud": [
        "Contact your bank or financial institution immediately.",
        "Request an immediate freeze on all affected accounts.",
        "Preserve all evidence (emails, transaction IDs, SMS).",
        "Report the incident to the military police and cyber cell.",
    ],
    "attack-pattern": [
        "Monitor accounts for unauthorized login attempts.",
        "Change passwords for critical operational portals immediately.",
        "Report the unusual activity pattern to unit IT officers.",
    ],
    "threat-actor": [
        "Assume communications may be compromised - maintain strict OPSEC.",
        "Elevate situational awareness and physical security of devices.",
        "Await specific intelligence briefs from command.",
    ],
    "vulnerability": [
        "Ensure all systems are updated to the latest available patches.",
        "Avoid using the vulnerable software/protocol until cleared by IT.",
        "Report any unpatched critical systems to the unit security officer.",
    ]
}

DEFAULT_MITIGATION = [
    "Log out of all current sessions and disconnect from the network if compromised.",
    "Do not delete any files or logs; preserve the state for investigation.",
    "Report the incident to your immediate commanding officer and IT support.",
    "Maintain strict OPSEC until the situation is resolved."
]

def get_mitigation_steps(category: str) -> List[str]:
    if not category:
        return DEFAULT_MITIGATION
        
    cat_lower = category.lower()
    
    if cat_lower in MITIGATION_PLAYBOOKS:
        return MITIGATION_PLAYBOOKS[cat_lower]
        
    for key, steps in MITIGATION_PLAYBOOKS.items():
        if key in cat_lower:
            return steps
            
    return DEFAULT_MITIGATION

if __name__ == "__main__":
    print("=" * 60)
    print("  DEFENCE MITIGATION ENGINE TEST")
    print("=" * 60)
    
    test_categories = ["phishing", "malware", "opsec_risk", "unknown_threat"]
    
    for cat in test_categories:
        print(f"\n Threat Category: {cat.upper()}")
        print("-" * 60)
        
        steps = get_mitigation_steps(cat)
        for i, step in enumerate(steps, 1):
            print(f"  {i}. {step}")
            
    print("\n" + "=" * 60)
