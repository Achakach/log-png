# Huawei Network Log Screenshot Generator

แปลง Huawei VRP CLI log file เป็น PNG screenshot สไตล์ terminal เพื่อใช้ใน documentation, report, หรือ audit

## Prerequisites

ก่อนใช้งานต้องมีสิ่งต่อไปนี้:

| สิ่งที่ต้องมี | เวอร์ชันขั้นต่ำ | ใช้สำหรับ |
|---|---|---|
| **Python** | 3.10+ | รัน script ทั้งหมด |
| **pip** | ล่าสุด | ติดตั้ง dependencies |
| **Chromium** | ล่าสุด | Playwright ใช้ render HTML → PNG (ติดตั้งผ่าน `playwright install chromium`) |
| **Huawei VRP log** | - | ไฟล์ `.txt` ที่มี prompt format `<Router>` หรือ `[Router]` |

### ขั้นตอนติดตั้ง

```bash
pip install -r requirements.txt
playwright install chromium
```

### Dependencies หลัก

| Package | ใช้สำหรับ |
|---------|----------|
| `jinja2` | HTML template rendering |
| `playwright` | Headless Chromium screenshot |
| `python-docx` | Word document manipulation |
| `pywin32` *(Windows only)* | Required by `word_com_embed.py` for OLE embedding |
| `filename_utils.py` | Shared `sanitize_filename()` utility for consistent filename handling |
| `re` | ใช้ใน `extract_commands.py` สำหรับ regex matching |
| `abbreviations.json` | ไฟล์ข้อมูล abbreviation 198 entries — จำเป็นต้องมีในที่เดียวกับ script |

## Version

**1.3.0** — 2026-05-21

- Abbreviation expansion migrated from hardcoded to JSON: `abbreviations.json` with 198 entries, loaded dynamically by `run.py`, `putpnginword.py`, `putpnginxlsx_v2.py`, and `extract_commands.py`
- Added `extract_commands.py`: extract commands from logs, compare against `abbreviations.json`, report missing commands
- Added `font_size` and `line_height` to `run_config.json` for screenshot rendering density control
- Added `xxx.*` wildcard support in `putpnginword.py` for flexible file extension matching
- Added strict error preference in `putpnginword.py`: `prefer_error=True` returns `None` if no `[error]` PNG exists
- Fixed 7 ambiguous abbreviation collisions in `abbreviations.json`

**1.2.0** — 2026-05-11

- Codebase cleanup: removed 86 unused tracked files, deduplicated `sanitize_filename()` to `filename_utils.py`
- Added error handling: clear messages for missing docx, no PNGs, Word COM failures
- Pinned dependency versions in `requirements.txt`

**1.1.0** — 2026-05-02

- Implemented Option B (block-scoped node matching): same node can now receive multiple images when it appears after different command blocks in the same cell
- Added error detection and preference: PNGs with `[error]` suffix are skipped in favor of clean PNGs

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

```bash
pip install -r requirements.txt
playwright install chromium
```

## วิธีใช้

### 1. วาง log file
  วางไฟล์ `.txt` หรือ `.log` ในโฟลเดอร์ `logs/`

### 2. รัน
```bash
python run.py
```

### 3. ผลลัพธ์
PNG อยู่ในโฟลเดอร์ `screenshots/`

### Config (`run_config.json`)

ไฟล์ `run_config.json` จะถูกสร้างอัตโนมัติหากยังไม่มี:
```json
{
  "logs_dir": "logs",
  "output_dir": "screenshots",
  "whitelist": [],
  "font_size": 6,
  "line_height": 1.3
}
```

- `whitelist` — ระบุคำสั่งที่ต้องการประมวลผลเท่านั้น (`[]` = ทั้งหมด)
- `font_size` — ขนาดตัวอักษรใน screenshot (px)
- `line_height` — ความสูงบรรทัดใน screenshot

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

สร้างไฟล์ `.txt` หรือ `.log` ด้วย Huawei VRP prompt format (`<Router>` / `[Router]`)

## เพิ่ม PNG ลง Excel / Word

มี 3 เวอร์ชันของ Excel inserter ที่มี layout ต่างกัน:

