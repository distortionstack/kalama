# ส่วนที่ 2 — หาเป้าหมายที่มีช่องโหว่จริง (Testbed)
# เราไม่สร้างช่องโหว่เอง แต่ใช้ Vulhub คลังสำเร็จรูปที่มี container ช่องโหว่พร้อม PoC เป็นร้อยตัว

git clone https://github.com/vulhub/vulhub.git
cd vulhub/log4j/CVE-2021-44228     # ตัวอย่าง Log4Shell ที่ได้ตั้ง
docker compose up -d                # สั่งรันเป้าหมาย

# เปิดเบราว์เซอร์ไปที่ http://localhost:8080 จะเห็นเว็บแอปที่ (แอบ) มีช่องโหว่ log4j อยู่ข้างใน
