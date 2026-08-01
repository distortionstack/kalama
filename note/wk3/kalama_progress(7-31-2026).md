# Kalama (GUIDE-1) — บันทึกความคืบหน้า (ต่อจาก 7-30)

**เฟส Automation — ตกผลึกวิธี patch จากการลองจริงกับ CVE ตัวที่ 2 (Struts s2-045)**
ต่อจาก `kalama_progress(7-30-2026).md` (section 10–15)
บันทึกวันที่: 2026-07-31

> ไฟล์นี้บันทึก session ที่เริ่มจากไอเดียของ Atthapol เรื่อง "การอัพเดท" แล้วลองทำจริงกับ
> CVE-2017-5638 (s2-045) จนเจอว่า vulhub แต่ละ CVE โครงสร้างไม่เหมือนกันเลย
> — จบด้วยการทิ้งแนวคิด "template เดียวเป๊ะ" มาเป็น "อ่านสูตรที่มี + แทน token เวอร์ชัน"

---

## 16. จุดตั้งต้น: 2 ไอเดียของ Atthapol เรื่องการอัพเดท

Atthapol เสนอ 2 ทางสำหรับ automate การเตรียม/patch environment:

1. **Universal update** — มี updater กลางตัวเดียว อ่านผล scan ปุ๊บ อัพเดทให้เลย generic พอจะแก้ได้ทุกเคส
2. **Template-based** — ไม่มีสูตรสำเร็จตัวเดียว ต้องประกอบจาก piece ย่อยตาม fix-type

**ทั้งสองทางเริ่มจาก scan เหมือนกัน** ต่างกันที่ขั้นตอน "หลัง scan" ว่าจะแก้ยังไง

**ข้อสรุป:** เอียงไป template-based เพราะมีหลักฐานขัดแย้งในมืออยู่แล้ว — log4j fix ด้วย version bump แต่ Ghostcat fix ด้วย config เป็นคนละ "shape" กัน updater ตัวเดียวครอบไม่ได้ (สอดคล้องข้อ 14 เดิม)

**และตัด scope เพิ่ม:** เฟสนี้รับเฉพาะ **version-bump** เท่านั้น เพราะเราไม่มีฐานข้อมูล fix-type ที่เชื่อถือได้ (config-fix เป็น text ใน advisory ที่ต้องคนอ่าน — ข้อ 7.1 เดิม) → ตัด config-patch ออกไปก่อน เหลือปัญหาเดียวคือ "เปลี่ยนเวอร์ชันในสูตรยังไงให้อัตโนมัติ"

---

## 17. ปมเรื่อง hardcode: อะไรที่ Trivy ให้ได้ / ให้ไม่ได้

ประเด็นที่ push กันในรอบนี้: **ไม่อยากเขียน `case.yaml` ที่ hardcode `dep_property: log4j.version`, `dep_version: 2.8.2` เอง** ทั้งที่ข้อมูลพวกนี้ Trivy มีอยู่แล้ว → ทำงานซ้ำ + เสี่ยงหลุด sync กับ scan จริง

แยกให้ชัดว่าอะไรดึงจาก Trivy ได้:

| ข้อมูล | Trivy ให้ได้ไหม | หมายเหตุ |
|---|---|---|
| InstalledVersion | ✅ | scan output ตรงๆ |
| FixedVersion | ✅ | scan output ตรงๆ |
| CPE (vendor/product) | ✅ | scan output ตรงๆ |
| **ชื่อ property ใน pom** (`log4j.version`) | ❌ | Trivy สแกน jar ที่ build แล้ว ไม่รู้จัก source/pom ของเรา |
| **template ไหนที่ควรใช้** | ❌ | fix-type เป็น text ใน advisory Trivy ไม่มี field นี้ |

**สรุป:** เวอร์ชันดึงจาก Trivy ได้หมด ไม่ต้อง hardcode — แต่ "จะแก้ยังไง" (ชื่อ property / วิธี build) เป็นสิ่งที่ scanner ให้ไม่ได้ ต้องหาจากที่อื่น

