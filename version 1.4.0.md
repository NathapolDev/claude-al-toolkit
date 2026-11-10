# แผนปรับปรุง bc365-al-toolkit รุ่น 1.4.0

- **Branch:** `version-1.4.0`
- **รุ่นเดิม:** 1.3.0 → **รุ่นใหม่:** 1.4.0
- **อ้างอิง:** Business Central 2026 release wave 2 (v29, AL runtime 18), ข้อมูลจาก Microsoft Learn ณ วันที่ 2026-11-10
- **สถานะ:** แผนงาน ยังไม่ได้ลงมือแก้ skill หรือ script (มีเพียง `version` ใน `plugin.json` ที่ปรับเป็น 1.4.0 แล้ว)

## เป้าหมาย

การใช้งานปกติคือ `al-analyst` → `al-developer` → `al-reviewer` และวนกลับไป `al-developer`
เมื่อ reviewer ไม่ผ่าน รุ่น 1.4.0 มีเป้าหมายเดียว: **ลดจำนวนรอบที่วนกลับ** โดยจับปัญหาให้ได้
ตั้งแต่ขั้นที่เกิด และให้ทุกขั้นตัดสินจากหลักฐานที่เครื่องมือยืนยัน ไม่ใช่การเดา

## สิ่งที่ไม่เปลี่ยน

- ทุก path ยังอ้างผ่าน `${CLAUDE_PLUGIN_ROOT}` เท่านั้น
- ไม่ bundle AL toolchain ยังค้นหาตอน launch ผ่าน `find-al-bin.cmd` ที่เดียว
- script ยังเป็น batch (`setlocal enabledelayedexpansion`, `!VAR!` ใน `for`)
- regex ให้คะแนน build ใน `al-build.cmd` (`error [A-Z][A-Z]*[0-9][0-9]*:`) คงไว้เป็นทางสำรอง
- นโยบาย "เขียน test เมื่อผู้ใช้ขอเท่านั้น" และ "ห้าม publish ขึ้น production"
- หัวข้อ output ของแต่ละ skill เพิ่มได้แต่ไม่เปลี่ยนชื่อหัวข้อเดิม เพราะขั้นถัดไปอ่านต่อ

## ของใหม่ใน BC v29 ที่แผนนี้นำมาใช้

| ของใหม่ | ใช้ใน Phase |
|---|---|
| ตัวเลือก `launchmcpserver`: `--packagecachepath`, `--ruleset`, `--codeanalyzers`, `--logfile`, `--loglevel` | 1 |
| `al_getnextobjectid` | 2 |
| `al_symbolsearch` แบบ `filters.source = "environment"` (ต้องใช้ AL extension 18+) | 2 |
| `al_addproject`, `al_getpackagedependencies`, พารามิเตอร์ `projectPath` | 2 |
| `al runtests` (ผล JSON, exit code 0/1, `--testgroups`) | 3 |
| `al workspace compile --errorlogdirectory` (error log JSON ต่อโปรเจกต์) | 3 |
| AL LSP server (`altool launchlspserver`) | 4 |
| `al graph` (call graph: extract → stitch → query) | 4 |
| Snapshot debugging / Profiling MCP proxy | 4 |
| ภาษา AL runtime 18: default interface method, `[RequiredPending]` (AL0924, AS0148, AS0149) | 4 |

---

## Phase 1 — แก้ของที่ผิดหรือค้างอยู่

ความเสี่ยงต่ำ แก้ Markdown และ launcher เล็กน้อย

