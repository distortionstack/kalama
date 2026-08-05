# Kalama (GUIDE-1) — บันทึกความคืบหน้า (ต่อจาก 7-31)

**เฟส Automation — สืบสวน scope + วรรณกรรมอ้างอิง + ทดลอง pipeline POC**
ต่อจาก `kalama_progress(7-31-2026).md` (section 16–23)
บันทึกวันที่: 2026-08-05

> ไฟล์นี้บันทึก session ที่เริ่มจากคำถาม "1 dependency ต่อ Dockerfile พอไหมสำหรับธีสิส"
> ไล่ผ่านการอ่าน lab note จริง 3 CVE, หา literature สนับสนุน, ไปจนถึงทดลอง pipeline
> จบด้วยข้อค้นพบสำคัญ: **แนวทาง "hardcode dep_property ต่อ CVE" ที่ทดลองใน session นี้
> ขัดกับข้อสรุปของ 7-31 ที่เลิกใช้วิธีนั้นไปแล้ว (เปลี่ยนเป็น "อ่านสูตร+แทน token" แทน)**
> ต้องเคลียร์จุดนี้ก่อนเดินหน้าต่อ

---

## 24. จุดตั้งต้น: กลัว scope "1 dependency ต่อ Dockerfile" น้อยไป

เริ่มจากคำถามว่า scope ปัจจุบัน (template ต่อ fix-type, เน้น version bump) พอสำหรับ thesis ไหม
กลัวว่าไม่ full automate

**ข้อสรุปเบื้องต้น:** แยกคำถามเป็น 2 ชั้น
1. พอสำหรับ **thesis claim** ไหม — core thesis (empirical exploitation ดีกว่า theoretical score)
   ไม่ต้องพึ่ง automation เต็มรูปแบบเลยด้วยซ้ำ CVE-2017-5645 แบบ manual ก็ demo ได้ครบแล้ว
2. พอสำหรับ **"full automation" ตามที่ Atthapol สั่ง** ไหม — อันนี้ต้องเคลียร์ขอบเขตให้ชัด

---

## 25. อ่าน CVE-2017-9805 (S2-052) จริง — เจอว่าทำนายผิด

ทวนสมมติฐานเดิมที่คิดว่า S2-052 น่าจะยังเป็น Maven fat-jar (แค่คนละ artifact จาก log4j)
พออ่าน lab note จริงแล้ว **ผิดคาด**:

- **Fix type จริง: webapp-rebuild** — `wget` WAR สำเร็จรูปจาก `archive.apache.org` แล้ว swap เข้า `webapps/ROOT.war`
- ไม่มี `pom.xml` ให้ `mvn versions:set-property` จับต้องเลย เพราะไม่ได้ compile จาก source

**ผลต่อแนวคิด "ต่อ dependency vs ต่อ ecosystem":**
แม้อยู่ ecosystem เดียวกัน (struts) source type ก็ต่างกันได้ — ไม่ใช่แค่ "dependency คนละตัว"
แต่ "กลไก build/deploy คนละแบบ" ตั้งแต่ต้น

---

## 26. อ่าน CVE-2017-5638 (S2-045) เทียบเพิ่ม — ยืนยัน pattern ซ้ำ

จากบันทึก 7-31 (§18) ที่ไปลองจริงแล้ว: S2-045 **ก็ไม่มี pom.xml เหมือนกัน** —
`vulhub/struts2/s2-045/` มีแค่ `docker-compose.yml` ที่ pull image สำเร็จรูปตรงๆ (`vulhub/struts2:2.3.30`)

สรุปตาราง 3 CVE ที่ทำมือแล้ว ณ จุดนี้:

| CVE | package | build mechanism | หมายเหตุ |
|---|---|---|---|
| 2017-5645 (log4j) | log4j-core | Maven compile → assembly:single | มี pom.xml จริง, build เองได้ |
| 2017-5638 (S2-045) | struts2-core | pre-built image (pull ตรง) | ไม่มี pom.xml ให้แก้เลย |
| 2017-9805 (S2-052) | struts2-rest-plugin | prebuilt WAR download | ไม่มี pom.xml เช่นกัน |

**ข้อสรุปตอนนั้น (ก่อนจะรู้ทางออกจาก 7-31):**
แม้แต่ 2 CVE ใน ecosystem เดียวกัน (struts) ก็ยังไม่ match กันเอง —
ยิ่งตอกย้ำว่า "1 template ครอบ 1 ecosystem" ใช้ไม่ได้จริง

