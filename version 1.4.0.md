# แผนปรับปรุง bc365-al-toolkit รุ่น 1.4.0

- **Branch:** `version-1.4.0`
- **รุ่นเดิม:** 1.3.0 → **รุ่นใหม่:** 1.4.0
- **อ้างอิง:** Business Central 2026 release wave 2 (v29, AL runtime 18) จาก Microsoft Learn ณ 2026-11-10
  และตรวจซ้ำบนเครื่องจริง (Windows 11) ณ 2026-11-11 กับ toolchain สองชุด:
  - .NET global tool `Microsoft.Dynamics.BusinessCentral.Development.Tools` **30.0.43-beta** (net10.0) ← resolver เลือกตัวนี้
  - VS Code extension `ms-dynamics-smb.al-18.1.2842859` (เมื่อไม่มี `dotnet` บน PATH)
- **สถานะ:** Phase 1–4 เสร็จและทดสอบแล้ว (2026-11-12); plugin 1.4.0 ติดตั้งในเครื่องนี้
  จาก local marketplace (`D:\claude-al-toolkit`) — เมื่อ merge เข้า `main` แล้วให้สลับ marketplace กลับเป็น GitHub
- **โปรเจกต์ทดสอบหลัก:** PTE ของลูกค้าบนเครื่องนักพัฒนา (ไม่ระบุชื่อใน repo; runtime 17, BC 28, 62 ไฟล์ `.al`,
  `launch.json` → cloud Sandbox) — publish ไป Sandbox ได้ **แต่ห้ามแก้ source ของโปรเจกต์นี้แล้ว publish**;
  การทดสอบที่ต้องแก้โค้ด (เช่น จงใจทำให้ build ล้ม) ทำบนสำเนาใน temp และ compile ในเครื่องเท่านั้น

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

## ข้อเท็จจริงที่ยืนยันบนเครื่องจริง (2026-11-11)

| เรื่อง | ผลที่พบ | กระทบข้อ |
|---|---|---|
| `tools/list` ของ MCP server (ทั้ง 30.0 และ 18.1) | 16 เครื่องมือ: `al_addproject`, `al_auth_login`, `al_auth_logout`, `al_build`, `al_compile`, `al_downloadsymbols`, `al_getdiagnostics`, `al_getnextobjectid`, `al_getpackagedependencies`, `al_inspectpage`, `al_publish`, `al_run_tests`, `al_searchtranslations`, `al_symbolrelations`, `al_symbolsearch`, `al_writetranslation` | 1.1, 2.x, 3.x |
| ลำดับ argument ของ `launchmcpserver` | `--packagecachepath` รับหลายค่า ถ้าวาง project ไว้หลังมัน project จะถูกกลืนเป็น cache path แล้ว server ตอบ "No projects are loaded" ตลอด **ต้องวาง project ก่อน option** | 1.5 |
| `<projects>` ของ `launchmcpserver` / `launchlspserver` | เป็น optional ตั้งแต่ 18.1 เพิ่มทีหลังได้ด้วย `al_addproject` | 1.9 |
| `--codeanalyzers` | ต้องใช้รูปแบบ `${CodeCop}` เพราะ `CodeCop` เฉย ๆ **ไม่ error แต่ไม่รัน analyzer** | 1.6 |
| `--ruleset` โดยไม่มี `--codeanalyzers` | server เตือนว่า "Ruleset severity overrides will not apply" | 1.6 |
| ตำแหน่ง log ของ MCP server | `%LOCALAPPDATA%\Microsoft\ALLanguageServer\almcp.log` (เครื่องนี้ ~12 MB) ส่วน `~/.al-mcp/almcp.log` เป็น default ของ `launchlspserver` เท่านั้น | 1.7, 4.1 |
| `al_getnextobjectid` | คืน ID พร้อม warning "IDs ... other extensions published to the same dev sandbox are not detected" ตรงกับข้อ 2.3 | 2.3 |
| `alc.exe` 30.0 | รองรับ `/ruleset:`, `/errorlog:<file>` (SARIF-like JSON) และยัง exit 0 แม้มี error | 1.6, 3.3 |
| `altool runtests` | มีทั้ง 30.0 และ 18.1, รองรับ `--testgroups`, ใช้ `BC_SERVER_*` และ `launch.json` (`--project`) | 3.1 |
| `altool workspace compile` | มีทั้ง 30.0 และ 18.1, `--errorlogdirectory` ใช้ได้, ค่า `--analyzers` คือ `AppSourceCop\|CodeCop\|None\|PTECop\|UICop` | 3.3 |
| คำสั่งที่มีเฉพาะ 30.0 | `downloadsymbols` (มี `--globalsourcesonly`), `listtests`, `doc` ไม่มีใน 18.1 | 3.x, การทดสอบ |
| `GetLatestSupportedRuntimeVersion` | 27.0→16.1, 28.0→17.1, 29.0→18.0, **30.0→30.0** (เลข runtime กระโดดจาก 18 เป็น 30) | 4.4 |
| `altool graph` | `extract` → `stitch` ใช้ ~1 วินาทีกับโปรเจกต์เล็ก, selector `obj:<ObjectName>` ใช้ได้ แต่ `obj:<ID>` ได้ 0 node และ `id:` ต้องเป็น symbol moniker เต็ม | 4.2 |
| `launchlspserver` | ตอบ `initialize` ได้ ประกาศ `referencesProvider`, `definitionProvider`, `workspaceSymbolProvider`, `renameProvider` แต่ยังไม่ได้ทดสอบ find-references จริง | 4.1 |
| snapshot / profiling MCP proxy | `--environmenttype` มี **default = Production** | 4.3 |
| plugin ที่ Claude Code โหลดอยู่ | 1.3.0 จาก plugin cache (commit `9d65cc8`) ไม่ใช่ working tree | การทดสอบ |