**ทางเลี่ยง hardcode ชื่อ property:** ไม่ต้อง "รู้" ชื่อ property ล่วงหน้า — อ่านจาก pom.xml ตรงๆ (grep หา artifactId ที่ตรง CPE แล้วดูว่า `<version>` เป็น `${xxx}` หรือ literal) แทนการเดา

---

## 18. ลองจริงกับ CVE-2017-5638 (s2-045) — แล้วเจอความจริงของ vulhub

เอา flow "scan → grep pom → set-property" ไปลองกับ s2-045 จริง แล้วเจอปัญหาเป็นชั้นๆ:

### 18.1 s2-045 ไม่มี pom.xml ให้ grep เลย
```
~/vulhub/struts2/s2-045/
├── README.md
└── docker-compose.yml   ← image: vulhub/struts2:2.3.30 (pull ตรงๆ)
```
ไม่มี source ให้ build — เป็น pre-built image สำเร็จรูป **เหมือน s2-052 ที่ทำมือไปแล้ว** (`vulhub/struts2:2.5.12-rest-showcase`)
→ flow เดิมพังตั้งแต่ขั้น grep เพราะไม่มีไฟล์ให้ grep

**นี่ไม่ใช่ bug ของ flow** — filter ทำงานถูก: s2-045 แค่ไม่เข้าเงื่อนไข `maven-fatjar` (เหมือน Ghostcat ที่ตกเพราะเป็น config)

### 18.2 ไล่หา source ทางเลือก — เจอหลายแบบ ไม่มีอันไหน "มาตรฐาน"
- `vulhub/base/struts2/2.3.32-showcase/Dockerfile` → ใช้ `ARG ST2_VERSION` + `wget` .war จาก `archive.apache.org` (ของสำเร็จรูป ไม่ build)
- `vulhub/struts2:2.3.32-showcase` → มีบน Docker Hub จริง (pull ตรงๆได้)
- `org.pwntester:Struts2FileUpload` (PoC repo) → pom.xml **hardcode** `<version>2.3.30</version>`
- `apache/struts` (monorepo) → `apps/showcase` ใช้ `${project.version}` (built-in ไม่ใช่ custom property)

**บทเรียน:** vulhub ไม่ได้ออกแบบให้มี pattern เดียว แต่ละ CVE maintainer เขียนตามสะดวก → **ยิ่งฝืนหา "1 flow ครอบทุก CVE" ยิ่งเจอ exception ใหม่ทุกครั้ง**

---

## 19. ทางตันของแต่ละทางเลือก (ทำไมถึงไม่เลือก)

| ทางเลือก | ปัญหา |
|---|---|
| `wget` .war จาก `archive.apache.org` | ขัดหลักการข้อ 5 — `archive.apache.org` ไม่ใช่ central registry immutable แบบ Maven Central (เสี่ยง drift เหมือน `openjdk` หายตอน log4j) |
| `docker pull vulhub/struts2:<ver>-showcase` | พึ่ง vulhub ทั้ง before **และ** after — vulhub ไม่ maintain patched image ระยะยาว (log4j 2.8.2 หายไปจริงมาแล้ว = หลักฐาน) |
| git clone `apache/struts` + tag + `mvn build` | ตรงหลักการ (Maven Central) แต่: ต้อง map version→git tag เอง (`2.3.32`→`STRUTS_2_3_32`), ใช้ `${project.version}` ทำให้ `set-property` ใช้ไม่ได้ ต้อง checkout tag แทน, และ repo อายุ ~9 ปี เสี่ยง transitive dep หลุด Central ตอน build |

