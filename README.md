# Exploitation-Validated Vulnerability Prioritization

ระบบจัดลำดับช่องโหว่ Container ที่พิสูจน์ด้วยการโจมตีจริง (ยิงจริง → แก้อัตโนมัติ → ยิงซ้ำเพื่อพิสูจน์ว่าปิดช่องได้)
โค้ดในโปรเจกต์นี้ลอกมาจาก `GUIDE1.pdf` ตรงๆ ทุก section ยังไม่ได้เชื่อมกันเป็น pipeline สมบูรณ์

## โครงสร้างไฟล์ปัจจุบัน

```
cases/
  cve-2021-44228.yaml     # นิยาม test case: เป้าหมาย, วิธียิง, วิธีแก้
adapters/
  log4shell.py             # ตัวยิงช่องโหว่ Log4Shell
core/
  oracle.py                 # ตัวเช็คว่ายิงสำเร็จไหม (ฟังพอร์ต callback)
  exploiter.py               # ยิง 1 ครั้งแล้วบอกผล (สำเร็จ/ไม่สำเร็จ)
  scoring.py                  # EPSS + CISA KEV + risk_score (ส่วนที่ 4)
  fix_lookup.py                # อ่านวิธีแก้จากผลสแกน Trivy (ส่วนที่ 7.1)
  corrector.py                  # แก้ช่องโหว่ตามกลยุทธ์ (bump_dependency / swap_base_image)
  pipeline.py                    # ยิงก่อนแก้ → แก้ → ยิงซ้ำ (ต่อ 1 case)
dashboard.py                      # หน้าเว็บ Streamlit โชว์ผลจาก results.csv
evaluate.py                        # คำนวณ precision/recall/F1 จาก results.csv
setup.sh / testbed.sh / scan.sh /
reachability.sh / requirements.txt  # คำสั่งเตรียมแล็บ (ส่วนที่ 1-3, 5)
```

## สิ่งที่ยังขาด เพื่อให้ pipeline สมบูรณ์

**1. ฟังก์ชันที่ `pipeline.py` เรียกใช้ แต่ไม่มีใครนิยามไว้**
- `correct_case()` — pipeline.py เรียกชื่อนี้ แต่ `corrector.py` มีแค่ `correct(case)` (ชื่อไม่ตรง และรับ argument คนละแบบ: pipeline ส่ง path, corrector ต้องการ case ที่ parse แล้ว)
- `redeploy_fixed_target()` — ไม่มีนิยามที่ไหนเลยในเล่ม ต้องเขียนเองว่าจะ stop container เดิม แล้วรัน image ที่ build ใหม่ (`target:fixed`) อย่างไร

**2. ฟังก์ชันที่เป็นแค่ stub**
- `swap_base_image()` ใน `corrector.py` ยังเป็น `...` เฉยๆ ยังไม่มี logic จริง

**3. ไม่มีตัวควบคุมภาพรวม (orchestrator)**
- ไม่มีสคริปต์ที่ loop ผ่าน `cases/*.yaml` ทุกไฟล์ → เรียก `validate_and_fix()` ทีละตัว → รวมผลเป็น `results.csv`
- ตอนนี้มีแต่ฟังก์ชันที่ทำทีละ 1 case เท่านั้น

**4. โครงสร้างข้อมูลไม่ตรงกันระหว่างไฟล์**
- `pipeline.py` คืนค่า dict คีย์ `cve / before / after / fixed`
- แต่ `dashboard.py` และ `evaluate.py` อ่าน `results.csv` โดยคาดหวังคอลัมน์ `cve / predicted / exploited / fixed / predicted_high`
- ต้อง map ชื่อคีย์ให้ตรงกันตอนเขียนลง csv

**5. Scoring layer (ส่วนที่ 4) ยังลอยตัว**
- `risk_score()` / `get_epss()` / `load_kev()` ไม่มีจุดไหนเรียกใช้จริง ไม่มีใครเอาผลไปเขียนเป็น `predicted_priority` ใน case yaml หรือ `predicted_high` ใน results.csv

**6. Fix lookup (ส่วนที่ 7.1) ก็ยังลอยตัว**
- `get_fixes()` / `choose_strategy()` อ่านผลสแกน Trivy ได้ แต่ไม่มีใครเอาผลลัพธ์ไปเขียนลงบล็อก `correction:` ใน case yaml อัตโนมัติ (ตอนนี้ต้องกรอกมือ)

**7. Reachability (ส่วนที่ 5) มีแค่คำสั่งติดตั้ง**
- ยังไม่มี logic ที่เอา output จาก Kubescape มาแปลงเป็นค่า `reachable = True/False` แล้วส่งเข้า `risk_score()`

**8. `bump_dependency()` อ้างอิง path ตายตัว**
- ใช้ `target/Dockerfile` และ `target/` ตรงๆ แต่ไม่มีขั้นตอนไหนเตรียม target repo ไว้ที่ path นั้นก่อน

**9. ไฟล์ที่คู่มืออ้างถึงในผังโฟลเดอร์ แต่ไม่มีเนื้อหาให้**
- `cases/cve-2017-5638.yaml`
- `adapters/struts_rce.py`
- `results.csv` (ไฟล์ผลลัพธ์ที่เกิดจากการรันจริง)

## สรุป

ส่วน "ยิง" (ส่วนที่ 6) และ "แก้" (ส่วนที่ 7) ทำงานได้เดี่ยวๆ ในตัวเอง แต่ยังไม่มีตัวเชื่อมให้เป็น loop เต็มระบบ ไม่มีตัวสร้าง `results.csv` และ scoring / fix-lookup / reachability สามชิ้นเขียนแยกไว้เฉยๆ ยังไม่ต่อสายเข้ากับ pipeline หลัก
