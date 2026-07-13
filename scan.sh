# ส่วนที่ 3 — สแกนหาช่องโหว่ (เห็นปัญหากับตา)
# ใช้ Trivy สแกนเนอร์ยอดนิยม (ฟรี)

# ติดตั้ง Trivy
sudo apt install -y wget
wget https://github.com/aquasecurity/trivy/releases/download/v0.50.0/trivy_0.50.0_Linux-64bit.deb
sudo dpkg -i trivy_0.50.0_Linux-64bit.deb

# สแกน image ของเป้าหมาย แล้วเซฟผลเป็น JSON
trivy image --format json --output scan.json vulhub/log4j:2.14.1

# เปิด scan.json จะเห็น CVE เป็นร้อยๆ ตัว — นี่แหละคือปัญหา alert fatigue ที่เราจะโชว์กรรมการ
# ลองนับจำนวนเล่นๆ:
cat scan.json | python3 -c "import sys,json; d=json.load(sys.stdin); \
print('CVE ทั้งหมด:', sum(len(r.get('Vulnerabilities',[])) for r in d['Results']))"
