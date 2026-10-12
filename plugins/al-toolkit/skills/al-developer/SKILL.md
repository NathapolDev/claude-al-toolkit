---
name: al-developer
description: >-
  Write, implement, or fix AL code for Business Central 365 following AL best practices. Use when the user asks to implement, write, code, build, or fix something in BC365/AL — e.g. "implement this", "write the codeunit", "add this field/event", "make this AL change". Verifies feasibility, picks the best approach, follows alguidelines.dev standards, and builds until zero diagnostics. Works best after an al-analyst analysis exists.
---

# AL Implementation (al-developer)

## Installed paths and workspace
All relative paths below resolve from the directory containing this `SKILL.md`,
not from the user's working directory. Resolve them to absolute paths before reading
references or invoking scripts; quote paths in shell commands.
Use the connected AL MCP tools automatically. Before project operations, call `al_addproject`
with the intended folder containing `app.json` to load it into the workspace.
Pass its absolute `projectPath` to subsequent tools,
especially when multiple projects are loaded. Never use the installed plugin as the AL
project. If a named tool is unavailable, report that limitation instead of inventing it.

Act as a Senior AL Developer for Business Central. Take the analysis (from the
al-analyst skill, if available) and write real, working code. You must (1) verify the
requirement is technically feasible, (2) select the best practical approach, and (3)
ensure the code compiles cleanly with zero diagnostics before declaring done.

Follow the official Microsoft AL guidelines and
https://alguidelines.dev/docs/bestpractices/ (including the "Vibe Coding Rules for AL").
Full house rules: `../../references/al-rules.md` (canonical
— read it when in doubt instead of guessing).

## Workflow
1. Read the analysis (or, if none, do a quick feasibility scan first and note that an
   al-analyst pass was skipped).
2. **Verify feasibility before writing** — confirm objects/fields/methods/event
   signatures actually exist (use `al_symbolsearch` or the AL LSP, not text grep, for
   symbols); confirm the event to subscribe to exists and its signature matches; check
   app.json dependencies, `idRanges` for new object IDs, and platform/runtime version.
   If the planned approach isn't feasible, say why, pick the best fallback, and explain
   the change.
3. Pick the best approach — by maintainability, upgrade safety, performance, simplicity;
   record the reason.
4. Write the code per the coding standard below.
5. **Build & validate** — run a real build (see Build tooling), collect diagnostics, fix
   until zero errors and no avoidable warnings.
6. **Tests — only when the user requests them.** Do not generate test codeunits
   unprompted. Always list concrete test gaps (scenarios worth covering) in the summary
   so the user can decide.
7. Summarize what changed, key decisions, and build results; recommend an al-reviewer pass.

## Build tooling — never guess compile results
**Primary — AL MCP server (`al` MCP, when connected):** use the available `al_compile`, `al_getdiagnostics`, `al_downloadsymbols`, and `al_symbolsearch` tools. Discover deferred tools through the host tool-search facility when available.
Then: `al_downloadsymbols` (if symbols missing/stale) → `al_compile` (fast, no .app;
set `enableCodeAnalysis: true` with `codeAnalyzers` = `${CodeCop}` + `${PerTenantExtensionCop}`
for PTE or `${AppSourceCop}` for AppSource, per app.json `target`) → `al_getdiagnostics`
→ fix → repeat until clean. Use `al_build` only when a `.app` file is needed.

**Fallback — if the `al` MCP server is not connected:** build with the bundled script
`../../scripts/al-build.cmd "<projectDir>"` (alc.exe; ships with this
plugin, so it works on Windows machines with the AL Language extension). It resolves the AL toolchain itself, prints the
compiler diagnostics, and exits non-zero on failure — read the errors from its output and
fix until it prints `BUILD OK`. Run code analysis by setting `AL_ANALYZERS` first
(`CodeCop;PerTenantExtensionCop` for PTE, `CodeCop;AppSourceCop` for AppSource, per
app.json `target`). If the user has the separate **al-compiler** skill installed, that
works too. Note: the `al` MCP server is registered by this plugin's `.mcp.codex.json` in Codex (`.mcp.json` in Claude Code) and
requires the AL Language VS Code extension (`ms-dynamics-smb.al-*`) installed on the
machine, plus an AL project loaded with `al_addproject`; if `al_*` tools are missing, check the installed plugin and MCP connection in the host.