### `putpnginxlsx.py` (v1 — Vertical Stack)
วาง PNG ซ้อนกันเป็นคอลัมน์เดียว

### `putpnginxlsx_v2.py` (v2 — Horizontal Gallery)
วาง PNG เรียงแนวนอน: 1 row ต่อ device, มี device name ในคอลัมน์แรก

### `putpnginxlsx_v3.py` (v3 — Vertical Gallery)
วาง PNG เรียงแนวตั้ง: 1 column ต่อ device, device name อยู่ใน row 1 (bold)

ทั้ง 3 เวอร์ชันอ่าน config จากไฟล์ `<script>_config.json` ที่อยู่ใน directory เดียวกัน

## แทรก PNG ลง Word (`putpnginword.py`)

แทรก PNG screenshot ลงในเอกสาร Word .docx โดยจับคู่คำสั่งในตารางกับชื่อไฟล์ PNG

### วิธีใช้
```bash
python putpnginword.py
```

ตั้งค่าผ่าน `putpnginword_config.json`:
```json
{
  "docx_input": "input.docx",
  "png_path": "screenshots/*.png",
  "docx_output": "output.docx",
  "target_sections": []
}
```

ตั้งค่า path ที่ด้านบนของ script:
```python
DOCX_INPUT = r"replaced_document.docx"      # ไฟล์ Word ต้นทาง
PNG_PATH = r"path\to\png\*.png"             # path ของ PNG files
DOCX_OUTPUT = "output.docx"                  # ไฟล์ผลลัพธ์
```

### วิธีการทำงาน

1. **อ่านตาราง** ใน Word document → แต่ละ cell หา prompt+command lines และ node names
   - ข้าม prompt เปล่าที่ไม่มีคำสั่ง (เช่น `[HUAWEI]`)
   - ข้าม model label เช่น `CEx01`, `CEx02` (ไม่มีผลต่อการ match)
2. **ขยายคำย่อ** จาก `abbreviations.json` (198 entries) ก่อนจับคู่ — รองรับ abbreviation ทั้งหมดที่อยู่ใน JSON (`dis th`→`display this`, `system`→`system-view`, `dis ospf rou`→`display ospf routing`, ฯลฯ)
3. **จับคู่** ชื่อไฟล์ PNG ด้วย contiguous subsequence matching (case-insensitive)
   - คำสั่งทั้งหมดใน cell ต้องปรากฏติดกันเป็นชุดในชื่อไฟล์ PNG
   - รองรับ cell ที่ไม่มี `quit` (match แค่ส่วนที่ cell มี)
   - ป้องกัน false positive (เช่น `system-view set cpu` จะไม่ match กับ `system-view display current-config`)
4. **แทรกรูป** ลงที่ `<NodeName>` paragraph แรกที่เจอใน cell (กว้าง 6.495 นิ้ว)
   - **Option B (block-scoped):** แต่ละ command block "เป็นเจ้าของ" nodes ที่อยู่หลังจากนั้น หาก node เดียวกันปรากฏหลังหลาย block จะได้รับหลายรูป (หนึ่งรูปต่อ block)
   - **Empty Block Merge:** หาก standalone block ใด block หนึ่งไม่มี node (เช่น `CEx01` อยู่บรรทัดเดียวกับคำสั่งแต่ไม่มี node ตามหลัง) block ว่างจะถูก merge เข้ากับ block ถัดไปที่มี node ทำให้ทุก node สามารถลอง match กับทุกคำสั่งใน pool
   - **Error Preference:** หากพบ PNG ที่มี `[error]` จะถูก skip และลองคำสั่งถัดไปจนกว่าจะเจอ PNG ที่ไม่มี error
   - **Wildcard Matching:** รองรับ `xxx.*` และ `xxx.zip`/`xxx.cfg` เป็น placeholder — DOCX มี `xxx.*` จะ match PNG ใดก็ได้ที่มี extension ใดก็ได้ (เช่น `startup saved-configuration backup.zip`)
   - **Strict Error Preference:** หาก `prefer_error=True` และไม่พบ PNG ที่มี `[error]` จะคืน `None` (ไม่มี fallback ไปหา clean PNG)
   - Deduplication เป็นระดับ paragraph (ไม่ใช่ระดับ cell) เพื่อป้องกันการแทรกซ้ำที่ paragraph เดียวกัน

