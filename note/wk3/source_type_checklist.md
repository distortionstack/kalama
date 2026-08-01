# Source Type Checklist — ใช้ก่อนเขียน case config ของทุก CVE

> เป้าหมาย: ตอบคำถามเดียว — "vulhub เอา vulnerable artifact มาจากไหน / patch ผ่านกลไกอะไร"
> Trivy บอกไม่ได้ ต้องเปิดไฟล์เช็คเอง ทำตามลำดับ หยุดทันทีที่เจอ match

---

## ขั้นตอน

### 1. เปิด `docker-compose.yml`
- [ ] มี `image: vulhub/xxx:tag` เฉยๆ (ไม่มี `build:`) → prebuilt image ล้วน ข้ามไปข้อ 3
- [ ] มี `build: .` หรือ `build: ./path` → มี Dockerfile ให้เปิดต่อ ไปข้อ 2

### 2. เปิด `Dockerfile` — grep หา keyword

| เจอคำว่า | ความหมาย | → source_type |
|---|---|---|
| `mvn`, `npm install`, `pip install`, `go build`, `assembly:single` | compile จาก source | **A: build-from-source** |
| `wget`/`curl` ดึง `.war`/`.jar`/`.tar.gz`/`.zip` ที่ build เสร็จแล้ว | ของสำเร็จรูป | **B: prebuilt-download** |
| `apt install`/`apk add` (pin version) | OS package repo | **C: os-package** |
| ไม่มี dependency step เลย มีแต่ `COPY`/`ENV`/`sed` แก้ config | ไม่แตะ artifact | **D: config-only** |

สัญญาณเสริม (เดาได้จากรูปร่างไฟล์ก่อนอ่านละเอียด):
- มี `pom.xml`/`package.json` อยู่ใน build context (`COPY . /src`) → มักเป็น **A**
- Dockerfile สั้นมาก (5–10 บรรทัด) ไม่มี compile step → มักเป็น **B** หรือ **D**

### 3. ถ้ายังไม่ชัด — เปิด `README.md` ของ vulhub
- [ ] มักบอกตรงๆ ท้ายไฟล์ว่า "upgrade to X" (→ A/B/C) หรือ "set config Y" (→ D)

### 4. ถ้ายังไม่ชัด — เช็ค NVD / CISA KEV `requiredAction` / vendor advisory
- [ ] เป็น text ที่ต้องอ่านเอง parse อัตโนมัติไม่ได้ — encode เป็น manual field

---

## ผลที่ยืนยันแล้ว

| CVE | docker-compose | Dockerfile keyword | source_type | หมายเหตุ |
|---|---|---|---|---|
| CVE-2017-5645 (log4j TcpSocketServer) | `build: .` | `mvn package assembly:single`, มี pom.xml | **A: build-from-source** | ต้อง build เองเพราะ vulhub ไม่มี patched image บน Hub |
| CVE-2017-5638 (S2-045 Struts2) | `build: .` | `wget .../struts-${VER}-apps.zip` ตรงๆ ไม่มี mvn | **B: prebuilt-download** | pom.xml ที่เจอ (Struts2FileUpload) เป็นคนละตัว ไม่เกี่ยวกับ build จริง |

## รอเช็ค

| CVE | คาดว่าเป็น | เหตุผลที่คาด | ต้องทำ |
|---|---|---|---|
| CVE-2021-44228 (Log4Shell) | A หรือ D (มี 2 ทางแก้จริง: version bump / ลบ JndiLookup.class) | มี dual-path fix ที่รู้จักทั่วไป | เปิด `vulhub/log4j/CVE-2021-44228/Dockerfile` |
| CVE-2017-9805 (S2-052) | A หรือ B (คาดว่าโครงสร้างคล้าย s2-045 เพราะเป็น struts2 showcase เหมือนกัน) | ช่องโหว่อยู่ที่ rest-plugin ไม่ใช่ core | เปิด `vulhub/struts2/s2-052/Dockerfile` |
| CVE-2020-1938 (Ghostcat/Tomcat AJP) | D: config-only | fix จริงคือ `secretRequired=true` / ปิด AJP connector เป็นที่รู้จักทั่วไป | เปิด README ยืนยัน |

---

## Field ที่ต้องเพิ่มใน case YAML

```yaml
CVE-<id>:
  source_type: build-from-source | prebuilt-download | os-package | config-only
  template: <ชื่อ template ที่ตรงกับ source_type>
  # เฉพาะกรณี A (build-from-source)
  dep_property: <ชื่อ property ใน pom.xml/package.json>
  dep_version: <จาก Trivy FixedVersion>
  # เฉพาะกรณี B (prebuilt-download)
  version_arg: <ชื่อ ARG ใน Dockerfile>
  dep_version: <จาก Trivy FixedVersion>
  # เฉพาะกรณี D (config-only)
  config_change: <บรรทัด config ที่ต้องแก้>
```

> field `source_type` นี้ Trivy ไม่มีให้ ต้อง manual เช็คทุก CVE — ไม่ automate ได้ 100%
> (ตรงกับ Type A/B ปัญหาที่คุยไว้ใน progress note 7-29 ข้อ 3)