## ของใหม่ใน BC v29+ ที่แผนนี้นำมาใช้

| ของใหม่ | ใช้ใน Phase |
|---|---|
| ตัวเลือก `launchmcpserver`: `--packagecachepath`, `--ruleset`, `--codeanalyzers`, `--logfile`, `--loglevel`, project แบบ optional | 1 |
| `al_getnextobjectid`, `al_symbolrelations` | 2 |
| `al_symbolsearch` แบบ `filters.source = "environment"` (ต้องใช้ AL extension 18+) | 2 |
| `al_addproject`, `al_getpackagedependencies`, พารามิเตอร์ `projectPath` | 2 |
| `al_run_tests` (MCP) และ `altool runtests` (CLI, ผล JSON, exit code 0/1, `--testgroups`) | 3 |
| `altool workspace compile --errorlogdirectory` และ `alc.exe /errorlog:` | 3 |
| AL LSP server (`altool launchlspserver`) | 4 |
| `altool graph` (call graph: extract → stitch → query) | 4 |
| Snapshot debugging / Profiling MCP proxy | 4 |
| ภาษา AL runtime 18: default interface method, `[RequiredPending]` (AL0924, AS0148, AS0149) | 4 |

---

## Phase 1 — แก้ของที่ผิดหรือค้างอยู่

ความเสี่ยงต่ำ แก้ Markdown และ launcher เล็กน้อย

| # | งาน | ไฟล์ | เหตุผล |
|---|---|---|---|
| 1.1 | ปรับรายชื่อเครื่องมือใน README ให้ตรง `tools/list` จริง 16 ตัว (ดูตารางข้อเท็จจริง) **คง** `al_run_tests` ไว้ และเพิ่ม `al_symbolrelations`, `al_inspectpage`, `al_getnextobjectid`, `al_addproject`, `al_getpackagedependencies`, `al_searchtranslations`, `al_writetranslation`, `al_auth_login`/`al_auth_logout` | `README.md`, `plugins/al-toolkit/README.md` | README ปัจจุบันระบุไว้เพียง 7 ตัว (`al_run_tests` มีอยู่จริง) |
| 1.2 | จัดการการอ้างถึง skill `bc365-permissionset` และ `al-compiler` ที่ไม่ได้อยู่ใน plugin | `skills/*/SKILL.md` | ผู้ติดตั้งเครื่องอื่นไม่มี skill สองตัวนี้ (ดู "สิ่งที่ต้องตัดสินใจ" ข้อ 1) |
| 1.3 | แก้กฎเรื่อง event ให้ตรงกัน: เลือกจุดยืนเดียวระหว่าง "ใช้ `IsHandled`" (`al-rules.md` บรรทัด 53, 203) กับ "เลี่ยง handled event" (analyst, developer, reviewer ข้อ E) | `references/al-rules.md`, `al-analyst`, `al-developer`, `al-reviewer` | ตอนนี้ developer ที่ทำตาม `al-rules.md` จะโดน reviewer ตีกลับระดับ Major |
| 1.4 | รวมหมวด "Vibe Coding Rules" เข้ากับครึ่งบนของไฟล์ ตัดข้อที่ซ้ำ คงตัวอย่างโค้ดไว้ | `references/al-rules.md` | กฎซ้ำสองที่ทำให้แก้แล้วไม่ตรงกัน |
| 1.5 | ให้ MCP launcher ส่ง `--packagecachepath` จาก `AL_PACKAGECACHE` **และวาง project path ไว้ก่อน option ทั้งหมด** (`launchmcpserver "<project>" --transport stdio --packagecachepath "<cache>" ...`) | `scripts/al-mcp.cmd` | ตอนนี้ตัวแปรนี้มีผลกับ `al-build.cmd` เท่านั้น และถ้าวาง project ไว้ท้าย server จะไม่โหลดโปรเจกต์ (ยืนยันแล้ว) |
| 1.6 | เพิ่มตัวแปร `AL_RULESET` ส่งเป็น `--ruleset` (MCP) และ `/ruleset:` (alc) และให้ `AL_ANALYZERS` ส่งเป็น `--codeanalyzers` ของ MCP ด้วย โดยแปลงชื่อเป็นรูปแบบ `${CodeCop}` (`PerTenantExtensionCop` → `${PerTenantExtensionCop}`) | `scripts/al-mcp.cmd`, `scripts/al-build.cmd` | build ของ Claude ควรใช้ ruleset เดียวกับ VS Code ของทีม และ ruleset ไม่มีผลถ้าไม่เปิด analyzer; ชื่อที่ไม่มี `${}` ถูกเพิกเฉยเงียบ ๆ |
| 1.7 | เพิ่มตัวแปร `AL_MCP_LOGLEVEL` ส่งเป็น `--loglevel` และเขียนวิธีดู log ที่ `%LOCALAPPDATA%\Microsoft\ALLanguageServer\almcp.log` (ตั้ง `AL_MCP_LOGFILE` → `--logfile` เมื่อต้องการแยกไฟล์) | `scripts/al-mcp.cmd`, `plugins/al-toolkit/README.md` | ช่วยวินิจฉัยเมื่อ `al_*` ไม่ทำงาน; log default โตไม่จำกัด (เครื่องนี้ 12 MB) |
| 1.8 | ลบข้อความ "not a git repository" และเพิ่มตัวแปรใหม่ (`AL_RULESET`, `AL_MCP_LOGLEVEL`, `AL_MCP_LOGFILE`) ในหมวด Environment overrides | `CLAUDE.md`, `README.md` | ข้อมูลเก่า |
| 1.9 | ส่ง project ให้ `launchmcpserver` เฉพาะเมื่อ `<project>\app.json` มีอยู่ ถ้าไม่มีให้เริ่ม server โดยไม่มี project และให้ skill เรียก `al_addproject` เอง | `scripts/al-mcp.cmd`, `al-developer`, `al-reviewer` | ตอนนี้ส่ง `%CD%` เสมอ เปิด Claude Code นอกโปรเจกต์ AL (เช่น repo นี้) server จะโหลดโฟลเดอร์ที่ไม่ใช่ AL |

