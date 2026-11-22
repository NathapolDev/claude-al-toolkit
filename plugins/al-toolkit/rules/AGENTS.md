# BC365 AL Toolkit Rules

These rules apply whenever the `bc365-al-toolkit` plugin is active. All AL code and reviews defer to `references/al-rules.md` as canonical.

## BC365 AL Skill Routing Table

For Business Central (BC365/AL) tasks, operate in the three-stage pipeline **`al-analyst` → `al-developer` → `al-reviewer`** (skip `al-analyst` only for trivial one-line fixes, and state that it was skipped):

| Stage / Role | Skill | When to Use | Output & Guardrails |
|---|---|---|---|
| **1. Analysis & Plan** | `al-analyst` | Analyze requirements, identify extension points, compare options, propose IDs ("how should I implement X", "analyze", "scope") | Read-only Solution Design comparing >=2 options with recommended approach; writes no code |
| **2. Implementation** | `al-developer` | Write, implement, or fix AL code ("implement this", "write codeunit", "add field/event", "fix AL error") | Verifies feasibility, follows canonical AL rules, compiles & runs cops until 0 errors; tests only on request |
| **3. Review & Validate** | `al-reviewer` | Audit or check AL code before merge ("review this code", "check my AL", "is this safe") | Read-only; independently re-runs build/tests, checks 12-part checklist, returns Approve or Request Changes |
| **Semantic LSP** | `al-lsp` | Resolve AL definitions, callers, `TransferFields` targets, hover types, document/workspace symbols, signature help, rename preview | Uses `al-lsp` MCP tools (or `scripts/al-lsp-mcp.cmd --cli`) instead of text grep |
| **Permission Sets** | `bc365-permissionset` | Create, analyze, or update BC tenant XML or AL `permissionset` objects | Uses Python 3 stdlib scripts under `skills/bc365-permissionset/scripts/` |
| **Snapshot Debug** | `al-debugger` | Opt-in: capture/analyze BC snapshot debugging for live environment failures | Outside main pipeline; requires user-configured `al-snapshot` MCP server |
| **Perf Profiling** | `al-profiler` | Opt-in: profile slow BC sessions or analyze `.alcpuprofile` files | Outside main pipeline; requires user-configured `al-profiling` MCP server |

Never publish to Production. Never write test codeunits unless the user explicitly asks for tests.

## AL MCP (`al`) & AL LSP MCP (`al-lsp`) Tooling Guidance

### `al` MCP Server (16 tools)

Microsoft's AL MCP server (`scripts/al-mcp.cmd` → `altool.exe launchmcpserver`) exposes 16 tools:
- **Build & symbols cache:** `al_compile`, `al_build`, `al_getdiagnostics`, `al_downloadsymbols`
- **Symbol & metadata discovery:** `al_symbolsearch`, `al_symbolrelations`, `al_getnextobjectid`, `al_getpackagedependencies`, `al_inspectpage`
- **Workspace:** `al_addproject`
- **Environment & testing (Sandbox/Container only):** `al_publish`, `al_run_tests`, `al_auth_login`, `al_auth_logout`
- **Translations:** `al_searchtranslations`, `al_writetranslation`

Mandatory `al` MCP usage rules:
- If any tool responds `"No projects are loaded"`, or the workspace has multiple projects (e.g. App + Test), call `al_addproject` for each project and pass `projectPath` to subsequent tool calls.
- Never guess compile status. Run `al_compile` with `onlyErrors: true` until `succeeded: true` (0 errors), then run `al_compile` with `onlyErrors: false`, `enableCodeAnalysis: true`, `codeAnalyzers` matching `app.json` `target` (`["${CodeCop}", "${PerTenantExtensionCop}"]` for PTE or `["${CodeCop}", "${AppSourceCop}"]` for AppSource), and `maxDiagnosticsPerCompilation: 500`.
- `al_getdiagnostics` returns `Compiler` diagnostics only — analyzer (`CodeCop` / `PTECop` / `AppSourceCop`) findings appear only in `al_compile` output (or `scripts/al-build.cmd` with `AL_ANALYZERS` when diagnostics hit the cap).
- If `al_downloadsymbols` is needed for missing symbols (`AL1021`, `AL1022`, `AL0185`), run it before modifying code.
- If `al` MCP is unavailable, use the bundled fallbacks `scripts/al-build.cmd` (builds) and `scripts/al-test.cmd` (tests; refuses Production). If neither MCP nor fallback scripts can run, report `BUILD NOT VERIFIED` / `TESTS NOT RUN`.