---

## 27. หาวรรณกรรมมาโต้แย้ง/สนับสนุน แทนการเดาเอง

ถูกทวงถามให้หาหลักอ้างอิงจริง แทนการอ้างแค่ observation ของตัวเอง — ไล่หาและอ่านได้ 3 ฉบับ:

### 27.1 Dissanayake et al. — ASE '22 (arXiv:2209.01518)
*An Empirical Study of Automation in Software Security Patch Management*

- **§4.2.4 "Lack of Scalability in Tool Design/Architecture":**
  ขาด unified platform deploy patch ข้าม heterogeneous environment
  เป็น infrastructure limitation ที่มีบันทึกจริงในอุตสาหกรรม (interview 17 practitioner)
  quote จาก P10: "The tool has only a finite number of products that it can patch."
- **§5 (Discussion):** unified solution ข้าม heterogeneous env "highly complex" เพราะ
  inherent differences — ยังเป็นแค่ future-work vision ไม่ใช่ solved problem
- **§4.4:** เหตุผลว่าทำไมต้องมี human-in-the-loop (contextual decision-making)

**ใช้ตีกรอบ:** สิ่งที่เจอกับ log4j vs S2-045 vs S2-052 ไม่ใช่ปัญหาเฉพาะโปรเจกต์เล็ก
แต่เป็น instance เล็กของปัญหาที่ practitioner ระดับ enterprise ก็เจอเหมือนกัน

### 27.2 Paixão et al. — PatchLens (arXiv:2606.25863)
*Automated Detection of Configuration-Specific Security Vulnerabilities via Patch Analysis*

- build system มีความหลากหลายโดยธรรมชาติ (non-standard) → ไม่มี universal tool
  วิเคราะห์ build system ได้ (Kbuild, Autotools ฯลฯ)
- (อ่านได้แค่ snippet, full text ดึงไม่สำเร็จหลายครั้ง)

**ใช้ตีกรอบ:** เหตุผลเชิงเทคนิคว่าทำไม template เดียวไม่ generalize ข้าม build mechanism

### 27.3 Hu et al. — SoK: Automated Vulnerability Repair (USENIX Security '25) ⭐ ตัวหลัก
อ่านเต็มจาก PDF ที่ผู้ใช้แปะมาเอง — เป็น SoK (Systematization of Knowledge) ครอบทั้ง field

**§2.2 AVR Workflow (Figure 1):** 3 ขั้น — vulnerability analysis → patch generation → patch validation
→ **map ตรงกับ Kalama pipeline:** scan=analysis, patch=generation, re-exploit=validation

**§4.2 Template-based Patch Generation:**
> "may fail due to its poor adaptability in dealing with abstract patch templates"

→ ยืนยัน pattern ที่เจอเอง (log4j template ใช้กับ struts ไม่ได้) มีหลักฐานจาก literature รองรับ

**§5.2 Dynamic Analysis-based Validation — "Triggering test":**
> "apply a candidate patch to a vulnerable program and retest the patched version
> via a known exploit"

→ **นิยามตรงกับ re-exploitation ของ Kalama คำต่อคำ** — มี technical term ที่ literature
ยอมรับแล้ว ไม่ต้องบัญญัติศัพท์เอง

**Table 5:** dynamic-validation tools (VulnFix 96.0% test pass rate) ชนะขาด
learning-based tools (VRepair 0.2%, VulRepair 4.3%) — สนับสนุนว่า exploit-based
validation น่าเชื่อถือกว่า static/learning-based

**§8 Direction 5:** "Future research should develop advanced and efficient
vulnerability validation methods" — **explicit gap ที่ Kalama กำลังตอบอยู่พอดี**

**ข้อควรระวัง:** Kalama ไม่ได้ generate patch เอง (ใช้ vendor patch จริง) —
อย่าสับสนคำว่า "patch generation" (paper นี้) กับ "patch deployment" (Kalama)
เวลาเขียน thesis

### 27.4 Ohaeche & Wang — ACR'25 / Springer (DOI: 10.1007/978-3-031-87647-9_32)
*Automating Vulnerability Scanning and Patching Along with OWASP and CVE Databases
on Docker Container Images*

