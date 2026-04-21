# Huawei Network Log Screenshot Generator

แปลง Huawei VRP CLI log file เป็น PNG screenshot สไตล์ terminal เพื่อใช้ใน documentation, report, หรือ audit

## Version

**1.0.0** — 2026-04-21

Converts Huawei VRP CLI log files into terminal-style PNG screenshots for use in documentation, reports, or audits.

## การติดตั้ง

```bash
pip install -r requirements.txt
playwright install chromium
```

## วิธีใช้

### 1. วาง log file
วางไฟล์ `.txt` ในโฟลเดอร์ `logs/`

### 2. รัน
```bash
python run.py
```

### 3. ผลลัพธ์
PNG อยู่ในโฟลเดอร์ `screenshots/`

## รูปแบบ Log File ที่รองรับ

รองรับเฉพาะ Huawei VRP prompt format:

| Prompt | ระดับ | ตัวอย่าง |
|--------|--------|----------|
| `<RouterName>` | User view | `<HW-Core-BKK-01>` |
| `[RouterName]` | System view | `[HW-Core-BKK-01]` |
| `[RouterName-subview]` | Sub-view | `[HW-Core-BKK-01-ospf-1]`, `[HW-Core-BKK-01-GigabitEthernet0/0/1]` |

## กฎสำคัญ: หลังจบ nested command ต้องกลับมาที่ user view เสมอ

Script ใช้ depth เพื่อจัดกลุ่มคำสั่งเป็น screenshot:

- **User view** (`<Router>`) = depth 0
- **System view** (`[Router]`) = depth 1
- **Sub-view** (`[Router-...]`) = depth 2+

จุดจบของ nested block คือการกลับไป depth 0 (`<Router>` prompt) **ดังนั้นทุกครั้งที่จบชุดคำสั่ง nested ต้องมี `quit` กลับไป user view เสมอ**

### ถูกต้อง

```
<HW-Core-BKK-01> system-view
[HW-Core-BKK-01] interface GigabitEthernet0/0/1
[HW-Core-BKK-01-GigabitEthernet0/0/1] display this
[HW-Core-BKK-01-GigabitEthernet0/0/1] quit
[HW-Core-BKK-01] quit
<HW-Core-BKK-01> display clock              ← จบ block ก่อนหน้า เริ่ม standalone ใหม่
```

### ผิด — จะทำให้จัดกลุ่มผิด

```
<HW-Core-BKK-01> system-view
[HW-Core-BKK-01] interface GigabitEthernet0/0/1
[HW-Core-BKK-01-GigabitEthernet0/0/1] display this
[HW-Core-BKK-01-GigabitEthernet0/0/1] quit
[HW-Core-BKK-01] quit
# ไม่มี <Router> prompt กลับมา → คำสั่งถัดไปจะถูกรวมเข้า block เดิม
```

### หลายชุดคำสั่ง — แต่ละชุดต้องกลับ user view ก่อนเข้าใหม่

```
<HW-Core-BKK-01> system-view               ← เริ่ม block ที่ 1
[HW-Core-BKK-01] interface GE0/0/1
[HW-Core-BKK-01-GE0/0/1] display this
[HW-Core-BKK-01-GE0/0/1] quit
[HW-Core-BKK-01] quit
<HW-Core-BKK-01> system-view               ← เริ่ม block ที่ 2
[HW-Core-BKK-01] ospf 1
[HW-Core-BKK-01-ospf-1] display this
[HW-Core-BKK-01-ospf-1] quit
[HW-Core-BKK-01] quit
<HW-Core-BKK-01> display clock              ← standalone
```

## การตั้งชื่อไฟล์ PNG

| ประเภท | รูปแบบ | ตัวอย่าง |
|--------|--------|----------|
| Standalone | `{device} {command}.png` | `HW-Core-BKK-01 display device.png` |
| Nested block | `{device} {entry-cmd} {sub-views}.png` | `HW-Core-BKK-01 system-view ospf-1 GigabitEthernet0/0/1.png` |

## สร้าง log file ตัวอย่าง

```bash
python nested_log_gen.py
```

สร้าง `nested_huawei_log.txt` ที่มีคำสั่งครบทุกอย่าง อย่างละครั้ง