### `al-lsp` MCP Server (7 tools)

The AL LSP MCP bridge (`scripts/al-lsp-mcp.cmd` → `al-lsp-mcp.py` → `altool.exe launchlspserver`) exposes 7 semantic code intelligence tools using **1-based** `line` and `character` positions:
1. `al_lsp_definition` (`filePath`, `line`, `character`, optional `projectPath`) — jump to symbol definition (`textDocument/definition`).
2. `al_lsp_references` (`filePath`, `line`, `character`, optional `includeDeclaration`, `projectPath`) — find all symbol references across the workspace (`textDocument/references`; skips comments and strings).
3. `al_lsp_hover` (`filePath`, `line`, `character`, optional `projectPath`) — inspect symbol type, signature, and XML documentation (`textDocument/hover`).
4. `al_lsp_document_symbols` (`filePath`, optional `projectPath`) — list objects, fields, triggers, and procedures in a file (`textDocument/documentSymbol`).
5. `al_lsp_workspace_symbols` (`query`, optional `projectPath`) — search AL symbols across the workspace (`workspace/symbol`).
6. `al_lsp_signature_help` (`filePath`, `line`, `character`, optional `projectPath`) — inspect procedure overloads and active parameters (`textDocument/signatureHelp`).
7. `al_lsp_rename_preview` (`filePath`, `line`, `character`, `newName`, optional `projectPath`) — preview workspace edits for a rename without modifying files on disk (`textDocument/rename`).

Use `al-lsp` tools instead of text grep whenever verifying symbol existence, checking callers of changed procedures, tracing `TransferFields` usage, or locating snappoint lines. If the `al-lsp` MCP server is unavailable, use the CLI fallback `scripts/al-lsp-mcp.cmd --cli <tool_name> '<json_args>'` (or `scripts/al-graph.cmd` for call-graph queries).

---

## Business Central AL Rules (Canonical)

### Official Sources

- Microsoft Learn Business Central: https://learn.microsoft.com/en-us/dynamics365/business-central/
- AL developer reference: https://learn.microsoft.com/en-us/dynamics365/business-central/dev-itpro/developer/
- Community AL guidelines: https://alguidelines.dev/docs/agentic-coding/vibe-coding-rules/

### AL Code Style

- Use PascalCase for variables, function names, object names, table names, page names, codeunits, reports, interfaces, and enums.
- Use descriptive names. Avoid abbreviations unless they are established Business Central terms such as `Cust.` or `Vend.`.
- Keep AL object names within the platform object name limit. When a project uses a 3-character prefix plus a space, keep the base name to 26 characters or less.
- Use 4-space indentation.
- Keep procedures small and focused.
- Organize new files by business feature unless the repo already has a clear different convention:
  ```
  src/
  ├── Sales/
  │   ├── Invoice/
  │   │   ├── SalesInvoice.Page.al
  │   │   └── SalesInvoicePosting.Codeunit.al
  │   └── Order/
  │       └── SalesOrder.Page.al
  └── Common/
      ├── Helpers/
      └── Interfaces/
  ```
- Name files as `<ObjectName>.<ObjectType>.al`, for example `NoSeries.Page.al`, `SalesHeader.TableExt.al`, `INoSeries.Interface.al`, `NoSeriesImpl.Codeunit.al`.
- Use XML documentation comments for global procedures in codeunits.
- Avoid comments that describe obvious operations. Use comments to explain why.

### Naming Patterns

- Use specific record variable names instead of generic names when possible.
- Use descriptive event subscriber parameter names, not generic `Rec`, unless required by local style.
- Prefix interfaces with `I`, for example `ICustomerService`.
- Suffix implementations with `Impl`, for example `CustomerServiceImpl`.
- Suffix codeunits containing only event subscribers with `Handler`.

### Data Access And Performance

- Set filters before `FindSet`, `FindFirst`, `FindLast`, or loops.
- Use `SetLoadFields` before `Get` or `Find*` when only some fields are needed.
- Use `CalcSums` instead of manual aggregation loops when possible.
- Use temporary tables, dictionaries, and lists for in-memory processing.
- Calculate changes first and write once when practical.
- Avoid unnecessary `Commit()` calls.
- Verify a field's `FieldClass` before reading it dynamically. For FlowFields, call `CalcFields` before using or assigning the value.
- A new field that must flow to another table via `TransferFields` (e.g. Sales Header → Sales Invoice Header, Sales Line → Sales Invoice Line) must exist in every target table extension with the **same field ID, same name, and same data type/length**. `TransferFields` matches by field ID only: a type mismatch errors at runtime (same extension) or is skipped silently (cross-extension), and a same-ID field with a different name receives the wrong data silently; the runtime tolerates only Text↔Code and enum↔enum (copied by ordinal — still require the same enum), and the target length must fit the source value.

