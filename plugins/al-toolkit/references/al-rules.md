# Business Central AL Rules

## Official Sources

- Microsoft Learn Business Central: https://learn.microsoft.com/en-us/dynamics365/business-central/
- AL developer reference: https://learn.microsoft.com/en-us/dynamics365/business-central/dev-itpro/developer/
- Community AL guidelines: https://alguidelines.dev/docs/agentic-coding/vibe-coding-rules/

## AL Code Style

- Use PascalCase for variables, function names, object names, table names, page names, codeunits, reports, interfaces, and enums.
- Use descriptive names. Avoid abbreviations unless they are established Business Central terms such as `Cust.` or `Vend.`.
- Keep AL object names within the platform object name limit. When a project uses a 3-character prefix plus a space, keep the base name to 26 characters or less.
- Use 4-space indentation.
- Keep procedures small and focused.
- Organize new files by business feature unless the repo already has a clear different convention.
- Name files as `<ObjectName>.<ObjectType>.al`, for example `NoSeries.Page.al`, `SalesHeader.TableExt.al`, `INoSeries.Interface.al`, `NoSeriesImpl.Codeunit.al`.
- Use XML documentation comments for global procedures in codeunits.
- Avoid comments that describe obvious operations. Use comments to explain why.

## Naming Patterns

- Use specific record variable names instead of generic names when possible.
- Use descriptive event subscriber parameter names, not generic `Rec`, unless required by local style.
- Prefix interfaces with `I`, for example `ICustomerService`.
- Suffix implementations with `Impl`, for example `CustomerServiceImpl`.
- Suffix codeunits containing only event subscribers with `Handler`.

## Data Access And Performance

- Set filters before `FindSet`, `FindFirst`, `FindLast`, or loops.
- Use `SetLoadFields` before `Get` or `Find*` when only some fields are needed.
- Use `CalcSums` instead of manual aggregation loops when possible.
- Use temporary tables, dictionaries, and lists for in-memory processing.
- Calculate changes first and write once when practical.
- Avoid unnecessary `Commit()` calls.
- Verify a field's `FieldClass` before reading it dynamically. For FlowFields, call `CalcFields` before using or assigning the value.

## Error Handling

- Use `Error`, `FieldError`, and `TestField` appropriately for validation.
- Never hardcode user-facing error or message strings. Use Label variables.
- Include label comments for placeholders.
- Use `Locked = true` for telemetry and technical labels that must not be translated.
- Use `[TryFunction]` for external calls or operations expected to fail.
- Prioritize correct business logic. If an event, function, or object name needs verification, leave a clear TODO/comment rather than guessing in a way that changes the intent.

## Events

- Subscribe to Business Central events instead of modifying base app objects.
- Add `[IntegrationEvent]` at meaningful business process points when extensibility is needed.
- Use the `IsHandled` pattern when subscribers need to override default logic.
- Pass enough context to event subscribers, including identity and date fields where relevant.
- Pass records by `var` only when subscribers need to modify data.

## APIs And Integrations

- Use custom API pages with `PageType = API`, `APIPublisher`, `APIGroup`, and `APIVersion` when exposing APIs.
- Prefer OAuth 2.0 patterns for Business Central integrations.
- Use AL `HttpClient`, JSON types, and proper error handling for REST calls.
- Never recommend direct SQL access for SaaS. For on-prem, mention risks and prefer supported AL/web service patterns.

## Tests

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

## Upgrade Code

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

## Vibe Coding Rules (AL Community Standard)

> Source: alguidelines.dev/docs/agentic-coding/vibe-coding-rules/

### Code Style & Formatting

- PascalCase for all variable names, function names, and object names.
- 4-space indentation consistently.
- Keep procedures small and focused — one procedure, one concern.
- Organize files by business feature:
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
- XML documentation comments on all global procedures.
- Comments explain WHY, not WHAT.

### Performance Patterns

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

### Upgrade Code Rules

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

## Review Checklist

| # | Check | Category |
|---|-------|----------|
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
| 16 | `IsHandled` pattern where override is intended | Events |
| 17 | Subscriber-only codeunits use `Handler` suffix | Events |
| 18 | Test files only in Test project | Testing |
| 19 | Given/When/Then test names | Testing |
| 20 | Library codeunits for test data | Testing |
| 21 | No direct implementation in upgrade triggers | Upgrade |
| 22 | Upgrade database reads protected with `if` | Upgrade |
| 23 | Upgrade Tags used instead of version checks | Upgrade |
| 24 | DataTransfer for large table upgrades | Upgrade |
| 25 | New `InitValue` fields have upgrade code when needed | Upgrade |