### รูปแบบ Cell ที่รองรับ

**Single command:**
```
<HUAWEI>display device
<TUC-TYB91G01HWLEFC303-CPLEF03>    ← แทรกรูปตรงนี้ (1 รูป)
```

**Nested command:**
```
<HUAWEI>system-view
[~HUAWEI]interface GigabitEthernet0/0/29
[~HUAWEI-GE0/0/29]display this
[~HUAWEI-GE0/0/29]quit
[~HUAWEI]quit
<TUC-TYB91G01HWLEFC303-CPLEF03>    ← แทรกรูปตรงนี้ (1 รูป)
```

**Multiple blocks per cell (Option B):**
```
<HUAWEI>cmd 7
<device1>                             ← แทรกรูป cmd 7 ตรงนี้
<device2>                             ← แทรกรูป cmd 7 ตรงนี้
<HUAWEI>cmd 8
<device1>                             ← แทรกรูป cmd 8 ตรงนี้
<device2>                             ← แทรกรูป cmd 8 ตรงนี้
```
รวม 4 รูปใน cell เดียว (device1 × 2, device2 × 2)

**Multi-model with empty block merge (e.g. different device models):**
```
CEx01                                ← model label (ignored)
<HUAWEI>display cpu-usage            ← command for model CEx01
CEx02                                ← model label (ignored)
<HUAWEI>display cpu                 ← command for model CEx02
<TUC-TEST01>                        ← device 1
tries: cpu-usage → match.png ✅ → INSERT
       cpu       → skipped (already inserted)
<TUC-TEST02>                        ← device 2
tries: cpu-usage → [error].png ❌ → SKIP
       cpu       → match.png ✅ → INSERT
```
ผลลัพธ์: device1 ได้ cpu-usage, device2 ได้ cpu (โดยใช้ [ERROR] เป็นตัวกรอง)

**หมายเหตุ:** 
- Prompt (`<HUAWEI>`, `[~HUAWEI]`, `[~HUAWEI-GE0/0/29]`) ไม่มีผลต่อการ match — ดึงเฉพาะส่วน command
- บรรทัดที่ไม่ใช่ prompt+command และไม่ใช่ `<NodeName>` (เช่น `CEx01`) จะถูกข้ามโดยอัตโนมัติ
- Empty block merge ใช้ได้เฉพาะกับ **standalone commands** (ไม่มี `system-view` หรือ sub-view)

## Extract Commands from Logs (`extract_commands.py`)

Extracts all commands from Huawei VRP log files and writes them as one command per line to `.txt` files. Automatically compares extracted commands against `abbreviations.json` and reports which commands are missing from the abbreviation list.

### Usage
```bash
# Process all .txt/.log in logs/ directory (combined output)
python extract_commands.py

# Process specific file
python extract_commands.py path/to/log.txt
```

### Output (Directory Mode)
- `all_commands.txt` — every unique command from all logs (deduplicated, sorted)
- `all_missing.txt` — commands not found in `abbreviations.json`

### Config
Reads from `extract_commands_config.json`:
```json
{
  "logs_dir": "logs",
  "output_dir": "extracted_commands",
  "expand_abbreviations": true,
  "combine_output": true
}
```

### Features
- Reuses `_split_into_segments()` from `process_network_logs.py` — zero parsing logic duplication
- Abbreviations expanded by default (`dis th` → `display this`)
- Automatic comparison: loads `abbreviations.json`, reports missing commands
- Sanitizes non-command tokens before comparison: `username`, `local-user`, file extensions, interface identifiers, IP addresses, placeholder tokens (`xxx.zip`, `xxx.*`), trailing `all`, trailing numbers
- PyInstaller-compatible (`get_base_dir()` for `.exe` mode)

### Single-File Mode
When processing a single file, outputs per-file `.txt`:
```bash
python extract_commands.py path/to/log.txt
```
→ `{name}_commands.txt` + `{name}_missing.txt`