**สิ่งที่ verify แล้วจริงในรอบนี้ (ทดสอบใน sandbox):**
- ✅ git tag `STRUTS_2_3_32` มีจริง, clone ได้
- ✅ `apps/showcase/pom.xml` มีจริง, struts2-core อ้าง `${project.version}`
- ✅ struts2-showcase/core/plugins เวอร์ชัน 2.3.32 อยู่บน Maven Central ครบ
- ❌ **ยังไม่ยืนยัน** ว่า `mvn -pl apps/showcase -am package` build ผ่านจริง (ไม่มี Docker/Maven Central ใน sandbox)

---

## 20. 🎯 แนวทางที่ตกผลึก: "อ่านสูตร → แทน token เวอร์ชัน" (ไม่แกะ container)

มีการเสนอให้ "แกะ container ที่รันอยู่ → ดึง jar/war ออกมา → สร้าง Dockerfile ใหม่" — **ตกไป**

เหตุผล (จุดสำคัญของ session นี้):
> **ถ้าจะรัน container ได้ ต้นทางต้องมี "สูตร" (Dockerfile/pom.xml) อยู่แล้วเสมอ**
> → อ่านสูตรที่มีอยู่ ดีกว่าไปแกะ binary จาก container ที่ build เสร็จแล้ว
> การแกะ container = ทำงานย้อนกลับโดยไม่จำเป็น ในเมื่อสูตรมีให้อ่านตรงๆ

**หลักการที่ได้:** ไม่ว่าสูตรเป็น Dockerfile หรือ pom.xml — หา **token ที่เป็นเวอร์ชันของ product ที่ Trivy ชี้** แล้วแทนด้วย FixedVersion

### 20.1 POC ที่ทดสอบแล้ว (ได้ผลจริงใน sandbox)

logic เดียว ใช้ได้กับสูตร 2 แบบ:

**Dockerfile (ARG-based):**
```
ARG ST2_VERSION=2.3.32   → sed แทน default ของ ARG
```
**pom.xml (hardcode):**
```xml
<artifactId>struts2-core</artifactId>
<version>2.3.30</version>   → sed แทน <version> ที่อยู่ใต้ artifactId ที่ตรง product
```
ทั้งสองแบบ: หา token เวอร์ชันที่ผูกกับ product (จาก CPE) → แทนด้วย FixedVersion → เสร็จ ไม่ต้องแกะ container

### 20.2 Flow ใหม่
```
1. Trivy scan → product (CPE) + InstalledVersion + FixedVersion
2. เปิดโฟลเดอร์ CVE ใน vulhub → หาสูตร (Dockerfile? pom.xml? docker-compose?)
3. หา token เวอร์ชันในสูตรที่ผูกกับ product นั้น
4. แทนที่ด้วย FixedVersion
5. docker build → re-exploit → ตรวจผล /tmp/success
```

---

## 21. การจัดกลุ่มใหม่ (แทน "template ต่อ fix-type" ด้วยเกณฑ์รูปธรรมกว่า)

| กลุ่ม | เจออะไรในโฟลเดอร์ CVE | วิธีจัดการ | ตัวอย่าง |
|---|---|---|---|
| **A. สูตรมี + official base** | Dockerfile ARG version หรือ pom `<version>` + base image ทางการ | อ่าน+แทน token อัตโนมัติ (POC ข้อ 20) | s2-045 (showcase), Struts2FileUpload |
| **B. Edge case** | image หาย / artifact ไม่อยู่ registry / build แปลก | จัดการเฉพาะตัว (แบบ log4j pipeline ครบ) | CVE-2017-5645 (image 2.8.2 หาย ต้อง build เอง) |

**นิยามใหม่ของ "edge case":** ไม่ใช่ "fix-type ต่างกัน" แต่คือ **"สูตรมาตรฐานใช้ไม่ได้"** — image ไม่ official / artifact ไม่อยู่ registry immutable / ต้อง build ท่าพิเศษ. log4j ที่ทำ pipeline ครบไปแล้วคือตัวอย่าง edge case ที่สมบูรณ์

