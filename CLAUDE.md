# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

This is **not** an AL project — it is a Claude Code **plugin marketplace** whose payload
is tooling for Business Central AL development. There is no application source, no test
suite, and no package manager. The deliverables are Markdown skills, JSON manifests, and
Windows `.cmd` launcher scripts that get installed onto *other* machines.

Consequence: "does it build" here means "does the plugin install and do the scripts
resolve on a clean machine", not "does a compiler run".

## Layout and how the pieces bind

```
.claude-plugin/marketplace.json          marketplace manifest; plugins[].source -> ./plugins/al-toolkit
plugins/al-toolkit/
  .claude-plugin/plugin.json             plugin manifest (name, version, author)
  .mcp.json                              registers the `al` MCP server (auto-detected at plugin root)
  scripts/find-al-bin.cmd                shared AL toolchain path resolver
  scripts/al-mcp.cmd                     MCP server launcher  -> altool.exe launchmcpserver
  scripts/al-build.cmd                   build fallback       -> alc.exe
  references/al-rules.md                 canonical AL house rules (single source of truth)
  skills/{al-analyst,al-developer,al-reviewer}/SKILL.md
```

Two invariants hold the distribution together:

1. **Every path is `${CLAUDE_PLUGIN_ROOT}`-relative.** `.mcp.json` and all three
   `SKILL.md` files reference the plugin root variable, never an absolute or
   user-specific path. Introducing a machine-specific path breaks installs elsewhere —
   this is the single most common way to regress this repo.
2. **The AL toolchain is never bundled.** `altool.exe` / `alc.exe` come from Microsoft's
   AL Development Tools .NET global tool (`Microsoft.Dynamics.BusinessCentral.Development.Tools`,
   no VS Code needed) or the AL Language VS Code extension (`ms-dynamics-smb.al-*`),
   resolved at *launch time*, not install time, so updates cannot break a registered command.

### Path resolution (`find-al-bin.cmd`)

Both runnable scripts delegate discovery to `find-al-bin.cmd <exeName>`, which prints the
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
logic to `al-mcp.cmd` or `al-build.cmd`.

Environment overrides: `AL_BIN`, `AL_EXTENSIONS_DIR`, `AL_PROJECT_DIR` (project handed to
the MCP server, default `%CD%`), `AL_PACKAGECACHE` (default `<project>\.alpackages`),
`AL_ANALYZERS` (semicolon list of cop names, mapped to
`Microsoft.Dynamics.Nav.<Cop>.dll` next to `alc.exe`, else `..\Analyzers\` for the
legacy `bin\win32` layout).

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

All three defer to `references/al-rules.md` as canonical. Put AL coding rules there, not
in the individual skills; the skills should only reference it.

Each skill has a two-tier build strategy that must stay in sync across
`al-developer` and `al-reviewer`: primary = `al` MCP tools (deferred — load via
`ToolSearch` with `select:al_compile,al_getdiagnostics,...`), fallback =
`${CLAUDE_PLUGIN_ROOT}/scripts/al-build.cmd`. If neither can run, the skills must report
the build as NOT VERIFIED rather than assume success.

## Verifying changes

There is no test runner. Verify by exercising the scripts directly (PowerShell 7):

```powershell
$s = "plugins\al-toolkit\scripts"

# resolver: happy path, override, and failure path
cmd /c "$s\find-al-bin.cmd altool.exe"          # -> .NET tool or extension bin, exit 0
cmd /c "set PATH=C:\Windows\system32&& $s\find-al-bin.cmd altool.exe"  # no dotnet -> extension
cmd /c "$s\find-al-bin.cmd nope.exe"            # -> stderr guidance, exit 1
$env:AL_BIN = "C:\bogus"; cmd /c "$s\find-al-bin.cmd alc.exe"   # warns, falls through

# build wrapper: guard, failure grading, analyzer mapping
cmd /c "$s\al-build.cmd `"C:\path\to\AlProject`""              # -> BUILD OK / BUILD FAILED
$env:AL_ANALYZERS = "CodeCop;PerTenantExtensionCop"

# MCP launcher: start and kill; expect "AL MCP Server starting in STDIO mode..."
cmd /c "$s\al-mcp.cmd"
```

Full install check (do this before distributing):

```
/plugin marketplace add "C:\BPC BC Project\claude-al-toolkit"
/plugin install al-toolkit@al-toolkit-marketplace
/reload-plugins
```

Then `claude mcp list` must show `al`. Claude Code has to be started from inside an AL
project folder — `altool` needs a project path to resolve symbols against.

## Distribution

Consumers install via `/plugin marketplace add <git-url | local path | UNC share>` then
`/plugin install al-toolkit@al-toolkit-marketplace`. Installed skills are namespaced
(`/al-toolkit:al-analyst`, etc.) and also auto-trigger from natural language via each
`SKILL.md` frontmatter `description`.

Bump `version` in `plugins/al-toolkit/.claude-plugin/plugin.json` when shipping changes,
otherwise version-pinned installs won't pick them up. Consumers then run
`/plugin marketplace update al-toolkit-marketplace` and
`/plugin update al-toolkit@al-toolkit-marketplace`.

## Constraints

- **Windows-only by design** — launchers are `.cmd` and resolve `altool.exe` /
  `alc.exe` Windows binaries. Keep scripts as batch; PowerShell 7
  (`pwsh`) is the preferred shell for *running* them, not for rewriting them.
- Batch scripts use `setlocal enabledelayedexpansion` with `!VAR!` inside `for` bodies —
  preserve this when editing, `%VAR%` expands at parse time and silently misbehaves.
- This repo is currently **not a git repository**; the git-based install path in
  `README.md` requires `git init` and a push first.
