---
name: bc365-permissionset
description: Create, analyze, and manage Microsoft Dynamics 365 Business Central (BC365) permission sets. Generates import-ready Tenant XML files and AL extension permission set objects from job-role requirements. Use when the user needs to create, analyze, or review BC365 permission sets.
---

# BC365 Permission Set Creator & Analyzer

## Workflow

1. Interpret the requested job role and scope: department, tasks, read/edit/posting needs, and any excluded areas.
2. Prefer including existing system permission sets over listing many object permissions manually.
3. Start every importable tenant permission set with `LOGIN` unless the user gives a complete alternative.
4. Add direct object permissions only for gaps that included sets do not cover.
5. Use `generate_permission_xml.py` (JSON-spec-driven) for validated XML generation, or `bc365_permission_creator.py` (CLI-driven) for quick create/analyze. Both live in `${CLAUDE_PLUGIN_ROOT}/skills/bc365-permissionset/scripts/` and need only Python 3 (standard library); run them with `python` or `uv run python`.
6. Parse the XML result before delivering it.
7. Tell the user that duplicate Role IDs during import depend on the BC import choice: update/merge or skip.

## Required XML Shape

```xml
<?xml version="1.0" encoding="utf-8"?>
<PermissionSets Version="2.0">
  <TenantPermissionSet RoleID="SALES_DEPT" RoleName="Sales Department" Assignable="Yes">
    <TenantPermissionSetRel>
      <ObjectType>Include</ObjectType>
      <ObjectRelatedScope>System</ObjectRelatedScope>
      <ObjectRelatedRoleId>LOGIN</ObjectRelatedRoleId>
      <ObjectRelatedAppId>{63ca2fa4-4f03-4f2b-a480-172fef340d3f}</ObjectRelatedAppId>
    </TenantPermissionSetRel>
  </TenantPermissionSet>
</PermissionSets>
```

For full schema details and examples, read `${CLAUDE_PLUGIN_ROOT}/skills/bc365-permissionset/references/permission_xml.md`.

## Guardrails

- Keep `RoleID` at 20 characters or fewer. Use uppercase, digits, and underscores.
- Do not generate `SUPER`.
- Do not grant write permissions on security-sensitive tables unless user explicitly requests and understands the risk.
- For tenant XML: use `TenantPermissionSet`, `TenantPermissionSetRel`, and `TenantPermission`.
- For included system sets: set `ObjectRelatedScope` to `System`.
- Use `PermissionType` value `Include` on every `TenantPermission`.
- Use `Yes` for direct permissions by default. Use `Indirect` only when user requests it or the task requires indirect access.

## Common System App IDs

- `LOGIN`, `SYSTEM APP - BASIC`, System Application sets: `{63ca2fa4-4f03-4f2b-a480-172fef340d3f}`
- Base Application sets (`D365 BASIC`, `D365 SALES DOC, EDIT`, `D365 CUSTOMER, EDIT`, etc.): `{437dbf0e-84ff-417a-965d-ed2bb9650972}`

## Utility Scripts

`<scripts>` below is `${CLAUDE_PLUGIN_ROOT}/skills/bc365-permissionset/scripts`.

### 1. Generate XML from JSON spec (validated)
```bash
python "<scripts>/generate_permission_xml.py" --input "spec.json" --output "MyRole.xml"
```
JSON spec shape:
```json
{
  "role_id": "SALES_DEPT",
  "role_name": "Sales Department",
  "includes": ["LOGIN", "D365 BASIC"],
  "permissions": [
    {"object_type": "Table Data", "object_id": 36, "ReadPermission": "Yes", "InsertPermission": "Yes"}
  ]
}
```

### 2. Analyze existing XML file
```bash
python "<scripts>/bc365_permission_creator.py" analyze --input "PermissionSets.xml" --output "summary.json"
```

### 3. Create Tenant XML (quick CLI)
```bash
python "<scripts>/bc365_permission_creator.py" create-xml --role-id "MY_ROLE" --role-name "My Role" --include-system-roles "LOGIN,D365 BASIC" --output "MyRole.xml"
```

### 4. Create AL permission set object
```bash
python "<scripts>/bc365_permission_creator.py" create-al --role-id "MY_ROLE" --role-name "My Role" --include-system-roles "LOGIN,D365 BASIC" --object-id 77001 --output "MyRole.permissionset.al"
```
Get `--object-id` from `al_getnextobjectid` (`objectType: "PermissionSet"`) when the AL MCP
server is connected; otherwise pick a free ID inside `app.json` `idRanges`. Without it the
script uses 50100, which is outside most apps' ranges.

## Reference Data

Use `${CLAUDE_PLUGIN_ROOT}/skills/bc365-permissionset/references/BC365_PermissionSets_Summary.csv` for Role ID, Role Name, Source, and Thai descriptions (exported from BC 28).

If the user provides full exports from their own tenant (for example `SystemPermissionSets.xml` for standard sets and app IDs, or `UserDefinedPermissionSets.xml` for existing tenant sets), prefer them over the bundled summary.

## Common Mistakes

1. Using `<PermissionSetRel>` instead of `<TenantPermissionSetRel>` in user-defined XML.
2. Missing `LOGIN` — always include or bundle it.
3. Invalid JSON formatting when passing `--object-permissions` on the CLI.

## Output

Deliver either:
- A complete XML file in the workspace when the user asks for a file.
- A concise fenced `xml` block when the user asks for content only.

Include a brief import note: open **Permission Sets** > **Import Permission Sets**, select the XML file, choose whether to update/merge or skip existing matching sets.