- scope ตรงที่สุด (Docker + CI/CD scan-gate-patch-deploy) แต่ **เข้าเนื้อในไม่ได้**
  (Springer paywall + มมส. ไม่มี SSO/institutional access กับ Springer,
  GVSU ScholarWorks preprint โดน bot-detection บล็อก)
- ส่งอีเมลขอ full-text จาก corresponding author (Joseph U. Ohaeche, GVSU) แล้ว —
  รอผลตอบกลับ
- **ใช้ได้แค่ abstract-level:** ไม่มี exploit-validation ในงานนี้ (พูดแค่ scan+suggest fix
  จาก OWASP/CVE database) — ต่างจาก Kalama ตรงที่ไม่มี oracle ยืนยันด้วย exploit จริง

---

## 28. สรุปทิศทางจาก literature ทั้งหมด — ชี้ไปทางเดียวกัน

**สิ่งที่ Dissanayake + PatchLens + Hu et al. ยืนยันตรงกันหมด:**
generalized automation ข้าม heterogeneous build/environment context
ยังเป็น **open problem ระดับ USENIX/ASE เอง** — ไม่ใช่แค่ปัญหาที่ Kalama เจอเอง

**ข้อเสนอ reframe thesis:**
ไม่ต้องพยายามแก้ปัญหาที่ field ระดับ top-tier conference ยังแก้ไม่ได้
(generalized automation) — ควรวางตำแหน่งเป็น **validation-methodology contribution**
แทน **automation-engineering contribution**

เหตุผล: ไม่มีงานไหนใน literature ที่เจอ (รวม Hu et al. เอง) เทียบ
**scanner prediction (Trivy FixedVersion) กับ exploit ground truth เป็น Precision/Recall/F1**
— Kalama เติมช่องว่างนี้พอดี ตรงกับ §8 Direction 5 ของ Hu et al. ที่ชี้ว่า
validation mechanism คือจุดที่ field ยังขาด

**คำถามที่ต้องเอาไปคุยกับ Atthapol:**
frame thesis เป็น "validation-methodology contribution" แทน "automation-engineering
contribution" ได้ไหม — จะได้ไม่โดนเทียบกับงานที่ automate ได้กว้างกว่าแล้วแพ้

---

## 29. Semantics-based patch generation ≠ Dockerfile generation (เคลียร์ความเข้าใจผิด)

เกิดคำถามว่า "semantics-based generate Dockerfile เองหรอ" — คำตอบคือ **ไม่**
คนละชั้นกันเลย:

| | semantics-based (Hu et al. §4.3) | Kalama |
|---|---|---|
| Input | vulnerable source code (C/C++, Solidity, PHP) | Dockerfile + build config |
| Output | โค้ดแพตช์ที่ generate ขึ้นใหม่ (เช่น เพิ่ม if-condition) | Dockerfile ที่ bump version (ใช้ vendor patch จริง) |
| ระดับ | statement/function level ในแอป | environment/build config level |

**สรุป:** semantics-based generation = "เขียนแพตช์ให้เอง" ส่วน Kalama's Dockerfile
template = "เอาแพตช์ที่ vendor เขียนไว้แล้วมา deploy ให้อัตโนมัติ" — literature กลุ่ม AVR
ทั้งหมดที่อ่านมาไม่มีตัวไหนทำสิ่งที่ Kalama ทำจริงๆ (ยืนยันอีกครั้งว่าเป็นช่องว่างจริง)

---

## 30. คำถาม: ต้องมี "ฐานข้อมูล image + dependency source" ขนาดใหญ่ไหม

เกิดจากคำถามว่าถ้าจะ automate Dockerfile generation "ต้องมีฐานข้อมูลใหญ่ที่ดึง image
+ dependency source มาได้ไหม"

**คำตอบ:** ไม่ต้องเป็น universal/industry-scale database — งาน master's thesis
ควรทำแค่ **scope เดียวกับที่ Vulhub ครอบคลุม** (6 CVE ที่เลือกไว้) ไม่ใช่ solve
สิ่งที่ literature ระดับ ASE/USENIX เองก็ยังแก้ไม่ได้

ตัวอย่าง scope ที่พอ (6 entry ไม่ใช่ 6,000 entry):
```yaml
CVE-2017-5645:
  source_type: A
  fetch: {registry: "maven-central", artifact: "log4j:log4j"}

CVE-2017-9805:
  source_type: B
  fetch: {url: "https://archive.apache.org/dist/struts/${V}/struts-${V}-apps.zip"}
```

---

