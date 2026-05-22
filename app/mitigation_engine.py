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


api_key = os.getenv("GROQ_API_KEY")
client = Groq(api_key=api_key) if api_key else None


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

    if not client:
        return {
            "category": category,
            "priority": priority_level,
            "risk_score": risk_score,
            "ml_confidence": ml_confidence,
            "mode": "fallback_static",
            "action_steps": base_steps,
            "error": "Groq API key not configured.",
        }

    prompt = f"""
You are an expert cybersecurity incident response assistant for a defence cyber incident portal.

Your job is to generate dynamic mitigation advice and infer the specific threat classification.

STRICT FORMAT RULES:
1. The first line of your response MUST be exactly: "INFERRED THREAT: <Specific Inferred Threat Category/Type>"
   For example: "INFERRED THREAT: Server Scanning & Reconnaissance" or "INFERRED THREAT: Credential Harvesting Phishing".
2. After the first line, leave a blank line.
3. Then, list between 6 and 10 concise mitigation steps as bullet points.

STRICT CONTENT RULES:
- Use the approved mitigation steps provided below as the foundation.
- NEVER contradict the approved steps.
- Treat the ML classification as a supporting signal, NOT absolute truth.
- If the incident report clearly contradicts the ML category, prioritize the actual incident narrative.
- Infer the likely real threat from the user's report.
- Expand mitigation based on the full incident context.
- If the user already clicked/opened/shared credentials, adapt accordingly.
- If the threat is critical, emphasize immediate escalation.
- If active deployment is true, mention operational security implications.
- If AI confidence is low, mention analyst/manual review.

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

        # Parse inferred threat type and steps
        lines = [line.strip() for line in content.split("\n") if line.strip()]
        inferred_threat = category.replace("-", " ").title() if category else "Unknown Threat"
        steps = []

        for line in lines:
            if line.upper().startswith("INFERRED THREAT:"):
                inferred_threat = line[len("INFERRED THREAT:"):].strip("*-•\"' ")
            else:
                cleaned_line = line.strip("*-• ")
                if cleaned_line:
                    steps.append(cleaned_line)

        if not steps:
            steps = base_steps

        # Map inferred threat category to known categories for classification integrity
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

        return {
            "category": effective_category,
            "inferred_threat_type": inferred_threat,
            "priority": priority_level,
            "risk_score": risk_score,
            "ml_confidence": ml_confidence,
            "mode": "ai_dynamic",
            "action_steps": steps,
        }

    except Exception as e:
        return {
            "category": category,
            "inferred_threat_type": category.replace("-", " ").title() if category else "Unknown Threat",
            "priority": priority_level,
            "risk_score": risk_score,
            "ml_confidence": ml_confidence,
            "mode": "fallback_static",
            "action_steps": base_steps,
            "error": str(e),
        }

import google.generativeai as genai
import requests
import json
from io import BytesIO
from PIL import Image

def analyze_evidence_with_gemini(image_url: str) -> str:
    """
    Downloads the image from the given URL and uses Gemini Vision
    to analyze the evidence.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return "Gemini API key not configured."
    
    genai.configure(api_key=api_key)
    
    try:
        response = requests.get(image_url)
        response.raise_for_status()
        img = Image.open(BytesIO(response.content))
        
        model = genai.GenerativeModel('gemini-2.5-flash')
        prompt = "Analyze this image which was submitted as evidence for a cybersecurity incident. Briefly describe what is visible and whether it confirms any malicious activity or anomalies."
        result = model.generate_content([prompt, img])
        return result.text.strip()
    except Exception as e:
        print(f"Gemini Vision error: {str(e)}")
        return f"Failed to analyze evidence: {str(e)}"

def fallback_classification(text: str) -> str:
    """
    Uses Groq to classify the incident when local model confidence is < 70%.
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return "Unknown"
        
    client = Groq(api_key=api_key)
    
    prompt = f"""
    You are a cybersecurity expert. Classify the following incident report into EXACTLY ONE of these categories:
    Phishing, Ransomware, DDoS, Malware, attack-pattern, threat-actor, vulnerability, identity, benign.
    
    Report: "{text}"
    
    Respond ONLY with the exact category name. Nothing else.
    """
    
    try:
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
            temperature=0.0,
            max_tokens=20,
        )
        cat = chat_completion.choices[0].message.content.strip()
        
        valid_cats = ["Phishing", "Ransomware", "DDoS", "Malware", "attack-pattern", "threat-actor", "vulnerability", "identity", "benign"]
        for v in valid_cats:
            if v.lower() in cat.lower():
                return v
        return cat
    except Exception as e:
        print(f"Groq Classification error: {str(e)}")
        return "Unknown"