```al
// Good: filter early
Customer.SetRange(City, CityFilter);
Customer.SetRange(Blocked, Customer.Blocked::" ");
if Customer.FindSet() then ...

// Good: SetLoadFields BEFORE SetRange
Item.SetLoadFields("Item Category Code");
Item.SetRange("Third Party Item Exists", false);
Item.FindFirst();

// Good: CalcSums for aggregation
CustLedgerEntry.SetRange("Customer No.", CustomerNo);
CustLedgerEntry.CalcSums(Amount);
exit(CustLedgerEntry.Amount);
```

### Error Handling

- Use `Error`, `FieldError`, and `TestField` appropriately for validation.
- Never hardcode user-facing error or message strings. Use Label variables.
- Include label comments for placeholders.
- Use `Locked = true` for telemetry and technical labels that must not be translated.
- Use `[TryFunction]` for external calls or operations expected to fail.
- Prioritize correct business logic. If an event, function, or object name needs verification, leave a clear TODO/comment rather than guessing in a way that changes the intent.

```al
// Good: Label variables with comments
var
  CustomerNotFoundErr: Label 'Customer %1 does not exist for sales document %2.',
    Comment = '%1 = Customer No., %2 = Sales Header No.';

// Good: TryFunction for external calls
[TryFunction]
local procedure TryProcessPaymentInternal(Amount: Decimal)
begin
  PaymentService.ProcessPayment(Amount);
end;

// Good: Locked = true for telemetry
SalesDocPostedMsg: Label 'Sales document posted successfully', Locked = true;
```

### Events

- Subscribe to Business Central events instead of modifying base app objects.
- Add `[IntegrationEvent]` at meaningful business process points when extensibility is needed.
- Avoid handled events by default — they are low quality and don't scale; prefer events that let subscribers add or skip behavior. Use the `IsHandled` pattern (subscribing to one, or publishing one) only when the requirement needs a subscriber to replace the default logic, and state that reason in the design and code.
- Pass enough context to event subscribers, including identity and date fields where relevant.
- Pass records by `var` only when subscribers need to modify data.

### Runtime-Gated Features

Read `runtime` (and `application`) in `app.json` before recommending a language feature. An extension needs a server that supports its runtime or later, and the compiler doesn't check the target server: raising `runtime` compiles fine against older symbols and then fails to deploy. Never raise `runtime` to unlock a feature without confirming every target environment's version.

| `runtime` | Business Central | Release |
|---|---|---|
| 16.0 | 27.0 | 2025 release wave 2 |
| 17.0 | 28.0 | 2026 release wave 1 |
| 18.0 | 29.0 | 2026 release wave 2 |

