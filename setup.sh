# 1.2 ติดตั้งเครื่องมือพื้นฐาน

# 1) Docker + Docker Compose — ตัวรัน container
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER   # ให้รัน docker ได้โดยไม่ต้อง sudo (ล็อกเอาต์แล้วเข้าใหม่)

# 2) Git — ไว้ดึงโค้ด/testbed
sudo apt install -y git

# 3) Python 3 + pip — ภาษาหลักที่เราจะเขียนระบบ
sudo apt install -y python3 python3-pip

# 4) VS Code — เขียนโค้ด (จะใช้ตัวไหนก็ได้)