## 31. A/B ต่างกันยังไง — เคลียร์นิยาม (เวอร์ชัน session นี้ ก่อนจะพบว่าขัดกับ 7-31)

**Type A (log4j)** — ดึงจาก **package registry** (Maven Central)
- ดึง dependency ตัวเดียว (jar) แล้ว compile ต่อ
- ต้องมี pom.xml/build script อยู่แล้วในโปรเจกต์
- input = version number → output = jar ที่ build เอง

**Type B (S2-052)** — ดึงจาก **vendor release archive**
- ดึงทั้งแอปสำเร็จรูป (WAR ที่ build ไว้แล้ว) ไม่ใช่ dependency ตัวเดียว
- ไม่มีการ compile เลย — แค่ wget + unzip แล้ววางแทนที่
- ไม่มี pom.xml เกี่ยวข้องเลย
- input = URL ทั้งไฟล์ → output = ไฟล์ WAR สำเร็จรูป

**⚠️ หมายเหตุสำคัญ:** นิยาม A/B แบบนี้ (แยกตาม fetch mechanism) **ต่างจากนิยามที่
ตกผลึกใน progress 7-31 §21** ซึ่งแยกตาม "อัตโนมัติได้ไหม" แทน
(A = สูตรมี+official base, B = edge case ที่สูตรมาตรฐานใช้ไม่ได้)
**ต้องเคลียร์ให้ตรงกันก่อนใช้จริง — ดู §33 ท้ายไฟล์นี้**

---

## 32. ต่อ dependency vs แค่ 2 source_type — ไม่ใช่เลือกอันใดอันหนึ่ง

เกิดคำถามว่า "ถ้าแยกแค่ 2 แบบ (A/B) แล้วที่ตกลงกันว่าต้อง 'ต่อ dependency' จะทิ้งไปหรอ"

**คำตอบ: เป็น 2 ชั้น ไม่ใช่แทนที่กัน**

```
source_type (A/B/C/D)          → เลือก "กลไก" ว่าจะ wget หรือ mvn
    └── dependency config       → เลือก "รายละเอียด" ต่อตัว (base_image, run_cmd, property name)
```

หลักฐาน: log4j กับ S2-045 ทั้งคู่เป็น source_type A (Maven build) แต่
`base_image` ต่างกัน (`eclipse-temurin` vs `maven:3-jdk-8`),
`run_cmd`/`build_cmd` ต่างกัน (`assembly:single` vs `jetty:run`)
→ ถ้าใช้แค่ "source_type A" เป็น template ตัวเดียวจะพัง ต้องมี per-dependency
config อยู่ใต้ source_type เสมอ

**สรุป:** source_type ลดจำนวน "แบบของกลไก" (จาก 6 CVE เหลือ 2-3 mechanism)
ส่วน per-dependency config ยังต้องมีครบทุกตัว แต่เบากว่าเพราะ reuse ส่วน core ได้

---

## 33. Trivy ให้ข้อมูลอะไรได้บ้าง vs ต้อง hardcode อะไรบ้าง

ตรวจสอบ `scan.json` จริงจาก CVE-2021-44228 (Log4Shell) พบ:

```json
"PkgName": "org.apache.logging.log4j:log4j-core",
"PURL": "pkg:maven/org.apache.logging.log4j/log4j-core@2.8.1",
"FixVersion": "2.15.0, 2.3.1, 2.12.2",
"InstallVersion": "2.8.1",
"Status": "fixed"
```

**สังเกตสำคัญ:** PkgName ของ Log4Shell (`org.apache.logging.log4j:log4j-core`)
**ต่างจาก** CVE-2017-5645 (`log4j:log4j`) — แม้เป็น "log4j" เหมือนกันในหัวเรื่อง
แต่คนละ artifact group เพราะ log4j 1.x → 2.x เปลี่ยน package structure
→ ต้องเช็คว่า Maven property name เปลี่ยนตามไหม (`log4j.version` vs `log4j2.version`)
ก่อนสรุป — **ยังไม่ได้เช็คจริง**

### สรุปว่า Trivy ให้อะไรได้/ไม่ได้ (ตรงกับ progress 7-31 §17 อยู่แล้ว):

| ข้อมูล | Trivy ให้ได้ไหม |
|---|---|
| InstalledVersion, FixedVersion, PkgName, PURL | ✅ ดึง runtime ได้เลย |
| ชื่อ property ใน pom.xml จริง (`log4j.version`) | ❌ Trivy สแกน jar ที่ build แล้ว ไม่รู้จัก source |
| source_type / build mechanism | ❌ ไม่มี field นี้ |