| # | งาน | ไฟล์ | เหตุผล |
|---|---|---|---|
| 1.1 | ยืนยันรายชื่อเครื่องมือจาก `tools/list` ของ MCP server จริง แล้วแก้ข้อความที่อ้าง `al_run_tests` | `plugins/al-toolkit/README.md` | เอกสาร Microsoft ไม่มีเครื่องมือชื่อนี้ใน AL MCP server |
| 1.2 | จัดการการอ้างถึง skill `bc365-permissionset` และ `al-compiler` ที่ไม่ได้อยู่ใน plugin | `skills/*/SKILL.md` | ผู้ติดตั้งเครื่องอื่นไม่มี skill สองตัวนี้ (ดู "สิ่งที่ต้องตัดสินใจ" ข้อ 1) |
| 1.3 | แก้กฎเรื่อง event ให้ตรงกัน: เลือกจุดยืนเดียวระหว่าง "ใช้ `IsHandled`" กับ "เลี่ยง handled event" | `references/al-rules.md`, `al-analyst`, `al-developer`, `al-reviewer` | ตอนนี้ developer ที่ทำตาม `al-rules.md` จะโดน reviewer ตีกลับระดับ Major |
| 1.4 | รวมหมวด "Vibe Coding Rules" เข้ากับครึ่งบนของไฟล์ ตัดข้อที่ซ้ำ คงตัวอย่างโค้ดไว้ | `references/al-rules.md` | กฎซ้ำสองที่ทำให้แก้แล้วไม่ตรงกัน |
| 1.5 | ให้ MCP launcher ส่ง `--packagecachepath` จาก `AL_PACKAGECACHE` | `scripts/al-mcp.cmd` | ตอนนี้ตัวแปรนี้มีผลกับ `al-build.cmd` เท่านั้น |
| 1.6 | เพิ่มตัวแปร `AL_RULESET` ส่งเป็น `--ruleset` (MCP) และ `/ruleset:` (alc) | `scripts/al-mcp.cmd`, `scripts/al-build.cmd` | build ของ Claude ควรใช้ ruleset เดียวกับ VS Code ของทีม |
| 1.7 | เพิ่มตัวแปร `AL_MCP_LOGLEVEL` ส่งเป็น `--loglevel` และเขียนวิธีดู log ที่ `~/.al-mcp/almcp.log` | `scripts/al-mcp.cmd`, `plugins/al-toolkit/README.md` | ช่วยวินิจฉัยเมื่อ `al_*` ไม่ทำงาน |
| 1.8 | ลบข้อความ "not a git repository" และเพิ่มตัวแปรใหม่ในหมวด Environment overrides | `CLAUDE.md`, `README.md` | ข้อมูลเก่า |

**เกณฑ์ผ่าน:** `al-mcp.cmd` เริ่มได้และพิมพ์ "AL MCP Server starting in STDIO mode..." ทั้งกรณี
ตั้งและไม่ตั้งตัวแปรใหม่; path ที่มีช่องว่างทำงานได้; ไม่มีกฎข้อใดใน `al-rules.md` ขัดกับ checklist
ของ reviewer

---

## Phase 2 — ใช้เครื่องมือ AL MCP ที่มีอยู่แล้วให้ครบ

แก้เฉพาะ `SKILL.md` ไม่แตะ script

### al-analyst
- 2.1 ขั้น "Explore the codebase": เรียก `al_getpackagedependencies` เพื่อดู dependency จริง
- 2.2 ขั้น "Find extension points": เมื่อ `al_symbolsearch` ใน workspace ไม่เจอ ให้ค้นซ้ำด้วย
  `filters.source = "environment"` แล้วบันทึก `appId` / `appName` / `appVersion` ของ app
  เจ้าของ เพื่อเสนอ dependency ที่ต้องเพิ่มใน `app.json` ถ้าไม่มีการเชื่อมต่อ environment
  ให้ระบุ "needs confirmation" เหมือนเดิม
- 2.3 ขั้น "Recommended Approach": จอง ID ด้วย `al_getnextobjectid` (ใช้ `count` เมื่อสร้าง
  หลาย object ชนิดเดียวกัน) และเขียนคำเตือนของเครื่องมือลงในแผน: มันไม่เห็น ID ของ
  extension อื่นบน sandbox เดียวกัน
- 2.4 เพิ่มในหัวข้อ output เดิม: dependency ที่ต้องเพิ่ม, runtime ของโปรเจกต์, ID ที่จองแล้ว

### al-developer
- 2.5 ถ้าแผนไม่มี ID ที่จองไว้ ให้เรียก `al_getnextobjectid` ก่อนสร้าง object
- 2.6 workspace แบบ App + Test: เรียก `al_addproject` สำหรับโปรเจกต์ที่ยังไม่ถูกโหลด และ
  ส่ง `projectPath` ทุกครั้งที่มีมากกว่าหนึ่งโปรเจกต์
- 2.7 ปรับรายการ ToolSearch เป็น
  `select:al_compile,al_getdiagnostics,al_downloadsymbols,al_symbolsearch,al_getnextobjectid,al_addproject,al_getpackagedependencies`
- 2.8 เมื่อ compile แจ้งว่าไม่พบ symbol ให้เรียก `al_downloadsymbols` ก่อนแก้โค้ด

### al-reviewer
- 2.9 ใช้ `projectPath` และ `al_addproject` แบบเดียวกับ developer (สองขั้นต้องตรงกัน)
- 2.10 checklist ข้อ B: ยืนยัน ID อยู่ใน `idRanges` ด้วยผล compile ไม่ใช่การอ่านด้วยตา
- 2.11 เรียก `al_getdiagnostics` พร้อม `areas` ของ cop ที่ตรงกับ `target` ใน `app.json`