**เกณฑ์ผ่าน (ผลจริง 2026-11-11 บน โปรเจกต์ทดสอบหลัก):**
- ✅ A1 ไม่ตั้งตัวแปร: `al_compile` `succeeded:true` ครั้งแรก, 0 error
- ✅ A2 `AL_ANALYZERS=CodeCop;PerTenantExtensionCop`: ได้ทั้ง `AA*` และ `PTE*` (ใส่ `--codeanalyzers` ซ้ำได้)
- ✅ A3 ตั้งครบ `AL_PACKAGECACHE` + `AL_RULESET` + `AL_ANALYZERS` + `AL_MCP_LOGLEVEL=Debug` + `AL_MCP_LOGFILE`
  (path มีช่องว่าง): compile สำเร็จ และสร้างไฟล์ log
- ✅ A4 เริ่มจาก `D:\claude-al-toolkit` (ไม่มี `app.json`): stderr แสดง "No projects specified at startup"
- ✅ A5 `AL_BIN` = extension 18.1: compile สำเร็จพร้อม CodeCop
- ✅ A6 `al-build.cmd` + `AL_RULESET` → `BUILD OK`; ruleset ไม่มีจริง → เตือนแล้วข้าม;
  สำเนาโปรเจกต์ที่ใส่ error → `BUILD FAILED` exit 1
- ✅ กฎ event ตรงกันทุกไฟล์ (`al-rules.md`, analyst, developer, reviewer ข้อ E, checklist #16)
- ✅ `bc365-permissionset` อยู่ใน plugin, script รันได้ด้วย `python` (stdlib); ไม่เหลือ path เฉพาะเครื่อง
- ✅ ไม่เหลือการอ้าง `al-compiler` ใน skill (หน้าที่ถูกแทนด้วย `al-build.cmd`; ไม่ได้นำ `compile.ps1` เข้ามา
  เพราะเชื่อ exit code ของ `alc.exe` และหาเฉพาะ VS Code)

---

## Phase 2 — ใช้เครื่องมือ AL MCP ที่มีอยู่แล้วให้ครบ

แก้เฉพาะ `SKILL.md` ไม่แตะ script

### al-analyst
- 2.1 ขั้น "Explore the codebase": เรียก `al_getpackagedependencies` เพื่อดู dependency จริง
- 2.2 ขั้น "Find extension points": เมื่อ `al_symbolsearch` ใน workspace ไม่เจอ ให้ค้นซ้ำด้วย
  `filters.source = "environment"` แล้วบันทึก `appId` / `appName` / `appVersion` ของ app
  เจ้าของ เพื่อเสนอ dependency ที่ต้องเพิ่มใน `app.json` ถ้าไม่มีการเชื่อมต่อ environment
  ให้ระบุ "needs confirmation" เหมือนเดิม
- 2.3 ขั้น "Recommended Approach": หา ID ด้วย `al_getnextobjectid` (ใช้ `count` เมื่อสร้าง
  หลาย object ชนิดเดียวกัน) และเขียนคำเตือนของเครื่องมือลงในแผน: มัน **ไม่จอง** ID
  (เรียกซ้ำได้ค่าเดิมจนกว่าจะเขียนไฟล์) และไม่เห็น ID ของ extension อื่นบน sandbox เดียวกัน
- 2.4 เพิ่มในหัวข้อ output เดิม: dependency ที่ต้องเพิ่ม, runtime ของโปรเจกต์, ID ที่เสนอ
- 2.5 ขั้นวิเคราะห์ผลกระทบ: ใช้ `al_symbolrelations` (`ExtendedBy`, `UsedAsSourceTable`,
  `ImplementedBy`) ดู object ที่ขยายหรืออ้าง table/interface ที่จะแก้ ก่อนเสนอแนวทาง

### al-developer
- 2.6 ถ้าแผนไม่มี ID ที่เสนอไว้ ให้เรียก `al_getnextobjectid` ก่อนสร้าง object
- 2.7 workspace แบบ App + Test หรือเมื่อ `al_compile` ตอบ "No projects are loaded": เรียก
  `al_addproject` สำหรับโปรเจกต์ที่ยังไม่ถูกโหลด และส่ง `projectPath` ทุกครั้งที่มีมากกว่าหนึ่งโปรเจกต์
- 2.8 ปรับรายการ ToolSearch เป็น
  `select:al_compile,al_getdiagnostics,al_downloadsymbols,al_symbolsearch,al_symbolrelations,al_getnextobjectid,al_addproject,al_getpackagedependencies`
- 2.9 เมื่อ compile แจ้งว่าไม่พบ symbol ให้เรียก `al_downloadsymbols` ก่อนแก้โค้ด
- 2.10 เปิด analyzer ต่อครั้งด้วย `al_compile` `options.enableCodeAnalysis=true` +
  `codeAnalyzers=["${CodeCop}", ...]` ตาม `target` ใน `app.json` ไม่พึ่ง config ตอน launch อย่างเดียว

### al-reviewer
- 2.11 ใช้ `projectPath` และ `al_addproject` แบบเดียวกับ developer (สองขั้นต้องตรงกัน)
- 2.12 checklist ข้อ B: ยืนยัน ID อยู่ใน `idRanges` ด้วยผล compile ไม่ใช่การอ่านด้วยตา
- 2.13 compile ด้วย `codeAnalyzers` ที่ตรงกับ `target` ใน `app.json` (`${PerTenantExtensionCop}`
  สำหรับ PTE, `${AppSourceCop}` สำหรับ AppSource, `${CodeCop}` ทุกกรณี) แล้วอ่านด้วย `al_getdiagnostics`
- 2.14 checklist ข้อ I (TransferFields / ผลกระทบ): ใช้ `al_symbolrelations` ก่อน grep

### ผลการทำ Phase 2 (2026-11-11) — ต่างจากแผนเดิม

- **2.5 และ 2.14 (`al_symbolrelations`) เลื่อนออก:** ทุกการเรียกคืน "An error occurred invoking
  'al_symbolrelations'" บนทั้ง 30.0-beta และ 18.1 (ลองทั้ง `symbolName`+`symbolKind`, `symbolId`,
  `projectId`, symbol ของ base app และของโปรเจกต์เอง) และ log ระดับ Debug ไม่บันทึกสาเหตุ
  ตรวจซ้ำเมื่อ toolchain อัปเดต; ระหว่างนี้ใช้ `al_symbolsearch` + grep ตามเดิม
