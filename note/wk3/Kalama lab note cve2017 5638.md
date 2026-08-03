# Kalama Lab Note — CVE-2017-5638
**GUIDE-1: Exploitation-Validated Vulnerability Prioritization**
**วันที่ทดสอบ:** 2026-08-01
**ผู้ทดสอบ:** Natapat
**อาจารย์ที่ปรึกษา:** Atthapol

---

## 1. ข้อมูล CVE (จาก Trivy / Grype Scan)

| หัวข้อ | รายละเอียด |
|---|---|
| **CVE ID** | CVE-2017-5638 |
| **ชื่ออื่น** | S2-045 (Apache Struts 2) |
| **Package** | `org.apache.struts:struts2-core` |
| **เวอร์ชันที่มีช่องโหว่** | 2.3.30 |
| **เวอร์ชันที่แก้แล้ว (FixedVersion)** | 2.3.32 (เลือกใช้ same-branch) |
| **Status** | fixed |
| **CWE** | Improper Input Validation (OGNL injection ผ่าน Content-Type header) |
| **Severity** | CRITICAL |
| **CVSS v2 Score** | 10.0 |
| **CVSS v2 Vector** | `AV:N/AC:L/Au:N/C:C/I:C/A:C` |
| **MSF Module** | `exploit/multi/http/struts2_content_type_ognl` |
| **ExploitDB** | มี (EDB #41570, #41614) |

---

## 2. กลไกช่องโหว่ (Vulnerability Mechanism)

Apache Struts 2 เวอร์ชัน 2.3.5–2.3.31 และ 2.5–2.5.10 มีช่องโหว่ใน **Jakarta Multipart parser** ซึ่งใช้จัดการ file upload ผ่าน HTTP request

ปัญหาอยู่ที่ **`Content-Type` header ถูกนำไปประมวลผลผ่าน OGNL expression โดยไม่มีการ sanitize** — หากค่า `Content-Type` ไม่ใช่รูปแบบที่ valid ระบบจะโยน exception ซึ่งข้อความ exception นั้นถูกสร้างจากการประเมิน OGNL expression ที่ผู้โจมตีฝังเข้าไปได้โดยตรง ทำให้สามารถ execute code ได้ทันทีโดยไม่ต้อง authenticate

**Attack Flow:**
```
Attacker
   └── ส่ง HTTP request พร้อม Content-Type header ที่ฝัง OGNL payload
         └──> Struts2 Jakarta Multipart parser ประมวลผล header
               └── OGNL context ถูกเปิด (bypass DEFAULT_MEMBER_ACCESS)
                     └── ProcessBuilder.start() ถูกเรียกผ่าน OGNL
                           └── trigger: touch /tmp/success (RCE)
```

**ข้อสังเกตสำหรับงานวิจัย:**
CVE นี้ต่างจาก CVE-2017-5645 (Java deserialization) ตรงที่เป็น **injection ผ่าน HTTP header ธรรมดา** — ไม่ต้องมี service พิเศษเปิดอยู่ (เช่น TcpSocketServer) เพียงแค่ Struts2 web app รันอยู่ก็โจมตีได้ทันที attack surface กว้างกว่ามาก สอดคล้องกับ CVSS 10.0 ที่ให้คะแนนเต็ม

---

## 3. สภาพแวดล้อมการทดสอบ (Test Environment)

| รายการ | รายละเอียด |
|---|---|
| **Host** | Ubuntu (distorion-HP-Pavilion-Laptop) |
| **Testbed** | Vulhub Docker environment |
| **Before-patch image** | `vulhub/struts2:2.3.30` (pre-built จาก Docker Hub) |
| **After-patch image** | build เองจาก `vulhub/base/struts2/2.3.30/` |
| **Exploit tool** | Metasploit Framework (container: `metasploitframework/metasploit-framework`) |
| **Scanner** | Trivy + Grype |

**โครงสร้างโฟลเดอร์:**
```
vulhub/struts2/
├── s2-045/                   ← before-patch (ห้ามแก้)
│   └── docker-compose.yml    (image: vulhub/struts2:2.3.30)
└── s2-045-patch/              ← after-patch (build เอง)
    ├── Dockerfile             (ARG STRUTS2_VERSION + mvn versions:set-property)
    ├── pom.xml                (refactor เป็น ${struts2.version} property)
    ├── src/...
    └── docker-compose.yml    (build: . / args: STRUTS2_VERSION=2.3.32)
```

---

## 4. Oracle Scan (Trivy + Grype)

**คำสั่ง:**
```bash
trivy image vulhub/struts2:2.3.30 -f json -o trivy_s2045_before.json
grype vulhub/struts2:2.3.30 -o json > grype_s2045_before.json
```

**ผลลัพธ์ Trivy:**
```json
{
  "VulnerabilityID": "CVE-2017-5638",
  "PkgName": "org.apache.struts:struts2-core",
  "InstalledVersion": "2.3.30",
  "FixedVersion": "2.3.32, 2.5.10.1"
}
```

**ผลลัพธ์ Grype:**
```json
{
  "id": "GHSA-j77q-2qgg-6989",
  "package": "struts2-core",
  "version": "2.3.30",
  "fix": {
    "versions": ["2.3.32"],
    "state": "fixed"
  }
}
```

**ตีความ:**
- Trivy รายงาน FixedVersion 2 ค่า (multi-branch: 2.3.32 กับ 2.5.10.1) — ต้องมี policy เลือก
- Grype index ด้วย GHSA ID เป็นหลัก ไม่ใช่ CVE ID โดยตรง (CVE ผูกอยู่ใน `relatedVulnerabilities`)
- **ตัดสินใจเลือก 2.3.32** (same-branch กับ installed version 2.3.30) ตามหลัก simplest-first และลดความเสี่ยง transitive dependency พัง

---

## 5. Before-Patch Exploitation

### 5.1 Setup
```bash
cd vulhub/struts2/s2-045
docker compose up -d
```

Container: `s2-045-struts2-1`
Container IP: `172.20.0.2` (network: `s2-045_default`)
Port: `8080`

### 5.2 รัน Exploit ด้วย Metasploit

```
use exploit/multi/http/struts2_content_type_ognl
set RHOSTS 172.20.0.2
set RPORT 8080
set TARGETURI /
set PAYLOAD cmd/unix/generic
set CMD touch /tmp/success
run
```

**สังเกต:** ครั้งแรกที่ยิงเจอ `Connection timed out` เพราะ MSF container (`trusting_mcnulty`) อยู่คนละ Docker network กับ target — ต้อง `docker network connect` เพิ่มก่อนถึงจะยิงถึง

### 5.3 ตรวจสอบผล
```bash
docker exec -it s2-045-struts2-1 ls -la /tmp/
```

**ผลลัพธ์:**
```
-rw-r--r-- 1 root root 0 Aug  1 ... success
```

✅ **Exploit สำเร็จ** — `/tmp/success` ถูกสร้างขึ้นจากภายใน container

---

## 6. Patch Process

### 6.1 สาเหตุที่ต้อง Build เอง

`vulhub/struts2:2.3.32` ไม่มีบน Docker Hub เช่นเดียวกับกรณี log4j — ต้อง build image เวอร์ชัน patched เองจาก source ที่อยู่ใน `vulhub/base/struts2/2.3.30/`

### 6.2 การเตรียมโฟลเดอร์ Patch

```bash
mkdir -p vulhub/struts2/s2-045-patch
sudo cp -r vulhub/base/struts2/2.3.30/. vulhub/struts2/s2-045-patch/
sudo chown -R $USER:$USER vulhub/struts2/s2-045-patch/
```

### 6.3 Refactor pom.xml — hardcode version → property

**ก่อนแก้:**
```xml
<dependency>
  <groupId>org.apache.struts</groupId>
  <artifactId>struts2-core</artifactId>
  <version>2.3.30</version>
</dependency>
```

**หลังแก้:**
```xml
<properties>
  <struts2.version>2.3.30</struts2.version>
</properties>

<dependencies>
  <dependency>
    <groupId>org.apache.struts</groupId>
    <artifactId>struts2-core</artifactId>
    <version>${struts2.version}</version>
  </dependency>
</dependencies>
```

**หมายเหตุ:** ต่างจาก log4j ตรงที่ pom.xml เดิมของ struts2 **hardcode เวอร์ชันตรงๆ** ไม่ได้ใช้ property มาก่อน ต้อง refactor ก่อนถึงจะใช้ `mvn versions:set-property` ได้ (เป็นงาน one-time ต่อ product)

### 6.4 แก้ Dockerfile ให้รับ ARG

```dockerfile
FROM maven:3-jdk-8
LABEL maintainer="phithon <root@leavesongs.com>"
ARG STRUTS2_VERSION=2.3.30
COPY ./ /usr/src/
WORKDIR /usr/src
RUN mvn versions:set-property -Dproperty=struts2.version -DnewVersion=${STRUTS2_VERSION} \
    && mvn compile jetty:help
EXPOSE 8080
CMD ["mvn", "jetty:run"]
```

**หมายเหตุ:** struts2-showcase ตัวนี้ packaging เป็น `war` รันด้วย jetty-maven-plugin (`mvn jetty:run`) ไม่ใช่ fat-jar แบบ log4j (`assembly:single`) — base image `maven:3-jdk-8` ยัง pull ได้ปกติ ไม่ต้องเปลี่ยนเป็น `eclipse-temurin` เหมือนเคส log4j

### 6.5 docker-compose.yml สำหรับ Patch

```yaml
services:
  struts2:
    build:
      context: .
      args:
        STRUTS2_VERSION: 2.3.32
    ports:
      - "8080:8080"
```

### 6.6 Build

```bash
cd vulhub/struts2/s2-045-patch
docker compose up --build -d
```

**ผลลัพธ์:**
```
[+] Building 304.3s
✔ Image s2-045-patch-struts2       Built
✔ Network s2-045-patch_default     Created
✔ Container s2-045-patch-struts2-1 Started
```

---

## 7. After-Patch Exploitation (Re-exploit)

### 7.1 ยืนยัน Container IP
```bash
docker inspect s2-045-patch-struts2-1 --format '{{range $net,$conf := .NetworkSettings.Networks}}{{$net}}: {{$conf.IPAddress}}{{"\n"}}{{end}}'
# ผล: s2-045-patch_default: 172.19.0.2
```

### 7.2 เชื่อม Network ระหว่าง MSF container กับ Target

```bash
docker network connect s2-045-patch_default trusting_mcnulty
docker exec -it trusting_mcnulty ping -c 3 172.19.0.2
# 3 packets transmitted, 3 packets received, 0% packet loss
```

### 7.3 รัน Exploit ซ้ำด้วย Payload เดิม

```
set RHOSTS 172.19.0.2
run
```

```
[+] touch /tmp/success
[*] Exploit completed, but no session was created.
```

### 7.4 ตรวจสอบผล
```bash
docker exec -it s2-045-patch-struts2-1 ls -la /tmp/
```

**ผลลัพธ์:**
```
drwxr-xr-x 1 root root 4096 Aug  1 07:22 hsperfdata_root
-rwxr--r-- 1 root root 15800 Aug  1 07:22 jansi-2.4.0-...-libjansi.so
-rw-r--r-- 1 root root     0 Aug  1 07:22 jansi-2.4.0-...-libjansi.so.lck
```

❌ **Exploit ล้มเหลว** — ไม่มี `/tmp/success` ปรากฏ แสดงว่า patch เวิร์คจริง

---

## 8. สรุปผล Pipeline (Full Loop)

| ขั้นตอน | เครื่องมือ | ผลลัพธ์ |
|---|---|---|
| **Oracle Scan** | Trivy + Grype | พบ CVE-2017-5638 ใน struts2-core 2.3.30, FixedVersion=2.3.32 (เลือก same-branch) |
| **Before-patch Exploit** | Metasploit `struts2_content_type_ognl` | ✅ สำเร็จ (`/tmp/success` ถูกสร้าง) |
| **Patch** | refactor pom.xml → property, rebuild ด้วย `struts2.version=2.3.32` | Build สำเร็จ |
| **After-patch Re-exploit** | Metasploit (payload เดิม) | ❌ ล้มเหลว (ไม่มี `/tmp/success`) |

**ข้อสรุปเชิงวิจัย:**
`FixedVersion` ที่เลือกใช้ (2.3.32) ยืนยันได้จริงด้วยการ exploit จริง — เป็น True Positive สำหรับ patch recommendation สอดคล้องกับ core thesis ของ Kalama

---

## 9. ปัญหาที่พบระหว่างทาง (Lessons Learned)

| ปัญหา | สาเหตุ | วิธีแก้ |
|---|---|---|
| `vulhub/struts2:2.3.32` ไม่มีบน Docker Hub | Vulhub ไม่ push image เวอร์ชัน patched | Build เองจาก `base/struts2/2.3.30/` |
| pom.xml hardcode เวอร์ชันตรงๆ | Source เดิมของ Vulhub ไม่ได้ใช้ Maven property | Refactor เป็น `${struts2.version}` (one-time ต่อ product) |
| MSF exploit timeout ครั้งแรก | MSF container กับ target อยู่คนละ Docker network | `docker network connect <network> <msf-container>` |
| `sudo cd` ใช้ไม่ได้ | `cd` เป็น shell builtin ไม่ใช่โปรแกรมแยก | ใช้ `sudo chown -R $USER:$USER` แก้ ownership แทน |
| ไฟล์ที่ copy มาเป็นของ root หลัง `sudo cp` | mkdir แรกไม่ได้ sudo แล้วเปลี่ยนไปใช้ sudo cp ทำให้ owner ไม่ตรงกัน | `sudo chown -R $USER:$USER` ก่อนแก้ไฟล์ |
| MSF บอก "Exploit completed, but no session was created" | payload `cmd/unix/generic` เป็นแบบ inline ไม่เปิด session | ปกติ — เช็คหลักฐานจาก `/tmp/success` ในคอนเทนเนอร์แทน |

---

## 10. หมายเหตุสำหรับ Thesis

- Trivy ให้ FixedVersion มาหลายค่า (multi-branch) ในเคสนี้เป็นครั้งแรกที่เจอจริง — ตัดสินใจเลือก same-branch version (2.3.32) ตามหลัก simplest-first และยืนยัน patch เวิร์คจริง เป็นตัวอย่างที่ใช้ตอบคำถามเรื่อง resolver policy ที่ค้างไว้ในเฟส design
- pom.xml ที่ hardcode เวอร์ชันต้อง refactor ก่อนถึงจะใช้ template automation ได้ — เป็นงาน one-time ต่อ product ไม่ใช่ต่อ CVE ตรงตามที่ออกแบบไว้
- Template ที่ใช้กับ log4j (fat-jar/assembly:single) ใช้กับ struts2 (war/jetty:run) ไม่ได้ตรงๆ ต้องปรับ Dockerfile ให้เหมาะกับ build mechanism ของแต่ละ product — เป็นข้อมูลสำคัญสำหรับออกแบบ template ต่อ fix-type ในเฟส automation ถัดไป
- MSF module `struts2_content_type_ognl` ใช้งานได้จริงกับทั้ง before และ after patch โดยไม่ต้องแก้ payload

---

*Lab note นี้เป็นส่วนหนึ่งของโปรเจกต์ Kalama (GUIDE-1) ภายใต้การดูแลของ Atthapol*
