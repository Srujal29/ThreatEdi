from app.database import SessionLocal, Rank, Unit, MitigationPlaybook, init_db

def seed_ranks(db):
    ranks = [
        ("Sepoy", 1),
        ("Lance Naik", 2),
        ("Naik", 3),
        ("Havildar", 4),
        ("Naib Subedar", 5),
        ("Subedar", 6),
        ("Subedar Major", 7),
        ("Lieutenant", 8),
        ("Captain", 9),
        ("Major", 10),
        ("Lieutenant Colonel", 11),
        ("Colonel", 12),
        ("Brigadier", 13),
        ("Major General", 14),
        ("Lieutenant General", 15),
        ("General", 16),
    ]
    for name, level in ranks:
        if not db.query(Rank).filter_by(rank_name=name).first():
            db.add(Rank(rank_name=name, hierarchy_level=level))
    db.commit()

def seed_units(db):
    units = [
        ("1st Armoured Division", "Hisar", False),
        ("4 PARA (Special Forces)", "Agra", True),
        ("9 Infantry Division", "Yol Cantonment", False),
        ("15 Corps", "Srinagar", True),
        ("17 Mountain Division", "Gangtok", True),
        ("33 Corps", "Sukna", True),
        ("Army Cyber Group", "New Delhi", False),
        ("Military Intelligence Directorate", "New Delhi", False),
        ("56 Infantry Division", "Pathankot", False),
        ("Rashtriya Rifles", "Srinagar", True),
    ]
    for name, location, active in units:
        if not db.query(Unit).filter_by(unit_name=name).first():
            db.add(Unit(unit_name=name, base_location=location, is_active_deployment=active))
    db.commit()

def seed_playbooks(db):
    playbooks = {
        "Phishing": [
            "Isolate affected email accounts immediately",
            "Block sender domain at mail gateway",
            "Scan all endpoints that interacted with the email",
            "Reset credentials for compromised accounts",
            "Issue unit-wide phishing awareness alert",
            "Report to CERT-In with IOCs",
        ],
        "Malware": [
            "Disconnect infected systems from network",
            "Capture memory dump and disk image for forensics",
            "Run full AV scan across the segment",
            "Identify malware family and check for lateral movement",
            "Block C2 domains/IPs at perimeter firewall",
            "Patch identified vulnerability exploited by malware",
            "Restore from last known clean backup",
        ],
        "Ransomware": [
            "IMMEDIATELY isolate affected systems — do NOT power off",
            "Preserve encrypted file samples for analysis",
            "Check for data exfiltration before encryption",
            "Identify ransomware variant (check ransom note, extension)",
            "DO NOT pay ransom — contact CERT-In and legal",
            "Restore from offline/air-gapped backups",
            "Conduct full network sweep for persistence mechanisms",
            "Reset all domain credentials",
        ],
        "DDoS": [
            "Activate DDoS mitigation / scrubbing service",
            "Rate-limit traffic at edge routers",
            "Identify attack type (volumetric, protocol, application)",
            "Block attacking IP ranges at firewall",
            "Enable GeoIP blocking if traffic source is identifiable",
            "Coordinate with ISP for upstream filtering",
            "Monitor for secondary attacks during DDoS distraction",
        ],
        "attack-pattern": [
            "Identify attack vector and entry point",
            "Collect logs from IDS/IPS, SIEM, and endpoints",
            "Apply relevant patches/fixes for exploited vulnerability",
            "Update firewall and WAF rules",
            "Conduct threat hunt for related indicators",
            "Brief command on attack TTP and attribution if available",
        ],
        "malware": [
            "Disconnect infected systems from network",
            "Capture forensic image of affected machine",
            "Identify malware family and propagation method",
            "Block associated IOCs (hashes, domains, IPs)",
            "Scan all connected systems for lateral movement",
            "Restore from clean backup after full remediation",
        ],
        "threat-actor": [
            "Collect all IOCs associated with the threat actor",
            "Cross-reference with known APT group TTPs",
            "Brief military intelligence on attribution",
            "Implement targeted blocking (domains, IPs, hashes)",
            "Increase monitoring on likely target systems",
            "Coordinate with national CERT for intelligence sharing",
        ],
        "vulnerability": [
            "Verify vulnerability with CVE details",
            "Assess exposure — which systems are affected",
            "Apply vendor patch or implement workaround immediately",
            "Scan for signs of exploitation",
            "Update vulnerability management tracker",
            "Schedule follow-up scan to confirm remediation",
        ],
        "benign": [
            "No immediate action required",
            "Log event for audit trail",
            "Verify classification with analyst if confidence is low",
        ],
    }
    for category, steps in playbooks.items():
        if not db.query(MitigationPlaybook).filter_by(incident_category=category).first():
            db.add(MitigationPlaybook(incident_category=category, action_steps=steps))
    db.commit()

def seed_all():
    init_db()
    db = SessionLocal()
    try:
        seed_ranks(db)
        seed_units(db)
        seed_playbooks(db)
        print(" Database seeded successfully!")
    finally:
        db.close()

if __name__ == "__main__":
    seed_all()
