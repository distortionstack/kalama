# core/corrector.py
import subprocess

def bump_dependency(case):
    """เปลี่ยนเวอร์ชัน library ที่มีช่องโหว่ให้เป็นเวอร์ชันที่แก้แล้ว"""
    pkg = case["correction"]["package"]
    ver = case["correction"]["fixed_version"]
    # แก้ Dockerfile / pom.xml ให้ใช้เวอร์ชันใหม่ (ตัวอย่างแบบง่าย)
    subprocess.run(["sed", "-i",
        f"s/{pkg}:.*/{pkg}:{ver}/", "target/Dockerfile"])
    # build image ใหม่
    subprocess.run(["docker", "build", "-t", "target:fixed", "target/"])

def swap_base_image(case):
    """เปลี่ยน base image เป็นตัวที่ patched แล้ว หรือ distroless ที่เล็ก/ปลอดภัยกว่า"""
    ...

STRATEGIES = {
    "bump_dependency": bump_dependency,
    "swap_base_image": swap_base_image,
}

def correct(case):
    STRATEGIES[case["correction"]["strategy"]](case)