- **2.13 แก้:** `al_getdiagnostics` คืนเฉพาะ diagnostic ที่ `source = "Compiler"` ไม่มีผลจาก analyzer
  (`areas` จึงกรอง cop ไม่ได้) ผลจาก cop อ่านได้จาก output ของ `al_compile` เท่านั้น
- **เพิ่ม:** โปรเจกต์เก่ามี cop finding มาก (โปรเจกต์ทดสอบหลัก มี 1,505 รายการ = JSON 555 KB)
  skill จึงใช้ `maxDiagnosticsPerCompilation: 500` และเมื่อชนเพดานให้ใช้ `al-build.cmd` + `AL_ANALYZERS`
  แล้วกรองเฉพาะไฟล์ที่เปลี่ยน (ทดสอบแล้ว: 138 บรรทัด, ~11 วินาที)
- **ยืนยัน:** ID นอก `idRanges` → `AL0297` จาก compile (reviewer ข้อ B ใช้ผล compile ได้จริง);
  symbol หาย → `AL1022` / `AL0185` (developer ข้อ 2.9); `al_getnextobjectid` คืน ID ไม่ติดกันได้
  (`count=2` → 77000, 77012); ToolSearch `select:` ใช้ชื่อสั้น `al_*` ได้
- **ยังไม่ทดสอบ:** `al_symbolsearch` แบบ `source = "environment"` (อาจเปิด sign-in) — skill ให้บอกผู้ใช้ก่อนเรียก
- **เพิ่ม:** `bc365_permission_creator.py create-al --object-id` (เดิม ID 50100 ตายตัว) ให้ใช้ ID จาก
  `al_getnextobjectid`
- ลำดับขั้นของ developer ทดสอบบนสำเนา โปรเจกต์ทดสอบหลัก: `al_getnextobjectid` → เขียน codeunit
  77000 → `al_compile` onlyErrors `succeeded:true` 0 error → compile พร้อม CodeCop + PTE cop เห็น finding
  ของไฟล์ใหม่ (`AA0247`)

**เกณฑ์ผ่าน (เดิม):** ทดลองกับ โปรเจกต์ทดสอบหลัก หนึ่ง requirement ตั้งแต่ analyst
ถึง reviewer โดย ID มาจากเครื่องมือ, reviewer ได้ diagnostic `AA*`/`PTE*` จาก analyzer จริง
และ build strategy สองชั้นใน developer กับ reviewer ยังเขียนตรงกัน — โค้ดที่ developer เขียน
ต้องอยู่บนสำเนาหรือ branch ทิ้ง และ **ไม่ publish** ข้อ App + Test (`al_addproject`, `projectPath`)
ทดสอบเพิ่มกับ `D:\BPC Project\al-extension-template` (ต้องดึง `.alpackages` ก่อน)

---

## Phase 3 — ปิดช่องว่างเรื่อง test และ build

ใช้รูปแบบสองชั้นเดียวกับ build: **ทางหลัก = MCP `al_run_tests`**, ทางสำรอง = `scripts/al-test.cmd`

### 3.1 เพิ่ม `scripts/al-test.cmd` (ทางสำรอง)
- หา `altool.exe` ผ่าน `find-al-bin.cmd` (ไม่เพิ่ม logic ค้นหาใน script ใหม่)
- รูปแบบ: `al-test.cmd <projectDir> <codeunitId> [testMethods]` และ
  `al-test.cmd <projectDir> --testgroups <file.json>`
- เรียก `altool.exe runtests ... --project <projectDir>` ส่ง JSON ออก stdout ตามเดิม
- exit code ตาม `runtests`: 0 = ผ่านทั้งหมด, 1 = มี test ไม่ผ่านหรือเชื่อมต่อไม่ได้
- การเชื่อมต่อ: ใช้ `launch.json` ของโปรเจกต์ หรือ `BC_SERVER_URL` / `BC_SERVER_INSTANCE` /
  `BC_SERVER_PORT` / `BC_SERVER_USERNAME` / `BC_SERVER_PASSWORD` สำหรับ on-prem และ container
- ตรวจความสามารถด้วย `altool runtests --help` ไม่ใช่เลขเวอร์ชัน ถ้าไม่มีคำสั่งให้แจ้งชัดเจนและ exit 1
- script ไม่เก็บรหัสผ่านและไม่พิมพ์ค่าตัวแปรที่เป็นความลับ

