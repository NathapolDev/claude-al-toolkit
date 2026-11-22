# bc365-al-toolkit

Business Central AL development plugin for **Antigravity (`agy`)**. It registers Microsoft's AL Language MCP server (`al`, 16 tools) and the AL LSP MCP server (`al-lsp`, 7 semantic code intelligence tools), ships always-on Antigravity rules (`rules/AGENTS.md`), and provides 7 specialized AL/BC365 skills:

- **al-analyst** — turns a BC365 requirement into a Solution Design (read-only, no code).
- **al-developer** — implements the design in AL and builds until there are zero errors.
- **al-reviewer** — re-runs the build independently and returns Approve or Request Changes (read-only).
- **al-lsp** — guides semantic AL symbol lookup (`al_lsp_definition`, `al_lsp_references`, `al_lsp_hover`, `al_lsp_document_symbols`, `al_lsp_workspace_symbols`, `al_lsp_signature_help`, `al_lsp_rename_preview`) and `--cli` fallback.
- **bc365-permissionset** — creates and analyzes permission sets (tenant XML and AL `permissionset` objects). Python 3, standard library only.
- **al-debugger** / **al-profiler** — opt-in snapshot debugging and performance profiling on a Business Central environment (requires user-configured `al-snapshot` / `al-profiling` MCP servers).

All pipeline skills defer to the house rules in `references/al-rules.md` (mirrored in `rules/AGENTS.md`), based on the official Microsoft AL guidelines and alguidelines.dev.

## Requirements

- **Windows only.** The launchers are `.cmd` scripts that run Windows binaries.
- **Antigravity (`agy`)**. Both `al` and `al-lsp` run as local stdio MCP servers.
- **Python 3** on `PATH` (`python.exe`, standard library only) — required for `scripts/al-lsp-mcp.py` (`al-lsp`) and `skills/bc365-permissionset/scripts/`.
- Microsoft's AL toolchain, installed separately. The plugin does **not** bundle it. Use either:
  - the AL Development Tools .NET global tool:
    `dotnet tool install -g Microsoft.Dynamics.BusinessCentral.Development.Tools`, or
  - the AL Language VS Code extension (`ms-dynamics-smb.al`).
- Open or point at an AL project folder (containing `app.json` or `*.code-workspace`).

## Install in Antigravity (`agy`)

From the repository root, run:

```cmd
install-agy-plugin.cmd
```

