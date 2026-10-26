# Initialize the AL project on every skill invocation

Run this setup before analysis, implementation, or review, including a handoff from
another AL skill. The workspace and user-selected project determine the target;
an inherited `AL_PROJECT_DIR` is only a hint and must not override that selection.

1. Identify the AL project containing the current working directory or selected AL
   file. Find its nearest parent `app.json`. If the workspace contains several apps,
   use the project identified by the task or selected files. If none is identifiable,
   discover workspace `app.json` files (exclude symbol caches and vendor folders).
   Select a sole matching project automatically; ask only if multiple plausible
   projects remain. Do not choose the plugin installation/cache directory.
2. Resolve `../scripts/Initialize-AlProject.ps1` relative to this reference file.
   It walks up from a selected file's directory to find the containing project. Run
   its absolute path in PowerShell 7 with the chosen project directory:

   ```powershell
   & '<installed-plugin>/scripts/Initialize-AlProject.ps1' -ProjectDir '<selected-project>'
   ```

   It validates `app.json`, sets `$env:AL_PROJECT_DIR` in that PowerShell process,
   and prints the absolute project path. Record that result for this invocation.
   It writes no project files or persistent user/machine environment settings.
   For subsequent shell calls in a new process, run the initializer again before
   the project command; environment changes do not survive a shell process ending.
3. Discover `al_addproject` from the connected AL MCP server and call it with
   `projectPath` equal to the resolved path. Inspect the response; a transport-level
   success alone does not prove loading succeeded. Call this for the current project
   even if an earlier skill initialized it. The Codex server starts without projects
   and does not need restarting to add one. Setting a shell variable alone does not
   configure an already-running MCP process. Claude may have loaded the workspace at
   startup; calling `al_addproject` with the same path confirms it is in the session.
4. Use the resolved path as `projectPath` on tools that support that parameter. For
   workspace-wide tools such as `al_compile`, report the project paths in the returned
   diagnostics: the server can retain other projects added during the session.
   Do not misattribute another app's failures to this project.

If `al_addproject` is unavailable, report that dynamic project loading needs a newer
AL toolchain. Use the compiler fallback with the resolved path where appropriate;
do not claim the MCP project was configured. If project loading reports missing
symbols, download only when needed under the skill's normal rules.

For the fallback, initialize and build in the same PowerShell call:

```powershell
& '<installed-plugin>/scripts/Initialize-AlProject.ps1' -ProjectDir '<selected-project>'
& '<installed-plugin>/scripts/al-build.cmd' $env:AL_PROJECT_DIR
```

Reference: [Microsoft AL MCP server](https://learn.microsoft.com/en-us/dynamics365/business-central/dev-itpro/developer/al-agent-tools/al-mcp-server).