### 3.2 ปรับ skill ให้รัน test จริง
- เพิ่ม `al_run_tests` ในรายการ ToolSearch ของ developer และ reviewer
- `al-developer` ขั้น 6: เมื่อผู้ใช้ขอ test ให้เขียนแล้วรันจริงด้วย `al_run_tests` (สำรอง `al-test.cmd`)
  รายงานจำนวน passed / failed / skipped ถ้ารันไม่ได้ให้รายงาน "TESTS NOT RUN" พร้อมเหตุผล
- `al-reviewer` ขั้น 5: เมื่อมี test ให้รันซ้ำเอง ไม่เชื่อรายงานของ developer
- test ต้องรันบน sandbox หรือ container เท่านั้น ห้ามชี้ไป production
  (ตรวจ `environmentType` ใน `launch.json` ก่อนรัน ถ้าเป็น `Production` ให้หยุด)

### 3.3 ปรับ `scripts/al-build.cmd`
- เมื่อ toolchain มี `altool.exe` ที่รองรับ `workspace compile` และโฟลเดอร์มีไฟล์
  `.code-workspace` ให้ใช้ `altool workspace compile <file> --packagecachepath <cache>
  --errorlogdirectory <temp>` แล้วให้คะแนนจาก error log JSON
- กรณีอื่นใช้ `alc.exe` กับ regex เดิมทุกประการ
- ข้อความสรุป `BUILD OK` / `BUILD FAILED` และ exit code คงเดิม เพื่อไม่ให้ skill ต้องแก้ตาม
- map ชื่อ cop: `PerTenantExtensionCop` ของ `AL_ANALYZERS` → `PTECop` ของ `--analyzers`
  (ค่าที่รับได้: `AppSourceCop`, `CodeCop`, `None`, `PTECop`, `UICop`)
- ส่ง `AL_RULESET` เป็น `--ruleset` ทั้งสองเส้นทาง
- ตรวจรูปแบบ JSON ของ `--errorlogdirectory` จริงก่อนเขียนตัวให้คะแนน (`alc /errorlog:` ให้
  `{"version":"0.2","issues":[{"ruleId", "properties":{"severity":...}}]}` คาดว่าเหมือนกัน แต่ยังไม่ยืนยัน)

### ผลการทำ Phase 3 (2026-11-11)

**สภาพแวดล้อม:** environment `Develop` (Sandbox, BC 28.5) ของ tenant ที่ใช้พัฒนา (sign-in ด้วย token ที่ cache ไว้)
— ใช้ probe test app แยก "BPC AL Toolkit Probe Tests" (publisher "BPC AL Toolkit Probe",
codeunit 99950: `PassingTest`, `FailingTest`, ไม่มี UI/table/subscriber) **ยังติดตั้งอยู่บน Develop** ถอนได้จาก
Extension Management; ไม่ใช้ `al-extension-template` เพราะ app หลักมี pageextension ที่เด้ง Message ทุกครั้งที่เปิด
Customer List

| กรณี | `al-test.cmd` | `al_run_tests` (MCP) |
|---|---|---|
| `PassingTest` | exit 0, PassingTest=passed | succeeded=true |
| `FailingTest` | exit 1, FailingTest=failed + call stack | succeeded=false |
| environment ไม่มีจริง | exit 1 (400 Bad Request) | — |
| `--environmenttype Production` / launch.json Production / ไม่ระบุเป้าหมาย | ปฏิเสธ exit 1 | — |
| launch.json → Sandbox Develop | exit 0 | — |
| toolchain 18.1 (`AL_BIN`) | exit 0 | — |

- **ต่างจากแผน:** `data.results[]` มีแถวสรุประดับ codeunit (`methodName` ว่าง) ทำให้ `passed`/`failed` นับเกิน
  1 ต่อ codeunit — skill ให้นับเฉพาะแถวที่มี `methodName`
- **bug ที่เจอและแก้:** `exit /b 1` ใน `( )` ซ้อนคืน 0 เมื่อรัน script ตรง (ไม่ผ่าน `call`) → refusal ใช้ label
- **3.3 workspace compile:** ใช้ cache เดียวทุกโปรเจกต์ (`--packagecachepath` ซ้ำไม่ได้) จึงเข้าโหมด workspace
  เฉพาะเมื่อมี shared cache ไม่งั้นถอยไป `alc.exe` พร้อมบอกเหตุผล; `--analyzers` ต้องเป็น `CodeCop,PTECop`
  (คอมมา); exit code ของ workspace compile เชื่อได้; error log ต้อง match `^ *"severity": "Error"` เพราะ
  `"defaultSeverity"` ชนกับ pattern แบบไม่ยึดต้นบรรทัด
- **ผล 3.3:** workspace มี error → `BUILD FAILED` exit 1 ตรงกับเส้นทาง `alc.exe` บนโปรเจกต์เดียวกัน (AL0118 เดียวกัน);
  workspace สะอาด + cops + ruleset → `BUILD OK` และ `.app` ทั้งสองไฟล์ลง output folder; 18.1 ผ่าน; ไม่มีไฟล์ค้างใน
  workspace หรือ `%TEMP%`; โปรเจกต์ทดสอบหลัก จริงยัง `BUILD OK` ผ่าน `alc.exe`
- **ไม่ได้ทดสอบ:** toolchain ที่ไม่มี `runtests` / `workspace compile` (ไม่มีบนเครื่อง) — โค้ดตรวจด้วย `--help`

**เกณฑ์ผ่าน (เดิม):**
- `al_run_tests` และ `al-test.cmd` คืนผลเดียวกันกับ test codeunit ใน `al-extension-template\test`:
  ผ่านได้ 0 / ล้มได้ 1 เมื่อจงใจทำให้ test ล้ม
- `al-build.cmd` ให้ผลเดียวกันทั้งสองเส้นทางกับโปรเจกต์ที่มี error จริง
  (เส้นทาง workspace: `al-extension-template.code-workspace`)
