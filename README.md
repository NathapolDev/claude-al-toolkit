# AL Toolkit for Codex

A Codex plugin for Microsoft Dynamics 365 Business Central AL development.
It bundles the official AL MCP launcher, a compiler fallback, and three skills:

| Skill | Result |
|---|---|
| `al-analyst` | Read-only requirement analysis and solution design |
| `al-developer` | Implementation with observed compiler diagnostics |
| `al-reviewer` | Read-only review with independent build verification |

Shared AL standards live in `plugins/al-toolkit/references/al-rules.md`.
Claude Code installation remains supported through the original marketplace.

## Requirements on each machine

- Windows with Codex CLI supporting `codex plugin add` and marketplace commands
  (tested with 0.162.0), or a compatible Codex desktop plugin host.
- Git for installation and updates from GitHub; repository access if it is private.
- VS Code with Microsoft's AL Language extension that includes `altool.exe`
  and supports STDIO MCP and `al_addproject` (tested with AL 18.1).
- AL project dependencies downloaded into `.alpackages` before compilation.

The plugin does not bundle Microsoft binaries, credentials, or symbol packages.
The included `.cmd` launchers support Windows; macOS/Linux execution is not supported
by this package. Skills can still be read on those systems, but builds are unverified.

## Install on another machine

Once this branch has been pushed to GitHub, run:

```powershell
codex plugin marketplace add NathapolDev/claude-al-toolkit --ref codexaltools
codex plugin add al-toolkit@codex-al-toolkit
codex plugin list --json
```

Restart Codex or start a fresh session in your AL project. In a desktop host,
select the **Codex AL Toolkit** marketplace in Plugins and install **AL Toolkit**.
If your CLI lacks the commands above, update Codex first.

For local testing, copying, or a network share, add the repository root:

```powershell
codex plugin marketplace add "D:\path with spaces\claude-al-toolkit"
codex plugin add al-toolkit@codex-al-toolkit
```

The marketplace is `.agents/plugins/marketplace.json`. Paths resolve from the
repository root. Codex copies the payload into its plugin cache; no machine-specific
paths are embedded in the package.

## Use

Select a skill from Codex's skill picker, or ask in Thai or English:

- "Use al-analyst to analyze this AL requirement."
- "Use al-developer to implement this change and verify compiler diagnostics."
- "Use al-reviewer to review these changes before merge."

The MCP server starts without a project, because its working directory is the
installed plugin. The skills call `al_addproject`
with the intended AL project folder, and pass `projectPath` to later calls.
They resolve bundled references and fallback scripts relative to their installed
`SKILL.md`, including paths containing spaces.

If the MCP connection is unavailable, the developer/reviewer can run:

```powershell
& "<installed-plugin>\scripts\al-build.cmd" "C:\path\to\ALProject"
```

Set `AL_ANALYZERS=CodeCop;PerTenantExtensionCop` for PTE, or
`CodeCop;AppSourceCop` for AppSource. Read diagnostics as well as the exit status.
If neither MCP nor the fallback can compile, the skills report **NOT VERIFIED**.
Publishing is not part of installation; production publishing is prohibited by
these skills. Test codeunits are generated only when requested.

## Toolchain locations

The resolver searches `AL_BIN`, `AL_EXTENSIONS_DIR`, `VSCODE_EXTENSIONS`, standard
VS Code/Insiders/Server/OSS user roots, then portable/system installation roots.
It supports both `bin\win32` and the current `bin` executable layout.
It resolves again on each launch, so extension updates do not require editing MCP paths.

For a custom location, set one override before starting Codex:

```powershell
$env:AL_EXTENSIONS_DIR = "D:\VS Code extensions"
# Or point directly to the folder containing altool.exe and alc.exe:
$env:AL_BIN = "D:\tools\AL\bin"
```

| Variable | Purpose |
|---|---|
| `AL_BIN` | Explicit folder containing AL executables |
| `AL_EXTENSIONS_DIR` / `VSCODE_EXTENSIONS` | Custom extension root |
| `AL_PROJECT_DIR` | Optional project loaded when MCP starts; otherwise use `al_addproject` |
| `AL_PACKAGECACHE` | Fallback symbol cache; defaults to `<project>\.alpackages` |
| `AL_ANALYZERS` | Semicolon-separated analyzer names for the fallback |

Use user environment settings for persistent overrides and restart Codex afterward.
Do not put a particular machine's paths or secrets into plugin manifests.

## Update every installed machine

Publish changes to the tracked branch, then run on each machine:

```powershell
codex plugin marketplace upgrade codex-al-toolkit
codex plugin add al-toolkit@codex-al-toolkit
```

Restart Codex/start a fresh session and confirm the version with
`codex plugin list --json`. Re-running `plugin add` refreshes the installed payload;
there is no `codex plugin update` command in the tested CLI.
For local/share installations, replace or pull the source folder first, then re-run
`plugin add`; marketplace upgrade refreshes Git sources only.

For a release, bump the same version in both manifests:

- `plugins/al-toolkit/.codex-plugin/plugin.json`
- `plugins/al-toolkit/.claude-plugin/plugin.json`

Keep marketplace/plugin names stable across releases. After merging into `main`,
new installations can track `--ref main`. Existing machines tracking `codexaltools`
keep following that branch until their marketplace source is changed.

## Verify packaging

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\Test-CodexPlugin.ps1
```

This installs from a relocated path containing spaces, verifies the cached payload,
and refreshes a newer version in an isolated temporary `CODEX_HOME`. It does not
change your normal Codex installation. The temporary test location is printed.

With Python installed, check the real STDIO MCP handshake (use the installed cache path to verify an installation):

```powershell
python -X utf8 tests\mcp_smoke.py plugins\al-toolkit
```

Check the resolver directly:

```powershell
cmd /d /c plugins\al-toolkit\scripts\find-al-bin.cmd altool.exe
```

| Problem | Action |
|---|---|
| `altool.exe` missing | Install/update AL Language or set `AL_BIN` / `AL_EXTENSIONS_DIR` |
| No AL project loaded | Call `al_addproject` with the folder containing `app.json` |
| AL1021 / AL1022 | Download the project's symbols before compiling |
| Skills absent | Confirm the plugin is enabled with `codex plugin list --json`; restart |
| Update still shows old version | Check tracked branch, upgrade marketplace, re-run `plugin add` |

## Claude Code compatibility

The original `.claude-plugin` marketplace and `.mcp.json` remain available:

```text
/plugin marketplace add NathapolDev/claude-al-toolkit
/plugin install al-toolkit@al-toolkit-marketplace
/reload-plugins
```

Claude's launcher still defaults to the current AL project directory. Codex uses
`.mcp.codex.json` with plugin-relative `cwd` and deferred project loading.
Shared skills do not require Claude-specific environment variables or ToolSearch.

## Packaging reference

The supported Codex compatibility manifest is used intentionally alongside the
existing Claude package. See [OpenAI plugin packaging documentation](https://developers.openai.com/plugins/build/plugins)
and [Microsoft AL agent tools](https://learn.microsoft.com/en-us/dynamics365/business-central/dev-itpro/developer/al-agent-tools/al-agent-tools-overview).