**เกณฑ์ผ่าน:** ทดลองกับโปรเจกต์ AL จริงหนึ่งงาน ตั้งแต่ analyst ถึง reviewer โดย ID มาจาก
เครื่องมือ และ build strategy สองชั้นใน developer กับ reviewer ยังเขียนตรงกัน

---

## Phase 3 — ปิดช่องว่างเรื่อง test และ build

### 3.1 เพิ่ม `scripts/al-test.cmd`
- หา `altool.exe` ผ่าน `find-al-bin.cmd` (ไม่เพิ่ม logic ค้นหาใน script ใหม่)
- รูปแบบ: `al-test.cmd <projectDir> <codeunitId> [testMethods]` และ
  `al-test.cmd <projectDir> --testgroups <file.json>`
- เรียก `altool.exe runtests ... --project <projectDir>` ส่ง JSON ออก stdout ตามเดิม
- exit code ตาม `runtests`: 0 = ผ่านทั้งหมด, 1 = มี test ไม่ผ่านหรือเชื่อมต่อไม่ได้
- การเชื่อมต่อ: ใช้ `launch.json` ของโปรเจกต์ หรือ `BC_SERVER_URL` / `BC_SERVER_INSTANCE` /
  `BC_SERVER_PORT` / `BC_SERVER_USERNAME` / `BC_SERVER_PASSWORD` สำหรับ on-prem และ container
- ถ้า toolchain เก่ากว่า v29 (ไม่มีคำสั่ง `runtests`) ให้แจ้งชัดเจนและ exit 1
- script ไม่เก็บรหัสผ่านและไม่พิมพ์ค่าตัวแปรที่เป็นความลับ

### 3.2 ปรับ skill ให้ใช้ `al-test.cmd`
- `al-developer` ขั้น 6: เมื่อผู้ใช้ขอ test ให้เขียนแล้วรันจริง รายงานจำนวน passed / failed /
  skipped ถ้ารันไม่ได้ให้รายงาน "TESTS NOT RUN" พร้อมเหตุผล
- `al-reviewer` ขั้น 5: เมื่อมี test ให้รันซ้ำเอง ไม่เชื่อรายงานของ developer
- test ต้องรันบน sandbox หรือ container เท่านั้น ห้ามชี้ไป production

### 3.3 ปรับ `scripts/al-build.cmd`
- เมื่อ toolchain มี `altool.exe` ที่รองรับ `workspace compile` และโฟลเดอร์มีไฟล์
  `.code-workspace` ให้ใช้ `altool workspace compile --errorlogdirectory <temp>` แล้วให้คะแนน
  จาก error log JSON
- กรณีอื่นใช้ `alc.exe` กับ regex เดิมทุกประการ
- ข้อความสรุป `BUILD OK` / `BUILD FAILED` และ exit code คงเดิม เพื่อไม่ให้ skill ต้องแก้ตาม
- map ชื่อ cop: `PerTenantExtensionCop` ของ `AL_ANALYZERS` → `PTECop` ของ `--analyzers`

**เกณฑ์ผ่าน:** `al-test.cmd` คืน 0 เมื่อ test ผ่าน และ 1 เมื่อจงใจทำให้ test ล้ม;
`al-build.cmd` ให้ผลเดียวกันทั้งสองเส้นทางกับโปรเจกต์ที่มี error จริง; toolchain รุ่น v28
ยัง build ได้ผ่านทาง `alc.exe`

---

## Phase 4 — ความสามารถใหม่

ทุกข้อใน Phase นี้ต้องทดสอบบน Windows จริงก่อนรวมเข้า 1.4.0 ข้อใดทดสอบไม่ผ่านให้เลื่อนไป
รุ่นถัดไปโดยไม่กระทบ Phase 1–3

### 4.1 AL LSP server
- ยืนยันรูปแบบ LSP config ของ Claude Code plugin จากเอกสารปัจจุบันก่อนเขียนไฟล์
- เพิ่ม `scripts/al-lsp.cmd`: หา `altool.exe` ผ่าน `find-al-bin.cmd` แล้วรัน
  `altool.exe launchlspserver "<project>" --packagecachepath "<cache>"`
- ลงทะเบียน LSP สำหรับไฟล์ `.al` โดยอ้าง `${CLAUDE_PLUGIN_ROOT}/scripts/al-lsp.cmd`
- `al-reviewer` checklist ข้อ I (TransferFields) และ `al-developer` ขั้น feasibility ใช้
  find-references จาก LSP ก่อน และใช้ grep เมื่อ LSP ไม่พร้อม

