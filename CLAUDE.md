# CLAUDE.md

This file provides guidance to coding agents (**Antigravity** and **Claude Code**) when working with code in this repository.

## What this repo is

This is **not** an AL project — it is a dual-harness **plugin repository** (**Antigravity (`agy`)** and **Claude Code**) whose payload is tooling for Microsoft Dynamics 365 Business Central AL development. There is no AL application source and no package manager; the deliverables are Markdown skills, rules, JSON manifests, Windows `.cmd` / PowerShell scripts, and stdlib-only Python scripts that get installed onto *other* machines.

Consequence: "does it build" here means "does the plugin install cleanly, do the manifests/frontmatter validate, and do the MCP/LSP/build scripts resolve and run on a clean machine", not "does an AL app compile inside this repo".

## Layout and how the pieces bind

```
.agents/plugins.json                     Antigravity workspace plugin registry -> plugins
.claude-plugin/marketplace.json          Claude Code marketplace manifest -> ./plugins/al-toolkit
install-agy-plugin.ps1                   Antigravity global installer (copies plugin, rewrites mcp_config.json, archives loose skills)
install-agy-plugin.cmd                   Batch entry point -> powershell -NoProfile -ExecutionPolicy Bypass -File install-agy-plugin.ps1
plugins/al-toolkit/
  plugin.json                            Antigravity plugin manifest (strictly valid agy top-level fields only)
  mcp_config.json                        Antigravity MCP config -> `al` (al-mcp.cmd) and `al-lsp` (al-lsp-mcp.cmd)
  assets/logo.svg                        128x128 transparent-bg badge SVG (10% margin baked in)
  rules/AGENTS.md                        Always-on Antigravity rules (plain Markdown, no frontmatter, <24 KB)
  .claude-plugin/plugin.json             Claude Code plugin manifest (name, version, author)
  .mcp.json                              Claude Code MCP config -> ${CLAUDE_PLUGIN_ROOT}/scripts/al-mcp.cmd
  .lsp.json                              Claude Code native LSP config for .al files -> ${CLAUDE_PLUGIN_ROOT}/scripts/al-lsp.cmd
  scripts/find-al-bin.cmd                shared AL toolchain path resolver
  scripts/al-mcp.cmd                     AL MCP server launcher -> altool.exe launchmcpserver
  scripts/al-lsp.cmd                     AL LSP launcher -> altool.exe launchlspserver
  scripts/al-lsp-mcp.py                  Python 3 stdlib LSP-to-MCP stdio bridge + --cli mode wrapping al-lsp.cmd
  scripts/al-lsp-mcp.cmd                 Batch wrapper checking python and launching al-lsp-mcp.py
  scripts/al-build.cmd                   build fallback -> alc.exe, or altool workspace compile
  scripts/al-test.cmd                    test fallback -> altool.exe runtests
  scripts/al-graph.cmd                   call-graph query -> altool graph extract/stitch/query
  scripts/al-diag-mcp.cmd                opt-in proxies -> launchsnapshotmcpproxy | launchprofilingmcpproxy
                                         (NOT registered by default; users opt in manually)
  references/al-rules.md                 canonical AL house rules (single source of truth)
  skills/{al-analyst,al-developer,al-reviewer}/SKILL.md
  skills/al-lsp/SKILL.md                 Antigravity AL LSP MCP + CLI skill
  skills/{al-debugger,al-profiler}/SKILL.md
  skills/bc365-permissionset/            permission set skill + stdlib-only Python scripts
```

Core invariants that hold the distribution together:

1. **Portable paths — harness-aware rules:**
   - Claude Code manifests (`.mcp.json`, `.lsp.json`) use `${CLAUDE_PLUGIN_ROOT}`-relative paths.
   - All `SKILL.md` files use **portable relative paths** resolved relative to the directory containing the loaded `SKILL.md` (`../../references/al-rules.md`, `../../scripts/al-build.cmd`, etc.; `./scripts/...` and `./references/...` inside `bc365-permissionset/SKILL.md`), with `${CLAUDE_PLUGIN_ROOT}` fallback guidance for Claude Code. Never hardcode machine-specific paths inside `SKILL.md`.
   - Antigravity `mcp_config.json` does **not** expand `${CLAUDE_PLUGIN_ROOT}` or environment variables like `%USERPROFILE%`. The repo's `plugins/al-toolkit/mcp_config.json` points to the repo scripts for workspace discovery (`.agents/plugins.json`), and `install-agy-plugin.ps1` rewrites the installed `%USERPROFILE%\.gemini\config\plugins\bc365-al-toolkit\mcp_config.json` to the current user's resolved forward-slash absolute paths (`<USERPROFILE>/.gemini/config/plugins/bc365-al-toolkit/scripts/...`).