This copies `plugins/al-toolkit` to `%USERPROFILE%\.gemini\config\plugins\bc365-al-toolkit`, rewrites `mcp_config.json` with resolved forward-slash absolute paths to `al-mcp.cmd` and `al-lsp-mcp.cmd`, and archives any loose `al-analyst`, `al-developer`, or `al-reviewer` directories from `%USERPROFILE%\.gemini\config\skills\` into `skills_archived_by_bc365_al_toolkit\`. Restart or reload Antigravity afterwards.

When opening the repository itself in Antigravity, `.agents/plugins.json` also registers the workspace `plugins/` folder directly.

## Configuration (optional environment variables)

| Variable | Purpose |
|---|---|
| `AL_BIN` | Folder that contains `altool.exe` / `alc.exe`; skips auto-discovery |
| `AL_EXTENSIONS_DIR` | VS Code extensions root to search |
| `AL_PROJECT_DIR` | AL project passed to `al` / `al-lsp` (default: current directory or resolved from `filePath`; skipped on `al-mcp.cmd` when it has no `app.json`) |
| `AL_PACKAGECACHE` | Symbol folder for the MCP/LSP servers and builds (default: `<project>\.alpackages`) |
| `AL_ANALYZERS` | Semicolon list of cops for the MCP server and builds, e.g. `CodeCop;PerTenantExtensionCop` |
| `AL_RULESET` | Ruleset file for the MCP server and builds (needs `AL_ANALYZERS` on the MCP server) |
| `AL_MCP_LOGLEVEL` | MCP server log level: `Debug`, `Verbose`, `Normal` (default), `Warning`, `Error` |
| `AL_MCP_LOGFILE` | MCP server log file (default: `%LOCALAPPDATA%\Microsoft\ALLanguageServer\almcp.log`) |

## What this plugin runs, reads, and connects to

The plugin itself contains Markdown skills, `rules/AGENTS.md`, `assets/logo.svg`, JSON manifests (`plugin.json`, `mcp_config.json`), readable batch scripts, a stdlib-only Python LSP MCP bridge (`scripts/al-lsp-mcp.py`), and two Python scripts for permission sets that read and write only the files you name. It does not download anything, contact any server itself, or collect telemetry, and it doesn't change your permission settings.

- **`al` MCP server launch** (`mcp_config.json` → `scripts/al-mcp.cmd`): finds `altool.exe` with `scripts/find-al-bin.cmd`, then runs `altool.exe launchmcpserver <project> --transport stdio` plus any options from the variables above. The `al` server is Microsoft's software; its tools run locally with your credentials and log to `%LOCALAPPDATA%\Microsoft\ALLanguageServer\almcp.log` unless `AL_MCP_LOGFILE` is set.
- **`al-lsp` MCP bridge** (`mcp_config.json` → `scripts/al-lsp-mcp.cmd` → `scripts/al-lsp-mcp.py`): exposes Microsoft's AL Language Server (`scripts/al-lsp.cmd` → `altool.exe launchlspserver`) as 7 stdio MCP tools (and supports `--cli <tool> <json>` fallback). Resolves the project root from `projectPath` or walking up from `filePath` to find `*.code-workspace` / `app.json`, syncs open files with LSP `didOpen`/`didChange` from disk, and returns 1-based line/character locations without modifying files (`al_lsp_rename_preview` only returns edits).
- **Toolchain discovery** (`scripts/find-al-bin.cmd`): reads the environment variables above plus `%USERPROFILE%` and `%LOCALAPPDATA%`, runs `where dotnet` and `dotnet --list-runtimes` to pick a .NET tool folder, and lists VS Code extension folders. It only reads the file system.
- **Build fallback** (`scripts/al-build.cmd`): runs `alc.exe` on your project (or `altool.exe workspace compile` for a `.code-workspace` with a shared symbol cache) and writes temporary logs to `%TEMP%` that are deleted afterwards.
- **Diagnostics proxies — opt-in only** (`scripts/al-diag-mcp.cmd`): runs `altool.exe launchsnapshotmcpproxy` or `launchprofilingmcpproxy` against the environment set in `AL_ENV_TYPE` / `AL_ENV_NAME`. Snapshots and profiles can contain business data; profiles are stored under `%TEMP%\bc-profiling`. Not registered by default — add them explicitly in `%USERPROFILE%\.gemini\config\mcp_config.json`.
- **Call graph** (`scripts/al-graph.cmd`): runs `altool.exe graph extract`, `stitch`, and `query` offline, writing temporary graph files to `%TEMP%` and deleting them afterwards.
- **Test fallback** (`scripts/al-test.cmd`): runs `altool.exe runtests` against the Business Central environment in `launch.json` (or the specified target). Refuses Production targets, doesn't store credentials, and doesn't print `BC_SERVER_*` values.
- **Network access through the `al` MCP server.** Some of Microsoft's tools reach your Business Central environment or Microsoft services when called: `al_auth_login` / `al_auth_logout` (Microsoft Entra sign-in), `al_downloadsymbols` (downloads symbol packages), `al_publish` (deploys to the environment in `launch.json`), and `al_run_tests` (runs tests on that environment). All other tools (`al_compile`, `al_build`, `al_getdiagnostics`, `al_symbolsearch`, `al_symbolrelations`, `al_getnextobjectid`, `al_getpackagedependencies`, `al_inspectpage`, `al_addproject`, `al_searchtranslations`, `al_writetranslation`) work locally.

## License

MIT. See [LICENSE](LICENSE).
