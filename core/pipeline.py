# core/pipeline.py
from core.exploiter import run_exploit
from core.corrector import correct

def validate_and_fix(case_path):
    before = run_exploit(case_path)   # ก่อนแก้→คาดว่า exploited=True
    report = {"cve": before["cve"], "before": before["exploited"]}

    if before["exploited"]:
        correct_case(case_path)          # แก้อัตโนมัติ
        redeploy_fixed_target()          # รัน image ที่แก้แล้ว
        after = run_exploit(case_path)   # ยิงซ้ำ→คาดว่า exploited=False
        report["after"] = after["exploited"]
        report["fixed"] = (not after["exploited"])   # ปิดช่องได้ไหม

    return report
