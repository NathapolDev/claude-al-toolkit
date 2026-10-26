# BC365 AL Toolkit

Business Central AL tooling for Codex and Claude Code: `al-analyst` (read-only
design), `al-developer` (implementation and compiler verification), and `al-reviewer`
(read-only review with independent diagnostics). Shared defaults live in
`references/al-rules.md`; user instructions and the project's AGENTS.md take precedence.

## Installation

Requires Windows, a local executor, and Microsoft's AL Development Tools .NET
global tool or AL Language VS Code extension. Microsoft binaries are not bundled.

**Codex CLI 0.164.0:**

```powershell
codex plugin marketplace add C:\claude-al-toolkit
codex plugin add bc365-al-toolkit@al-toolkit-marketplace
Set-Location 'C:\path\to\AlProject'
codex
```

Inspect `/mcp`; invoke `$al-analyst`, `$al-developer`, and `$al-reviewer`.
Each skill finds the selected AL project, sets `AL_PROJECT_DIR` for shell commands,
and calls Microsoft’s `al_addproject` before using the AL MCP tools. The Codex server
starts without a default project and loads the selected app dynamically.

**Claude Code:** add the repository marketplace, run
`/plugin install bc365-al-toolkit@al-toolkit-marketplace`, then `/reload-plugins`.
Start in the AL project and inspect `claude mcp list`. Claude uses `.mcp.json` and
its working directory unless `AL_PROJECT_DIR` overrides it.

## Runtime access

The package contains skills, manifests, an icon, and readable batch scripts. It
changes no host permission settings.

- `scripts/find-al-bin.cmd` reads environment variables and installed tool folders;
  it uses `dotnet --list-runtimes` when checking the .NET global tool.
- `scripts/al-mcp-codex.cmd` launches `altool.exe launchmcpserver --transport stdio`
  without a default project. Skills add the selected project through `al_addproject`.
- `scripts/al-build.cmd` runs `alc.exe`, writes an `.app`, and removes its temporary
  log. Skills resolve the script relative to their installed file location.
- Microsoft's MCP tools can read metadata, compile, build, download symbols,
  authenticate, publish, and run tests with the host's permissions and user
  credentials. Skills restrict auth/publish to explicit deployment requests;
  Production requires a named target and confirmation. Environment tests require
  explicitly selected tests and a non-production target. Symbols download only
  when missing/stale or required by diagnostics.
- Microsoft Learn MCP and permission-set skills are optional and are not bundled.
  When unavailable, use official documentation and direct permission-set work.

Overrides: `AL_BIN`, `AL_EXTENSIONS_DIR`, `VSCODE_EXTENSIONS` for discovery;
`AL_PROJECT_DIR` is set by each skill for shell commands; `AL_PACKAGECACHE` and `AL_ANALYZERS` for compiler
fallback. Missing compiler evidence means **NOT VERIFIED**.

MIT. See [LICENSE](LICENSE).
