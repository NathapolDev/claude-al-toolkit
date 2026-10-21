# al-toolkit

Business Central AL development tooling for Claude Code. The plugin registers the
Microsoft AL Language MCP server (`al`) and adds a three-stage skill pipeline:

- **al-analyst** — turns a BC365 requirement into a Solution Design (read-only, no code).
- **al-developer** — implements the design in AL and builds until there are zero errors.
- **al-reviewer** — re-runs the build independently and returns Approve or Request Changes (read-only).

All three skills follow the house rules in `references/al-rules.md`, which is based on
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
/plugin install al-toolkit@<marketplace>
/reload-plugins
```

Then `claude mcp list` should show `al`.

## Configuration (optional environment variables)

| Variable | Purpose |
|---|---|
| `AL_BIN` | Folder that contains `altool.exe` / `alc.exe`; skips auto-discovery |
| `AL_EXTENSIONS_DIR` | VS Code extensions root to search |
| `AL_PROJECT_DIR` | AL project passed to the MCP server (default: current directory) |
| `AL_PACKAGECACHE` | Symbol folder for builds (default: `<project>\.alpackages`) |
| `AL_ANALYZERS` | Semicolon list of cops for builds, e.g. `CodeCop;PerTenantExtensionCop` |

## What this plugin runs, reads, and connects to

The plugin itself contains only Markdown skills, JSON manifests, and three readable
batch scripts. It does not download anything, contact any server itself, or collect
telemetry, and it doesn't change Claude's permission settings.

- **MCP server launch** (`scripts/al-mcp.cmd`): finds
  `altool.exe` with `scripts/find-al-bin.cmd`, then runs
  `altool.exe launchmcpserver --transport stdio <project>`. The `al` server is
  Microsoft's software. Its tools run on your machine, with your credentials.
- **Toolchain discovery** (`scripts/find-al-bin.cmd`): reads the environment variables
  above plus `%USERPROFILE%` and `%LOCALAPPDATA%`, runs `where dotnet` and
  `dotnet --list-runtimes` to pick a .NET tool folder, and lists VS Code extension
  folders (stable, Insiders, Server, OSS, portable, Program Files). It only reads the
  file system and doesn't change anything.
- **Build fallback** (`scripts/al-build.cmd`): runs `alc.exe` on your project and
  writes the `.app` file the compiler produces. It writes a temporary log to `%TEMP%`
  and deletes it after the build.
- **Network access through the `al` MCP server.** Some of Microsoft's tools reach
  your Business Central environment or Microsoft services when Claude calls them:
  `al_auth_login` / `al_auth_logout` (Microsoft Entra sign-in), `al_downloadsymbols`
  (downloads symbol packages from your environment), `al_publish` (deploys your
  extension to the environment in your `launch.json`), and `al_run_tests` (runs tests
  on that environment). The skills call only `al_compile`, `al_getdiagnostics`,
  `al_downloadsymbols`, and `al_symbolsearch`; they never publish. Claude Code asks for
  your permission before it calls an MCP tool unless you've allowed it.

## License

MIT. See [LICENSE](LICENSE).
