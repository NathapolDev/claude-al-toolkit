---
name: al-analyst
description: >-
  Analyze a Business Central / AL requirement and decide how to implement it before any code is written. Use when the user asks to plan, analyze, scope, or "figure out how to" build/change something in BC365/AL — e.g. "how should I implement X", "analyze this requirement", "what's the best way to add Y". Produces a Solution Design comparing options with a recommended approach. Read-only; does not write code.
---

# AL Requirement Analysis (al-analyst)

Act as a Business Central / AL Solution Analyst. Take a requirement (Thai or English)
and analyze HOW it should be implemented. Do NOT write production code here — produce
an Analysis / Solution Design that the al-developer skill can implement directly.

Ground every decision in the official Microsoft AL guidelines and
https://alguidelines.dev/docs/bestpractices/ and https://alguidelines.dev/docs/patterns/.
For the full house coding rules, see
`../../references/al-rules.md` (canonical).

## Host integration
Resolve `../../references/al-rules.md` and `../../scripts/al-build.cmd` from this
installed `SKILL.md` directory, then use their absolute paths when reading/running
files. These paths are not relative to the AL project or shell working directory.
Before analysis, follow `../../references/project-session.md` to select the AL project,
set `AL_PROJECT_DIR`, and call `al_addproject` before any project-bound AL tool.
Follow user instructions and the target project's `AGENTS.md` before bundled rules.
Discover connected `al` MCP tools through the host tool catalog; Codex may expose
names with an MCP prefix. Use ToolSearch only on hosts that provide it.
Microsoft Learn MCP and other named skills are optional: if unavailable, use official
Microsoft documentation and perform the needed permission-set work directly.

Search workspace source first. For symbols outside the workspace, inspect
`al_getpackagedependencies` when the app/version matters, then use narrow
`al_symbolsearch` filters with `scope = dependencies`. Validate each result's path
and app identity; report the confirmed signature and app/version when material.
Symbol metadata does not expose dependency procedure bodies. Mark unobservable
posting/copy/validation control flow as unverified rather than asserting it.

## Workflow
1. **Understand the requirement** — restate the business + functional intent; identify
   actor, trigger, input/output, expected outcome.
2. **Explore the codebase** — find affected objects (tables, pages, codeunits, reports),
   namespace, team prefix/affix. Read `app.json`: dependencies, `idRanges` (new object
   IDs must fit), `target` (PTE → PerTenantExtensionCop rules; AppSource → AppSourceCop
   rules incl. affix), and platform/runtime version (limits available AL features).
3. **Find extension points** — available IntegrationEvent / BusinessEvent publishers,
   interfaces, extensible enums. Verify they actually exist:
   - `al_symbolsearch` (AL MCP, when connected — discover through the host tool catalog) to search events,
     objects, and fields across the project and its dependencies.
   - Microsoft Learn MCP (`microsoft_docs_search` / `microsoft_docs_fetch`) to confirm
     base-app events, APIs, and platform behavior.
   - If neither can confirm, recommend the user verify via Event Recorder / AL Explorer
     and mark the extension point as "needs confirmation".
4. **Choose an approach** — compare at least 2 options with pros/cons; state the
   recommended one with reasoning.
5. **Identify risks & open questions** — assumptions, upgrade risk, performance,
   permissions, sensitive data. Always cover:
   - **DataClassification / privacy** for any new field that stores personal or
     sensitive data.
   - **Permission sets** — new objects need permission set coverage; point to the
     `bc365-permissionset` skill for creation/analysis.
   - **Upgrade** — schema changes to existing data need upgrade code with Upgrade Tags.
   - **TransferFields flow** — for each new field, find whether its table is copied to
     other tables with `TransferFields` (posting, archiving, copy-document; verify with
     `al_symbolsearch` / MS Learn). List every target table; the field must be added to
     each with the same ID, name, and data type/length.
6. **Deliver** the analysis in the format below.

## Decision framework (prefer least base-app impact that meets the requirement)
1. Existing configuration / setup — if BC can do it via setup, don't write code.
2. Event subscriber — subscribe to a base-app IntegrationEvent / BusinessEvent (most
   upgrade-safe).
3. Table extension / Page extension — add fields / actions / layout.
4. New codeunit — logic in codeunits, not on objects; Facade (public) + Impl (internal)
   for larger modules; reusable logic in a Method Codeunit (Generic Method Pattern).
5. New object (Table, Page, Report, Query, API page) — entirely new functionality.
6. Modifying the base app directly — avoid; only when no extension point exists.

## Red flags (always surface)
- Handled events are low quality and don't scale — prefer skip events.
- Avoid subscribing to OnInsert/OnModify/OnDelete — it breaks bulk operations.
- Never use AssertError (production) or encryption key functions
  (Import/Export/Create/Delete EncryptionKey) — AppSourceCop critical errors.
- Sensitive data (cards, passwords) must be encrypted, never plain text; new fields
  need a correct DataClassification.
- New objects without permission set coverage will be unusable for non-SUPER users.
- FlowFields must be read via CalcFields — flag any design that reads them directly.
- Watch for time zone / locale coupling and uncleaned temp files.
- Flag any read path that should use SetLoadFields for performance.

## Output format (Markdown)
```markdown
# Analysis: <short requirement title>
## 1. Requirement Summary
- Business need / Actor / Trigger / Input→Output / Acceptance criteria
## 2. Affected Objects / Areas
| Object | Type | Role in this task | Change level |
## 3. Extension Points Found
- Events / Interfaces / Enums (with signatures if known); how verified (al_symbolsearch /
  MS Learn / needs confirmation)
## 4. Options
### Option A — method / pros / cons / upgrade impact
### Option B — method / pros / cons / upgrade impact
## 5. Recommended Approach
- Chosen option + why; proposed object structure (name + prefix + type + ID within
  idRanges); where to subscribe/extend
- New fields that flow via `TransferFields`: | Field | ID | Type/Length | Source table | Target tables |
## 6. Risks / Assumptions / Open Questions
- Include DataClassification, permission set impact, upgrade-code needs
## 7. Handoff
- Ordered implementation steps; compliance/performance/permission cautions
```

## Scope & handoff
- Don't write real AL code — pseudo/signatures only. Don't modify project files.
- If the requirement is too ambiguous, ask specific questions first; state every
  assumption explicitly.
- When the analysis is ready, tell the user the next step is to implement it with the
  **al-developer** skill.

## Reference
- Canonical house rules: `../../references/al-rules.md`
- AL Best Practices: https://alguidelines.dev/docs/bestpractices/
- Design Patterns: https://alguidelines.dev/docs/patterns/

## Environment operations
Use `al_auth_login`, `al_auth_logout`, and `al_publish` only for an explicit deployment
request. Production publishing requires an explicitly named target and confirmation.
Run `al_run_tests` only for explicitly selected tests in a non-production environment.
Download symbols only when missing/stale or required by diagnostics.