2. **Strict Antigravity manifest & rule constraints:**
   - `plugins/al-toolkit/plugin.json` must contain **only** valid Antigravity top-level fields (`name`, `displayName`, `version`, `description`, `logo`, `author`, `suggestedPrompts`, `homepage`, `repository`, `disabled`) — unknown fields are silently discarded. Keep `.claude-plugin/plugin.json`, `.mcp.json`, and `.lsp.json` intact for Claude Code compatibility.
   - `plugins/al-toolkit/rules/AGENTS.md` must be plain Markdown with **no YAML frontmatter** and strictly **under 24 KB (24,000 bytes)**, synced with `references/al-rules.md`.
3. **The AL toolchain is never bundled.** `altool.exe` / `alc.exe` come from Microsoft's AL Development Tools .NET global tool (`Microsoft.Dynamics.BusinessCentral.Development.Tools`, no VS Code needed) or the AL Language VS Code extension (`ms-dynamics-smb.al-*`), resolved at *launch time*, not install time, so updates cannot break a registered command.

### Path resolution (`find-al-bin.cmd`)

Runnable AL batch scripts delegate discovery to `find-al-bin.cmd <exeName>`, which prints the
resolved bin folder to stdout (exit 0) or a diagnostic to stderr (exit 1). Callers
capture it with `for /f`. Search order: `%AL_BIN%` → `%AL_EXTENSIONS_DIR%` → .NET global
tool store (`%USERPROFILE%\.dotnet\tools\.store\...\tools\net10.0|net8.0\any`, only the
TFM whose ASP.NET Core runtime is installed) → `%VSCODE_EXTENSIONS%` → VS Code
stable/Insiders/Server/OSS user roots → portable and Program Files installs; newest
`ms-dynamics-smb.al-*` folder wins within a root, accepting `bin\` (AL 18+) or
`bin\win32` (older).

Batch gotcha: piping from a command that isn't on PATH inside a `call`ed block aborts the
whole script (exit 255) — the resolver guards with `where dotnet` before piping.

Add new machine layouts to the candidate list in that one script — do not add lookup
logic to `al-mcp.cmd`, `al-lsp.cmd`, or `al-build.cmd`.

Environment overrides: `AL_BIN`, `AL_EXTENSIONS_DIR`, `AL_PROJECT_DIR` (project handed to
the MCP/LSP servers, default `%CD%`; skipped on `al-mcp.cmd` when it has no `app.json`),
`AL_PACKAGECACHE` (default `<project>\.alpackages`), `AL_ANALYZERS` (semicolon list of cop
names; for `alc.exe` mapped to `Microsoft.Dynamics.Nav.<Cop>.dll` next to `alc.exe`, else
`..\Analyzers\` for the legacy `bin\win32` layout; for the MCP server passed as one
`--codeanalyzers ${<Cop>}` per cop), `AL_RULESET` (`--ruleset` / `/ruleset:`),
`AL_MCP_LOGLEVEL` (`--loglevel`), `AL_MCP_LOGFILE` (`--logfile`; default log is
`%LOCALAPPDATA%\Microsoft\ALLanguageServer\almcp.log`).

### `altool launchmcpserver` argument gotchas

Both fail silently, so keep them when editing `al-mcp.cmd`:

- **Project path first.** `--packagecachepath` takes several values and swallows a
  trailing project path; the server then starts with no project and every `al_compile`
  answers "No projects are loaded".
- **Analyzers as `${CodeCop}`.** A bare `CodeCop` is accepted and ignored. A ruleset has
  no effect on the MCP server unless analyzers are enabled.

`al-mcp.cmd` writes only to stderr — stdout is the MCP stdio channel.

### `al-lsp-mcp.py` & `al-lsp-mcp.cmd` (Antigravity LSP bridge)

- Python 3 **stdlib only** (`json`, `sys`, `os`, `subprocess`, `threading`, `pathlib`, `urllib.parse`, `urllib.request`) — zero external packages.
- Speaks MCP stdio (`protocolVersion: "2024-11-05"`, newline-delimited JSON-RPC over stdin/stdout; logs to stderr) **and** single-shot `--cli <tool_name> <json_args_or_file>` mode.
- Manages a lazy `LspSession` running `cmd /c al-lsp.cmd` with `AL_PROJECT_DIR` set to the resolved workspace root (`projectPath` -> walk up from `filePath` for `*.code-workspace` or `app.json` -> `AL_PROJECT_DIR` -> `os.getcwd()`). Restart the child LSP if a subsequent call targets a different project root.
- Translates MCP calls into `Content-Length`-framed LSP JSON-RPC, auto-sending `textDocument/didOpen` / `textDocument/didChange` when a file changes on disk, and converts between 1-based tool inputs and 0-based LSP coordinates.
- Exposes 7 tools: `al_lsp_definition`, `al_lsp_references`, `al_lsp_hover`, `al_lsp_document_symbols`, `al_lsp_workspace_symbols`, `al_lsp_signature_help`, `al_lsp_rename_preview`.

### `al-build.cmd` workspace mode and `al-test.cmd`

- `altool workspace compile` takes **one** `--packagecachepath` for every project
  (default `<workspace dir>\.alpackages`), so workspace mode runs only when that shared
  cache exists; otherwise the script falls back to `alc.exe`. Its `--analyzers` wants a
  single comma list (`CodeCop,PTECop`) — repeating the option or using spaces fails. Its
  exit code is meaningful (unlike `alc.exe`); the script also checks the per-project
  error logs with `^ *"severity": "Error"` — a bare `"severity": "Error"` also matches
  `"defaultSeverity"`.
- `altool runtests` returns 0/1 reliably. Its `data.results[]` includes a codeunit
  summary row with an empty `methodName`, so `data.passed` / `data.failed` overcount.
- `al-lsp.cmd` passes `--workspacefile` when the project folder has a `.code-workspace`,
  else the folder when it has `app.json` (project before `--packagecachepath`, as for
  MCP). Claude Code expands `${CLAUDE_PLUGIN_ROOT}` in `.lsp.json` `command` and runs the
  `.cmd` directly; Antigravity calls it indirectly via `al-lsp-mcp.cmd`. When writing an
  LSP test client in PowerShell, find the header end with
  `IndexOf("`r`n`r`n", [StringComparison]::Ordinal)` — the culture-sensitive default
  mis-matches `\r\n` on .NET 5+.
- `altool graph query` selectors match object **names**: `obj:<Object Name>` and
  `obj:<Object Name>#<Procedure>`. `obj:<ID>`, `obj:Object.Procedure`, wildcards, and bare
  procedure names return "0 node(s)" with exit 0. Calls into apps without source in the
  extracted folder (base app, test libraries) are dropped, not reported.
