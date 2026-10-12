# Contributor guidance

When modifying this marketplace, follow these packaging decisions (2026-10-12):

- Codex and Claude share skills, references, and the Microsoft toolchain resolver.
  Separate MCP configuration is intentional: Claude starts in the AL project;
  Codex resolves `cwd: "."` from the installed plugin and defers project loading to
  `al_addproject`. Do not restore a Claude-only root variable in shared skills.
- Resolve skill resource paths from the installed `SKILL.md` directory, not from
  the user's current directory. Quote paths when invoking fallback scripts.
- Keep Microsoft binaries and credentials outside the package. Resolve binaries
  at launch so editor extension upgrades do not invalidate registered commands.
  Support both the legacy `bin/win32` and current `bin` layouts.
- Keep Codex and Claude manifest versions synchronized. Stable marketplace and
  plugin names let existing installations continue to refresh correctly.
- The fallback must check both process failure and compiler diagnostics: an exit
  status alone does not establish that AL compilation succeeded.
- Preserve the analyst/developer/reviewer handoff and AL house rules. Review and
  analysis remain read-only; implementation requires observed compiler evidence.

Recheck live Codex CLI help and Microsoft AL tool behavior before changing packaging;
client capabilities and extension layouts can change.

For installation and verification commands, use [README.md](README.md).
Run `scripts/Test-CodexPlugin.ps1` for an isolated relocated install/version refresh.
With AL Language and Python installed, run
`python -X utf8 tests/mcp_smoke.py plugins/al-toolkit` for a real STDIO handshake.