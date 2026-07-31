# Kalama (GUIDE-1) — บันทึกความคืบหน้า (ต่อจาก Notebook)

**เฟส Automation — ส่วน "การอัพเดท/แพตช์" โดยเฉพาะ**
ต่อจาก `kalama_progress.ipynb` (section 1–9)
บันทึกวันที่: 2026-07-30

> ไฟล์นี้สรุปสิ่งที่คุยกันต่อจาก notebook — เจาะลงที่ **stage การ patch (rebuild image)**
> หัวใจคือ: เทียบ 3 วิธี build patched image → เลือกแนวทางที่ automate ง่ายสุด → ตกผลึกเป็นแนวคิด "template ต่อ fix-type"

---

## 10. หลักการที่ยืนยันแล้ว: patch = rebuild image ใหม่ (ไม่ใช่แก้ container ที่รันอยู่)

มีการเสนอไอเดีย `docker exec` เข้าไป `apt install` ใน container ที่รันอยู่ — **ตกไป**

เหตุผล:
1. **ปัญหาส่วนใหญ่เกิดก่อน container ขึ้นด้วยซ้ำ** — พังตอน `docker pull`/`docker build` ไม่ใช่ตอน runtime
2. **ขัด core thesis เรื่อง reproducibility** — ถ้า container อัพเดทตัวเอง สภาพแวดล้อมจะไม่คงที่ ผล exploit อาจเปลี่ยนโดยไม่รู้ว่าเปลี่ยนเพราะอะไร
3. หลักการ container = immutable — วิธีที่ถูกคือ **สร้าง image ใหม่** ไม่ใช่ mutate ของเดิม

> สรุปหลักการ: **แก้ที่ "สูตร" (Dockerfile/source) แล้ว rebuild** ไม่ใช่แก้ที่ "ของสำเร็จ" (running container)

---

## 11. บทเรียนสำคัญ: environment drift มีตัวตนจริง วัดได้

ได้หลักฐานรูปธรรมจากการเทียบ Dockerfile 3 เวอร์ชันของ log4j (CVE-2017-5645):

**Vulhub Dockerfile ต้นฉบับ วันนี้ build ไม่ผ่านแล้ว** ทั้งที่ CVE เดียวกัน โค้ดเดียวกัน — เปลี่ยนแค่ "เวลา" ที่มา build เพราะมันเน่าไป 2 จุด:

| จุดที่พัง | อาการ | สาเหตุ |
|---|---|---|
| Maven mirror (build-env) | โหลด Maven ผ่าน `http://archive.apache.org` ไม่ได้ | Maven Central ปิด HTTP ตั้งแต่ 2020 |
| runtime base image | `openjdk:8-jre-slim` pull ไม่ได้ | ถูกถอดจาก Docker Hub |

**นัยต่อ thesis:** นี่คือมิติที่ CVSS/EPSS/KEV มองไม่เห็นเลย — score บอกว่า CVE อันตรายแค่ไหน แต่ไม่มีตัวไหนบอกว่า "testbed ของมันวันนี้ reproduce ไม่ได้แล้วถ้าไม่แก้ 2 จุด"

**Metric ที่ควรจดต่อ CVE:** จำนวนจุด drift ที่ต้องแก้ + จำนวน external resource ที่ Dockerfile พึ่งพา
สมมติฐานที่ทดสอบได้: *ยิ่ง CVE เก่า ยิ่ง drift เยอะ ยิ่ง reproduce ยาก* — มุมใหม่ที่ไม่มีใน scoring system ไหน

---

## 12. เทียบ 3 วิธี build patched image

โจทย์: ต้อง rebuild เพราะ log4j-core ถูก compile ฝังใน fat jar (`assembly:single`) — swap jar/layer ทีหลังไม่ได้
คำถามจริงคือ **"rebuild ยังไงให้เปลี่ยนเวอร์ชันได้โดยไม่แก้ไฟล์มือ"**