**ย้ำ (ตรงกับ 7-31):** ตัวเลข (version) ดึงจาก Trivy ได้จริง แต่ตัวโครงสร้าง
(property name, build mechanism) ต้องหาจากที่อื่น — คนละชั้นข้อมูล

**⚠️ จุดที่ยังไม่ตรงกับ 7-31:** 7-31 สรุปว่า "ทางเลี่ยง hardcode" คือ
**อ่านจาก pom.xml ตรงๆ** (grep หา artifactId ที่ตรง CPE) แทนการเดา/hardcode
ชื่อ property ไว้ล่วงหน้าใน config — ส่วน session นี้ (ก่อนจะอ่าน 7-31 ทัน)
ยังทดลองแบบ hardcode `dep_property` ใน `cve_config.yaml` อยู่ (ดู §34)

---

## 34. ทดลอง pipeline POC จริง — CVE-2017-5645

สร้างไฟล์ทดลองใน `/home/claude/kalama-demo/`:
- `output/scan/before-patch/trivy/scan.json` (จำลอง structure ตรงกับของจริง)
- `cve_config.yaml` (per-CVE config: source_type, base_image, dep_property)
- `patch_and_verify.sh` (อ่าน Trivy runtime + config → generate Dockerfile)

**ผลรัน:** สำเร็จครบ 4 step — อ่าน `FixedVersion=2.8.2` จาก scan.json จริง,
อ่าน `dep_property=log4j.version` จาก config, ประกอบเป็น Dockerfile,
พิมพ์เตือน silent-failure verification step

**Dockerfile ที่ generate ได้:**
```dockerfile
FROM eclipse-temurin:8-jre
ARG DEP_VERSION=2.8.2
ARG DEP_PROPERTY=log4j.version
RUN mkdir -p /root/.m2 && echo '...' > /root/.m2/settings.xml
WORKDIR /app
COPY . .
RUN mvn versions:set-property -Dproperty=${DEP_PROPERTY} -DnewVersion=${DEP_VERSION} ...
RUN mvn -s /root/.m2/settings.xml package assembly:single
EXPOSE 4712
CMD ["java", "-jar", "target/log4jrce-1.0-SNAPSHOT-all.jar"]
```

**⚠️ ข้อจำกัดสำคัญที่ต้องแก้ก่อนใช้จริง:**
Pipeline นี้ **hardcode `dep_property: log4j.version` ใน `cve_config.yaml` ล่วงหน้า**
— นี่คือแนวทางที่ **progress 7-31 §17 บอกไว้แล้วว่าเป็นปัญหา** ("ไม่อยากเขียน
`case.yaml` ที่ hardcode ... ทั้งที่ข้อมูลพวกนี้ Trivy มีอยู่แล้ว") และ 7-31 ได้
เปลี่ยนไปใช้แนวทาง **"อ่านสูตรที่มี (grep pom.xml จริง) → หา token เวอร์ชัน →
แทนที่ด้วย FixedVersion"** แทนแล้ว (§20 ของ 7-31)

**ต้อง sync:** demo POC นี้เป็น**แนวทางเก่าที่ 7-31 ทิ้งไปแล้ว** ต้องปรับให้ตรงกับ
"อ่านสูตร+แทน token" ก่อนเอาไปต่อยอดจริง — ไม่ใช่ config แบบ hardcode ต่อ CVE

---

## 35. โอกาส automate มากขึ้นจาก demo — แต่ต้องแยกให้ชัดว่ามากขึ้นตรงไหน

Demo POC พิสูจน์ automate ได้แค่ **1 ใน 4 ช่วงของ pipeline**:

- ✅ **Automate ได้:** "ประกอบ Dockerfile" หลังจากรู้ `source_type` + `dep_property`/token
  location แล้ว (assembly step)
- ❌ **ยัง manual:** "หา `source_type` + `dep_property`/token location" สำหรับ CVE ใหม่
  (decision/classification step) — ต้องเปิดไฟล์สูตรเองเสมอ

**เทียบกับ literature:** ตรงกับ Hu et al. §4.2 ที่บอกว่า template-based generation
**"can generate quality candidate patches for specific types"** ได้จริง แต่
**"poor adaptability"** (การ classify CVE ใหม่เข้า type ไหน) ยังเป็นจุดที่ human
ต้องทำ — Kalama อยู่ในสถานะเดียวกับที่ literature ยอมรับว่าเป็นขีดจำกัดปกติ

**ข้อเสนอสำหรับ thesis:** รายงานเป็น **"template-based deployment automation
หลัง manual classification"** ไม่ใช่ **"automated pipeline"** เฉยๆ

---

## 36. สถานะล่าสุด & next step (รวมของค้างจาก 7-31 + session นี้)

**ตกผลึกเพิ่มจาก session นี้:**
- มี literature 3 ฉบับอ่านเต็มแล้ว (Dissanayake, Hu et al., PatchLens แค่ snippet)
  รองรับทิศทาง "validation-methodology contribution" แทน "automation-engineering"
- เคลียร์แล้วว่า semantics-based patch generation (AVR) ≠ Kalama's Dockerfile
  deployment automation — คนละ layer, ไม่ควรสับสนตอนเขียน thesis
- ยืนยันด้วย demo จริงว่า pipeline "อ่าน Trivy runtime + per-CVE detail →
  generate Dockerfile" รันได้จริงในหลักการ (แต่ implementation ยังใช้วิธี
  hardcode ที่ 7-31 เลิกใช้ไปแล้ว ต้องแก้)