- Batch gotcha: `exit /b 1` inside a nested `( )` block can return 0 when the script is
  run directly (not via `call`). `al-test.cmd` routes refusals through labels and exits at
  top level — keep that pattern for new error paths.

### `alc.exe` always exits 0

Even on compile errors. `al-build.cmd` therefore captures output to a temp log, prints it,
and grades it with `findstr /r "error [A-Z][A-Z]*[0-9][0-9]*:"` — matching real
diagnostics while ignoring `warning`/`info` lines — then emits `BUILD OK` (exit 0) or
`BUILD FAILED` (exit 1). Never call `alc.exe` directly and trust its exit code, and keep
that regex intact when touching the script.

## The skill pipeline

`al-analyst` → `al-developer` → `al-reviewer` is a deliberate handoff chain: analyst
produces a Solution Design (read-only, no code), developer implements it and must reach a
verified zero-error build, reviewer independently re-runs the build and returns Approve /
Request Changes (read-only, no edits). Each `SKILL.md` ends with a fixed Markdown output
format that the next stage consumes — changing one stage's output headings means updating
the consumer's expectations.

All pipeline skills defer to `references/al-rules.md` as canonical (and `rules/AGENTS.md`
mirrors it for Antigravity). Put AL coding rules in `references/al-rules.md` (and keep
`rules/AGENTS.md` in sync, under 24 KB), not duplicated in individual skills.

