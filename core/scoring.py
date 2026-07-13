# core/scoring.py
import requests

def get_epss(cve_id):
    url = f"https://api.first.org/data/v1/epss?cve={cve_id}"
    data = requests.get(url).json()["data"]
    return float(data[0]["epss"]) if data else 0.0

print(get_epss("CVE-2021-44228"))   # เช่น 0.97 = โอกาสถูกโจมตีสูงมาก


def load_kev():
    url = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"
    items = requests.get(url).json()["vulnerabilities"]
    return {v["cveID"] for v in items}   # เก็บเป็น set ของ CVE id

kev = load_kev()
print("CVE-2021-44228" in kev)   # True = อยู่ในบัญชีอันตรายจริง


def risk_score(cvss, epss, in_kev, reachable):
    score = cvss                       # ฐานจากความรุนแรง (0-10)
    score *= (1 + epss)                # คูณด้วยโอกาสถูกโจมตี
    if in_kev:     score += 3          # ถ้าเคยถูกโจมตีจริง บวกหนัก
    if reachable: score += 2           # ถ้าโค้ดถูกเรียกใช้จริง บวกอีก
    return round(min(score, 15), 2)
