"""Test the ML model on custom army-style threat reports — output to file."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.ml_model import predict, load_model

load_model()

TEST_CASES = [
    ("Suspicious phishing email received by battalion HQ from unknown sender asking for login credentials.", "Phishing"),
    ("WannaCry ransomware detected on 3 workstations. Files encrypted with .wcry extension.", "Ransomware"),
    ("DDoS attack targeting command portal. 500k requests per second from botnet.", "DDoS"),
    ("Trojan malware found in USB drive. Keylogger identified exfiltrating data.", "Malware"),
    ("Unauthorized access from IP 192.168.1.50 targeting personnel database.", "attack-pattern"),
    ("APT group Fancy Bear targeting military communications.", "threat-actor"),
    ("CVE-2024-1234 vulnerability found in Apache server on base network.", "vulnerability"),
    ("Malware signature detected in encrypted traffic from command server.", "Malware"),
    ("Phishing SMS with link to fake leave portal sent to officers.", "Phishing"),
    ("Ransomware gang demanding 50 BTC after encrypting document server.", "Ransomware"),
    ("DDoS flooding military intranet with UDP packets.", "DDoS"),
    ("Spyware on officer mobile transmitting location data.", "Malware"),
    ("Brute force on VPN - 10000 failed logins from Chinese IP.", "attack-pattern"),
    ("Routine backup completed successfully for server cluster 4.", "benign"),
    ("Antivirus update deployed across all terminals.", "benign"),
    ("Zero-day exploit targeting Windows SMB protocol.", "vulnerability"),
    ("Malicious macro Excel attachment sent to 200 army emails.", "Phishing"),
    ("Backdoor via supply chain compromise in monitoring software.", "Malware"),
    ("HTTP flood from 150 IPs targeting recruitment portal.", "DDoS"),
    ("Classified data exfiltrated through covert C2 channel.", "Malware"),
]

lines = []
correct = 0
for i, (text, expected) in enumerate(TEST_CASES, 1):
    result = predict(text)
    pred = result["category"]
    conf = result["confidence"]
    ok = pred.lower() == expected.lower()
    if ok:
        correct += 1
    flag = "OK" if ok else "XX"
    line = f"{i:2}. [{flag}] Expected: {expected:<16} Got: {pred:<16} Conf: {conf:.3f}"
    if not ok:
        top3 = ", ".join([f"{x['category']}({x['confidence']:.2f})" for x in result["top_predictions"]])
        line += f"\n          Top-3: {top3}"
    lines.append(line)

with open("test_results.txt", "w") as f:
    f.write("ML MODEL ACCURACY TEST - Custom Army Threat Reports\n")
    f.write("=" * 80 + "\n\n")
    for l in lines:
        f.write(l + "\n")
    f.write("\n" + "=" * 80 + "\n")
    f.write(f"ACCURACY: {correct}/{len(TEST_CASES)} = {correct/len(TEST_CASES)*100:.1f}%\n")
    f.write(f"Correct: {correct} | Wrong: {len(TEST_CASES) - correct}\n")

print(f"Results written to test_results.txt")
print(f"ACCURACY: {correct}/{len(TEST_CASES)} = {correct/len(TEST_CASES)*100:.1f}%")