For a platform not in the table, check with `altool GetLatestSupportedRuntimeVersion <platformVersion>` (the 30.0 beta toolchain reports runtime 30.0 for platform 30.0; Microsoft Learn doesn't list it yet).

**Runtime 18.0+ — default interface methods:**
- An interface method may have a body; implementing codeunits may omit it. Below 18.0 the compiler rejects it (`AL0413: Procedure cannot have a body`).
- Default methods dispatch only through an `Interface` variable, not through the implementing codeunit's own variable.
- Adding a default method to a published interface is non-breaking. Making it required is two-phase: first mark it `[RequiredPending('<reason>', '<tag>')]` (implementors get `AL0924`), and only in a later major version remove the body and the attribute (`AS0149` warns about the runtime identifier change). Removing the body directly is `AS0148` (error). `[RequiredPending]` on a method without a body is `AL0923`.

```al
interface "BPC IPaymentMethod"
{
    procedure ValidateAmount(Amount: Decimal): Boolean;   // required

    procedure GetTransactionFee(): Decimal                // default, runtime 18.0+
    begin
        exit(0);
    end;
}
```

### APIs And Integrations

- Use custom API pages with `PageType = API`, `APIPublisher`, `APIGroup`, and `APIVersion` when exposing APIs.
- Prefer OAuth 2.0 patterns for Business Central integrations.
- Use AL `HttpClient`, JSON types, and proper error handling for REST calls.
- Never recommend direct SQL access for SaaS. For on-prem, mention risks and prefer supported AL/web service patterns.

### Tests

- Do not create test code unless explicitly requested.
- Keep App and Test projects separated in AL-Go workspaces.
- App project contains production objects only.
- Test project contains test codeunits, mocks, and test data factories only.
- Test project `app.json` references the App project and required Microsoft test libraries such as Library Assert.
- App project must not reference the Test project.
- Use Given/When/Then test procedure names.
- Use standard library codeunits such as `Library - Sales`, `Library - Inventory`, `Library - Random`, and `Library - ERM` where available.
- Use Assert codeunits for validation.
- Put shared test helpers in `Test/src/Common/TestHelpers/`.

### Upgrade Code

- Use `Subtype = Upgrade` for upgrade codeunits.
- Keep `OnUpgradePerCompany` and `OnUpgradePerDatabase` triggers as delegators only. Put implementation in local procedures.
- Do not use `OnValidateUpgradePerCompany`, `OnValidateUpgradePerDatabase`, `OnCheckPreconditionsPerCompany`, or `OnCheckPreconditionsPerDatabase` without explicit justification.
- Never call external services, `HttpClient`, or DotNet interop during upgrade.
- Guard every `Get`, `FindSet`, `FindFirst`, and `FindLast` in upgrade code with an `if ... then`.
- Use Upgrade Tags instead of version checks.
- Register every new upgrade tag in either `OnGetPerCompanyUpgradeTags` or `OnGetPerDatabaseUpgradeTags`, never both.
- Reuse existing upgrade tag subscriber procedures where possible.
- Use `DataTransfer` for large table migrations, especially tables above roughly 300k records.
- Add upgrade code for new fields whose existing records need a value different from the datatype default; `InitValue` only affects new records.
- If code must skip behavior during `ExecutionContext::Upgrade`, include a comment explaining why.
- Prefer telemetry logging over throwing errors from upgrade code where recovery is possible.

```al
// Good: delegate from trigger
trigger OnUpgradePerCompany()
begin
  UpgradeMyFeature();
end;

local procedure UpgradeMyFeature()
var
  UpgradeTag: Codeunit "Upgrade Tag";
begin
  if UpgradeTag.HasUpgradeTag(MyFeatureUpgradeTag()) then
    exit;
  // upgrade logic
  UpgradeTag.SetUpgradeTag(MyFeatureUpgradeTag());
end;

// Good: protect all DB reads
if Customer.Get(CustomerNo) then
  Customer.Modify();

if MyTable.FindSet() then
  repeat
    // process
  until MyTable.Next() = 0;
```

### Review Checklist

| # | Check | Category |
|---|---|---|
| 1 | PascalCase for all names | Naming |
| 2 | File named `<Name>.<Type>.al` | Naming |
| 3 | Object name respects platform and prefix limits | Naming |
| 4 | 4-space indentation | Style |
| 5 | One procedure, one concern | Style |
| 6 | Feature-based folder structure for new files | Style |
| 7 | XML documentation on global procedures | Style |
| 8 | `SetLoadFields` before reads where useful | Performance |
| 9 | Filters set before `FindSet` | Performance |
| 10 | `CalcSums` instead of manual sum loops | Performance |
| 11 | Label variables for messages and errors | Error Handling |
| 12 | `[TryFunction]` around external calls | Error Handling |
| 13 | `Locked = true` for telemetry labels | Error Handling |
| 14 | Event subscribers instead of base app edits | Events |
| 15 | Integration events at meaningful extension points | Events |
| 16 | Handled events avoided; `IsHandled` only where replacing default logic is required and justified | Events |
| 17 | Subscriber-only codeunits use `Handler` suffix | Events |
| 18 | Test files only in Test project | Testing |
| 19 | Given/When/Then test names | Testing |
| 20 | Library codeunits for test data | Testing |
| 21 | No direct implementation in upgrade triggers | Upgrade |
| 22 | Upgrade database reads protected with `if` | Upgrade |
| 23 | Upgrade Tags used instead of version checks | Upgrade |
| 24 | DataTransfer for large table upgrades | Upgrade |
| 25 | New `InitValue` fields have upgrade code when needed | Upgrade |
| 26 | Fields flowing via `TransferFields` match ID, name, and data type in every target table | Data |
| 27 | Language features used are supported by `app.json` `runtime`; `runtime` not raised beyond the target environments | Runtime |
| 28 | Interface default methods made required only via `[RequiredPending]` first | Runtime |