- toolchain 18.1 (`AL_BIN` ชี้ไป extension) ยัง build ได้ทั้งสองเส้นทาง

---

## Phase 4 — ความสามารถใหม่

ทุกข้อใน Phase นี้ต้องทดสอบบน Windows จริงก่อนรวมเข้า 1.4.0 ข้อใดทดสอบไม่ผ่านให้เลื่อนไป
รุ่นถัดไปโดยไม่กระทบ Phase 1–3

### 4.1 AL LSP server
- ยืนยันรูปแบบ LSP config ของ Claude Code plugin จากเอกสารปัจจุบันก่อนเขียนไฟล์
- เพิ่ม `scripts/al-lsp.cmd`: หา `altool.exe` ผ่าน `find-al-bin.cmd` แล้วรัน
  `altool.exe launchlspserver "<project>" --packagecachepath "<cache>"` (project ก่อน option
  เหมือนข้อ 1.5; ถ้ามี `.code-workspace` ให้ส่ง `--workspacefile` แทน)
- log ของ LSP ไปที่ `~/.al-mcp/almcp.log` (คนละไฟล์กับ MCP) ระบุใน README
- ลงทะเบียน LSP สำหรับไฟล์ `.al` โดยอ้าง `${CLAUDE_PLUGIN_ROOT}/scripts/al-lsp.cmd`
- `al-reviewer` checklist ข้อ I และ `al-developer` ขั้น feasibility ใช้ find-references จาก LSP
  เมื่อพร้อม ไม่เช่นนั้นใช้ `al_symbolrelations` (ข้อ 2.5) แล้วจึง grep

### 4.2 `al graph` สำหรับวิเคราะห์ผลกระทบ
- เพิ่ม `scripts/al-graph.cmd` ครอบ `graph extract` → `graph stitch` → `graph query`
  เก็บ graph ไว้ในโฟลเดอร์ชั่วคราวนอกโปรเจกต์
- selector ใช้ **ชื่อ object** (`obj:<ObjectName>`) ไม่ใช่ ID; `obj:56900` ได้ 0 node และ `id:`
  ต้องเป็น symbol moniker เต็ม script ต้องรับชื่อ object หรือแปลงจาก ID ผ่าน node ใน graph
- workspace App + Test ใช้ `extract` ต่อโปรเจกต์ หรือ `extract-whole --graph` เมื่อต้องการ edge ข้าม app
- `al-analyst`: ดู caller ของ procedure ที่จะแก้ (`--to "obj:..." --direction callers`)
- `al-reviewer`: ตรวจ caller ของ procedure ที่ signature เปลี่ยน และรายงานเป็น Major เมื่อมี
  caller ที่ไม่ได้แก้ตาม
- ระบุข้อจำกัดใน skill: `--paths` เป็นตัวอย่างที่มีเพดาน ไม่ใช่ข้อพิสูจน์ว่าเข้าไม่ถึง และ
  ผล 0 node อาจเกิดจาก selector ผิด ไม่ใช่ "ไม่มี caller" ให้ตรวจด้วย `--from` ของ object เดียวกันก่อน

### 4.3 skill ใหม่ `al-debugger` และ `al-profiler` (opt-in)
- ไม่ลงทะเบียนใน `.mcp.json` หลัก เพื่อไม่ให้ทุกเครื่องเปิดการเชื่อมต่อออกไปยัง environment
- เพิ่ม launcher `scripts/al-snapshot-mcp.cmd` และ `scripts/al-profiling-mcp.cmd` อ่านเป้าหมาย
  จากตัวแปร `AL_ENV_TYPE`, `AL_ENV_NAME`, `AL_TENANT`
- **`--environmenttype` ของ proxy ทั้งสองมี default = Production** launcher ต้องปฏิเสธ (exit 1)
  เมื่อไม่ได้ตั้ง `AL_ENV_TYPE` และส่ง `--environmenttype` ทุกครั้ง ห้ามปล่อยให้ใช้ default
- README อธิบายวิธีเปิดใช้เอง: `altool auth login` หนึ่งครั้ง แล้วเพิ่ม MCP server
- skill ระบุข้อควรระวัง: snapshot และ profile อาจมีข้อมูลธุรกิจ, snapshot แบบ `Full` เพิ่ม
  ภาระ server, ต้องเรียก stop ทุกครั้งแม้ test ล้ม; profile ถูกเก็บที่ `%TEMP%\bc-profiling`
  (ปรับด้วย `--profilefolder`)
- ทั้งสอง skill อยู่นอกวงจร analyst → developer → reviewer และไม่ถูกเรียกอัตโนมัติจากสามขั้นนั้น

### 4.4 กฎแยกตาม runtime ใน `references/al-rules.md`
- เพิ่มหมวด "Runtime-gated features": อ่าน `runtime` จาก `app.json` ก่อนแนะนำฟีเจอร์
- ตาราง runtime: 16.x = BC 27, 17.x = BC 28, 18.0 = BC 29, **30.0 = BC 30** (เลขกระโดด
  จาก 18 เป็น 30) และให้ skill ยืนยันด้วย `altool GetLatestSupportedRuntimeVersion <platform>`
  เมื่อเจอ platform ที่ไม่อยู่ในตาราง
- runtime 18: default interface method; ใช้ `[RequiredPending]` เมื่อ method จะกลายเป็น
  required (AL0924); ห้ามลบ body ตรง ๆ (AS0148); เรียก default method ผ่านตัวแปร Interface
- ฟีเจอร์ v29 อื่น (index ข้าม table extension, เปิด/ปิด index ในโค้ด, action สืบทอด tooltip,
  ตรวจ uncommitted changes) และฟีเจอร์ runtime 30 ให้ยืนยันรายละเอียดจาก Microsoft Learn
  ก่อนเขียนเป็นกฎ
