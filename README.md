# BC365 AL Toolkit

A Windows plugin for **Codex and Claude Code**, bundling Microsoft's local `al` MCP
server and three Business Central AL skills:

- **al-analyst**: requirement analysis and Solution Design; read-only.
- **al-developer**: implementation with observed compiler diagnostics.
- **al-reviewer**: read-only review with independent compiler verification.

Includes shared [AL rules](plugins/al-toolkit/references/al-rules.md), automatic
toolchain discovery, and an `alc.exe` compiler fallback. Microsoft binaries are not bundled.

## Requirements

- Windows and a local Codex executor or Claude Code. This stdio server needs local
  tooling; it cannot operate as a hosted web connector.
- Microsoft's AL Development Tools .NET global tool or AL Language VS Code extension
  (`ms-dynamics-smb.al`). Install the standalone tool with:

  ```powershell
  dotnet tool install -g Microsoft.Dynamics.BusinessCentral.Development.Tools
  ```

- An AL project with `app.json`; matching dependency symbols are needed to compile.
  The .NET tool needs its matching ASP.NET Core runtime. Discovery supports the
  net10.0 and net8.0 global-tool layouts.

## Codex installation

Commands target **Codex CLI 0.164.0**. The supported `.codex-plugin/plugin.json`
format explicitly declares the three skills and the Codex MCP configuration.

```powershell
codex plugin marketplace add C:\claude-al-toolkit
codex plugin list --marketplace al-toolkit-marketplace --available --json
codex plugin add bc365-al-toolkit@al-toolkit-marketplace
```

For Git distribution, push the changes first, then register the intended branch:

```powershell
codex plugin marketplace add NathapolDev/claude-al-toolkit --ref feat/codex-plugin
```

Open Codex in the AL workspace as usual. Each toolkit skill identifies the project
from the workspace or selected files, invokes its bundled PowerShell initializer to
set `AL_PROJECT_DIR` for shell commands, and calls Microsoft's `al_addproject` MCP
tool before using project tools. No machine or user environment setup is needed.
If several AL apps match the task, the skill selects by the requested/selected files
or asks which project to use.

Codex starts the bundled AL server without a default project. The skill loads the
selected project into the running MCP session, which Microsoft's server supports
without a restart.

Inspect `/mcp` in Codex to confirm the plugin's `al` server connected, then invoke:

```text
$al-analyst Analyze this Business Central requirement.
$al-developer Implement the recommended approach and verify compilation.
$al-reviewer Review these AL changes and independently verify diagnostics.
```

Skills also support automatic selection from Thai or English requests. Codex lists
them with a plugin namespace, such as `bc365-al-toolkit:al-analyst`; select this
plugin's skill in the picker if another plugin exposes the same base names.
Each skill includes `agents/openai.yaml` for its Codex name and example prompt.

## Claude Code installation

The original Claude marketplace and MCP entry remain available:

```text
/plugin marketplace add C:\claude-al-toolkit
/plugin install bc365-al-toolkit@al-toolkit-marketplace
/reload-plugins
```

Start Claude Code in the AL project and inspect `claude mcp list`. Invoke
`/bc365-al-toolkit:al-analyst`, `/bc365-al-toolkit:al-developer`, or
`/bc365-al-toolkit:al-reviewer`. `AL_PROJECT_DIR` overrides the default project here too.

## Configuration and compiler fallback

Variables are read at launch:

| Variable | Purpose |
|---|---|
| `AL_PROJECT_DIR` | Skill-selected absolute AL project for shell/compiler commands |
| `AL_BIN` | Folder containing `altool.exe` / `alc.exe` |
| `AL_EXTENSIONS_DIR` | Alternate VS Code extensions root |
| `VSCODE_EXTENSIONS` | Additional VS Code extensions root |
| `AL_PACKAGECACHE` | Build fallback symbols; default `<project>\.alpackages` |
| `AL_ANALYZERS` | Build fallback cops, e.g. `CodeCop;PerTenantExtensionCop` |

Discovery searches overrides, the .NET global tool, and standard VS Code
stable/Insiders/Server/OSS, portable, and Program Files locations. Extension folders
are considered by modification date, newest first within each root.

To build without MCP, run from this checkout:

```powershell
$env:AL_ANALYZERS = 'CodeCop;PerTenantExtensionCop'
& .\plugins\al-toolkit\scripts\al-build.cmd 'C:\path\to\AlProject'
```

Use `CodeCop;AppSourceCop` for AppSource. The wrapper grades compiler output and
returns nonzero on AL errors; `alc.exe` alone can exit zero on compilation errors.
It produces an `.app` and deletes its temporary diagnostic log. No observed compiler
result means **NOT VERIFIED**.

## Package structure

```text
.agents/plugins/marketplace.json      Codex marketplace
.claude-plugin/marketplace.json       Claude marketplace
plugins/al-toolkit/
  .codex-plugin/plugin.json           Codex manifest, UI, skills and MCP paths
  .claude-plugin/plugin.json          Claude manifest and icon
  .mcp.codex.json                     Codex stdio server and forwarded variables
  .mcp.json                           Claude stdio server
  scripts/al-mcp-codex.cmd             Starts an empty Codex AL MCP session
  scripts/Initialize-AlProject.ps1     Finds app.json and sets the shell variable
  references/project-session.md        Shared per-skill project initialization
  scripts/al-mcp.cmd                   Shared MCP launcher
  scripts/find-al-bin.cmd              Shared toolchain resolver
  scripts/al-build.cmd                 Compiler fallback
  skills/*/SKILL.md                    Three shared workflows
  skills/*/agents/openai.yaml          Codex skill metadata
  references/al-rules.md               Shared AL defaults
```

## Troubleshooting and updates

- MCP startup fails: inspect `/mcp` and verify the skill selected a folder containing
  `app.json` and that `al_addproject` succeeded. Each skill sets its own shell variable.
- Missing toolchain: install Microsoft's tooling or set `AL_BIN` /
  `AL_EXTENSIONS_DIR`. Discovery runs at every server launch.
- Missing/stale symbols: download matching symbols through AL tooling. Packaging
  validation does not authenticate or download symbols.
- Skills work but builds are unverified: check the project, symbols, runtime and
  compiler output; skill discovery alone does not verify MCP connectivity.

Bump both plugin manifests when releasing. For Git marketplaces, push and run
`codex plugin marketplace upgrade al-toolkit-marketplace`, then
`codex plugin add bc365-al-toolkit@al-toolkit-marketplace` and restart the host.
For local updates, re-run the add command after editing. Claude consumers use
`/plugin marketplace update al-toolkit-marketplace` and
`/plugin update bc365-al-toolkit@al-toolkit-marketplace`.

See [AGENTS.md](AGENTS.md) for contributor guidance and the
[plugin README](plugins/al-toolkit/README.md) for runtime access details.
Codex references: [packaging](https://developers.openai.com/plugins/build/plugins) and
[official example](https://github.com/openai/plugins/tree/main/plugins/openai-developers).

MIT. See [LICENSE](plugins/al-toolkit/LICENSE).
