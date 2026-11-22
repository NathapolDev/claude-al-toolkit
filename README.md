# bc365-al-toolkit

An **Antigravity (`agy`) Plugin** for Microsoft Dynamics 365 Business Central (BC365) AL development. It connects Antigravity to Microsoft's AL toolchain (`al` MCP server + `al-lsp` MCP server), applies always-on AL coding standards (`rules/AGENTS.md`), and enforces a three-stage skill pipeline (`al-analyst` → `al-developer` → `al-reviewer`) with verified builds at every code-producing stage.

| Component | What it does |
|---|---|
| **`plugin.json`** | Antigravity plugin manifest (`bc365-al-toolkit`, version `1.4.0`, `assets/logo.svg`, and suggested starter prompts). |
| **`al` MCP server** (`mcp_config.json` → `scripts/al-mcp.cmd`) | Launches Microsoft's AL MCP server (`altool.exe launchmcpserver`) from the standalone AL Development Tools .NET tool or the AL Language VS Code extension. Exposes 16 tools — build: `al_compile`, `al_build`, `al_getdiagnostics`, `al_downloadsymbols`; symbols: `al_symbolsearch`, `al_symbolrelations`, `al_getnextobjectid`, `al_getpackagedependencies`, `al_inspectpage`; workspace: `al_addproject`; environment: `al_publish`, `al_run_tests`, `al_auth_login`, `al_auth_logout`; translation: `al_searchtranslations`, `al_writetranslation`. Resolves the toolchain at launch time, so tool/extension updates never break it. |
| **`al-lsp` MCP server** (`mcp_config.json` → `scripts/al-lsp-mcp.cmd`) | Python 3 stdlib stdio MCP bridge (`scripts/al-lsp-mcp.py`) wrapping Microsoft's AL Language Server (`scripts/al-lsp.cmd` → `altool.exe launchlspserver`). Exposes 7 semantic code intelligence tools (plus `--cli` fallback): `al_lsp_definition`, `al_lsp_references`, `al_lsp_hover`, `al_lsp_document_symbols`, `al_lsp_workspace_symbols`, `al_lsp_signature_help`, and `al_lsp_rename_preview`. |
| **`rules/AGENTS.md`** | Always-on Antigravity plugin rules (plain Markdown, under 24 KB): BC365 skill routing table, `al` + `al-lsp` MCP usage rules, and the canonical AL coding standard. |
| **`al-build.cmd`** | Bundled `alc.exe` / `altool workspace compile` build fallback used when the `al` MCP server isn't connected — so every machine has a real build path. |
| **`al-test.cmd`** | Bundled `altool runtests` fallback for running AL tests on a sandbox or container when the `al` MCP server isn't connected. Refuses Production. |
| **`al-graph.cmd`** | Call-graph queries ("who calls this procedure?") via `altool graph`, used by `al-analyst` and `al-reviewer` for impact checks. Builds the graph in `%TEMP%` and deletes it. |
| **`al-lsp` skill** | Teaches Antigravity when and how to use the 7 `al-lsp` MCP tools and `--cli` fallback for definitions, callers, `TransferFields` checks, and hover inspection. |
| **`al-debugger`** / **`al-profiler`** skills | Opt-in: snapshot debugging and performance profiling on a Business Central environment through Microsoft's MCP proxies (`scripts/al-diag-mcp.cmd`), added per machine — see "Opt-in: snapshot debugging and profiling". Outside the analyst → developer → reviewer pipeline. |
| **`bc365-permissionset`** skill | Create/analyze permission sets: import-ready tenant XML and AL `permissionset` objects. Python 3 (standard library only). |
| **`al-analyst`** skill | Analyze a requirement → Solution Design comparing options. Read-only, writes no code. |
| **`al-developer`** skill | Implement AL code, build until zero diagnostics. |
| **`al-reviewer`** skill | Review AL code, independently re-verify the build, Approve / Request Changes. Read-only, edits nothing. |
| **`references/al-rules.md`** | Canonical AL house rules all pipeline skills and `rules/AGENTS.md` defer to. |

---

## 1. Prerequisites (every machine)

The AL toolchain is **not** shipped inside this plugin — `altool.exe` and `alc.exe` are Microsoft's binaries. Each machine needs:

- **Windows.** The launchers are `.cmd` scripts.
- **Python 3** on `PATH` (`python.exe`, standard library only) — required for the `al-lsp` MCP server (`scripts/al-lsp-mcp.py`) and the `bc365-permissionset` scripts.
- **One AL toolchain** — either works; the .NET tool needs no VS Code:
  - **AL Development Tools .NET tool** (recommended):
    `dotnet tool install -g Microsoft.Dynamics.BusinessCentral.Development.Tools`
    (add `--prerelease` for the newest beta). Needs the .NET 10 **or** .NET 8 ASP.NET Core runtime; the resolver picks the build whose runtime is installed.
  - **VS Code** with the **AL Language** extension (`ms-dynamics-smb.al-*`, normally under `%USERPROFILE%\.vscode\extensions`; binaries in `bin\` on AL 18+, `bin\win32` before).
- **Antigravity (`agy`)**, opened in or pointed at the AL project folder — `altool` needs a project path to resolve symbols against (`al_addproject` can load projects later for `al`, and `al-lsp-mcp.py` auto-discovers `*.code-workspace` or `app.json` from `filePath` / `projectPath`).

Without an AL toolchain, neither the `al`/`al-lsp` MCP servers nor `al-build.cmd` can run. The skills still work, but they will report the build as **NOT VERIFIED** rather than assume the code compiles.

### Toolchain benchmark

Measured 2026-10-20 through this plugin's `al-mcp.cmd` on one Windows 11 machine, against a real PTE project (281 `.al` files, 45 symbol packages). Times are wall-clock per MCP call; your numbers will vary with hardware and project size.

| Operation | .NET tool 30.0.43 (beta, net10.0) | VS Code AL extension 18.1 |
|---|---|---|
| Server start (`initialize`) | ~1 s | ~1 s |
| First `al_compile` (loads symbols) | 10–13 s | 10–14 s |
| `al_compile` after editing a file | 0.3–0.9 s | 0.3–0.9 s |
| `al_compile` + CodeCop + PerTenantExtensionCop | ~4.6 s | ~3.9 s |
| `al_symbolsearch` (`Sales Header`, Table) | **~1.7 s** | **~33 s** |
| `al-build.cmd` (alc.exe, both cops, writes `.app`) | ~13.5 s | — |

Takeaways: expect ~10 s once per session, then sub-second incremental compiles. The .NET tool is much faster for symbol search, which `al-analyst` leans on. `al_compile` returns at most 100 diagnostics by default, so use `onlyErrors: true` to grade a build and `al_getdiagnostics` to page through warnings.

### Non-default VS Code locations & environment overrides

The batch launchers resolve the toolchain through `scripts/find-al-bin.cmd`, which searches in order: `%AL_BIN%` → `%AL_EXTENSIONS_DIR%` → AL Development Tools .NET global tool → `%VSCODE_EXTENSIONS%` → VS Code stable / Insiders / Server / OSS user extension roots → portable and Program Files installs. Within a root, the newest `ms-dynamics-smb.al-*` folder wins.

If a machine keeps extensions somewhere unusual, set an environment variable — no script edits needed:

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
| `AL_PROJECT_DIR` | Project handed to `al` / `al-lsp`; skipped on `al` when it has no `app.json` (add one later with `al_addproject`) | current directory / resolved from `filePath` |
| `AL_PACKAGECACHE` | Symbol folder for the MCP/LSP servers and `al-build.cmd` | `<project>\.alpackages` |
| `AL_ANALYZERS` | Semicolon list of cops (`CodeCop;PerTenantExtensionCop`) for the MCP server and `al-build.cmd` | none |
| `AL_RULESET` | Ruleset file for the MCP server and `al-build.cmd`; on the MCP server it only matters when `AL_ANALYZERS` is set | none |
| `AL_MCP_LOGLEVEL` | MCP server log level: `Debug`, `Verbose`, `Normal`, `Warning`, `Error` | `Normal` |
| `AL_MCP_LOGFILE` | MCP server log file | `%LOCALAPPDATA%\Microsoft\ALLanguageServer\almcp.log` |

---

## 2. Install in Antigravity (`agy`)

### Option A — Global plugin install (recommended)

Clone or copy this repository to your machine, then run the bundled installer from the repository root:

```cmd
install-agy-plugin.cmd
```

(`install-agy-plugin.cmd` invokes `powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install-agy-plugin.ps1"`.)

What the installer does:
1. Performs a clean copy of `plugins\al-toolkit` into `%USERPROFILE%\.gemini\config\plugins\bc365-al-toolkit`.
2. Rewrites `%USERPROFILE%\.gemini\config\plugins\bc365-al-toolkit\mcp_config.json` with your user's resolved forward-slash absolute paths (`<USERPROFILE>/.gemini/config/plugins/bc365-al-toolkit/scripts/al-mcp.cmd` and `al-lsp-mcp.cmd`), because Antigravity plugin `mcp_config.json` does not expand environment variables or `${CLAUDE_PLUGIN_ROOT}`.
3. Checks `%USERPROFILE%\.gemini\config\skills\` for loose `al-analyst`, `al-developer`, or `al-reviewer` directories and moves them to `%USERPROFILE%\.gemini\config\skills_archived_by_bc365_al_toolkit\` so they cannot shadow the plugin's skills. (You can delete that archive folder once confirmed.)

### Option B — Workspace-scoped discovery (this repository only)

[`.agents/plugins.json`](.agents/plugins.json) declares `{"entries": [{"path": "plugins"}]}` so Antigravity automatically discovers `plugins/al-toolkit` (with `plugin.json`, `mcp_config.json`, `rules/AGENTS.md`, `assets/logo.svg`, and all 7 `skills/`) when opening this repository directly.

> [!NOTE]
> If you also have legacy standalone AL skills in `%USERPROFILE%\.gemini\skills\` or `%USERPROFILE%\.gemini\antigravity\skills\` (for example an old `al-build` folder), remove them so Antigravity resolves all BC365/AL workflows from the `bc365-al-toolkit` plugin cleanly.

### Verify the Antigravity install

1. **Restart or reload Antigravity** so the plugin, rules, and MCP servers load.
2. Open **Customizations > Plugins** (or `[bc365-al-toolkit](customization://bc365-al-toolkit)`) and confirm **BC365 AL Toolkit** (`bc365-al-toolkit`) is enabled and lists:
   - **Rules:** `rules/AGENTS.md`
   - **Skills (7):** `al-analyst`, `al-developer`, `al-reviewer`, `al-lsp`, `bc365-permissionset`, `al-debugger`, `al-profiler`
3. Open **Additional Options (...) > MCP Servers** and verify:
   - **`al`** — connected with 16 tools (`al_compile`, `al_symbolsearch`, `al_addproject`, etc.)
   - **`al-lsp`** — connected with 7 tools (`al_lsp_definition`, `al_lsp_references`, `al_lsp_hover`, `al_lsp_document_symbols`, `al_lsp_workspace_symbols`, `al_lsp_signature_help`, `al_lsp_rename_preview`)

---

## 3. Using the skills in Antigravity

The core three skills form a deliberate pipeline — each stage's output feeds the next:

```text
requirement ──▶ al-analyst ──▶ Solution Design ──▶ al-developer ──▶ code + green build ──▶ al-reviewer ──▶ Approve / Request Changes
                                                        ▲                                              │
                                                        └──────────── fix list on Request Changes ─────┘
```

Describe your task naturally in Thai or English — each skill's frontmatter `description` and the always-on routing table in `rules/AGENTS.md` trigger the appropriate stage automatically.

Skip stages when it makes sense: a one-line fix doesn't need an analysis pass. `al-developer` will note in its summary when the analyst stage was skipped.

### 3.1 `al-analyst` — analyze before coding

**Use when:** you have a requirement and don't yet know how to build it ("how should I implement X", "analyze this requirement", "what's the best way to add Y").

**What it does:** restates the requirement → explores your codebase and `app.json` (dependencies, `idRanges`, `target`, runtime version) → finds real extension points verified with `al_symbolsearch`, `al-lsp` (`al_lsp_definition` / `al_lsp_references`), and Microsoft Learn → compares **at least two options** → recommends one → surfaces risks.

**You get:** a Markdown Solution Design (`# Analysis: ...`) covering affected objects, verified extension points, Options A/B, recommended object names & IDs inside `idRanges`, `TransferFields` flow, DataClassification/permission/upgrade risks, and an ordered handoff plan. Read-only; writes no code.

### 3.2 `al-developer` — implement and build green

**Use when:** you're ready to write or fix AL code ("implement this", "write the codeunit", "add this field", "fix this AL error").

**What it does:** verifies feasibility **before** writing using `al_symbolsearch` and `al-lsp` (symbols, not text grep) → writes AL code following `references/al-rules.md` → runs a real build loop (`al_downloadsymbols` → `al_compile` with cops matching `app.json` `target` → `al_getdiagnostics` → fix → repeat until 0 errors).

**Notes:**
- Tests are written **only when you ask**. Test gaps are always listed so you can decide.
- If no real build can be run, it reports `NOT VERIFIED` rather than claiming success.
- It never publishes to production.

### 3.3 `al-reviewer` — audit and verify

**Use when:** code is written and you want an audit before merging ("review this code", "check my AL before I merge", "is this codeunit safe").

**What it does:** checks requirement coverage against a 12-part checklist (coding standard, architecture, performance, event quality, compliance/security, UX/DataClassification/permissions, upgrade safety, `TransferFields` mapping via `al-lsp`, callers of changed signatures, runtime fit, build & tests) and **independently re-runs the build** rather than trusting the developer's report. Read-only; edits no code.

### 3.4 `al-lsp` — semantic AL code intelligence

**Use when:** resolving symbol definitions, tracing all callers or `TransferFields` references without comment/string false positives, inspecting hover types/XML docs, listing document/workspace symbols, checking parameter overloads, or previewing a symbol rename. Uses the `al-lsp` MCP server (`al_lsp_*` tools) or its CLI fallback `scripts/al-lsp-mcp.cmd --cli <tool> "<json>"`.

### 3.5 `bc365-permissionset`, `al-debugger`, and `al-profiler`

- **`bc365-permissionset`**: generates and analyzes BC365 import-ready Tenant XML files and AL `permissionset` objects using Python 3 stdlib scripts (`skills/bc365-permissionset/scripts/`).
- **`al-debugger`** / **`al-profiler`**: opt-in snapshot debugging and performance profiling on a live BC sandbox (see Section 4).

### House rules

All pipeline skills defer to [`plugins/al-toolkit/references/al-rules.md`](plugins/al-toolkit/references/al-rules.md) as the single source of truth, mirrored in [`plugins/al-toolkit/rules/AGENTS.md`](plugins/al-toolkit/rules/AGENTS.md) as always-on Antigravity rules.

---

## 4. CLI fallbacks & opt-in diagnostics

### Building without the MCP server (`al-build.cmd`)

`al-build.cmd` is the fallback the skills use when the `al` MCP server isn't connected:

```cmd
plugins\al-toolkit\scripts\al-build.cmd "C:\path\to\AlProject"
plugins\al-toolkit\scripts\al-build.cmd "C:\path\to\AlProject" "C:\out\My.app"
```

With code analysis:

```powershell
$env:AL_ANALYZERS = "CodeCop;PerTenantExtensionCop"   # AppSource: CodeCop;AppSourceCop
plugins\al-toolkit\scripts\al-build.cmd "C:\path\to\AlProject"
```

It prints compiler diagnostics and exits with `BUILD OK` (0) or `BUILD FAILED` (1). For an App + Test `.code-workspace` with a shared `.alpackages` cache, it invokes `altool workspace compile`.

> **Why the wrapper exists:** `alc.exe` exits 0 even when compilation fails. Never call `alc.exe` directly and trust its exit code — `al-build.cmd` grades the output for you.

### Running tests without the MCP server (`al-test.cmd`)

```powershell
plugins\al-toolkit\scripts\al-test.cmd "C:\path\to\TestProject" 50150
plugins\al-toolkit\scripts\al-test.cmd "C:\path\to\TestProject" 50150 --testmethods MyTest
plugins\al-toolkit\scripts\al-test.cmd "C:\path\to\TestProject" 50150 --environmenttype Sandbox --environmentname Develop
```

It passes arguments to `altool runtests`, uses `launch.json` for connection details, refuses Production targets, and exits 0 when all tests pass or 1 otherwise. Ignore the summary row with an empty `methodName` when counting test methods.

### Calling AL LSP from CLI (`al-lsp-mcp.cmd --cli`)

```powershell
"%USERPROFILE%\.gemini\config\plugins\bc365-al-toolkit\scripts\al-lsp-mcp.cmd" --cli al_lsp_references '{"filePath":"src/MyFile.al","line":10,"character":20}'
```

### Opt-in: snapshot debugging and profiling (`al-snapshot` / `al-profiling`)

The `al-debugger` and `al-profiler` skills use Microsoft's snapshot debugging and performance profiling MCP proxies. They connect to a Business Central environment and can capture business data, so the plugin does not register them automatically.

Add them to your user Antigravity MCP config (`%USERPROFILE%\.gemini\config\mcp_config.json`) using forward-slash absolute paths to your installed plugin's `al-diag-mcp.cmd`:

```json
{
  "mcpServers": {
    "al-snapshot": {
      "command": "C:/Users/<you>/.gemini/config/plugins/bc365-al-toolkit/scripts/al-diag-mcp.cmd",
      "args": ["snapshot"],
      "env": {
        "AL_ENV_TYPE": "Sandbox",
        "AL_ENV_NAME": "Develop"
      }
    },
    "al-profiling": {
      "command": "C:/Users/<you>/.gemini/config/plugins/bc365-al-toolkit/scripts/al-diag-mcp.cmd",
      "args": ["profiling"],
      "env": {
        "AL_ENV_TYPE": "Sandbox",
        "AL_ENV_NAME": "Develop"
      }
    }
  }
}
```

- `AL_ENV_TYPE` is required (`Sandbox`, `Production`, or `OnPrem`); the launcher refuses to start without it because the proxies default to Production. Add `AL_TENANT` in `env` for a specific tenant.
- Sign in once with `altool auth login` or let the first tool call open Microsoft sign-in.

---

## 5. Updating

After pulling or editing skills, rules, manifests, or scripts:

1. Bump `version` in `plugins/al-toolkit/plugin.json`.
2. Re-run `install-agy-plugin.cmd` from the repository root.
3. Reload or restart Antigravity so the updated plugin and MCP servers take effect.

---

## 6. Troubleshooting

| Symptom | Cause / fix |
|---|---|
| Antigravity `al` or `al-lsp` MCP server fails to start | `mcp_config.json` does not expand `%USERPROFILE%` or `${CLAUDE_PLUGIN_ROOT}` — re-run `install-agy-plugin.cmd` so absolute forward-slash paths are written for your user profile, then reload Antigravity. |
| `al-lsp-mcp.cmd` fails with `python was not found on PATH` | Install Python 3 and ensure `python.exe` is on `PATH`. |
| Old `al-analyst` / `al-developer` / `al-reviewer` / `al-build` behavior in Antigravity | Standalone copies in `%USERPROFILE%\.gemini\config\skills\`, `%USERPROFILE%\.gemini\antigravity\skills\`, or `%USERPROFILE%\.gemini\skills\` shadow the plugin — run `install-agy-plugin.cmd` and delete any legacy standalone AL skill folders. |
| `[find-al-bin] Could not find altool.exe` | Install the AL Development Tools .NET tool or AL Language VS Code extension, or set `AL_BIN` to the folder holding the executables. |
| `error AL1021: The package cache path has not been specified` | No `.alpackages` in the project — download symbols first (`al_downloadsymbols`, or AL: Download Symbols in VS Code). |
| `error AL1022: … could not be found in the package cache` | Symbols are missing or stale for the `application` / `platform` version in `app.json`. |
| Skills load but every build is "NOT VERIFIED" | No AL toolchain found or no symbols are present in `.alpackages`. |
| `al_compile` says "No projects are loaded" | Antigravity started outside an AL project. Call `al_addproject` with the project folder path. |
| `al_*` tools misbehave | Set `AL_MCP_LOGLEVEL=Debug`, restart Antigravity, and inspect `%LOCALAPPDATA%\Microsoft\ALLanguageServer\almcp.log` (or `AL_MCP_LOGFILE`). |

Contributor notes — repository layout, Antigravity manifest constraints, and verification commands — are in [`CLAUDE.md`](CLAUDE.md).