- `al-reviewer` เพิ่มข้อตรวจ: ฟีเจอร์ที่ใช้ต้องไม่ใหม่กว่า `runtime` ของโปรเจกต์

### ผลการทำ Phase 4 (2026-11-12)

| ข้อ | ส่งมอบ | หลักฐาน |
|---|---|---|
| 4.4 | หมวด "Runtime-Gated Features" ใน `al-rules.md`, checklist K ของ reviewer | Microsoft Learn: ตาราง runtime 16/17/18, default interface method, `[RequiredPending]`, AL0923/AL0924/AS0148/AS0149; compile จริง: runtime 16 → `AL0413`, runtime 18 compile ผ่านแม้ symbol เป็น BC 28.5 (compiler ไม่ตรวจ server) |
| 4.2 | `scripts/al-graph.cmd`, analyst (callers), reviewer checklist L | callers ของ procedure ถูกต้องบน 30.0 และ 18.1, App + Test workspace extract ได้, ไม่มีไฟล์ค้างใน `%TEMP%` |
| 4.1 | `.lsp.json` + `scripts/al-lsp.cmd`, developer/reviewer ใช้ `LSP` tool | client LSP โดยตรง: `references` คืน call site + declaration (ข้าม `//ClearLS` ที่เป็น comment), `definition` ได้; โหมด `--workspacefile` ได้; **headless `claude -p` ได้ `LSP` tool และ `findReferences` คืนบรรทัด 46 และ 1734** |
| 4.3 | `scripts/al-diag-mcp.cmd snapshot\|profiling` (ไฟล์เดียวแทนสองไฟล์ตามแผนเดิม), skill `al-debugger` / `al-profiler`, README วิธีเพิ่ม | proxy ทั้งสองเริ่มบน Develop และ `tools/list` ได้ 4 เครื่องมือ (ไม่ได้ capture อะไร); ปฏิเสธเมื่อไม่ตั้ง `AL_ENV_TYPE` / `AL_ENV_NAME`; คำสั่ง `claude mcp add` ใน README ทดสอบแล้วขึ้น Connected แล้วลบออก |

- **ต่างจากแผน:** selector ของ `graph query` ใช้ `obj:<ชื่อ object>#<procedure>` (ID, `Object.Procedure`,
  wildcard ได้ 0 node โดยไม่ error); graph เห็นเฉพาะ source ในโฟลเดอร์ที่ extract — call ไป base app /
  test library หายไป
- **ยังไม่ยืนยัน:** AL LSP ส่ง diagnostics หลังแก้ไฟล์หรือไม่ (probe ไม่เห็น `publishDiagnostics` หลัง `didOpen`)
  — skill จึงไม่อ้างถึง; การ capture snapshot / profile จริง (ต้องให้ผู้ใช้ทำ repro ใน BC)
- **พบนอก scope:** `al-extension-template.code-workspace` ชี้ folder `app` ที่ไม่มี `app.json` แล้ว (commit
  "Move app.json to Root Folder" ของ template)

**เกณฑ์ผ่าน (เดิม):** LSP ตอบ `textDocument/references` (หลัง `didOpen`) ข้ามโปรเจกต์ App + Test ได้;
`al-graph.cmd` คืน caller ของ procedure ทดสอบได้ถูกต้อง; MCP proxy ทั้งสองเริ่มได้เมื่อเปิดใช้
และปฏิเสธเมื่อไม่ตั้ง `AL_ENV_TYPE`; plugin ทำงานปกติเมื่อไม่เปิดใช้

---

## ลำดับการทำงานและการส่งมอบ

1. Phase 1 → commit แยกตามหัวข้อ (กฎ, launcher, เอกสาร)
2. Phase 2 → commit เดียวต่อ skill
3. Phase 3 → `al-test.cmd` + skill ก่อน แล้ว `al-build.cmd`
4. Phase 4 → ทีละข้อ ข้อใดไม่ผ่านการทดสอบให้เลื่อนออก
5. อัปเดต `CLAUDE.md` (layout, ตัวแปร, วิธีทดสอบ script ใหม่, ลำดับ argument ของ altool) และ `README.md` ทั้งสองไฟล์
6. ทดสอบติดตั้งเต็มรูปแบบตามหมวด "Full install check" ใน `CLAUDE.md`

## การทดสอบ

repo นี้ไม่มี test runner และ script เป็น Windows batch จึงต้องทดสอบบนเครื่อง Windows จริง

**สภาพเครื่องทดสอบปัจจุบัน:** toolchain 30.0.43-beta (.NET tool) และ 18.1 (VS Code extension);
**ไม่มี** toolchain v28, Docker, หรือ BC container

**เตรียมก่อนทดสอบ:**
- โหลด plugin จาก working tree ไม่ใช่ cache 1.3.0: `/plugin marketplace update al-toolkit-marketplace`
  แล้ว `/plugin update bc365-al-toolkit@al-toolkit-marketplace` (marketplace ต้องชี้มาที่ repo นี้)
  แล้วตรวจว่า `installed_plugins.json` แสดง 1.4.0
- โปรเจกต์ทดสอบหลัก: PTE ของลูกค้า (มี symbol, path มีช่องว่าง,
  `launch.json` → Sandbox) ห้ามแก้ source แล้ว publish; รองคือ `D:\BPC Project\al-extension-template`
  (App + Test, `.code-workspace`, `bpc.ruleset.json`) สำหรับกรณี workspace และ test
- Phase 3 test: โปรเจกต์ทดสอบหลัก ไม่มี test codeunit และห้ามเพิ่มโค้ดแล้ว publish จึงต้องใช้
  test app แยก (เช่น `al-extension-template\test`) บน Sandbox — ต้องขออนุมัติก่อน publish test app นั้น
