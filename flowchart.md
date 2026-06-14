# Huawei VRP Log Processing Pipeline

``mermaid
flowchart LR
    subgraph P1["🔍 1. PARSE"]
        direction TB
        A["📁 logs/*.txt"] --> B{"Has Router prompt?"}
        B -->|"NO"| X["⛔ Skip file"]
        B -->|"YES"| C["Split into<br/>{prompt, command, output}"]
    end

    subgraph P2["📦 2. GROUP — EDGE CASES"]
        direction TB
        C --> D{"Command goes deeper?"}
        D -->|"YES (system-view)"| E["📎 Nested Block<br/>all cmds → 1 PNG"]
        D -->|"NO (standalone)"| F["📄 Standalone<br/>1 cmd → 1 PNG"]
        E --> G{"EOF before<br/>return to depth 0?"}
        G -->|"YES"| H["✂️ Truncate at EOF<br/>keep what was captured"]
        G -->|"NO"| I["✅ Full block<br/>ends with quit → &lt;Router&gt;"]
        C --> Z2a["⚠️ EDGE CASES"]
        Z2a --> E1["SSH/stelnet/telnet as<br/>first cmd → merge with<br/>next group (cross-device)"]
        Z2a --> E2["Log must start with<br/>&lt;Router&gt; (depth 0).<br/>[Router] at depth 1<br/>not supported"]
        Z2a --> E3["~ prefix = unsaved config<br/>* prefix = alarm/fault<br/>both stripped"]
        Z2a --> E4["Depth-0 segments after<br/>nested blocks fall through<br/>as standalone (never appended)"]
        Z2a --> E5["Nested filename = ALL cmds<br/>concatenated incl. quit<br/>max ~300 char (Windows limit)"]
        Z2a --> E6["display device: 1st occurrence<br/>= baseline. Subsequent =<br/>compare → [Card removed]"]
        Z2a --> E7["display alarm active: same<br/>baseline → compare →<br/>[alarm_id card_name removed]"]
    end

    subgraph P3["🎨 3. RENDER"]
        direction TB
        H --> J["Jinja2 → HTML string"]
        I --> J
        F --> J
        J --> K["page.set_content(html)"]
        K --> L["📸 Screenshot"]
        L --> M["🖼️ PNG saved"]
    end

    subgraph P4["📄 4. INSERT — EDGE CASES"]
        direction TB
        M --> N["📖 Read DOCX<br/>parse_paragraphs_detailed()"]
        N --> O["_merge_empty_blocks()<br/>blocks without nodes<br/>→ merge into next"]
        O --> P{"Block type?"}
        P -->|"NESTED"| Q["Concatenate all cmds<br/>→ contiguous subsequence"]
        Q --> QQ{"match?"}
        QQ -->|"found"| W["✅ Insert"]
        QQ -->|"not found"| Y["⛔ Skip"]
        P -->|"POOL"| R["Try each command"]
        R --> T{"Found match?"}
        T -->|"YES"| U{"Is [error] PNG?"}
        U -->|"YES"| V["🔄 Try next cmd (skip error)"]
        V --> T
        U -->|"NO"| W
        T -->|"NO cmds left"| Y
        P -->|"USERNAME"| S["NOISE_COMMANDS skip<br/>_extract_username()<br/>→ tag PNG filename"]
        S --> W
        M --> Z["⚠️ EDGE CASES"]
        Z --> Z1["[error] PNG skipped<br/>unless prefer_error=True"]
        Z1 --> Z1a["prefer_error=True +<br/>no [error] found<br/>→ return None ❌"]
        Z --> Z3["Long output truncated<br/>→ .txt file<br/>→ Word COM OLE embed"]
        Z --> Z4["xxx.* wildcard matches<br/>any extension.<br/>xxx.zip matches .zip only"]
        Z --> Z5["Same NodeName after<br/>different blocks →<br/>multiple images (Option B)"]
        Z --> Z6["Dedup per paragraph<br/>not per cell"]
        Z --> Z7["username <> → []<br/>.cfg/.zip aligned"]
    end

    style P1 fill:#1a1a2e,stroke:#e94560,color:#eee
    style P2 fill:#16213e,stroke:#0f3460,color:#eee
    style P3 fill:#0f3460,stroke:#533483,color:#eee
    style P4 fill:#533483,stroke:#e94560,color:#eee
    style W fill:#22c55e,color:#000
    style Y fill:#ef4444,color:#fff
    style X fill:#ef4444,color:#fff
    style Z2a fill:#1a1a2e,stroke:#f59e0b,color:#f59e0b
    style E1 fill:#2d2d44,stroke:#f59e0b,color:#eee
    style E2 fill:#2d2d44,stroke:#f59e0b,color:#eee
    style E3 fill:#2d2d44,stroke:#f59e0b,color:#eee
    style E4 fill:#2d2d44,stroke:#f59e0b,color:#eee
    style E5 fill:#2d2d44,stroke:#f59e0b,color:#eee
    style E6 fill:#2d2d44,stroke:#f59e0b,color:#eee
    style E7 fill:#2d2d44,stroke:#f59e0b,color:#eee
    style Z fill:#1a1a2e,stroke:#f59e0b,color:#f59e0b
    style Z1 fill:#2d2d44,stroke:#f59e0b,color:#eee
    style Z1a fill:#2d2d44,stroke:#f59e0b,color:#eee
    style Z3 fill:#2d2d44,stroke:#f59e0b,color:#eee
    style Z4 fill:#2d2d44,stroke:#f59e0b,color:#eee
    style Z5 fill:#2d2d44,stroke:#f59e0b,color:#eee
    style Z6 fill:#2d2d44,stroke:#f59e0b,color:#eee
    style Z7 fill:#2d2d44,stroke:#f59e0b,color:#eee
``