**ของค้างจาก 7-31 (ยังไม่ได้แตะ):**
- ยังไม่ยืนยันบน VM จริงว่า `mvn -pl apps/showcase -am package` (S2-045) build
  ผ่านจริงไหม
- s2-045 หลัง patch: re-exploit ต้อง fail ถึงจะยืนยันว่า patch เวิร์ค (ยังไม่ได้รัน)
- ยังไม่แตะ Ghostcat (คาดว่าตกกลุ่ม B/config, จะไม่เข้า scope version-bump)
- ปมเดิม: re-exploit สำเร็จหลัง patch = "FixedVersion ผิด" หรือ "fix ไม่เวิร์ค" —
  ยังแยกไม่ออก

**next step ใหม่จาก session นี้:**
1. **แก้ demo POC (§34) ให้ตรงกับแนวทาง 7-31** — เปลี่ยนจาก hardcode
   `dep_property` เป็น grep pom.xml จริงหา token เวอร์ชัน
2. คุยกับ Atthapol เรื่อง reframe thesis เป็น validation-methodology
   contribution (§28)
3. รอผลตอบกลับอีเมลจาก Ohaeche (Springer paper) — ถ้าได้มาจะเป็น
   complementary case study
4. เอา flow "อ่านสูตร+แทน token" (7-31 §20) ไปรันจริงบน VM กับ S2-045
   ตามที่ 7-31 วางแผนไว้เดิม

---

## 37. บทเรียนเชิงกระบวนการของ session นี้

- **การหา literature มาโต้แย้งตัวเอง** ดีกว่าการเชื่อ observation ของตัวเองเปล่าๆ —
  แต่ต้องอ่านให้ครบก่อนอ้าง (เจอปัญหาว่าอ้าง paper ที่ยังไม่ได้อ่านเต็มไปตอนแรก
  ต้องกลับมาแก้)
- **demo/POC ที่ทำไปเร็วเกินไปโดยไม่เช็ค progress note ล่าสุดก่อน** ทำให้หลงไปใช้
  แนวทางที่ตัวเองเลิกใช้ไปแล้ว (hardcode dep_property) — บทเรียน: ก่อนสร้างของใหม่
  ต้องเช็ค progress note ล่าสุดก่อนเสมอ ไม่ใช่แค่เช็ค lab note รายตัว CVE
- **Access ทาง institutional (SpringerLink ผ่าน มมส.)** ไม่มี SSO จริง มีแค่
  IP-based ผ่าน journal package เท่านั้น — บทเรียนสำหรับหา literature รอบต่อไป:
  เช็ค WiFi มหาลัยหรือ VPN ก่อน ไม่ใช่พึ่ง SSO login

---

*ต่อจาก kalama_progress(7-31-2026).md — section 24–37 เน้นหา literature รองรับ
scope + POC pipeline (ที่ต้องปรับให้ตรงกับแนวทาง 7-31 ก่อนใช้จริง)*
*ยังเป็นขั้น literature review + POC เก่าที่ต้องแก้ — ยังไม่ได้ sync กับ "อ่านสูตร+แทน token"*