- ดึง symbol ของ `al-extension-template` ด้วย `altool downloadsymbols --project <dir> --globalsourcesonly`
  (มีเฉพาะ 30.0 ไม่ต้องต่อ server)
- Phase 3 ต้องมี BC sandbox หรือ container และ `launch.json` (ตอนนี้ไม่มีทั้งคู่)
- เขียน output ทดสอบ (`.app`, log, graph) ลงโฟลเดอร์ชั่วคราว ไม่ใช่ในโปรเจกต์

**กรณีทดสอบ:**
- resolver: happy path, ไม่มี `dotnet` บน PATH (→ extension 18.1), exe ที่ไม่มีจริง, `AL_BIN` ผิด
- `al-mcp.cmd`: เริ่มได้ ทั้งกรณีตั้งและไม่ตั้ง `AL_PACKAGECACHE` / `AL_RULESET` / `AL_ANALYZERS`;
  `al_compile` สำเร็จในครั้งแรก; เริ่มนอกโปรเจกต์ AL ได้
- `al-build.cmd`: โปรเจกต์ที่ผ่าน, โปรเจกต์ที่มี error, ทั้งเส้นทาง workspace และ `alc.exe`
- `al-test.cmd` / `al_run_tests`: test ผ่าน, test ล้ม, เชื่อมต่อไม่ได้
- toolchain รุ่นเก่า: ทดสอบ 18.1 ด้วย `AL_BIN`; v28 ทดสอบบนเครื่องนี้ไม่ได้ ต้องติดตั้ง
  extension รุ่น 17.x แยกโฟลเดอร์แล้วชี้ `AL_BIN` หรือระบุใน release note ว่า "ไม่ได้ทดสอบ"
- ตรวจความสามารถของ toolchain ด้วย `altool <cmd> --help` ไม่ใช่เลขเวอร์ชัน
  (18.1 ไม่มี `downloadsymbols`, `listtests`, `doc`)
- วงจรเต็ม: หนึ่ง requirement จริงผ่าน analyst → developer → reviewer บน `al-extension-template`

## สิ่งที่ต้องตัดสินใจ

1. **~~`bc365-permissionset` และ `al-compiler`~~:** ตัดสินแล้ว (2026-11-11) รวมเข้า plugin —
   `bc365-permissionset` ทั้ง skill; `al-compiler` รวมเป็นหน้าที่ของ `al-build.cmd`
2. **~~จุดยืนเรื่อง handled event~~:** ตัดสินแล้ว (2026-11-11) "เลี่ยงเป็นค่าเริ่มต้น ใช้ `IsHandled`
   เฉพาะเมื่อ requirement ต้องการให้ subscriber แทนที่ logic เดิม"
3. **เวอร์ชัน toolchain ขั้นต่ำ:** แนะนำให้รองรับ v28 ต่อไปโดยฟีเจอร์ v29+ เป็นส่วนเสริม
   (ตรวจด้วย `--help` ไม่ใช่เลขเวอร์ชัน)
4. **Windows-only:** `altool` แบบ .NET tool รันข้ามแพลตฟอร์มได้ จะเพิ่ม launcher สำหรับ
   macOS/Linux หรือไม่ (แนะนำ: ไม่ทำในรุ่นนี้)
5. **~~เส้นทาง `workspace compile` ใน 3.3~~:** ตัดสินแล้ว (2026-11-11) คงไว้

## ความเสี่ยง

| ความเสี่ยง | การรับมือ |
|---|---|
| ชื่อเครื่องมือหรือตัวเลือกของ `altool` ต่างจากเอกสาร | ยืนยันแล้วบน 30.0 และ 18.1 (ดูตารางข้อเท็จจริง) ตรวจซ้ำเมื่อ toolchain อัปเดต |
| ลำดับ argument ทำให้ MCP server ไม่โหลดโปรเจกต์โดยไม่ error | วาง project ก่อน option เสมอ (ข้อ 1.5) และมีเกณฑ์ผ่าน "compile สำเร็จครั้งแรก" |
| ชื่อ analyzer ผิดรูปแบบถูกเพิกเฉยเงียบ ๆ | launcher แปลงเป็น `${Cop}` และเกณฑ์ผ่านต้องเห็น diagnostic `AA*` |
| .NET tool เป็นรุ่น beta (30.0.43-beta) พฤติกรรมเปลี่ยนได้ | ทดสอบทั้ง 30.0 และ 18.1, ไม่ผูก skill กับ flag ที่มีเฉพาะ beta โดยไม่มีทางสำรอง |
| รูปแบบ LSP config ของ Claude Code plugin ไม่ตรงที่คาด | ข้อ 4.1 แยกเป็นอิสระ เลื่อนได้โดยไม่กระทบส่วนอื่น |
| `SKILL.md` ยาวขึ้นจน Claude ทำตามไม่ครบ | ย้ายรายละเอียดไป `references/` และให้ skill อ้างถึง |
| test หรือ debugger ถูกชี้ไป production | skill ตรวจ `environmentType` ก่อนรัน, proxy ปฏิเสธเมื่อไม่ตั้ง `AL_ENV_TYPE`, MCP proxy เป็น opt-in |
| ผู้ใช้ toolchain รุ่นเก่าใช้งานไม่ได้ | ทุก script มีทางสำรองและทดสอบกับ 18.1; v28 ระบุสถานะการทดสอบตามจริง |
| ทดสอบ skill ผิดรุ่นเพราะ plugin cache ยังเป็น 1.3.0 | update plugin และตรวจ `installed_plugins.json` ก่อนทดสอบวงจรเต็ม |

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
- `altool <command> --help` บน 30.0.43-beta และ 18.1.43 (ตรวจ 2026-11-11)
