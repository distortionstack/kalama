# core/fix_lookup.py — อ่านวิธีแก้จากผลสแกนโดยตรง
import json

def get_fixes(scan_path):
    scan = json.load(open(scan_path))
    fixes = {}
    for result in scan["Results"]:
        for v in result.get("Vulnerabilities", []):
            fixes[v["VulnerabilityID"]] = {
                "package": v["PkgName"],
                "installed": v["InstalledVersion"],
                "fixed_version": v.get("FixedVersion"),   # อาจว่างถ้ายังไม่มี patch
                "type": result.get("Type"),                # os / maven / npm / pip ...
            }
    return fixes


def choose_strategy(fix, pkg_type):
    if not fix["fixed_version"]:
        return "apply_mitigation"          # ยังไม่มี patch → ไปอ่าน References/GHSA หาวิธีบรรเทา
    if pkg_type in ("debian", "alpine", "redhat"):
        return "swap_base_image"           # package OS → มักแก้ที่ base image
    return "bump_dependency"               # dependency ของแอป → อัปเวอร์ชันตรงๆ
