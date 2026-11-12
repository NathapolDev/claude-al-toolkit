# bc365-al-toolkit

Business Central AL development tooling for Claude Code. The plugin registers the
Microsoft AL Language MCP server (`al`) and adds a three-stage skill pipeline:

- **al-analyst** — turns a BC365 requirement into a Solution Design (read-only, no code).
- **al-developer** — implements the design in AL and builds until there are zero errors.
- **al-reviewer** — re-runs the build independently and returns Approve or Request Changes (read-only).

It also includes **bc365-permissionset**, which creates and analyzes permission sets
(tenant XML and AL `permissionset` objects). Its scripts need Python 3, standard library only.

All three pipeline skills follow the house rules in `references/al-rules.md`, which is based on
the official Microsoft AL guidelines and alguidelines.dev.

## Requirements

- **Windows only.** The launchers are `.cmd` scripts that run Windows binaries.
- **Claude Code** (CLI or desktop). The `al` MCP server is a local stdio server, so it
  doesn't run on claude.ai web.
- Microsoft's AL toolchain, installed separately. The plugin does **not** bundle it. Use either:
  - the AL Development Tools .NET global tool:
    `dotnet tool install -g Microsoft.Dynamics.BusinessCentral.Development.Tools`, or
  - the AL Language VS Code extension (`ms-dynamics-smb.al`).
- Start Claude Code from inside an AL project folder (one that contains `app.json`).

## Install

```
/plugin install bc365-al-toolkit@<marketplace>
/reload-plugins
```

Then `claude mcp list` should show `al`.

## Configuration (optional environment variables)

| Variable | Purpose |
|---|---|
| `AL_BIN` | Folder that contains `altool.exe` / `alc.exe`; skips auto-discovery |
| `AL_EXTENSIONS_DIR` | VS Code extensions root to search |
| `AL_PROJECT_DIR` | AL project passed to the MCP server (default: current directory; skipped when it has no `app.json`) |
| `AL_PACKAGECACHE` | Symbol folder for the MCP server and builds (default: `<project>\.alpackages`) |
| `AL_ANALYZERS` | Semicolon list of cops for the MCP server and builds, e.g. `CodeCop;PerTenantExtensionCop` |
| `AL_RULESET` | Ruleset file for the MCP server and builds (needs `AL_ANALYZERS` on the MCP server) |
| `AL_MCP_LOGLEVEL` | MCP server log level: `Debug`, `Verbose`, `Normal` (default), `Warning`, `Error` |
| `AL_MCP_LOGFILE` | MCP server log file (default: `%LOCALAPPDATA%\Microsoft\ALLanguageServer\almcp.log`) |

## What this plugin runs, reads, and connects to

The plugin itself contains only Markdown skills, JSON manifests, seven readable
batch scripts, and two Python scripts for permission sets that read and write only the
files you name. It does not download anything, contact any server itself, or collect
telemetry, and it doesn't change Claude's permission settings.

- **MCP server launch** (`scripts/al-mcp.cmd`): finds
  `altool.exe` with `scripts/find-al-bin.cmd`, then runs
  `altool.exe launchmcpserver <project> --transport stdio` plus any options from the
  variables above. The `al` server is Microsoft's software. Its tools run on your
  machine, with your credentials, and it writes a log to
  `%LOCALAPPDATA%\Microsoft\ALLanguageServer\almcp.log` unless `AL_MCP_LOGFILE` says otherwise.
- **Toolchain discovery** (`scripts/find-al-bin.cmd`): reads the environment variables
  above plus `%USERPROFILE%` and `%LOCALAPPDATA%`, runs `where dotnet` and
  `dotnet --list-runtimes` to pick a .NET tool folder, and lists VS Code extension
  folders (stable, Insiders, Server, OSS, portable, Program Files). It only reads the
  file system and doesn't change anything.
- **Build fallback** (`scripts/al-build.cmd`): runs `alc.exe` on your project and
  writes the `.app` file the compiler produces. It writes a temporary log to `%TEMP%`
  and deletes it after the build. For a folder with a `.code-workspace` and a shared
  symbol cache it runs `altool.exe workspace compile` instead (same temp handling).
- **Language server** (`.lsp.json` → `scripts/al-lsp.cmd`): Claude Code starts
  `altool.exe launchlspserver` for the project the first time it works with an `.al`
  file. It runs locally, reads your project and symbols, and logs to
  `~/.al-mcp/almcp.log`.
- **Diagnostics proxies — only if you add them** (`scripts/al-diag-mcp.cmd`): runs
  `altool.exe launchsnapshotmcpproxy` or `launchprofilingmcpproxy` against the
  environment you set in `AL_ENV_TYPE` / `AL_ENV_NAME`, with your sign-in. Snapshots and
  profiles can contain business data; profiles are stored under `%TEMP%\bc-profiling`.
  The plugin doesn't register these servers.
- **Call graph** (`scripts/al-graph.cmd`): runs `altool.exe graph extract`, `stitch`,
  and `query` on the AL source in the folder you name. It works offline, writes the graph
  to `%TEMP%`, and deletes it when the query finishes.
- **Test fallback** (`scripts/al-test.cmd`): runs `altool.exe runtests`, which connects
  to the Business Central environment in your `launch.json` (or the one you name) with
  your sign-in and runs tests against the apps already published there. It refuses
  Production targets, doesn't store credentials, and doesn't print `BC_SERVER_*` values.
- **Network access through the `al` MCP server.** Some of Microsoft's tools reach
  your Business Central environment or Microsoft services when Claude calls them:
  `al_auth_login` / `al_auth_logout` (Microsoft Entra sign-in), `al_downloadsymbols`
  (downloads symbol packages from your environment), `al_publish` (deploys your
  extension to the environment in your `launch.json`), and `al_run_tests` (runs tests
  on that environment). The server's other tools (`al_compile`, `al_build`,
  `al_getdiagnostics`, `al_symbolsearch`, `al_symbolrelations`, `al_getnextobjectid`,
  `al_getpackagedependencies`, `al_inspectpage`, `al_addproject`,
  `al_searchtranslations`, `al_writetranslation`) work locally. The skills call only
  `al_compile`, `al_getdiagnostics`, `al_downloadsymbols`, `al_symbolsearch`,
  `al_getnextobjectid`, `al_addproject`, `al_getpackagedependencies`, and `al_run_tests`
  (sandbox or container only, against what is already published). They don't publish
  unless you ask, and then only to a sandbox. `al-analyst` may call `al_symbolsearch` with `source = "environment"`, which
  reads your environment's installed apps and can open a Microsoft sign-in; it tells you
  before doing so. Claude Code asks for
  your permission before it calls an MCP tool unless you've allowed it.

## License

MIT. See [LICENSE](LICENSE).