### 4.2 `al graph` สำหรับวิเคราะห์ผลกระทบ
- เพิ่ม `scripts/al-graph.cmd` ครอบ `graph extract` → `graph stitch` → `graph query`
  เก็บ graph ไว้ในโฟลเดอร์ชั่วคราวนอกโปรเจกต์
- `al-analyst`: ดู caller ของ procedure ที่จะแก้ (`--to "obj:..." --direction callers`)
- `al-reviewer`: ตรวจ caller ของ procedure ที่ signature เปลี่ยน และรายงานเป็น Major เมื่อมี
  caller ที่ไม่ได้แก้ตาม
- ระบุข้อจำกัดใน skill: `--paths` เป็นตัวอย่างที่มีเพดาน ไม่ใช่ข้อพิสูจน์ว่าเข้าไม่ถึง

### 4.3 skill ใหม่ `al-debugger` และ `al-profiler` (opt-in)
- ไม่ลงทะเบียนใน `.mcp.json` หลัก เพื่อไม่ให้ทุกเครื่องเปิดการเชื่อมต่อออกไปยัง environment
- เพิ่ม launcher `scripts/al-snapshot-mcp.cmd` และ `scripts/al-profiling-mcp.cmd` อ่านเป้าหมาย
  จากตัวแปร `AL_ENV_TYPE`, `AL_ENV_NAME`, `AL_TENANT`
- README อธิบายวิธีเปิดใช้เอง: `altool auth login` หนึ่งครั้ง แล้วเพิ่ม MCP server
- skill ระบุข้อควรระวัง: snapshot และ profile อาจมีข้อมูลธุรกิจ, snapshot แบบ `Full` เพิ่ม
  ภาระ server, ต้องเรียก stop ทุกครั้งแม้ test ล้ม
- ทั้งสอง skill อยู่นอกวงจร analyst → developer → reviewer และไม่ถูกเรียกอัตโนมัติจากสามขั้นนั้น

### 4.4 กฎแยกตาม runtime ใน `references/al-rules.md`
- เพิ่มหมวด "Runtime-gated features": อ่าน `runtime` จาก `app.json` ก่อนแนะนำฟีเจอร์
- ตาราง runtime: 16.0 = BC 27, 17.0 = BC 28, 18.0 = BC 29
- runtime 18: default interface method; ใช้ `[RequiredPending]` เมื่อ method จะกลายเป็น
  required (AL0924); ห้ามลบ body ตรง ๆ (AS0148); เรียก default method ผ่านตัวแปร Interface
- ฟีเจอร์ v29 อื่น (index ข้าม table extension, เปิด/ปิด index ในโค้ด, action สืบทอด tooltip,
  ตรวจ uncommitted changes) ให้ยืนยันรายละเอียดจาก Microsoft Learn ก่อนเขียนเป็นกฎ
- `al-reviewer` เพิ่มข้อตรวจ: ฟีเจอร์ที่ใช้ต้องไม่ใหม่กว่า `runtime` ของโปรเจกต์

**เกณฑ์ผ่าน:** LSP ตอบ find-references ข้ามโปรเจกต์ App + Test ได้; `al-graph.cmd` คืน caller
ของ procedure ทดสอบได้ถูกต้อง; MCP proxy ทั้งสองเริ่มได้เมื่อเปิดใช้ และ plugin ทำงานปกติ
เมื่อไม่เปิดใช้

---

## ลำดับการทำงานและการส่งมอบ

1. Phase 1 → commit แยกตามหัวข้อ (กฎ, launcher, เอกสาร)
2. Phase 2 → commit เดียวต่อ skill
3. Phase 3 → `al-test.cmd` ก่อน แล้ว `al-build.cmd`
4. Phase 4 → ทีละข้อ ข้อใดไม่ผ่านการทดสอบให้เลื่อนออก
5. อัปเดต `CLAUDE.md` (layout, ตัวแปร, วิธีทดสอบ script ใหม่) และ `README.md` ทั้งสองไฟล์
6. ทดสอบติดตั้งเต็มรูปแบบตามหมวด "Full install check" ใน `CLAUDE.md`

## การทดสอบ

repo นี้ไม่มี test runner และ script เป็น Windows batch จึงต้องทดสอบบนเครื่อง Windows
ที่มี AL toolchain v29:

- resolver: happy path, ไม่มี `dotnet` บน PATH, exe ที่ไม่มีจริง, `AL_BIN` ผิด
- `al-mcp.cmd`: เริ่มได้ ทั้งกรณีตั้งและไม่ตั้ง `AL_PACKAGECACHE` / `AL_RULESET`
- `al-build.cmd`: โปรเจกต์ที่ผ่าน, โปรเจกต์ที่มี error, ทั้งเส้นทาง workspace และ `alc.exe`
- `al-test.cmd`: test ผ่าน, test ล้ม, เชื่อมต่อไม่ได้
- toolchain รุ่นเก่า (v28): ทุก script ต้องถอยไปใช้เส้นทางเดิมหรือแจ้งชัดเจน
- วงจรเต็ม: หนึ่ง requirement จริงผ่าน analyst → developer → reviewer

## สิ่งที่ต้องตัดสินใจ

1. **`bc365-permissionset` และ `al-compiler`:** รวมเข้ามาใน plugin หรือตัดการอ้างอิงออก
   (แนะนำ: ตัด `al-compiler` เพราะ `al-build.cmd` ทำหน้าที่แทนแล้ว และรวม
   `bc365-permissionset` ถ้าเป็น skill ของทีมเอง)
2. **จุดยืนเรื่อง handled event (ข้อ 1.3):** แนะนำ "เลี่ยงเป็นค่าเริ่มต้น ใช้ `IsHandled`
   เฉพาะเมื่อ requirement ต้องการให้ subscriber แทนที่ logic เดิม"
3. **เวอร์ชัน toolchain ขั้นต่ำ:** แนะนำให้รองรับ v28 ต่อไปโดยฟีเจอร์ v29 เป็นส่วนเสริม
4. **Windows-only:** `altool` แบบ .NET tool รันข้ามแพลตฟอร์มได้ จะเพิ่ม launcher สำหรับ
   macOS/Linux หรือไม่ (แนะนำ: ไม่ทำในรุ่นนี้)

## ความเสี่ยง

| ความเสี่ยง | การรับมือ |
|---|---|
| ชื่อเครื่องมือหรือตัวเลือกของ `altool` ต่างจากเอกสาร | ยืนยันจาก `tools/list` และ `altool help` บนเครื่องจริงก่อนเขียนลง skill |
| รูปแบบ LSP config ของ Claude Code plugin ไม่ตรงที่คาด | ข้อ 4.1 แยกเป็นอิสระ เลื่อนได้โดยไม่กระทบส่วนอื่น |
| `SKILL.md` ยาวขึ้นจน Claude ทำตามไม่ครบ | ย้ายรายละเอียดไป `references/` และให้ skill อ้างถึง |
| test หรือ debugger ถูกชี้ไป production | skill ระบุให้ใช้ sandbox เท่านั้น และ MCP proxy เป็น opt-in |
| ผู้ใช้ toolchain รุ่นเก่าใช้งานไม่ได้ | ทุก script มีทางสำรองและทดสอบกับ v28 |

## แหล่งอ้างอิง

- [Develop AL extensions with ALTool](https://learn.microsoft.com/dynamics365/business-central/dev-itpro/developer/devenv-al-tool)
- [AL MCP server](https://learn.microsoft.com/dynamics365/business-central/dev-itpro/developer/al-agent-tools/al-mcp-server)
- [AI agent tools for AL development](https://learn.microsoft.com/dynamics365/business-central/dev-itpro/developer/al-agent-tools/al-agent-tools-overview)
- [al_getnextobjectid](https://learn.microsoft.com/dynamics365/business-central/dev-itpro/developer/al-agent-tools/al-tool-get-next-object-id)
- [al_symbolsearch](https://learn.microsoft.com/dynamics365/business-central/dev-itpro/developer/al-agent-tools/al-tool-symbol-search)
- [al_compile](https://learn.microsoft.com/dynamics365/business-central/dev-itpro/developer/al-agent-tools/al-tool-compile)
- [Snapshot debugging](https://learn.microsoft.com/dynamics365/business-central/dev-itpro/developer/devenv-snapshot-debugging)
- [Interfaces in AL](https://learn.microsoft.com/dynamics365/business-central/dev-itpro/developer/devenv-interfaces-in-al)
- [Choose runtime version in AL](https://learn.microsoft.com/dynamics365/business-central/dev-itpro/developer/devenv-choosing-runtime)
- [Update 29.0 for Business Central 2026 release wave 2](https://learn.microsoft.com/dynamics365/business-central/dev-itpro/whatsnew/whatsnew-update-29-0)
