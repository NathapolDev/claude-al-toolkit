---
name: al-debugger
description: >-
  Capture and read a Business Central snapshot debugging session (call stacks, variables, the AL error) to find why an AL scenario fails on a real environment. Use when the user asks to snapshot-debug, capture what happens when X fails in BC, or debug an error that only reproduces on a sandbox/production environment. Opt-in: needs the al-snapshot MCP server added by the user.
---

# AL Snapshot Debugging (al-debugger)

Find the root cause of an AL failure from a snapshot captured on a real Business Central
environment. Read-only toward code: report findings and hand fixes to **al-developer**.
This skill is outside the analyst → developer → reviewer pipeline; those skills never
call it.

## Prerequisite — the `al-snapshot` MCP server
In Antigravity (`agy`), call these tools via `call_mcp_tool` on server `al-snapshot` (or
directly if injected into your toolset); in Claude Code, load them first with
`ToolSearch`
(`select:initialize_snapshot_debugging,get_snapshot_status,stop_snapshot_debugging,run_tests`).
If they don't exist, stop and tell the user to add the server once (README section
"Opt-in: snapshot debugging and profiling"), resolving `../../scripts/al-diag-mcp.cmd`
relative to the directory containing this loaded `SKILL.md` file (or from
`${CLAUDE_PLUGIN_ROOT}` in Claude Code):

**Antigravity (`~/.gemini/config/mcp_config.json`):** replace `<resolved-path-to>` with
the absolute path to this plugin's folder (forward slashes, no env var placeholders):

```json
{
  "mcpServers": {
    "al-snapshot": {
      "command": "<resolved-path-to>/scripts/al-diag-mcp.cmd",
      "args": ["snapshot"],
      "env": {
        "AL_ENV_TYPE": "Sandbox",
        "AL_ENV_NAME": "<env>"
      }
    }
  }
}
```

**Claude Code:**

```powershell
claude mcp add al-snapshot -e AL_ENV_TYPE=Sandbox -e AL_ENV_NAME=<env> -- "<resolved-path-to>\scripts\al-diag-mcp.cmd" snapshot
```

The first call can open a Microsoft sign-in.

## Before arming — confirm with the user
- **Which environment** the server points at (`AL_ENV_TYPE` / `AL_ENV_NAME`). For
  **Production**, get explicit consent for this session: snapshots capture business data
  and add server load.
- **Verbosity:** `SnapPoint` (default). Use `Full` only for a short, targeted repro and
  say why — it materially increases server CPU, memory, disk, and archive size.
- **Snappoints:** object type, object ID or name, and 1-based line numbers where state
  matters. Verify those lines in the source before arming using the `al-lsp` MCP server
  tools (`al_lsp_definition`, `al_lsp_references`, `al_lsp_hover`,
  `al_lsp_document_symbols`, `al_lsp_workspace_symbols`, `al_lsp_signature_help`,
  `al_lsp_rename_preview` via `call_mcp_tool` on `al-lsp`, or CLI fallback
  `../../scripts/al-lsp-mcp.cmd --cli <tool_name> "<json>"`; in Claude Code, the `LSP`
  tool's `goToDefinition`) or `read_file` / `Read`.

## Workflow
1. `initialize_snapshot_debugging` — omit `sessionId` to arm and wait for the next
   session (the usual case), or pass the session the user names. Keep `debuggingContext`.
2. Relay the returned next step verbatim: the user reproduces the scenario in Business
   Central. You can't reproduce it yourself — except for tests: `run_tests` with the same
   `debuggingContext` attaches a test session.
3. `get_snapshot_status` only when the user says they're done or asks.
4. **Always** call `stop_snapshot_debugging` with the same `debuggingContext` — also when
   the repro or tests failed, or the user abandons the run. An armed session left
   running keeps costing the server.
5. Read the call stacks, variables, and AL error that `stop_snapshot_debugging` returns.
   Map each frame to source and name the root cause, not just the throwing line.

## Data handling
- Quote only the variables needed to explain the cause; mask personal or financial
  values (customer names, amounts, bank details) in what you write back.
- Don't write snapshot contents into the repository, commit messages, or issues.

## Output
```markdown
# Snapshot: <scenario>
## Environment — type/name, verbosity, snappoints, session
## What happened — error message and failing frame (object, procedure, line)
## Root cause — evidence from stack/variables (masked)
## Fix direction — for al-developer (no code here); test to add if requested
## Run closed — stop_snapshot_debugging called: yes/no (+ why if no)
```
