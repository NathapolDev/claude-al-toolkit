# bc365-al-toolkit

A Claude Code plugin marketplace for Microsoft Dynamics 365 Business Central AL
development. It gives Claude Code a real AL toolchain plus a three-stage skill pipeline
that takes a requirement from analysis → implementation → review, with a verified compile
at every stage that produces code.

| Component | What it does |
|---|---|
| **`al` MCP server** | Launches Microsoft's AL MCP server (`altool.exe launchmcpserver`) from the standalone AL Development Tools .NET tool or the AL Language VS Code extension. Gives Claude 16 tools — build: `al_compile`, `al_build`, `al_getdiagnostics`, `al_downloadsymbols`; symbols: `al_symbolsearch`, `al_symbolrelations`, `al_getnextobjectid`, `al_getpackagedependencies`, `al_inspectpage`; workspace: `al_addproject`; environment: `al_publish`, `al_run_tests`, `al_auth_login`, `al_auth_logout`; translation: `al_searchtranslations`, `al_writetranslation`. Resolves the toolchain at every launch, so tool/extension updates never break it. |
| **AL language server** (`.lsp.json`) | Registers Microsoft's AL LSP (`altool.exe launchlspserver`) for `.al` files, so Claude gets the `LSP` tool: go to definition and find references by symbol instead of text search. |
| **`al-build.cmd`** | Bundled `alc.exe` build fallback, used when the MCP server isn't connected — so every machine has a real build path. Replaces the old standalone `al-compiler` skill. |
| **`al-test.cmd`** | Bundled `altool runtests` fallback for running AL tests on a sandbox or container when the MCP server isn't connected. Refuses Production. |
| **`al-graph.cmd`** | Call-graph questions ("who calls this procedure?") via `altool graph`, used by `al-analyst` and `al-reviewer` for impact checks. Builds the graph in `%TEMP%` and deletes it. |
| **`al-debugger`** / **`al-profiler`** skills | Opt-in: snapshot debugging and performance profiling on a Business Central environment through Microsoft's MCP proxies (`scripts/al-diag-mcp.cmd`), added per machine — see "Opt-in: snapshot debugging and profiling". Outside the analyst → developer → reviewer pipeline. |
| **`bc365-permissionset`** skill | Create/analyze permission sets: import-ready tenant XML and AL `permissionset` objects. Python 3 (standard library only). |
| **`al-analyst`** skill | Analyze a requirement → Solution Design comparing options. Read-only, writes no code. |
| **`al-developer`** skill | Implement AL code, build until zero diagnostics. |
| **`al-reviewer`** skill | Review AL code, independently re-verify the build, Approve / Request Changes. Read-only, edits nothing. |
| **`references/al-rules.md`** | Canonical AL house rules all three skills defer to. |

---

## 1. Prerequisites (every machine)

The AL toolchain is **not** shipped inside this plugin — `altool.exe` and `alc.exe` are
Microsoft's binaries. Each machine needs:

- **Windows.** The launchers are `.cmd`.
- **One AL toolchain** — either works; the .NET tool needs no VS Code:
  - **AL Development Tools .NET tool** (recommended):
    `dotnet tool install -g Microsoft.Dynamics.BusinessCentral.Development.Tools`
    (add `--prerelease` for the newest beta). Needs the .NET 10 **or** .NET 8 ASP.NET Core
    runtime; the resolver picks the build whose runtime is installed.
  - **VS Code** with the **AL Language** extension (`ms-dynamics-smb.al-*`, normally under
    `%USERPROFILE%\.vscode\extensions`; binaries in `bin\` on AL 18+, `bin\win32` before).
- **Claude Code**, started from inside the AL project folder — `altool` needs a project
  path to resolve symbols against.

Without either toolchain, neither the `al` MCP server nor `al-build.cmd` can run. The
three skills still work, but they will report the build as **NOT VERIFIED** rather than
assume the code compiles.

### Toolchain benchmark

Measured 2026-10-20 through this plugin's `al-mcp.cmd` on one Windows 11 machine, against
a real PTE project (281 `.al` files, 45 symbol packages). Times are wall-clock per MCP
call; your numbers will vary with hardware and project size.

| Operation | .NET tool 30.0.43 (beta, net10.0) | VS Code AL extension 18.1 |
|---|---|---|
| Server start (`initialize`) | ~1 s | ~1 s |
| First `al_compile` (loads symbols) | 10–13 s | 10–14 s |
| `al_compile` after editing a file | 0.3–0.9 s | 0.3–0.9 s |
| `al_compile` + CodeCop + PerTenantExtensionCop | ~4.6 s | ~3.9 s |
| `al_symbolsearch` (`Sales Header`, Table) | **~1.7 s** | **~33 s** |
| `al-build.cmd` (alc.exe, both cops, writes `.app`) | ~13.5 s | — |

Correctness was identical on both: 0 errors on the clean project (matching
`al-build.cmd`), the same CodeCop / PTE cop diagnostic codes, and 24/24 edit cycles where
an injected `AL0132` error was reported at the right line/column and cleared immediately
after the fix — no file-watcher delay.

Takeaways: expect ~10 s once per session, then sub-second incremental compiles. The .NET
tool is much faster for symbol search, which `al-analyst` leans on. `al_compile` returns at
most 100 diagnostics by default, so use `onlyErrors: true` to grade a build and
`al_getdiagnostics` to page through warnings.

### Non-default VS Code locations

Both scripts resolve the toolchain through `scripts/find-al-bin.cmd`, which searches in
order: `%AL_BIN%` → `%AL_EXTENSIONS_DIR%` → AL Development Tools .NET global tool →
`%VSCODE_EXTENSIONS%` → VS Code stable / Insiders / Server / OSS user extension roots →
portable and Program Files installs. Within a root, the newest `ms-dynamics-smb.al-*`
folder wins.

If a machine keeps extensions somewhere unusual, set one environment variable — no script
edits needed:

```powershell
# point straight at the folder holding altool.exe / alc.exe
setx AL_BIN "D:\tools\al\bin"

# or point at the extensions root and let the script pick the newest AL version
setx AL_EXTENSIONS_DIR "D:\vscode-extensions"
```

| Variable | Purpose | Default |
|---|---|---|
| `AL_BIN` | Folder containing `altool.exe` / `alc.exe` | auto-resolved |
| `AL_EXTENSIONS_DIR` | VS Code extensions root | auto-resolved |
| `AL_PROJECT_DIR` | Project handed to the MCP server; skipped when it has no `app.json` (add one later with `al_addproject`) | folder Claude Code started in |
| `AL_PACKAGECACHE` | Symbol folder for the MCP server and `al-build.cmd` | `<project>\.alpackages` |
| `AL_ANALYZERS` | Semicolon list of cops (`CodeCop;PerTenantExtensionCop`) for the MCP server and `al-build.cmd` | none |
| `AL_RULESET` | Ruleset file for the MCP server and `al-build.cmd`; on the MCP server it only matters when `AL_ANALYZERS` is set | none |
| `AL_MCP_LOGLEVEL` | MCP server log level: `Debug`, `Verbose`, `Normal`, `Warning`, `Error` | `Normal` |
| `AL_MCP_LOGFILE` | MCP server log file | `%LOCALAPPDATA%\Microsoft\ALLanguageServer\almcp.log` |

---

## 2. Install

### Option A — from a git repository (recommended)

1. Push this folder to a private git repo (GitHub, Azure DevOps, GitLab, …).
2. On the target machine, inside Claude Code:

```
/plugin marketplace add <git-url-or-owner/repo>
/plugin install bc365-al-toolkit@al-toolkit-marketplace
/reload-plugins
```

### Option B — from a local folder or network share

Copy the whole `claude-al-toolkit` folder to the target machine (USB, share, `robocopy`),
then:

```
/plugin marketplace add "\\server\share\claude-al-toolkit"
/plugin install bc365-al-toolkit@al-toolkit-marketplace
/reload-plugins
```

A local path also works for testing before distributing:

```
/plugin marketplace add "C:\BPC BC Project\claude-al-toolkit"
```

### Verify the install

```
claude mcp list          # must list `al`
```

Then in Claude Code, `/bc365-al-toolkit:al-analyst` should appear. If `al_*` tools are missing,
check that the AL Language extension is installed and that Claude Code was started from
the AL project folder.

---

## 3. Using the skills

The three skills are a deliberate pipeline — each one's output is the next one's input:

```
requirement ──▶ al-analyst ──▶ Solution Design ──▶ al-developer ──▶ code + green build ──▶ al-reviewer ──▶ Approve / Request Changes
                                                        ▲                                              │
                                                        └──────────── fix list on Request Changes ─────┘
```

Invoke a skill in either way:

- **Explicitly** — `/bc365-al-toolkit:al-analyst <your requirement>`
- **Implicitly** — just describe the task. Each skill's frontmatter `description` makes
  Claude pick the right one from natural language, in Thai or English.

Skip stages when it makes sense: a one-line fix doesn't need an analysis pass. But
`al-developer` will note in its summary when the analyst stage was skipped.

### 3.1 `al-analyst` — analyze before coding

**Use when:** you have a requirement and don't yet know how to build it. "How should I
implement X", "analyze this requirement", "what's the best way to add Y".

```
/bc365-al-toolkit:al-analyst Add an approval workflow to the Purchase Order card so orders
above 100,000 THB need a manager's approval before release.
```

**What it does:** restates the requirement → explores your codebase and `app.json`
(dependencies, `idRanges`, `target`, runtime version) → finds real extension points,
verified with `al_symbolsearch` and Microsoft Learn (never guessed) → compares **at least
two options** → recommends one → surfaces risks.

It works down a decision framework that prefers the least base-app impact:
setup/configuration → event subscriber → table/page extension → new codeunit → new object →
modifying the base app (avoid).

**You get:** a Markdown Solution Design — Requirement Summary, Affected Objects table,
Extension Points Found (with how each was verified), Options A/B with pros/cons/upgrade
impact, Recommended Approach with proposed object names and IDs inside `idRanges`, Risks &
Open Questions (DataClassification, permission sets, upgrade code), and an ordered handoff
plan.

**It will not:** write production AL, or modify any project file. If the requirement is
ambiguous it asks specific questions first.

### 3.2 `al-developer` — implement and build green

**Use when:** you're ready to write code. "Implement this", "write the codeunit", "add
this field", "fix this AL error".

```
/bc365-al-toolkit:al-developer Implement the recommended Option B from the analysis above.
```

**What it does:** verifies feasibility **before** writing — confirms objects, fields,
methods and event signatures actually exist via `al_symbolsearch` (symbols, not text
grep), checks `app.json` dependencies, `idRanges` and runtime version. If the planned
approach turns out infeasible it says why, picks the best fallback and explains the
change. Then it writes code against the house standard and runs a real build loop:
`al_downloadsymbols` → `al_compile` (with the cops matching `app.json` `target`) →
`al_getdiagnostics` → fix → repeat until zero errors.

**You get:** the code, plus a summary — approach used, feasibility confirmation, files
changed table, key code decisions, **build result** (which tool, PASS/FAIL, zero errors
confirmed), test gaps, and focus areas for review.

**Notes:**
- Tests are written **only when you ask**. Test gaps are always listed so you can decide.
- If no real build can be run, it will not report the task as done.
- It never publishes to production.

### 3.3 `al-reviewer` — audit and verify

**Use when:** code is written and you want it checked. "Review this code", "check my AL
before I merge", "is this codeunit safe".

```
/bc365-al-toolkit:al-reviewer Review the changes in src/PurchaseApproval/.
```

**What it does:** checks requirement coverage, reads the changed code against an
twelve-part checklist (requirement, coding standard, architecture, performance, event
quality, compliance/security, data & UX correctness, upgrade safety, `TransferFields`
mapping, runtime fit, callers of changed signatures, build & tests), and — this is
the point — **re-runs the build itself** rather than trusting the developer's report. If it
cannot run any build, it marks the build check NOT VERIFIED instead of assuming.

**You get:** a verdict (✅ Approve / 🔁 Request Changes) with issues graded 🔴 Blocker /
🟠 Major / 🟡 Minor / 🟢 Suggestion, each with `file:line`, the reason, and a suggested fix
— plus an ordered fix list when changes are requested.

**It will not:** edit code. Code that doesn't compile is an immediate 🔴 Blocker.

### House rules

All three skills defer to `references/al-rules.md` as the single source of truth: AL code
style, naming, data access & performance, error handling, events, APIs, tests, upgrade
code, and the AL community "Vibe Coding Rules". Change a rule there and all three stages
pick it up.

---

## 4. Building without the MCP server

`al-build.cmd` is the fallback the skills use, and you can run it directly:

```
plugins\al-toolkit\scripts\al-build.cmd "C:\path\to\AlProject"
plugins\al-toolkit\scripts\al-build.cmd "C:\path\to\AlProject" "C:\out\My.app"
```

With code analysis:

```powershell
$env:AL_ANALYZERS = "CodeCop;PerTenantExtensionCop"   # AppSource: CodeCop;AppSourceCop
plugins\al-toolkit\scripts\al-build.cmd "C:\path\to\AlProject"
```

It prints the compiler diagnostics, then `BUILD OK` (exit 0) or `BUILD FAILED` (exit 1).

**Whole workspace (App + Test):** point it at the folder that holds the `.code-workspace`.
When that folder also has a shared symbol cache (`.alpackages`, or `AL_PACKAGECACHE`) and
the toolchain has `altool workspace compile`, every project is built in one run and the
second argument becomes an output *folder*. Without a shared cache it falls back to
`alc.exe` on that one folder and says why.

### Running tests without the MCP server

```powershell
plugins\al-toolkit\scripts\al-test.cmd "C:\path\to\TestProject" 50150
plugins\al-toolkit\scripts\al-test.cmd "C:\path\to\TestProject" 50150 --testmethods MyTest
plugins\al-toolkit\scripts\al-test.cmd "C:\path\to\TestProject" 50150 --environmenttype Sandbox --environmentname Develop
```

It passes everything after the project folder to `altool runtests`, uses the project's
`launch.json` for the connection, prints the JSON result, and exits 0 when all tests pass,
1 otherwise. Tests run against the apps already published on that environment. It refuses
to run when the target is Production or can't be determined. In the result, ignore the
row with an empty `methodName` — it's the codeunit summary.

> **Why the wrapper exists:** `alc.exe` exits 0 even when compilation fails. Never call
> `alc.exe` directly and trust its exit code — `al-build.cmd` grades the output for you.

### Opt-in: snapshot debugging and profiling

The `al-debugger` and `al-profiler` skills use Microsoft's snapshot debugging and
performance profiling MCP proxies. They connect to a Business Central environment and can
capture business data, so the plugin doesn't register them. Add the ones you want, once
per machine, pointing at a **sandbox** unless you mean production:

```powershell
# where the installed plugin lives (local-folder installs report readFromFolder)
$p = claude plugin list --json | ConvertFrom-Json | Where-Object id -like 'bc365-al-toolkit@*'
$root = if ($p.readFromFolder) { $p.readFromFolder } else { $p.installPath }

claude mcp add al-snapshot  -e AL_ENV_TYPE=Sandbox -e AL_ENV_NAME=Develop -- "$root\scripts\al-diag-mcp.cmd" snapshot
claude mcp add al-profiling -e AL_ENV_TYPE=Sandbox -e AL_ENV_NAME=Develop -- "$root\scripts\al-diag-mcp.cmd" profiling
```

- `AL_ENV_TYPE` is required (`Sandbox`, `Production`, or `OnPrem`); the launcher refuses
  to start without it because the proxies default to Production. Add `-e AL_TENANT=...`
  for a specific tenant. For on-prem, append altool options after the mode, e.g.
  `profiling --server http://bc --serverinstance BC --port 7047` (the API/OData port, not
  the dev port).