**สำคัญ:** การแยก A/B อัตโนมัติเต็มที่ไม่ได้ — บางทีรู้ว่าเป็น B ก็ต่อเมื่อลอง A แล้วพังก่อน (เช่น image หายถึงรู้)
→ flow จริง = **"ลอง A ก่อน พังแล้วตกไป B"** ตรงกับหลักการ Type A ข้อ 3 เดิม ("probe ก่อนใช้ เดาล่วงหน้าไม่ได้")

---

## 22. สถานะล่าสุด & next step

**ตกผลึกแล้วในรอบนี้:**
- เฟส automation scope แค่ **version-bump** (ตัด config-fix ออกก่อน — ไม่มีฐานข้อมูลรองรับ)
- วิธี patch = **อ่านสูตรที่มี (Dockerfile/pom) → แทน token เวอร์ชันด้วย Trivy FixedVersion → rebuild** (ไม่แกะ container)
- แบ่งงานเป็น 2 กลุ่ม: A (สูตรมาตรฐาน อัตโนมัติได้) / B (edge case จัดการมือแบบ log4j)
- POC การหา+แทน token ทำงานได้จริงกับทั้ง Dockerfile ARG และ pom hardcode

**ยังไม่ยืนยัน (ต้องทำบน VM จริง):**
- แทน token แล้ว `docker build` / `mvn package` **ผ่านจริงไหม** — เวอร์ชันใหม่อาจลาก transitive dep พัง (ข้อ 7.3 เดิม)
- s2-045 หลัง patch: re-exploit ต้อง **fail** ถึงจะยืนยันว่า patch เวิร์ค (ยังไม่ได้รัน)
- ยังไม่แตะ 3 CVE ที่เหลือ (Log4Shell มือเสร็จแล้ว, S2-052 มือเสร็จแล้ว, Ghostcat = คาดว่าตกกลุ่ม B/config)

**next step รูปธรรม:**
1. เอา Dockerfile git-clone template (ข้อ 20) ไปรันจริงบน VM กับ s2-045 → ดูว่า `mvn -pl apps/showcase -am package` พังตรงไหน
2. ถ้าผ่าน → re-exploit ด้วย payload S2-045 เดิม → ต้องได้ไม่มี `/tmp/success` (patch เวิร์ค)
3. ถ้า build พังเพราะ dep หลุด Central → บันทึกเป็นหลักฐาน "s2-045 = edge case กลุ่ม B" (drift ตามอายุ repo)

**ปมเดิมที่ยังค้าง (ยกมาจาก notebook §7.4):**
re-exploit สำเร็จหลัง patch = "FixedVersion ผิด" หรือ "fix ไม่เวิร์ค" — ยังแยกไม่ออก ยังไม่มีคำตอบ

---

## 23. บทเรียนเชิงกระบวนการของ session นี้ (เก็บเข้า thesis ได้)

- **vulhub ไม่มี pattern เดียว** — เป็นหลักฐานรูปธรรมว่า "reproducible testbed" ไม่ได้มาฟรี แต่ละ CVE ต้องเข้าใจสูตรของมันเอง → ตอกย้ำ core thesis ว่า empirical ต่อเคสสำคัญกว่าสมมติว่าทุกอย่างเหมือนกัน
- **การไล่ debug จนเจอ `${project.version}`** = ตัวอย่างว่า "สมมติฐาน fix=อัพ property" (§7.1) พังจริงในทางปฏิบัติ ไม่ใช่แค่ในทฤษฎี
- **เลิกฝืน generalize ก่อนเวลา** — แนวทาง "อ่านสูตร+แทน token" มาจากการยอมรับความมั่วของ vulhub แทนการบังคับให้มันเป็นระเบียบ = empirical rigor แบบเดียวกับ core thesis ("ดูของจริง ไม่เดา")

---

*ต่อจาก kalama_progress(7-30-2026).md — section 16–23 เน้นการลองจริงกับ s2-045 จนตกผลึกวิธี "อ่านสูตร+แทน token"*
*ยังเป็นขั้น design + POC — ยังไม่ยืนยัน build จริงบน VM*