| | **ของเรา** (patch-in-place) | **ของเพื่อน** (replace-with-maintained) | **แนวทางที่ 3** (template + variable) |
|---|---|---|---|
| build-env base | `vulhub/java:8u162-jdk` (เดิม) | `maven:3.9.9-eclipse-temurin-8` | รับเป็น `ARG` (default = ของเพื่อน) |
| Maven | โหลด 3.2.2 เอง + แก้ HTTPS mirror | มากับ image | มากับ image |
| runtime base | `eclipse-temurin:8-jre` | `eclipse-temurin:8-jre` | รับเป็น `ARG` |
| เปลี่ยนเวอร์ชัน = | แก้ไฟล์มือ | แก้ไฟล์มือ | **เปลี่ยน `--build-arg`** |
| Dockerfile ต่อ CVE | เขียนใหม่ | เขียนใหม่ | **ตัวเดิมทุกตัว** |
| เวอร์ชันมาจาก Trivy ตรงๆ | ❌ | ❌ | ✅ |
| external resource ที่พึ่ง | 3 จุด (vulhub img + archive + mirror) | 2 จุด (maven img + temurin) | 2 จุด |
| setup ล่วงหน้า | ไม่มี | ไม่มี | refactor pom เป็น property ครั้งเดียว/product |

**สอง strategy ที่เห็นชัดจากของเรา vs เพื่อน:**
- **patch-in-place** = ซ่อมของเดิมทีละจุดที่พัง
- **replace-with-maintained** = ทิ้ง base ที่พัง ไปใช้ image ที่ยัง maintained → พึ่ง external resource น้อยจุดกว่า = จุดพังในอนาคตน้อยกว่า

---

## 13. แนวทางที่เลือกสำหรับ automation: Template + version-as-variable

Dockerfile ตัวเดียว รับทุกอย่างเป็น build ARG — automation แค่เติมค่า ไม่แตะไฟล์:

```dockerfile
ARG MAVEN_IMAGE=maven:3.9.9-eclipse-temurin-8
ARG RUNTIME_IMAGE=eclipse-temurin:8-jre
ARG DEP_PROPERTY           # เช่น log4j.version / struts2.version
ARG DEP_VERSION            # ← มาจาก Trivy FixedVersion ตรงๆ

FROM ${MAVEN_IMAGE} AS build-env
COPY . /usr/src/
WORKDIR /usr/src
RUN mvn versions:set-property \
      -Dproperty=${DEP_PROPERTY} -DnewVersion=${DEP_VERSION} && \
    mvn package assembly:single

FROM ${RUNTIME_IMAGE}
COPY --from=build-env /usr/src/target/*-all.jar /app.jar
CMD ["java","-jar","/app.jar"]
```

automation เรียกแค่:
```bash
docker build --build-arg DEP_PROPERTY=log4j.version \
             --build-arg DEP_VERSION=2.8.2 \
             -t log4j:2.8.2-patched .
```

**ทำไมอันนี้ automate ง่ายสุด:**
1. ไม่แก้ไฟล์เลย เปลี่ยนแค่ตัวแปร → Dockerfile ตัวเดิมใช้ซ้ำทุก CVE ที่เป็น Maven fat-jar
2. เวอร์ชันมาจาก Trivy `FixedVersion` ตรงๆ → traceable ย้อนได้ว่ามาจาก scan ไหน
3. รวมข้อดีเพื่อน (maven official image เป็น default) + fallback ของเรา (override ARG ได้ถ้าเจอ JDK แปลกๆ) ไว้ที่เดียว
4. `mvn versions:set-property` = เปลี่ยนเวอร์ชันผ่าน property โดยไม่ parse/แก้ pom เอง → เลี่ยงความเสี่ยง string manipulation

**เงื่อนไข setup ครั้งเดียว:** `versions:set-property` ทำงานได้ถ้า pom.xml ใช้ property (`${log4j.version}`) ถ้า pom เดิม hardcode เวอร์ชันตรงๆ ต้อง refactor ให้ดึงเป็น property ก่อน — **หนึ่งครั้งต่อ product ไม่ใช่ต่อ CVE**
→ *ต้องเปิด pom ของ Vulhub log4j ดูจริงว่าใช้ property อยู่แล้วหรือ hardcode*

---

## 14. ตกผลึก: Kalama = "ชุด template ต่อ fix-type" ไม่ใช่ "template เดียวจบ"

Template ข้อ 13 ครอบเฉพาะ fix แบบ **Maven version bump** เท่านั้น ซึ่งไม่ใช่ทุก CVE:

| CVE | fix แบบไหน | template นี้ใช้ได้ไหม |
|---|---|---|
| CVE-2017-5645 (log4j) | Maven version bump | ✅ |
| CVE-2017-5638 / S2-045 (Struts) | Maven version bump | ✅ (รอเช็ค property) |
| CVE-2017-9805 / S2-052 | version bump คนละ artifact (`rest-plugin`) | ⚠️ ได้ถ้า property ชี้ถูก artifact |
| CVE-2021-44228 (Log4Shell) | version bump **หรือ** ลบ class JndiLookup | ⚠️ ได้ถ้าเลือกทาง version |
| CVE-2020-1938 (Ghostcat) | **config (secretRequired) + Tomcat เป็น base image** | ❌ ไม่ใช่เลย |

**ภาพที่ถูก** — case config ของแต่ละ CVE ระบุว่าใช้ template ไหน + ป้อนตัวแปรที่ template นั้นต้องการ:

```yaml
CVE-2017-5645:
  template: maven-fatjar
  dep_property: log4j.version
  dep_version: <จาก Trivy>

CVE-2020-1938:
  template: config-patch
  config_change: "secretRequired=true"
```

จำนวน template น้อย (คาดว่า 2–3 อัน) ครอบเคสส่วนใหญ่:
```
maven-fatjar-template   → log4j, struts (fix ด้วย version bump) — 4/6 ตัว
config-patch-template   → Ghostcat (fix ด้วยแก้ config)
[เผื่ออนาคต: os-package-template]
```

**ข้อดี:** ไม่ over-fit (ไม่ยัด Ghostcat เข้า Maven template จนพัง), ยังได้ reuse เต็มที่กับ 4/6 ตัวที่เป็น Maven, และ map กับ fix-type ที่ Trivy บอกไม่ได้ → ตรงกับ knowledge layer เล็กๆ ที่ยอมรับว่าต้องมี

---

## 15. สถานะล่าสุด & next step

**ตกลงแล้ว:**
- patch = rebuild image ใหม่ (ไม่แตะ running container)
- แนวทาง automation = **template + version-as-variable** (ข้อ 13) ขับด้วยค่าจาก Trivy
- โครงใหญ่ = **template ต่อ fix-type** (ข้อ 14) เลือก template ผ่าน case config
- design principle ใหม่: *ยิ่งพึ่ง external resource น้อยจุด ยิ่งทน drift* — เก็บ "จำนวนจุดพึ่งพา" เป็น metric

**ยังไม่ตัดสิน (ยกไปคิดหลังทำมือ):**
- วิธีคัดแยก/จัดกลุ่ม template (จะรู้ว่าต้องมีกี่อันจริงๆ หลังทำมือครบ 6 ตัว)
- pom ของ Vulhub log4j ใช้ property อยู่แล้วหรือต้อง refactor (เปิดดูของจริง)
- ปมเดิมจาก notebook §7.4: re-exploit สำเร็จ = "FixedVersion ผิด" หรือ "fix ไม่เวิร์ค" (ยังไม่มีคำตอบ)

**แผนที่ยืนยัน:** ทำมือครบทั้ง 6 CVE ก่อน แล้วหา pattern ที่ซ้ำมากที่สุด → นั่นคือตัวที่ควร automate ก่อน
เหตุผล: ตรงกับ methodology ของ Atthapol ("เข้าใจก่อน automate", "simplest first") และ pattern ที่โผล่จากการทำมือจริงน่าเชื่อกว่า design ที่เดาไว้ก่อน — เป็น empirical rigor แบบเดียวกับ core thesis

**ก่อนเริ่มแล็ปควรล็อกให้ชัดกับ Atthapol 2 อย่าง (แก้ทีหลังแพงสุด):**
1. **ground truth มาจากไหน** — ค่าที่ถือว่า "ถูก" ที่เอาไปเทียบกับ Trivy คำนวณ Precision/Recall/F1
2. **freeze schema การจด lab note** — จดฟิลด์เดียวกันทุก CVE โดยเฉพาะช่อง "ปัญหาที่พบระหว่างทาง" (= ที่ pattern จะโผล่)

---

*ต่อจาก kalama_progress.ipynb — ส่วนนี้เน้น stage การ patch/rebuild ยังเป็นขั้น design ยังไม่มีโค้ด automation จริง เริ่มเขียนหลังทำมือครบ 6 CVE*