Each pipeline skill keeps its two-tier build/test strategy in sync across `al-developer`
and `al-reviewer`:
- **Build primary:** `al` MCP tools (`call_mcp_tool` in Antigravity; `ToolSearch` with `select:al_compile,al_getdiagnostics,...` in Claude Code). **Fallback:** `../../scripts/al-build.cmd`.
- **Tests primary:** `al_run_tests`. **Fallback:** `../../scripts/al-test.cmd`.
- **LSP code intelligence:** `al-lsp` MCP tools (`al_lsp_definition`, `al_lsp_references`, `al_lsp_hover`, `al_lsp_document_symbols`, `al_lsp_workspace_symbols`, `al_lsp_signature_help`, `al_lsp_rename_preview`), CLI fallback `../../scripts/al-lsp-mcp.cmd --cli <tool> "<json>"`, or Claude Code's native `LSP` tool.
- If neither build or test tier can run, report `NOT VERIFIED` / `TESTS NOT RUN` rather than assuming success.

## Verifying changes

There is no test runner. Verify by validating manifests/skills and exercising the installer and scripts directly (PowerShell 7):

```powershell
# 1. Antigravity install & JSON validation
cmd /c "d:\claude-al-toolkit\install-agy-plugin.cmd"
# Confirm %USERPROFILE%\.gemini\config\plugins\bc365-al-toolkit exists,
# mcp_config.json has resolved forward-slash commands, and any loose
# al-analyst/al-developer/al-reviewer folders were moved to skills_archived_by_bc365_al_toolkit.

$s = "plugins\al-toolkit\scripts"

# 2. Resolver: happy path, override, and failure path
cmd /c "$s\find-al-bin.cmd altool.exe"          # -> .NET tool or extension bin, exit 0
cmd /c "set PATH=C:\Windows\system32&& $s\find-al-bin.cmd altool.exe"  # no dotnet -> extension
cmd /c "$s\find-al-bin.cmd nope.exe"            # -> stderr guidance, exit 1
$env:AL_BIN = "C:\bogus"; cmd /c "$s\find-al-bin.cmd alc.exe"   # warns, falls through

# 3. Build wrapper: guard, failure grading, analyzer mapping
cmd /c "$s\al-build.cmd `"C:\path\to\AlProject`""              # -> BUILD OK / BUILD FAILED
$env:AL_ANALYZERS = "CodeCop;PerTenantExtensionCop"
$env:AL_RULESET = "C:\path\to\my.ruleset.json"                   # missing file -> warns, skipped

# 4. AL MCP & AL LSP MCP stdio checks:
# Drive al-mcp.cmd (initialize + tools/list -> 16 tools; compile from AL project -> succeeded: true)
# Drive al-lsp-mcp.cmd (initialize + tools/list -> 7 al_lsp_* tools; --cli test on a temp AL project)
```

Tests (`al-test.cmd`) need a sandbox with the test app published. Check: a passing method
exits 0, a failing one exits 1, an unknown environment exits 1, and `--environmenttype
Production` / a Production `launch.json` / no target at all are refused with exit 1 —
run the script directly (not via `call`) when checking exit codes.

For Claude Code full install verification:

```
/plugin marketplace add "D:\claude-al-toolkit"
/plugin install bc365-al-toolkit@al-toolkit-marketplace
/reload-plugins
```

Then `claude mcp list` must show `al`.

## Distribution

- **Antigravity (`agy`):** users clone/copy this repo and run `install-agy-plugin.cmd` (for global `%USERPROFILE%\.gemini\config\plugins\bc365-al-toolkit` installation) or open the repo directly where `.agents/plugins.json` exposes `plugins/`.
- **Claude Code:** consumers install via `/plugin marketplace add <git-url | local path | UNC share>` then `/plugin install bc365-al-toolkit@al-toolkit-marketplace`. Installed skills are namespaced (`/bc365-al-toolkit:al-analyst`, etc.) and auto-trigger via `SKILL.md` frontmatter `description`.

Bump `version` in **both** `plugins/al-toolkit/plugin.json` and `plugins/al-toolkit/.claude-plugin/plugin.json` when shipping changes.

## Constraints

- **Windows-only by design** — launchers are `.cmd` and resolve `altool.exe` /
  `alc.exe` Windows binaries. Keep scripts as batch (plus `install-agy-plugin.ps1` and
  Python 3 stdlib scripts); PowerShell 7 (`pwsh`) is the preferred shell for *running*
  them, not for rewriting `.cmd` scripts.
- Batch scripts use `setlocal enabledelayedexpansion` with `!VAR!` inside `for` bodies —
  preserve this when editing, `%VAR%` expands at parse time and silently misbehaves.
