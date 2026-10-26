# Contributor guidance

This repository distributes `bc365-al-toolkit` for Codex and Claude Code. It is not
an AL application. Deliverables are skills, manifests, shared references, and Windows
batch launchers. Microsoft's binaries are installed separately.

## Layout and runtime invariants

- `.agents/plugins/marketplace.json`: Codex catalog; source paths resolve from the
  repository root, not `.agents/plugins/`.
- `.claude-plugin/marketplace.json`: Claude catalog.
- `plugins/al-toolkit/.codex-plugin/plugin.json`: Codex manifest, explicitly declaring
  `skills/` and `.mcp.codex.json`.
- `plugins/al-toolkit/.claude-plugin/plugin.json`: Claude manifest, using `.mcp.json`.
- `plugins/al-toolkit/skills/*/SKILL.md`: three shared workflows.
- `plugins/al-toolkit/references/al-rules.md`: shared AL defaults, subordinate to user
  instructions and the target project's AGENTS.md.

Codex runs `cmd.exe /d /c scripts\al-mcp-codex.cmd` with plugin-root `cwd = "."`.
The Codex launcher starts Microsoft's MCP server without a project. Every skill references
`references/project-session.md`, runs
`Initialize-AlProject.ps1`, sets `AL_PROJECT_DIR` in its shell, and calls Microsoft's
`al_addproject` with the selected project before project-bound tools. Adding a project does not require restarting the MCP process.
The PowerShell variable is invocation-local, so re-run the initializer for each new shell.
Claude retains its `${CLAUDE_PLUGIN_ROOT}` MCP command and working-directory default.
Skill resources resolve from the installed SKILL.md; use absolute paths in the shell.
Keep installations portable and machine-specific paths out of manifests.

Keep discovery in `scripts/find-al-bin.cmd`. Both hosts share that resolver and
`scripts/al-build.cmd`. Preserve batch quoting, delayed expansion, and compiler
diagnostic grading: `alc.exe` can exit zero while reporting AL errors.

The analyst and reviewer remain read-only. The developer reports observed compiler
results. Missing tools/symbols mean NOT VERIFIED. Dependency symbol metadata does not
prove procedure control flow.

## Validation and release

Use PowerShell 7. Parse both catalogs, both manifests, and both MCP configurations.
Validate all three skills and relative references. Inspect the package through Codex
`plugin/list` and `plugin/read` when available. Exercise MCP `initialize` and
`tools/list` with no initial project, then `al_addproject` against a temporary AL
project. Validate PowerShell project discovery from a nested folder too.
Packaging validation must not authenticate, publish, download symbols, or run tests
on a Business Central environment.

Update both manifest versions together. Keep installation instructions aligned with
the observed CLI version. No package manager or AL application build exists here.