### Directory Mode (Default)
When processing a directory, accumulates all commands and writes combined output:
```bash
python extract_commands.py
```
→ `all_commands.txt` + `all_missing.txt`







```mermaid
flowchart TD
    %% --------------------------------------------------------
    %% การตั้งค่าความสวยงามและชุดสีตาม Theme (Dark Mode)
    %% --------------------------------------------------------
    classDef phase1 fill:#1a1a2e,stroke:#e94560,stroke-width:2px,color:#eee;
    classDef phase2 fill:#16213e,stroke:#0f3460,stroke-width:2px,color:#eee;
    classDef phase3 fill:#0f3460,stroke:#533483,stroke-width:2px,color:#eee;
    classDef phase4 fill:#533483,stroke:#e94560,stroke-width:2px,color:#eee;
    
    classDef success fill:#22c55e,stroke:#16a34a,stroke-width:2px,color:#000;
    classDef danger fill:#ef4444,stroke:#dc2626,stroke-width:2px,color:#fff;

    %% --------------------------------------------------------
    %% 🔍 1. PARSE
    %% --------------------------------------------------------
    subgraph P1["🔍 1. PARSE"]
        A["📁 logs/*.txt"] --> B{"Has Router prompt?"}
        B -->|"NO"| X["⛔ Skip file"]
        B -->|"YES"| C["Split into<br/>{prompt, command, output}"]
    end
    class P1,A,B,C phase1;
    class X danger;

    %% --------------------------------------------------------
    %% 📦 2. GROUP
    %% --------------------------------------------------------
    subgraph P2["📦 2. GROUP"]
        C --> D{"Command goes deeper?"}
        D -->|"YES (system-view)"| E["📎 Nested Block<br/>all cmds → 1 PNG"]
        D -->|"NO (standalone)"| F["📄 Standalone<br/>1 cmd → 1 PNG"]
        E --> G{"EOF before return<br/>to depth 0?"}
        G -->|"YES"| H["✂️ Truncate at EOF"]
        G -->|"NO"| I["✅ Full block with quit"]
    end
    class P2,D,E,F,G,H,I phase2;

    %% --------------------------------------------------------
    %% 🎨 3. RENDER
    %% --------------------------------------------------------
    subgraph P3["🎨 3. RENDER"]
        H --> J["Jinja2 autoescape<br/>template.render() → HTML string"]
        I --> J
        F --> J
        J --> K["page.set_content(html)"]
        K --> L["📸 Screenshot #capture-area"]
        L --> M["🖼️ PNG saved"]
    end
    class P3,J,K,L,M phase3;

    %% --------------------------------------------------------
    %% 📄 4. INSERT — DETAILED
    %% --------------------------------------------------------
    subgraph P4["📄 4. INSERT — DETAILED"]
        M --> N["📖 Read DOCX<br/>parse into blocks"]
        N --> O["_merge_empty_blocks()<br/>blocks without nodes<br/>→ merge into next"]
        O --> P{"Block type?"}
        
        %% แขนงขา NESTED
        P -->|"NESTED"| Q["Concatenate all commands<br/>→ find_best_match()"]
        Q --> X1{"find_best_match()"}
        X1 -->|"match"| W["✅ INSERT IMAGE<br/>at NodeName paragraph<br/>dedup per paragraph"]
        X1 -->|"no match"| Y["⛔ SKIP"]
        
        %% แขนงขา POOL
        P -->|"POOL"| R["Try each command<br/>individually"]
        R --> T{"Match found?"}
        T -->|"YES"| U{"Is [error] PNG?"}
        T -->|"NO"| V["Try next cmd in pool"]
        U -->|"YES → skip"| V
        U -->|"NO → use it"| W
        V --> T
        
        %% แขนงขา USERNAME
        P -->|"USERNAME"| S["NOISE_COMMANDS skip<br/>_extract_username()<br/>→ tag PNG filename"]
        S --> W
    end
    class P4,N,O,P,Q,R,S,T,U,V,X1 phase4;
    class W success;
    class Y danger;