- Sign in once with `altool auth login` or let the first tool call open the sign-in.
- `installPath` contains the plugin version, so re-run the `claude mcp add` lines after
  a plugin update (git installs); remove with `claude mcp remove al-snapshot`.

---

## 5. Updating

After changing skills or rules here:

1. Bump `version` in `plugins/al-toolkit/.claude-plugin/plugin.json`.
2. Push / re-copy the marketplace folder.
3. On each installed machine:

```
/plugin marketplace update al-toolkit-marketplace
/plugin update bc365-al-toolkit@al-toolkit-marketplace
```

---

## 6. Troubleshooting

| Symptom | Cause / fix |
|---|---|
| `claude mcp list` doesn't show `al` | AL Language extension missing, or in a non-default location — set `AL_BIN` / `AL_EXTENSIONS_DIR`. |
| `al_*` tools "not found" | They're deferred; Claude loads them via ToolSearch on demand. If they never load, the MCP server isn't connected. |
| `[find-al-bin] Could not find altool.exe` | Install the AL Language extension, or set `AL_BIN` to the folder holding the executables. |
| `error AL1021: The package cache path has not been specified` | No `.alpackages` in the project — download symbols first (`al_downloadsymbols`, or AL: Download Symbols in VS Code). |
| `error AL1022: … could not be found in the package cache` | Symbols are missing or stale for the `application` / `platform` version in `app.json`. |
| Skills load but every build is "NOT VERIFIED" | Claude Code wasn't started inside the AL project folder, or no symbols are present. |
| `al_compile` says "No projects are loaded" | Claude Code was started outside an AL project. Ask Claude to call `al_addproject` with the project folder, or restart Claude Code inside it. |
| `al_*` tools misbehave | Set `AL_MCP_LOGLEVEL=Debug`, restart Claude Code, and read `%LOCALAPPDATA%\Microsoft\ALLanguageServer\almcp.log` (or `AL_MCP_LOGFILE`). |

Contributor notes — repo layout, invariants, and how to verify changes — are in
[`CLAUDE.md`](CLAUDE.md).
