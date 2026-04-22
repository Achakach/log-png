# Huawei Network Log Screenshot Generator

แปลง Huawei VRP CLI log file เป็น PNG screenshot สไตล์ terminal เพื่อใช้ใน documentation, report, หรือ audit

## Version

**1.0.0** — 2026-04-21

Converts Huawei VRP CLI log files into terminal-style PNG screenshots for use in documentation, reports, or audits.

## Script Flow

```
logs/*.txt                        process_network_logs.py                      screenshots/
┌──────────────┐                  ┌──────────────────────────────┐              ┌─────────────┐
│ Huawei VRP   │──── 1. Parse ──→ │ _split_into_segments()       │              │             │
│ CLI log      │                  │   regex match prompts        │              │             │
│              │                  │   → [{prompt, command,      │              │             │
│              │                  │       output}]               │              │             │
│              │                  │                              │              │             │
│              │──── 2. Group ──→ │ _group_segments()            │              │             │
│              │                  │   depth-based grouping       │── 3. Render ─→│  PNG files  │
│              │                  │   → [[group1], [group2], …]  │  + Capture   │             │
│              │                  │                              │              │             │
│              │                  │ generate_screenshots()       │              │             │
│              │                  │   Jinja2 autoescape → HTML   │              │             │
│              │                  │   Playwright headless → PNG  │              │             │
└──────────────┘                  └──────────────────────────────┘              └─────────────┘
```

### ขั้นตอนที่ 1: Parse — `_split_into_segments()`

Regex หาทุกบรรทัดที่ขึ้นต้นด้วย Huawei VRP prompt:

```
^(<[A-Za-z][\w.\-]*>|\[~?\*?[A-Za-z][\w.\-/]*\])\s+(.+)$
```

`~?\*?` รองรับ `~` (unsaved config) และ `*` (alarm/fault) prefix ใน square bracket prompts

แต่ละ match กลายเป็น segment: `{prompt, command, output}`
"output" คือทุกอย่างระหว่าง prompt ปัจจุบันถึง prompt ถัดไป

### ขั้นตอนที่ 2: Group — `_group_segments()`

กำหนด depth ของแต่ละ segment:
- `<Router>` → depth **0** (user view)
- `[Router]` → depth **1** (system view)
- `[Router-subview]` → depth **2+** (sub-view)

จัดกลุ่มตามกฎ:

**กฎ 1 — Standalone** (depth เท่าเดิม ไม่ลึกขึ้น):
```
<HW> display device     → 1 PNG เดี่ยว
<HW> display clock      → 1 PNG เดี่ยว
```

**กฎ 2 — Nested block** (depth ลึกขึ้น จนกว่าจะกลับ depth 0):
```
<HW> system-view           ← เริ่ม block (depth 0→1)
[HW] interface GE0/0/1      ← อยู่ใน block (depth 1→2)
[HW-GE0/0/1] display this  ← อยู่ใน block (depth 2)
[HW-GE0/0/1] quit           ← อยู่ใน block (depth 2→1)
[HW] quit                    ← อยู่ใน block (depth 1→0)
<HW> display clock          ← จบ block! → standalone ใหม่
```

**จุดจบของ block = กลับไป depth 0 (`<Router>`)**

### ขั้นตอนที่ 3: Render + Screenshot — `generate_screenshots()`

แต่ละ group ผ่าน pipeline:
```
group → Jinja2 autoescape render → HTML → Playwright set_content → screenshot #capture-area → PNG
```

## การติดตั้ง

### Prerequisites
- **Python 3.10+**
- **pip** (Python package manager)

### ติดตั้ง dependencies

```bash
pip install -r requirements.txt
playwright install chromium
```

### รายการ dependencies

| Package | ใช้สำหรับ | ติดตั้งอัตโนมัติ |
|---------|----------|------------|
| `jinja2` | HTML template rendering (autoescape เปิดอยู่) | ผ่าน `pip install -r requirements.txt` |
| `playwright` | Headless Chromium screenshot capture | ผ่าน `pip install -r requirements.txt` |
| `python-docx` | Word document manipulation (`putpnginword.py`) | ผ่าน `pip install -r requirements.txt` |
| Chromium browser | Playwright ใช้ render HTML → PNG | ผ่าน `playwright install chromium` (รันทีเดียว) |

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
| `[~RouterName]` | System view (unsaved config) | `[~HW-Core-BKK-01]` |
| `[*RouterName]` | System view (alarm/fault) | `[*HW-Core-BKK-01]` |
| `[RouterName-subview]` | Sub-view | `[HW-Core-BKK-01-ospf-1]`, `[HW-Core-BKK-01-GigabitEthernet0/0/1]` |
| `[~RouterName-subview]` | Sub-view (unsaved config) | `[~HW-Core-BKK-01-ospf-1]` |
| `[*RouterName-subview]` | Sub-view (alarm/fault) | `[*HW-Core-BKK-01-GigabitEthernet0/0/1]` |

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
| Nested block | `{device} {cmd1} {cmd2} ... .png` | `HW-Core-BKK-01 system-view interface GigabitEthernet0_0_29 display this shutdown quit quit.png` |

หมายเหตุ: Nested block จะต่อคำสั่งทั้งหมดเข้าด้วยกัน (`/` ในชื่อ interface จะถูกแทนที่ด้วย `_`)

## สร้าง log file ตัวอย่าง

```bash
python nested_log_gen.py
```

สร้าง `nested_huawei_log.txt` ที่มีคำสั่งครบทุกอย่าง อย่างละครั้ง

## แทรก PNG ลง Word (`putpnginword.py`)

แทรก PNG screenshot ลงในเอกสาร Word .docx โดยจับคู่คำสั่งในตารางกับชื่อไฟล์ PNG

### วิธีใช้
```bash
python putpnginword.py
```

ตั้งค่า path ที่ด้านบนของ script:
```python
DOCX_INPUT = r"replaced_document.docx"      # ไฟล์ Word ต้นทาง
PNG_PATH = r"path\to\png\*.png"             # path ของ PNG files
DOCX_OUTPUT = "output.docx"                  # ไฟล์ผลลัพธ์
```

### วิธีการทำงาน

1. **อ่านตาราง** ใน Word document → แต่ละ cell หา prompt+command lines และ node names
2. **จับคู่** ชื่อไฟล์ PNG ด้วย word-by-word prefix matching (case-insensitive)
   - รองรับคำสั่งย่อ: `system`→`system-view`, `dis`→`display`, `q`→`quit`
   - ต้องผ่าน 60% threshold ของ search tokens
3. **แทรกรูป** ลงที่ `<NodeName>` paragraph ใน cell (กว้าง 6.495 นิ้ว)

### รูปแบบ Cell ที่รองรับ

**Single command:**
```
<HUAWEI>display device
<TUC-TYB91G01HWLEFC303-CPLEF03>    ← แทรกรูปตรงนี้
```

**Nested command:**
```
<HUAWEI>system-view
[~HUAWEI]interface GigabitEthernet0/0/29
[~HUAWEI-GE0/0/29]display this
[~HUAWEI-GE0/0/29]quit
[~HUAWEI]quit
<TUC-TYB91G01HWLEFC303-CPLEF03>    ← แทรกรูปตรงนี้
```

**หมายเหตุ:** Prompt (`<HUAWEI>`, `[~HUAWEI]`, `[~HUAWEI-GE0/0/29]`) ไม่มีผลต่อการ match — ดึงเฉพาะส่วน command