import json
import os
from groq import Groq
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


client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def get_base_playbook(category: str) -> List[str]:
    if not category:
        return DEFAULT_MITIGATION

    cat_lower = category.lower()

    if cat_lower in MITIGATION_PLAYBOOKS:
        return MITIGATION_PLAYBOOKS[cat_lower]

    for key, steps in MITIGATION_PLAYBOOKS.items():
        if key in cat_lower:
            return steps

    return DEFAULT_MITIGATION


def generate_dynamic_mitigation(
    category: str,
    risk_score: float,
    priority_level: str,
    ml_confidence: float,
    report_text: str,
    rank_level: int,
    is_active_deployment: bool,
) -> Dict:

    base_steps = get_base_playbook(category)

    prompt = f"""
You are an expert cybersecurity incident response assistant for a defence cyber incident portal.

Your job is to generate dynamic mitigation advice.

STRICT RULES:
- Use the approved mitigation steps provided below as the foundation.
- NEVER contradict the approved steps.
- Treat the ML classification as a supporting signal, NOT absolute truth.
- If the incident report clearly contradicts the ML category, prioritize the actual incident narrative.
- Infer the likely real threat from the user's report if necessary.
- Expand mitigation based on the full incident context.
- If the user already clicked/opened/shared credentials, adapt accordingly.
- If the threat is critical, emphasize immediate escalation.
- If active deployment is true, mention operational security implications.
- If AI confidence is low, mention analyst/manual review.
- Return ONLY bullet points.
- Return between 6 and 10 concise mitigation steps.

APPROVED BASE MITIGATION:
{chr(10).join("- " + step for step in base_steps)}

INCIDENT CONTEXT:
Threat Category: {category}
Risk Score: {risk_score}/10
Priority Level: {priority_level}
ML Confidence: {ml_confidence}
Rank Level: {rank_level}
Active Deployment: {is_active_deployment}

USER INCIDENT REPORT:
{report_text}

TASK:
1. Determine the most likely REAL cyber threat category from the incident narrative.
2. Treat the ML category as a hint, not ground truth.
3. Use the approved mitigation steps as the foundation.
4. Add incident-specific mitigation actions.
5. If credentials were shared, clicked links, downloaded files, or impersonation is involved, adapt accordingly.
6. Mention the likely threat category in the first bullet.
"""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "You are a cybersecurity mitigation expert."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.2,
            max_tokens=500,
        )

        content = response.choices[0].message.content

        if not content:
            raise Exception("Groq returned empty response")

        content = content.strip()

        if content.startswith("```json"):
            content = content.replace("```json", "").replace("```", "").strip()
        elif content.startswith("```"):
            content = content.replace("```", "").strip()

        effective_category = category

        content_lower = content.lower()

        known_categories = [
            "phishing",
            "malware",
            "ransomware",
            "ddos",
            "impersonation",
            "opsec_risk",
            "financial_fraud",
            "attack-pattern",
            "threat-actor",
            "vulnerability"
        ]

        for cat in known_categories:
            if cat in content_lower:
                effective_category = cat
                break

        steps = [
            line.strip("*-• ").strip()
            for line in content.split("\n")
            if line.strip()
        ]

        if not steps:
            steps = base_steps

        return {
            "category": effective_category,
            "priority": priority_level,
            "risk_score": risk_score,
            "ml_confidence": ml_confidence,
            "mode": "ai_dynamic",
            "action_steps": steps,
        }

    except Exception as e:
        return {
            "category": category,
            "priority": priority_level,
            "risk_score": risk_score,
            "ml_confidence": ml_confidence,
            "mode": "fallback_static",
            "action_steps": base_steps,
            "error": str(e),
        }