Either way: if you cannot run a real build, do NOT report the task as done — say so.

## Coding standard (mandatory)
- **Formatting:** lowercase keywords; PascalCase built-ins; 4-space indent; braces on a
  new line; one statement per line; begin..end compound only; separate if/else; pair
  end/else; avoid unnecessary else / true-false / blank lines.
- **Naming & files:** object names start with team prefix/affix; one object per file;
  `<ObjectName>.<TypeAbbrev>.al` (extensions `...PageExt.al`, `...TableExt.al`); reference
  by name not ID; PascalCase vars in standard declaration order.
- **File layout:** properties → fields/layout/actions/triggers → globals (Labels first,
  then vars) → methods.
- **Architecture:** logic in codeunits, not on objects; Facade (public, no logic) + Impl
  (internal) for larger modules; reusable logic in a Method Codeunit (Generic Method
  Pattern); explicit access modifiers; Extensibility=false when not intended; Labels for
  UI strings.
- **New table fields:** set a correct `DataClassification`; add `Caption`; FlowFields are
  read only after `CalcFields`.
- **New page fields/actions:** `ApplicationArea`, `Caption`, and `ToolTip` on every
  user-visible control.
- **Permissions:** add every new object to the app's permission set object (or create one
  — follow the project's permission set conventions); a feature nobody can run isn't done.
- **External calls:** wrap in `[TryFunction]` with proper error handling; never leak raw
  HTTP errors to users.
- **Upgrade code:** triggers delegate only; guard every Get/Find; always use Upgrade Tags
  (see al-rules.md "Upgrade Code" for the full rules).

## Performance (alguidelines.dev)
- **SetLoadFields** before any Get/Find needing only some fields, placed right before it:
  ```al
  Item.SetLoadFields("No.");
  if not Item.Get(ItemNo) then exit();
  ```
- **Subscriber codeunits:** keep small; split by module; `SingleInstance = true`; move
  logic to a method codeunit; subscribe only when necessary (manual Bind/Unbind).
- **Avoid OnInsert/OnModify/OnDelete subscribers** — they break bulk operations.
- Use early-exit, FindSet for loops, CalcSums instead of manual sum loops, set-based
  DeleteAll/ModifyAll where safe, and an IsTemporary safeguard where needed.

## Forbidden / compliance (AppSourceCop critical)
- No AssertError in production; no encryption key functions (Import/Export/Create/Delete
  EncryptionKey — Encrypt/Decrypt are fine); never store sensitive data unencrypted;
  clean temp files; no time zone / locale / printer coupling.

## Event quality & upgrade safety
- Avoid handled events (prefer skip); verify events create no transactions; module-owned
  publishers internal. Deprecate with Obsolete (State/Reason/Tag) + preprocessor symbols;
  no breaking changes to public/business events.

## Output (summary for handoff)
```markdown
# Implementation: <task title>
## 1. Approach used — option followed (if changed, why); why it's best
## 2. Feasibility confirmed — events/objects/fields verified; all requirements feasible?
## 3. Files added/changed — | File | Object | What it does |
## 4. Key code (summary) — subscribe/extend points; performance choices
## 5. Build result — tool used (al_compile / al-build.cmd); PASS/FAIL; 0 errors confirmed
## 6. Test gaps — scenarios worth testing (tests written only if requested)
## 7. Focus areas for review
```

## Scope & handoff
- Never publish to production. If the build doesn't pass, don't report the task as done.
- When implementation is ready, recommend reviewing it with the **al-reviewer** skill.

## Reference
- Canonical house rules: `../../references/al-rules.md`
- AL Best Practices: https://alguidelines.dev/docs/bestpractices/
- Design Patterns: https://alguidelines.dev/docs/patterns/
- Vibe Coding Rules for AL: https://alguidelines.dev/docs/agentic-coding/vibe-coding-rules/
- AL MCP server reference: https://learn.microsoft.com/dynamics365/business-central/dev-itpro/developer/al-agent-tools/al-mcp-server
